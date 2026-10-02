# 排除 HiThink-Tech/Financial-API，不 vendor、不再分发

---
status: accepted
date: 2026-10-02
---

本项目**不包含、不 fork、不再分发** `https://github.com/HiThink-Tech/Financial-API.git` 的任何代码。该仓库属于上游数据服务方（`Copyright (c) 2026 HiThink-Tech`），作者是其付费用户，仅持有本地 clone。

## 依据

- 本地 clone 与上游 `git rev-list --left-right --count origin/main...HEAD` 为 **`0  0`**，无任何提交差异；35 个 commit 全部由 HiThink-Tech 署名；reflog 中除 `pull` 外唯一一条是 `clone`。
- 仓库根 `LICENSE` 为 MIT（可 fork，但必须保留 HiThink-Tech 版权声明，**不能换许可证挂在本项目名下**）。
- `python/pyproject.toml` 将 `marketdb` 包标记为 `license = { text = "Proprietary" }`，作者 `haoruilee`（此人在 git 历史中不存在）。**而 `marketdb` 恰是本项目 `market.duckdb` 数据的实际产出方**，其可再分发性无法从仓库内部判定，仓库内亦无任何成文 EULA。
- 作者在该仓库的全部本地足迹约 196 行，且从未提交。

## Considered Options

- **fork 并保留原版权声明后发布** —— 法律上可行（MIT 授予他人使用与再分发权）。但收益为零：`@hithink-tech/hithink-finance-cli` v0.1.13 **已公开发布在 npm**，任何人 `npm install` 即已拥有；把它抄进本项目不给任何人任何他们没有的东西，却引入"把别人的仓挂在自己 LICENSE 下"的风险。排除。
- **声明为外部依赖** —— 对 CLI 部分采用此方案。作为已发布 npm 包引用，不 vendored。
- **自己实现 Ingestor** —— 采纳。见 [ADR-0004](./0004-ingestor-protocol-with-fuyao-reference.md)。

## Consequences

- `market.duckdb` 的同步代码必须**重新实现**，不能沿用 `marketdb`。这是本项目最大的一块新增工作量。
- 本项目 README 需要写明如何获得行情数据，而**不能**假定用户已安装上游工具。
- 反过来：`marketdb` 标记为 Proprietary 的问题从此与本项目无关——本项目不碰那份代码。
