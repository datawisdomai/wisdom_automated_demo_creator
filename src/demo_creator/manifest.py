"""`demos/<name>/.state.json` — ids created in Snowflake/Wisdom and per-step status.

Committed with the demo so reruns are idempotent and `demo status` can read back
what exists. Never contains secrets.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _deep_merge(base: dict, ours: dict) -> dict:
    """Our values win key by key; nested dicts merge so sibling ids written by
    another process survive."""
    out = dict(base)
    for k, v in ours.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class State:
    def __init__(self, path: Path, data: dict[str, Any] | None = None):
        self.path = path
        self.data: dict[str, Any] = data or {"steps": {}, "wisdom": {}, "snowflake": {}}
        self.data.setdefault("steps", {})
        self.data.setdefault("wisdom", {})
        self.data.setdefault("snowflake", {})

    @classmethod
    def load(cls, demo_dir: Path) -> "State":
        path = Path(demo_dir) / ".state.json"
        if path.is_file():
            return cls(path, json.loads(path.read_text()))
        return cls(path)

    def save(self, delta: dict[str, Any] | None = None) -> None:
        """Read-merge-write under a file lock: several `demo` processes (eval, app,
        chat, a long publish) may run at once and each must not clobber the others.
        Only `delta` (the keys this call changed) is merged over the file; merging
        the whole in-memory copy would let a long-running process overwrite values
        another process wrote after this one last read the file (seen 2026-10-13:
        a 25-minute extraction wait reverted a fresh eval score). With no delta
        the full in-memory state is written (used by `overwrite`)."""
        import fcntl

        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_suffix(".lock")
        with lock.open("w") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            try:
                on_disk = json.loads(self.path.read_text()) if self.path.is_file() else {}
            except ValueError:
                on_disk = {}
            merged = _deep_merge(on_disk, delta if delta is not None else self.data)
            for section in ("steps", "wisdom", "snowflake"):
                merged.setdefault(section, {})
            self.data = merged
            self.path.write_text(json.dumps(merged, indent=2, sort_keys=True, default=str) + "\n")
            fcntl.flock(lk, fcntl.LOCK_UN)

    # ---- steps ----
    def mark(self, step: str, status: str, **info: Any) -> None:
        entry = {"status": status, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        entry.update(info)
        self.data["steps"][step] = entry
        self.save({"steps": {step: entry}})

    def step(self, name: str) -> dict[str, Any]:
        return self.data["steps"].get(name, {})

    def step_ok(self, name: str) -> bool:
        return self.step(name).get("status") == "ok"

    def overwrite(self, *, sections: dict[str, dict] | None = None, drop_steps: tuple[str, ...] = ()) -> None:
        """Write sections wholesale and remove steps, under the lock, WITHOUT merging
        the on-disk copy back in (teardown needs this; `save()` would resurrect ids)."""
        import fcntl

        lock = self.path.with_suffix(".lock")
        with lock.open("w") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            try:
                on_disk = json.loads(self.path.read_text()) if self.path.is_file() else {}
            except ValueError:
                on_disk = {}
            merged = _deep_merge(on_disk, self.data)
            for name, value in (sections or {}).items():
                merged[name] = value
            for step in list(merged.get("steps", {})):
                if any(step == d or step.startswith(d + ".") for d in drop_steps):
                    merged["steps"].pop(step)
            self.data = merged
            self.path.write_text(json.dumps(merged, indent=2, sort_keys=True, default=str) + "\n")
            fcntl.flock(lk, fcntl.LOCK_UN)

    # ---- ids ----
    @property
    def wisdom(self) -> dict[str, Any]:
        return self.data["wisdom"]

    @property
    def snowflake(self) -> dict[str, Any]:
        return self.data["snowflake"]

    def set(self, section: str, key: str, value: Any) -> None:
        self.data.setdefault(section, {})[key] = value
        self.save({section: {key: value}})
