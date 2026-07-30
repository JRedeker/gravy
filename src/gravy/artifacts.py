"""Review-scoped durable artifacts, separate from lifecycle metadata."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def create_namespace(self, review_id: str) -> Path:
        namespace = self.root / review_id
        namespace.mkdir(parents=True, exist_ok=False)
        return namespace

    def append_decision(self, review_id: str, decision: dict[str, object]) -> Path:
        path = self.root / review_id / "decisions.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(decision, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return path

    def discard_namespace(self, review_id: str) -> None:
        shutil.rmtree(self.root / review_id, ignore_errors=True)
        if self.root.exists() and not any(self.root.iterdir()):
            self.root.rmdir()
