#!/usr/bin/env python3
"""gen_field_dictionary.py — 从可执行 DDL 生成字段字典

依 [ADR-0005](../../docs/adr/0005-ddl-as-contract-source-of-truth.md)，
字段字典是**生成物**，不是手写文档。改 DDL 后重新运行本脚本。

    python scripts/gen_field_dictionary.py

输出 docs/field-dictionary.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from schema.ddl import _CREATE_RE, DOMAINS, _unquote, column_types, primary_key_of

DOC_OUT = Path(__file__).resolve().parent.parent / "docs" / "field-dictionary.md"

DOMAIN_TITLE = {
    "market": "行情",
    "financials": "财报",
    "index": "指数",
    "fund": "基金",
    "futures": "期货",
    "special": "特色数据",
    "indicators": "指标",
}

HEADER = """\
# 字段字典

<!-- 本文件由 scripts/gen_field_dictionary.py 生成，请勿手工编辑。 -->

数据契约的字段字典，全部从 [`schema/*.sql`](../schema) 推导，无手工维护成分。
改 DDL 后重新运行生成器。

术语定义见 [`CONTEXT.md`](../CONTEXT.md)。

> **关于主键**：DuckDB 不强制主键约束，表中的「PK」标记表达的是
> 「这一组列应当唯一」的设计意图，不等于唯一性被数据库保证。
> 详见 [`schema/README.md`](../schema/README.md)。
"""

COLUMN_NOTES = {
    "thscode": "同花顺证券标识符，跨数据域通用主键",
    "date": "交易日",
    "open": "开盘价（未复权）",
    "high": "最高价（未复权）",
    "low": "最低价（未复权）",
    "close": "收盘价（未复权）",
    "volume": "成交量（股）",
    "turnover": "成交额（原始货币）",
    "currency": "币种；A 股恒为 CNY",
    "interval": "K 线周期，本项目仅 `1d`",
    "adjusted": "价格口径；`raw_*` 表恒为 `none`（未复权）",
    "forward_factor": "前复权因子；`close * forward_factor` = 前复权收盘价",
    "backward_factor": "后复权因子；`close * backward_factor` = 后复权收盘价",
    "source_batch_id": "溯源：写入该行的批次号，见 `_import_batches`",
    "raw_payload": "上游响应的原样留存（JSON）",
    "captured_at": "落库时刻",
}


def main() -> int:
    doc = Path(__file__).resolve().parent.parent / "schema"
    out = [HEADER]
    grand_tables = 0
    grand_cols = 0

    for domain in DOMAINS:
        text = (doc / f"{domain}.sql").read_text()
        tables = [_unquote(m.group("name")) for m in _CREATE_RE.finditer(text)]
        views = re.findall(r"CREATE\s+VIEW\s+(\w+)\s+AS", text, re.IGNORECASE)
        if not tables and not views:
            continue

        out.append(f"\n## {DOMAIN_TITLE.get(domain, domain)}（`{domain}`）\n")
        out.append(f"{len(tables)} 张基表 / {len(views)} 个视图\n")

        for table in sorted(tables):
            cols = column_types(table)
            pk = set(primary_key_of(table))
            grand_tables += 1
            grand_cols += len(cols)
            out.append(f"\n### `{table}`\n")
            out.append("| 列 | 类型 | 说明 |")
            out.append("|---|---|---|")
            for col, typ in cols:
                mark = " **PK**" if col in pk else ""
                note = COLUMN_NOTES.get(col, "")
                out.append(f"| `{col}`{mark} | `{typ}` | {note} |")

        if views:
            out.append(f"\n视图（只读面，定义见 `schema/{domain}.sql`）：")
            out.append("")
            for v in sorted(views):
                out.append(f"- `{v}`")
            out.append("")

    out.append(f"\n---\n共 **{grand_tables}** 张基表、**{grand_cols}** 个基表列。\n")

    DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUT.write_text("\n".join(out) + "\n")
    print(f"已写入 {DOC_OUT}：{grand_tables} 张表 / {grand_cols} 列")
    return 0


if __name__ == "__main__":
    sys.exit(main())
