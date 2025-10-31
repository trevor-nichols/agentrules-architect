"""Package initializer for agentrules CLI."""

from __future__ import annotations

import warnings

warnings.filterwarnings(
    "ignore",
    message="urllib3 v2 only supports OpenSSL 1.1.1+",
)
