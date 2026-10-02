"""ingestors.fuyao — 上游数据服务的参考实现

**本包代码由 fuyao-ext 自行编写**，调用同花顺 hithink-finance 的公开 REST API。
它不包含上游任何代码 —— 上游的客户端仓库归其所有，见
[`docs/adr/0002`](../../docs/adr/0002-exclude-hithink-financial-api.md)。

换数据源时不必读这个包，只需要实现 `ingestors.base.Ingestor` 的四个方法。
"""

from ingestors.fuyao.client import (
    DEFAULT_BASE_URL,
    FuyaoClient,
    FuyaoError,
    MissingCredential,
    load_credential,
)
from ingestors.fuyao.market import FuyaoMarketIngestor
from ingestors.fuyao.writer import DuckDbMarketWriter, new_batch_id

__all__ = [
    "FuyaoClient",
    "FuyaoError",
    "MissingCredential",
    "load_credential",
    "DEFAULT_BASE_URL",
    "FuyaoMarketIngestor",
    "DuckDbMarketWriter",
    "new_batch_id",
]
