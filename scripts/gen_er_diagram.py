#!/usr/bin/env python3
"""gen_er_diagram.py — 从可执行 DDL 生成 ER 图（Mermaid）

依 ADR-0005，ER 图是**生成物**。改 DDL 后重新运行本脚本。

    python scripts/gen_er_diagram.py

输出 docs/er-diagram.md —— GitHub 原生渲染 Mermaid。

关于外键
--------
DuckDB 契约**不声明 FOREIGN KEY**（上游的建表语句里没有，本项目也不加）。
因此下图中的关系是按**共享键**推断的，分为两类：

* **实线** —— 显式定义的关系（见 :data:`RELATIONS`）
* **虚线** —— 共享 ``thscode`` 或 ``(thscode, date)`` 推断的关系

这些是**约定**，不是数据库强制的完整性约束。
"""

from __future__ import annotations

import sys
from pathlib import Path

from schema.ddl import _CREATE_RE, DOMAINS, _unquote, column_types, primary_key_of

DOC_OUT = Path(__file__).resolve().parent.parent / "docs" / "er-diagram.md"

DOMAIN_TITLE = {
    "market": "行情", "financials": "财报", "index": "指数",
    "fund": "基金", "futures": "期货", "special": "特色数据",
    "indicators": "指标",
}

#: 显式定义的关系：(子表, 父表, 连接键, 说明)
RELATIONS: list[tuple[str, str, str, str]] = [
    ("raw_kline_daily", "dim_symbol", "thscode", "行情 → 证券目录"),
    ("calc_adjust_factor_daily", "raw_kline_daily", "thscode, date", "复权因子 → 行情（同键）"),
    ("raw_adjustment_events", "dim_symbol", "thscode", "除权事件 → 证券目录"),
    ("raw_valuation_snapshot", "dim_symbol", "thscode", "估值快照 → 证券目录"),
    ("raw_financial_indicators", "dim_symbol", "thscode", "财务指标 → 证券目录"),
    ("raw_financial_indicators_detail", "dim_symbol", "thscode", "财务指标明细 → 证券目录"),
    ("v_indicators_daily", "raw_kline_daily", "thscode, date", "指标宽表 → 行情"),
]

HEADER = """\
# ER 图

<!-- 本文件由 scripts/gen_er_diagram.py 生成，请勿手工编辑。 -->

数据契约的实体关系图，全部从 [`schema/*.sql`](../schema) 推导。

> **关于外键**：数据契约**不声明 `FOREIGN KEY`**。下图中的关系是按共享键
> 推断的约定，不是数据库强制的完整性约束 —— DuckDB 也不强制主键。
> 实线是显式定义的关系，虚线是共享 `thscode` / `(thscode, date)` 推断的。
>
> 需要真实的约束保证时，请在你自己实现的 writer 里加校验。
"""

#: 记账表 —— 结构在每个域里都一样，不参与 ER 图
BOOKKEEPING = {"_meta", "_import_batches"}


def main() -> int:
    out = [HEADER]

    # --- 全局：核心契约 ---------------------------------------------------------
    out.append("\n## 核心契约\n")
    out.append("指标引擎只依赖这三张表。任何能产出它们的 Ingestor 都能接入。\n")
    out.append("```mermaid")
    out.append("erDiagram")
    for t in ("dim_symbol", "raw_kline_daily", "calc_adjust_factor_daily"):
        pk = set(primary_key_of(t))
        out.append(f"    {t} {{")
        for col, typ in column_types(t):
            key = "PK " if col in pk else ""
            out.append(f"        {typ.replace(' ', '_')} {key}{col}")
        out.append("    }")
    out.append("    dim_symbol ||--o{ raw_kline_daily : thscode")
    out.append("    raw_kline_daily ||--|| calc_adjust_factor_daily : \"thscode, date\"")
    out.append("```")
    out.append(
        "\n核心恒等式（`v_daily_qfq` 的定义）：\n"
        "\n```\nclose * forward_factor == 前复权收盘价\n```\n"
    )

    # --- 逐域 -----------------------------------------------------------------
    doc_dir = Path(__file__).resolve().parent.parent / "schema"
    for domain in DOMAINS:
        text = (doc_dir / f"{domain}.sql").read_text()
        tables = [
            _unquote(m.group("name"))
            for m in _CREATE_RE.finditer(text)
            if _unquote(m.group("name")) not in BOOKKEEPING
        ]
        if not tables:
            continue

        out.append(f"\n## {DOMAIN_TITLE.get(domain, domain)}（`{domain}`）\n")
        out.append(f"{len(tables)} 张表。\n")
        out.append("```mermaid")
        out.append("erDiagram")
        for t in sorted(tables):
            pk = set(primary_key_of(t))
            out.append(f"    {t} {{")
            for col, typ in column_types(t):
                key = "PK " if col in pk else ""
                out.append(f"        {typ.replace(' ', '_')} {key}{col}")
            out.append("    }")
        for child, parent, keys, _ in RELATIONS:
            if child in tables and parent in tables:
                out.append(f'    {parent} ||--o{{ {child} : "{keys}"')
        out.append("```")

    # --- 推断关系清单 ---------------------------------------------------------
    out.append("\n## 推断关系清单\n")
    out.append("| 子表 | 父表 | 连接键 | 说明 |")
    out.append("|---|---|---|---|")
    for child, parent, keys, note in RELATIONS:
        out.append(f"| `{child}` | `{parent}` | `{keys}` | {note} |")

    out.append(
        "\n> 每一行都可以用一句 SQL 验证：\n"
        ">\n"
        "> ```sql\n"
        "> SELECT count(*)\n"
        "> FROM child c LEFT JOIN parent p USING (<连接键>)\n"
        "> WHERE p.<主键> IS NULL;   -- 应为 0\n"
        "> ```\n"
    )

    DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUT.write_text("\n".join(out) + "\n")
    print(f"已写入 {DOC_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
