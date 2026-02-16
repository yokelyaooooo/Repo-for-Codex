# OpenAlex 公式共现检索脚本

该仓库提供 `openalex_cooccurrence.py`，用于调用 OpenAlex API 的 `fulltext.search` 高级检索，统计两个公式名称在论文全文中的共现情况。

## 功能

- 使用 `"公式A" AND "公式B"` 的高级检索表达式。
- 默认对给定的 10 组公式名逐组查询。
- 输出：
  - `cooccurrence_summary.csv`：每组公式的共现总次数。
  - `cooccurrence_works.csv`：共现论文明细（标题、年份、DOI、来源等）。
- OpenAlex 搜索默认大小写不敏感，因此满足“忽略公式名称大小写”要求。

## 运行

```bash
python openalex_cooccurrence.py your_email@example.com
```

> 建议传入有效邮箱（OpenAlex 推荐）。若不传，脚本会使用默认占位邮箱。

## 说明

如果运行环境无法访问 `https://api.openalex.org`，脚本会在每组查询上打印错误并继续执行，最终仍生成 CSV（该组结果为 0）。
