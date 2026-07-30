"""Review-scoped durable artifacts, separate from lifecycle metadata."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
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

    def write_recovery(self, review_id: str, payload: dict[str, object]) -> Path:
        """Persist a readable recovery artifact for a review.

        The recovery file is written to the review's own artifact namespace so it
        survives even if the review is later terminalized or its Tailnet mapping
        cleanup fails.  fsync is used to keep the pointer durable.
        """
        path = self.root / review_id / "recovery.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".recovery-", suffix=".tmp", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return path

    def discard_namespace(self, review_id: str) -> None:
        shutil.rmtree(self.root / review_id, ignore_errors=True)
        if self.root.exists() and not any(self.root.iterdir()):
            self.root.rmdir()
