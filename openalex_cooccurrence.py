#!/usr/bin/env python3
"""使用 OpenAlex fulltext 高级检索统计两个公式名称在论文中的共现。"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable

BASE_URL = "https://api.openalex.org/works"
DEFAULT_MAILTO = "your_email@example.com"
PER_PAGE = 200


@dataclass(frozen=True)
class FormulaPair:
    left: str
    right: str


DEFAULT_PAIRS: list[FormulaPair] = [
    FormulaPair("transverse mass", "Euclidean norm (L2 norm)"),
    FormulaPair(
        "Net demand for product p in country i",
        "Net demand for product p in country i",
    ),
    FormulaPair("forward-backward asymmetry", "asymmetry index"),
    FormulaPair(
        "bidoublet field",
        "conjugate transpose of the unitary operator",
    ),
    FormulaPair(
        "adjoint of a product of operators",
        "adjoint of a composition of linear operators",
    ),
    FormulaPair("cross-spectrum estimator", "average potential outcome estimator"),
    FormulaPair("d-type form factor", "helpful generalized Lee bound"),
    FormulaPair(
        "Polarization sum rule for W boson polarization vectors",
        "Exchangeability condition for the error term",
    ),
    FormulaPair("n-dimensional unit simplex", "unit simplex in N dimensions"),
    FormulaPair("n-dimensional standard simplex", "probability simplex"),
]


def build_fulltext_query(left: str, right: str) -> str:
    """构造 fulltext.search 高级检索表达式（大小写不敏感）。"""
    # OpenAlex 搜索默认大小写不敏感；这里使用双引号+AND 强制同时包含。
    return f'"{left}" AND "{right}"'


def openalex_get(url: str, retries: int = 4, sleep_s: float = 1.5) -> dict:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return json.load(resp)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries - 1:
                time.sleep(sleep_s * (attempt + 1))
    raise RuntimeError(f"请求失败: {url}\n错误: {last_error}")


def fetch_pair_results(pair: FormulaPair, mailto: str) -> tuple[int, list[dict[str, str]]]:
    query = build_fulltext_query(pair.left, pair.right)
    cursor = "*"
    count = 0
    works: list[dict[str, str]] = []

    while cursor:
        params = {
            "filter": f"fulltext.search:{query}",
            "per-page": str(PER_PAGE),
            "cursor": cursor,
            "mailto": mailto,
            "select": "id,doi,display_name,publication_year,primary_location",
        }
        url = BASE_URL + "?" + urllib.parse.urlencode(params)
        data = openalex_get(url)

        if count == 0:
            count = int(data.get("meta", {}).get("count", 0))

        for item in data.get("results", []):
            source = (
                (item.get("primary_location") or {}).get("source") or {}
            ).get("display_name")
            works.append(
                {
                    "pair_left": pair.left,
                    "pair_right": pair.right,
                    "work_id": item.get("id", ""),
                    "title": item.get("display_name", ""),
                    "year": str(item.get("publication_year", "")),
                    "doi": item.get("doi", ""),
                    "venue": source or "",
                }
            )

        next_cursor = data.get("meta", {}).get("next_cursor")
        cursor = next_cursor if next_cursor else ""

        if not data.get("results"):
            break

    return count, works


def write_outputs(summary_rows: Iterable[dict[str, str]], works_rows: Iterable[dict[str, str]]) -> None:
    with open("cooccurrence_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["pair_left", "pair_right", "cooccurrence_count"],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    with open("cooccurrence_works.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["pair_left", "pair_right", "work_id", "title", "year", "doi", "venue"],
        )
        writer.writeheader()
        writer.writerows(works_rows)


def main() -> int:
    mailto = DEFAULT_MAILTO
    if len(sys.argv) > 1:
        mailto = sys.argv[1].strip()

    summary: list[dict[str, str]] = []
    all_works: list[dict[str, str]] = []

    for idx, pair in enumerate(DEFAULT_PAIRS, start=1):
        print(f"[{idx}/{len(DEFAULT_PAIRS)}] 查询: {pair.left}  +  {pair.right}")
        try:
            count, works = fetch_pair_results(pair, mailto)
        except Exception as exc:  # noqa: BLE001
            print(f"  查询失败: {exc}")
            count, works = 0, []

        summary.append(
            {
                "pair_left": pair.left,
                "pair_right": pair.right,
                "cooccurrence_count": str(count),
            }
        )
        all_works.extend(works)
        print(f"  共现论文数: {count}")

    write_outputs(summary, all_works)
    print("\n已输出:")
    print("- cooccurrence_summary.csv（每组公式共现次数）")
    print("- cooccurrence_works.csv（共现论文明细）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
