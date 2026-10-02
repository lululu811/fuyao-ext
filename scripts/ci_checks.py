#!/usr/bin/env python3
"""ci_checks.py — 公开仓库的发布前闸门

四道检查，全部只读，不修改任何文件：

1. DDL 可执行   —— 把 schema/*.sql 灌进干净内存库，能建出来
2. 结构一致     —— export_schema.py --check（DDL 与源库同步）
3. 密钥扫描     —— 硬编码凭据、webhook、长随机串
4. 路径泄漏     —— 开发者本机绝对路径

任一失败退出码非 0。

    python scripts/ci_checks.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 扫描范围：源码与文档。不含 .git、缓存、生成物。
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".ruff_cache", ".omc"}
TEXT_SUFFIX = {".py", ".md", ".sql", ".yaml", ".yml", ".toml", ".json", ".sh", ".cfg", ".txt"}

# --- 密钥 ---------------------------------------------------------------------

#: 高置信度：赋值给凭据类变量的字面量
SECRET_ASSIGN = re.compile(
    r"""(?ix)
    \b (?: api[_-]?key | apikey | secret | token | password | passwd | pwd
         | client[_-]?secret | access[_-]?key | private[_-]?key | webhook[_-]?url )
    \s* [:=] \s*
    (?! \s* (?: os\.environ | process\.env | env\. | "" | '' | None | f" | "\$ ) )
    ["'] (?P<val> [^"']{8,} ) ["']
    """
)

#: 上游鉴权头直接带值
AUTH_HEADER_VALUE = re.compile(
    r"""(?ix) ["'] X-api-key ["'] \s* : \s* (?! api_key | self\.api_key | os\. ) ["'] [^"']{8,} ["'] """
)

#: 常见高熵串：hex>=32、base64/URLsafe>=40（带常见前缀更严格）
HIGH_ENTROPY = re.compile(
    r"""(?ix)
    \b (?:
        (?: sk|pk|ghp|gho|xox[abps]|AKIA) [A-Za-z0-9_\-]{16,}
      | [A-Fa-f0-9]{32,}
      | [A-Za-z0-9+/]{40,} ={1,2}
      | (?=.*[a-z])(?=.*[A-Z])(?=.*[0-9]) [A-Za-z0-9+/]{40,}
    ) \b
    """
)

#: 明显的占位符，不算密钥
PLACEHOLDER = re.compile(
    r"(?i)^(?:your|my|the|example|placeholder|dummy|fake|test|xxx+|todo|none|null|\.\.\.)"
)

# --- 路径泄漏 -----------------------------------------------------------------

ABS_PATH = re.compile(r"/Users/[A-Za-z0-9._\-]+")
LINUX_HOME = re.compile(r"/home/[a-z][a-z0-9._\-]{1,30}/")
WINDOWS_HOME = re.compile(r"[A-Z]:\\\\Users\\\\[A-Za-z0-9._\-]+")


def _files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIX:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p)
    return out


def check_secrets(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in files:
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if len(line) > 2000:
                continue
            for pattern, label in (
                (SECRET_ASSIGN, "疑似硬编码凭据"),
                (AUTH_HEADER_VALUE, "X-api-key 带字面量"),
            ):
                m = pattern.search(line)
                if m and not PLACEHOLDER.match(m.group("val")):
                    val = m.group("val")
                    problems.append(
                        f"{label}  {f.relative_to(ROOT)}:{i}  "
                        f"值已打码: {val[:3]}…({len(val)} 字符)"
                    )
            m = HIGH_ENTROPY.search(line)
            if m and not PLACEHOLDER.search(m.group(0)) and "sha256" not in line.lower():
                tok = m.group(0)
                # UUID 形态是误报常态，单独放行
                if re.fullmatch(r"[A-Fa-f0-9]{8}(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12}", tok):
                    continue
                problems.append(
                    f"高熵字符串      {f.relative_to(ROOT)}:{i}  "
                    f"{tok[:4]}…({len(tok)} 字符)"
                )
    return problems


def check_paths(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in files:
        rel = f.relative_to(ROOT)
        # 文档里可以显式举例说明"不要写绝对路径"，这些文件豁免行内容
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for pattern, label in ((ABS_PATH, "macOS"), (LINUX_HOME, "Linux"), (WINDOWS_HOME, "Windows")):
                if pattern.search(line):
                    problems.append(f"{label} 绝对路径  {rel}:{i}  {line.strip()[:80]}")
    return problems


def check_ddl_executable() -> list[str]:
    """每个数据域灌进**各自的**干净内存库。

    不能把所有域建进同一个库：``_meta`` 与 ``_import_batches`` 在每个域里
    都有定义，跨域重名。这与物理布局一致 —— 上游本来就是每域一个
    DuckDB 文件。
    """
    import duckdb

    problems: list[str] = []
    from schema.ddl import DOMAINS

    for domain in DOMAINS:
        sql = (ROOT / "schema" / f"{domain}.sql").read_text()
        con = duckdb.connect(":memory:")
        try:
            con.execute(sql)
        except duckdb.Error as exc:
            problems.append(f"DDL 执行失败  schema/{domain}.sql: {str(exc)[:160]}")
        finally:
            con.close()
    return problems, None


def check_schema_sync() -> tuple[list[str], str | None]:
    """比对 DDL 与源库。

    CI 环境没有作者的本地数据工作区，此时跳过（返回 skip 原因）而非失败 ——
    结构一致性是**作者本地**的检查，公开仓库的 CI 无法复现。
    """
    from paths import FUYAO_HOME

    dbs = list(FUYAO_HOME.glob("*.duckdb"))
    if not dbs:
        return [], f"未找到源库（{FUYAO_HOME}/*.duckdb），本项仅在作者本地运行"

    r = subprocess.run(
        [sys.executable, "scripts/export_schema.py", "--check"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if r.returncode != 0:
        return [f"DDL 与源库不同步：\n{(r.stdout + r.stderr).strip()[-600:]}"], None
    return [], None


CHECKS = [
    ("DDL 可执行", check_ddl_executable),
    ("结构一致", check_schema_sync),
    ("密钥扫描", lambda: (check_secrets(_files()), None)),
    ("路径泄漏", lambda: (check_paths(_files()), None)),
]


def main() -> int:
    files = _files()
    print(f"扫描 {len(files)} 个文件\n")

    failed = 0
    skipped = 0
    for name, fn in CHECKS:
        problems, skip = fn()
        if skip:
            skipped += 1
            print(f"– {name}  （跳过：{skip}）")
            continue
        if problems:
            failed += 1
            print(f"✗ {name}  ({len(problems)} 项)")
            for p in problems[:25]:
                print(f"    {p}")
            if len(problems) > 25:
                print(f"    … 另有 {len(problems) - 25} 项")
        else:
            print(f"✓ {name}")

    print()
    if failed:
        print(f"{failed}/{len(CHECKS)} 项检查未通过")
        return 1
    tail = f"（{skipped} 项跳过）" if skipped else ""
    print(f"全部 {len(CHECKS) - skipped} 项检查通过{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
