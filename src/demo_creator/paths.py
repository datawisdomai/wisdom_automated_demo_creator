"""Layout of one demo folder (`demos/<name>/`). Everything under `build/` is regenerable."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DemoPaths:
    root: Path

    @property
    def build(self) -> Path:
        return self.root / "build"

    @property
    def cache(self) -> Path:
        return self.build / "_cache"

    @property
    def duckdb(self) -> Path:
        return self.build / "demo.duckdb"

    @property
    def logs(self) -> Path:
        return self.build / "logs"

    @property
    def docs_out(self) -> Path:
        return self.build / "docs"

    @property
    def reviewed_csv(self) -> Path:
        return self.build / "reviewed-queries.csv"

    @property
    def eval_results(self) -> Path:
        return self.build / "eval_results.json"

    @property
    def state(self) -> Path:
        return self.root / ".state.json"

    def parquet(self, table: str) -> Path:
        return self.cache / f"{table}.parquet"

    def ensure(self) -> "DemoPaths":
        for d in (self.build, self.cache, self.logs, self.docs_out):
            d.mkdir(parents=True, exist_ok=True)
        return self
