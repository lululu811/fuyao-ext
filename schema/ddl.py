"""schema/ddl.py — 从可执行 DDL 解析目标表列定义

依 [ADR-0005](../../docs/adr/0005-ddl-as-contract-source-of-truth.md)，
``schema/*.sql`` 是数据契约的唯一事实源。writer 需要知道每张目标表有哪些列、
按什么顺序写入 —— 这些信息不应在 Python 里重抄一遍，因此从 DDL 解析。

用法::

    from schema.ddl import TARGET_COLUMNS, primary_key_of, table_columns
    TARGET_COLUMNS["raw_kline_daily"]
    # ['thscode', 'date', 'open', ...]
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent

#: 需要解析的数据域
DOMAINS = ("market", "financials", "index", "fund", "futures", "special", "indicators")

_CREATE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[\w\"]+)\s*\((?P<body>.*?)\)\s*;+",
    re.IGNORECASE | re.DOTALL,
)


def _split_top_level(body: str) -> list[str]:
    """按顶层逗号切分建表体，忽略括号与引号内的逗号。"""
    parts, buf, depth, in_quote = [], [], 0, False
    for ch in body:
        if ch == '"':
            in_quote = not in_quote
        elif not in_quote and ch == "(":
            depth += 1
        elif not in_quote and ch == ")":
            depth -= 1
        if ch == "," and depth == 0 and not in_quote:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return [p for p in parts if p]


def _unquote(name: str) -> str:
    name = name.strip()
    return name[1:-1] if name.startswith('"') and name.endswith('"') else name


@lru_cache(maxsize=1)
def _parse() -> dict[str, list[str]]:
    """{表名: [列名...]}，跨全部数据域。

    表名只在**数据域内**唯一 —— ``_meta`` 与 ``_import_batches`` 在 6 个域里
    同名。这里按表名聚合，聚合时校验各域的列定义是否一致；不一致则抛错，
    因为那意味着按表名取列定义会产生歧义，必须显式消歧而不是静默取最后一个。
    """
    out: dict[str, list[str]] = {}
    origin: dict[str, str] = {}
    for domain in DOMAINS:
        text = (SCHEMA_DIR / f"{domain}.sql").read_text()
        for m in _CREATE_RE.finditer(text):
            table = _unquote(m.group("name"))
            cols: list[str] = []
            for item in _split_top_level(m.group("body")):
                head = item.split()[0] if item.split() else ""
                if head.upper() in {"PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "CONSTRAINT"}:
                    continue
                cols.append(_unquote(head))
            if table in out and out[table] != cols:
                raise ValueError(
                    f"表名 {table!r} 在 {origin[table]} 与 {domain} 两个数据域中"
                    f"列定义不同，按表名索引会产生歧义。\n"
                    f"  {origin[table]}: {out[table]}\n"
                    f"  {domain}: {cols}\n"
                    f"请用 domain_tables({domain!r}) 显式取用。"
                )
            out[table] = cols
            origin.setdefault(table, domain)
    return out


#: {表名: [列名...]} —— writer 按此顺序写入。仅限在各数据域中定义一致的表。
#: 跨域不一致的表请改用 :func:`domain_tables`。
TARGET_COLUMNS: dict[str, list[str]] = _parse()


def domain_tables(domain: str) -> dict[str, list[str]]:
    """取单个数据域的 {表名: [列名...]}，不做跨域聚合。"""
    if domain not in DOMAINS:
        raise KeyError(f"未知数据域 {domain!r}，可选：{DOMAINS}")
    text = (SCHEMA_DIR / f"{domain}.sql").read_text()
    out: dict[str, list[str]] = {}
    for m in _CREATE_RE.finditer(text):
        table = _unquote(m.group("name"))
        cols = [
            _unquote(item.split()[0])
            for item in _split_top_level(m.group("body"))
            if item.split()
            and item.split()[0].upper()
            not in {"PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "CONSTRAINT"}
        ]
        out[table] = cols
    return out


def table_columns(table: str) -> list[str]:
    """取单表列名，未知表抛 KeyError 并列出可用表。"""
    try:
        return TARGET_COLUMNS[table]
    except KeyError:
        raise KeyError(
            f"未知表 {table!r}。schema/*.sql 中已定义的表：{sorted(TARGET_COLUMNS)}"
        ) from None


@lru_cache(maxsize=1)
def _pks() -> dict[str, tuple[str, ...]]:
    """{表名: (主键列...)}。

    主键有两种写法，都要认：
      - 表级   ``PRIMARY KEY (a, b)``            —— 多列
      - 行内   ``thscode VARCHAR PRIMARY KEY``   —— 单列
    """
    out: dict[str, tuple[str, ...]] = {}
    for domain in DOMAINS:
        text = (SCHEMA_DIR / f"{domain}.sql").read_text()
        for m in _CREATE_RE.finditer(text):
            table = _unquote(m.group("name"))
            inline: list[str] = []
            for item in _split_top_level(m.group("body")):
                upper = item.upper()
                if upper.startswith("PRIMARY KEY"):
                    inner = item[item.index("(") + 1 : item.rindex(")")]
                    out[table] = tuple(
                        _unquote(c) for c in (x.strip() for x in inner.split(",")) if c
                    )
                elif upper.startswith(("UNIQUE", "FOREIGN", "CHECK", "CONSTRAINT")):
                    continue
                elif "PRIMARY KEY" in upper:
                    head = item.split()[0]
                    inline.append(_unquote(head))
            if table not in out and inline:
                out[table] = tuple(inline)
    return out


def primary_key_of(table: str) -> tuple[str, ...]:
    """取主键列名元组；未声明主键返回空元组。"""
    return _pks().get(table, ())


__all__ = ["TARGET_COLUMNS", "DOMAINS", "table_columns", "domain_tables", "primary_key_of"]
