"""Bounded API usage and safe errors, journaled independently of graph checkpoints."""

import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class ServiceError(RuntimeError):
    pass


class BudgetExceeded(ServiceError):
    pass


class Usage:
    def __init__(self, db: Path, run_id: str, max_search: int = 30, max_model: int = 36):
        self.db, self.run_id = Path(db), run_id
        self.max_search, self.max_model = max_search, max_model
        self.started = time.monotonic()
        self.db.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.execute(
                "CREATE TABLE IF NOT EXISTS events (run_id TEXT, kind TEXT, detail TEXT, created TEXT)"
            )
            c.execute(
                "CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, label TEXT, created TEXT)"
            )

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.db, timeout=30)
        try:
            yield c
            c.commit()
        finally:
            c.close()

    def record(self, kind, detail):
        with self.connect() as c:
            c.execute(
                "INSERT INTO events VALUES (?,?,?,?)",
                (self.run_id, kind, detail, datetime.now(timezone.utc).isoformat()),
            )

    def reserve(self, kind):
        if time.monotonic() - self.started > 600:
            raise BudgetExceeded("Execution time budget reached; completed evidence is preserved.")
        limit = self.max_search if kind == "search" else self.max_model
        with self.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            count = c.execute(
                "SELECT COUNT(*) FROM events WHERE run_id=? AND kind=?", (self.run_id, kind)
            ).fetchone()[0]
            if count >= limit:
                raise BudgetExceeded(
                    f"{kind.title()} request budget reached; completed evidence is preserved."
                )
            c.execute(
                "INSERT INTO events VALUES (?,?,?,?)",
                (self.run_id, kind, "Request reserved", datetime.now(timezone.utc).isoformat()),
            )

    def counts(self):
        with self.connect() as c:
            return dict(
                c.execute(
                    "SELECT kind, COUNT(*) FROM events WHERE run_id=? GROUP BY kind", (self.run_id,)
                ).fetchall()
            )

    def events(self):
        with self.connect() as c:
            return c.execute(
                "SELECT kind, detail, created FROM events WHERE run_id=? ORDER BY rowid",
                (self.run_id,),
            ).fetchall()
