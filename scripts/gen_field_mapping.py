#!/usr/bin/env python3
"""gen_field_mapping.py — 从历史采集脚本抽取「上游字段 -> 契约列」映射

**这是一次性迁移工具**，不是日常构建步骤。

上游数据契约的字段映射原本散落在 ``~/.hithink-finance/scripts/*_db.py`` 的
``hfkit.upsert(...)`` 调用里 —— 那批代码是本项目作者自己的，但不在本仓库中。
本脚本用 AST 解析（不是正则，避免字符串/注释误判）把它们抽出来，生成
``docs/field-mapping.md``。

    python scripts/gen_field_mapping.py [--src ~/.hithink-finance/scripts]

无法静态解析的取值表达式不会被猜测，一律标为「需人工确认」。
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
from pathlib import Path

DOC_OUT = Path(__file__).resolve().parent.parent / "docs" / "field-mapping.md"

HEADER = """\
# 字段映射：上游字段 -> 数据契约列

<!-- 本文件由 scripts/gen_field_mapping.py 生成，请勿手工编辑。 -->

本文件是自建 Ingestor 的直接依据：给定一个数据源，按这里的映射把它的字段
落到契约列上即可。目标列的定义以 [`schema/*.sql`](../schema) 为准。

**「转换」列的记法**

| 记法 | 含义 |
|---|---|
| `直接取` | 上游同名字段，直接取值 |
| `常量` | 固定值，与数据源无关 |
| `表达式` | 需要转换，见备注 |
| `需人工确认` | 静态解析不出来，**请自行判断**，不要照抄 |

> 标为「需人工确认」的条目占少数。这些多半是跨表派生或复杂计算，
> 不同数据源的处理方式可能不同，抄错会静默产出错误数据。
"""


def _expr_desc(node: ast.AST) -> tuple[str, str]:
    """返回 (来源说明, 转换说明)。无法解析时来源为 '需人工确认'。"""
    if isinstance(node, ast.Constant):
        return ("常量", repr(node.value))

    if isinstance(node, ast.Call):
        func = node.func
        # item.get("x") / d.get("x") / payload.get("x")
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            src = node.args[0].value
            owner = ""
            if isinstance(func.value, ast.Name):
                owner = func.value.id
            elif isinstance(func.value, ast.Attribute):
                owner = func.value.attr
            return (f"直接取 `{src}`" + (f"（来自 `{owner}`）" if owner else ""), "")
        # hfkit.xxx(...) / ms_to_date(...)
        name = ""
        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        args = [a.value for a in node.args if isinstance(a, ast.Constant)]
        return (f"经 `{name}()` 转换", f"参数 {args}" if args else "")

    if isinstance(node, ast.Attribute):
        return (f"经属性 `{node.attr}`", "")

    if isinstance(node, ast.Name):
        return (f"变量 `{node.id}`", "")

    if isinstance(node, ast.BinOp):
        return ("表达式", ast.unparse(node)[:80])

    if isinstance(node, ast.IfExp):
        return ("表达式", ast.unparse(node)[:80])

    return ("需人工确认", ast.unparse(node)[:80] if hasattr(ast, "unparse") else "")


def extract_file(path: Path) -> list[tuple[str, str, str, str]]:
    """返回 [(表名, 目标列, 来源, 转换)]。"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        print(f"  ! 跳过 {path.name}: {exc}", file=sys.stderr)
        return []

    rows: list[tuple[str, str, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        fname = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
        if fname != "upsert" or len(node.args) < 3:
            continue

        # hfkit.upsert(con, table, cols, rows, [pk])
        table_node = node.args[1]
        if not isinstance(table_node, ast.Constant):
            continue
        table = str(table_node.value)
        if not table or table.startswith("_"):
            continue  # 跳过 _meta / _import_batches 等记账表

        cols_node = node.args[2]
        if not isinstance(cols_node, (ast.List, ast.Tuple)):
            continue
        cols = [e.value for e in cols_node.elts if isinstance(e, ast.Constant)]

        rows_node = node.args[3] if len(node.args) > 3 else None
        if not isinstance(rows_node, (ast.List, ast.Tuple)):
            continue

        for row in rows_node.elts:
            if not isinstance(row, (ast.Tuple, ast.List)):
                continue
            for col, val in zip(cols, row.elts):
                src, note = _expr_desc(val)
                rows.append((table, col, src, note))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="从历史采集脚本抽取字段映射")
    ap.add_argument("--src", default=str(Path.home() / ".hithink-finance" / "scripts"))
    args = ap.parse_args()

    src = Path(os.path.expanduser(args.src))
    if not src.is_dir():
        print(f"源目录不存在: {src}", file=sys.stderr)
        return 1

    by_table: dict[str, dict[str, tuple[str, str]]] = {}
    for py in sorted(src.glob("*_db.py")):
        for table, col, source, note in extract_file(py):
            by_table.setdefault(table, {}).setdefault(col, (source, note))

    unknown = sum(
        1
        for cols in by_table.values()
        for s, _ in cols.values()
        if s == "需人工确认"
    )
    total = sum(len(c) for c in by_table.values())

    out = [HEADER, f"\n共抽取 **{total}** 条映射，覆盖 **{len(by_table)}** 张表"
           f"（其中 {unknown} 条需人工确认）。\n"]
    for table in sorted(by_table):
        out.append(f"\n## `{table}`\n")
        out.append("| 契约列 | 上游来源 | 转换 |")
        out.append("|---|---|---|")
        for col, (source, note) in sorted(by_table[table].items()):
            out.append(f"| `{col}` | {source} | {note or '—'} |")

    DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUT.write_text("\n".join(out) + "\n")
    print(f"已写入 {DOC_OUT}：{total} 条映射 / {len(by_table)} 张表 / {unknown} 条待人工确认")
    return 0


if __name__ == "__main__":
    sys.exit(main())
