#!/usr/bin/env python3
"""export_schema.py — 从已建库反向导出数据契约 DDL

ADR-0005 规定：可执行 DDL 是数据契约的唯一事实源，文档产物由它生成。
本脚本负责**重新生成** DDL，并可校验已提交的 DDL 是否与现存库一致。

    python scripts/export_schema.py           # 导出到 schema/*.sql
    python scripts/export_schema.py --check   # 只校验，不写（CI 用）

只读打开源库，不做任何写入。

各数据域的 DDL 来源不同：

    market / financials / index / fund / futures / special
        从现存库的 duckdb_tables() / duckdb_views() 取原始 CREATE 语句。

    indicators
        从 indicators_config.yaml 生成（schema.indicators_schema.generate_create_table），
        因为该表是本项目自己的计算产物，其 DDL 由配置推导而非人工维护。
        本脚本会同时与现存库比对，两者必须一致。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

from paths import FUYAO_HOME, INDICATORS_CONFIG
from schema.indicators_schema import generate_create_table

# 数据域 -> 源库文件名。indicators 特殊处理，不走这个映射。
DOMAINS = {
    "market": "market.duckdb",
    "financials": "financials.duckdb",
    "index": "index.duckdb",
    "fund": "fund.duckdb",
    "futures": "futures.duckdb",
    "special": "special.duckdb",
}
INDICATORS_DOMAIN = "indicators"
ALL_DOMAINS = [*DOMAINS, INDICATORS_DOMAIN]

# 由专用脚本独占维护、不经 indicators_config.yaml 推导的列。
# 校验 config 推导结果时，这些列允许存在于线上表但不在 config 里。
# 任何新增都必须在此登记，否则 verify() 会报"未登记为脚本独占"。
#
# RSL 为何走脚本：config 的列名由单一 params 推导（indicator/compute.py 的
# _make_col_prefix），而 RSL 需要两组数字 —— pct_change 回看周期(3/21) 与
# 排名窗口(15/105) 不相等，产不出 zettaranc_rsl_rank_15 这个名字。
# 详见 indicators_config.yaml 中 zettaranc: 类目的注释。
SCRIPT_OWNED_COLUMNS = {
    "v_indicators_daily": {
        "zettaranc_rsl_rank_15",    # scripts/add_zettaranc_columns.py
        "zettaranc_rsl_rank_105",
    },
}

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"

HEADER = """\
-- =============================================================================
-- {domain} 数据域
-- =============================================================================
-- 本文件由 scripts/export_schema.py 自动生成，请勿手工编辑。
-- 改动请改源库结构或 indicators_config.yaml，然后重新运行导出。
--
-- 导出时间基准：见 git 历史。源库中未包含任何数据行，仅含结构定义。
-- 数据版权归上游服务方所有，本项目不分发任何数据（见 docs/adr/0001）。
-- =============================================================================

"""


def _fail(msg: str) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


def read_domain(domain: str, db_path: Path) -> tuple[list[str], list[str]]:
    """返回 (CREATE TABLE 语句列表, CREATE VIEW 语句列表)。"""
    if not db_path.exists():
        _fail(f"源库不存在: {db_path}")

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = [
            r[0]
            for r in con.execute(
                "SELECT sql FROM duckdb_tables() "
                "WHERE NOT internal AND schema_name='main' ORDER BY table_name"
            ).fetchall()
        ]
        views = [
            r[0]
            for r in con.execute(
                "SELECT sql FROM duckdb_views() "
                "WHERE NOT internal AND schema_name='main' ORDER BY view_name"
            ).fetchall()
        ]
    finally:
        con.close()

    # 视图可能依赖基表或其他视图。在探测库里先建全部基表，再迭代建视图，
    # 每轮成功的移出待建列表 —— 循环结束时即得到拓扑序。
    probe = duckdb.connect(":memory:")
    try:
        for t in tables:
            probe.execute(t)

        ordered: list[str] = []
        pending = views
        while pending:
            still_pending = []
            for stmt in pending:
                try:
                    probe.execute(stmt)
                    ordered.append(stmt)
                except duckdb.Error:
                    still_pending.append(stmt)
            if len(still_pending) == len(pending):
                _fail(
                    f"{domain}: 以下视图无法创建（可能引用了库外对象）:\n"
                    + "\n".join("  " + _view_name(s) for s in still_pending)
                )
            pending = still_pending
    finally:
        probe.close()

    return tables, ordered


def _view_name(stmt: str) -> str:
    head = stmt.split(" AS ", 1)[0]
    return head.replace("CREATE VIEW", "").strip()


def _indicators_ddl() -> str:
    import yaml

    cfg = yaml.safe_load(INDICATORS_CONFIG.read_text())
    # generate_create_table 已带结尾分号，先剥掉再统一补一个，
    # 否则会产出 `));;` 导致下游 DDL 解析器漏掉这张表。
    return generate_create_table(cfg).strip().rstrip(";") + ";"


def build() -> dict[str, str]:
    """生成 {数据域: DDL 文本}。"""
    out: dict[str, str] = {}

    for domain, fname in DOMAINS.items():
        tables, views = read_domain(domain, FUYAO_HOME / fname)
        parts = [HEADER.format(domain=domain), f"-- 基表 {len(tables)} 张 / 视图 {len(views)} 个\n"]
        if tables:
            parts.append("\n-- ---------- 基表 ----------\n")
            parts.append("\n\n".join(t.rstrip(";") + ";" for t in tables))
        if views:
            parts.append("\n\n-- ---------- 视图 ----------\n")
            parts.append("\n\n".join(v.rstrip(";") + ";" for v in views))
        out[domain] = "\n".join(parts) + "\n"

    out[INDICATORS_DOMAIN] = (
        HEADER.format(domain=INDICATORS_DOMAIN)
        + "-- 本域 DDL 由 indicators_config.yaml 推导生成。\n"
        + "-- 修改列 / 参数 / 后端请改 config，然后重新导出。\n\n"
        + _indicators_ddl()
        + "\n"
    )
    return out


def _strip_comments(sql: str) -> str:
    return "\n".join(
        ln for ln in sql.splitlines() if not ln.strip().startswith("--")
    ).strip()


def _apply(sql: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    for stmt in _split_statements(_strip_comments(sql)):
        con.execute(stmt)
    return con


def _split_statements(sql: str) -> list[str]:
    """按分号切分。DDL 中不含字面量分号，足够安全。"""
    return [s.strip() for s in sql.split(";") if s.strip()]


def _columns(con: duckdb.DuckDBPyConnection, name: str) -> set[str]:
    return {
        r[0]
        for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = ? AND table_schema = 'main'",
            [name],
        ).fetchall()
    }


def verify(files: dict[str, str]) -> list[str]:
    """把导出的 DDL 灌进干净内存库，与现存库逐对象比对列集合。"""
    problems: list[str] = []

    for domain, fname in DOMAINS.items():
        con = _apply(files[domain])
        live = duckdb.connect(str(FUYAO_HOME / fname), read_only=True)
        try:
            for (tbl,) in live.execute(
                "SELECT table_name FROM duckdb_tables() "
                "WHERE NOT internal AND schema_name='main' ORDER BY table_name"
            ).fetchall():
                got, want = _columns(con, tbl), _columns(live, tbl)
                if not want:
                    problems.append(f"{domain}: DDL 缺少基表 {tbl}")
                elif got != want:
                    miss, extra = want - got, got - want
                    problems.append(
                        f"{domain}.{tbl}: 列不一致"
                        + (f" 缺 {sorted(miss)}" if miss else "")
                        + (f" 多 {sorted(extra)}" if extra else "")
                    )
            for (vw,) in live.execute(
                "SELECT view_name FROM duckdb_views() "
                "WHERE NOT internal AND schema_name='main' ORDER BY view_name"
            ).fetchall():
                got, want = _columns(con, vw), _columns(live, vw)
                if not want:
                    problems.append(f"{domain}: DDL 缺少视图 {vw}")
                elif got != want:
                    miss, extra = want - got, got - want
                    problems.append(
                        f"{domain}.{vw}: 列不一致"
                        + (f" 缺 {sorted(miss)}" if miss else "")
                        + (f" 多 {sorted(extra)}" if extra else "")
                    )
        finally:
            live.close()
            con.close()

    # indicators: 与线上表逐列比对。
    #
    # 语义与其它数据域不同：config 推导出的列必须是线上表的**子集**
    # （config 不得声称线上不存在的列），但线上表可以多出由专用脚本维护的列。
    con = _apply(files[INDICATORS_DOMAIN])
    live = duckdb.connect(str(FUYAO_HOME / "indicators.duckdb"), read_only=True)
    try:
        tbl = "v_indicators_daily"
        want, have = _columns(con, tbl), _columns(live, tbl)
        # 由 scripts/add_zettaranc_columns.py 独占维护、不经 config 推导的列。
        script_owned = SCRIPT_OWNED_COLUMNS.get(tbl, set())
        for col in sorted(want - have):
            problems.append(
                f"indicators.{tbl}: config 推导出线上不存在的列 {col} "
                f"—— config 不得声称线上没有的列"
            )
        for col in sorted(have - want - script_owned):
            problems.append(
                f"indicators.{tbl}: 线上有列 {col} 既非 config 推导、"
                f"也未登记为脚本独占 —— 若确为脚本维护，请登记到 SCRIPT_OWNED_COLUMNS"
            )
    finally:
        live.close()
        con.close()

    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="导出 / 校验数据契约 DDL")
    ap.add_argument("--check", action="store_true", help="只校验，不写文件")
    args = ap.parse_args()

    files = build()

    print(f"[1/3] 已生成 {len(files)} 个数据域的 DDL")
    for domain in ALL_DOMAINS:
        target = SCHEMA_DIR / f"{domain}.sql"
        state = "已更新" if target.exists() and target.read_text() != files[domain] else "无变化"
        if not target.exists():
            state = "新建"
        print(f"      {domain:12} {len(files[domain]):>7,} 字符  {target.name}  [{state}]")

    print("[2/3] 在干净内存库中执行 DDL 并与现存库比对")
    problems = verify(files)
    if problems:
        print(f"      发现 {len(problems)} 处不一致：")
        for p in problems:
            print(f"        - {p}")
        return 1
    print("      ✓ 全部一致")

    if args.check:
        print("[3/3] --check 模式：不写文件")
        drift = [
            d
            for d in ALL_DOMAINS
            if (SCHEMA_DIR / f"{d}.sql").exists()
            and (SCHEMA_DIR / f"{d}.sql").read_text() != files[d]
        ]
        if drift:
            print(f"      ✗ 以下数据域的 DDL 与现存库不同步: {drift}")
            print("        运行 `python scripts/export_schema.py` 重新导出。")
            return 1
        print("      ✓ 已提交的 DDL 与现存库同步")
        return 0

    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for domain, text in files.items():
        (SCHEMA_DIR / f"{domain}.sql").write_text(text)
    print("[3/3] 已写入 schema/*.sql")
    return 0


if __name__ == "__main__":
    sys.exit(main())
