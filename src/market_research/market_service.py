"""Local run history and graph lifecycle. No credentials enter graph state."""
from pathlib import Path
from contextlib import contextmanager
from uuid import uuid4
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from market_research.config import load_settings, PROJECT_ROOT
from market_research.schemas import utcnow
from market_research.market_schemas import BusinessBrief
from market_research.runtime import Usage
from market_research.models import Models
from market_research.tools import YouSearch
from market_research.market_agents import MarketAgents
from market_research.graph import build_graph
from market_research.reporting import export_report

class MarketService:
    def __init__(self, data_dir=None, factory=None):
        self.data_dir = Path(data_dir) if data_dir else PROJECT_ROOT / "data" / "marketmate"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db = self.data_dir / "marketmate.sqlite"
        self.factory = factory

    @contextmanager
    def session(self, run_id):
        usage = Usage(self.db, run_id)
        if self.factory:
            agents = self.factory(usage)
        else:
            settings = load_settings()
            agents = MarketAgents(Models(settings, usage), YouSearch(settings.ydc_api_key.get_secret_value(), usage), usage)
        with SqliteSaver.from_conn_string(str(self.db)) as saver:
            yield build_graph(agents, saver), usage

    def new_run(self, brief: BusinessBrief):
        run_id = uuid4().hex
        usage = Usage(self.db, run_id)
        with usage.connect() as c:
            c.execute("INSERT INTO runs VALUES (?,?,?)", (run_id, brief.anchor_name + " · " + brief.goal[:70], utcnow()))
        # Store the initial checkpoint before the first remote request.
        with self.session(run_id) as (graph, _):
            graph.update_state(self.config(run_id), {
                "brief": brief.model_dump(), "created_at": utcnow(),
                "sources": {}, "profiles": {}, "company_sources": {}, "errors": [],
                "followups": 0, "revision_count": 0, "approved": False, "status": "ready",
                "next": "discovery",
            }, as_node="recovery")
        return run_id

    @staticmethod
    def config(run_id):
        return {"configurable": {"thread_id": run_id}, "recursion_limit": 100}

    def execute(self, run_id, answer=None, progress=None):
        with self.session(run_id) as (graph, usage):
            command = Command(resume=answer) if answer is not None else None
            for update in graph.stream(command, self.config(run_id), stream_mode="updates"):
                if progress:
                    for stage, value in update.items():
                        if stage != "__interrupt__":
                            progress(stage, value)
            snapshot = graph.get_state(self.config(run_id))
            return dict(snapshot.values)

    def snapshot(self, run_id):
        with self.session(run_id) as (graph, usage):
            snapshot = graph.get_state(self.config(run_id))
            pending = [i.value for t in snapshot.tasks for i in t.interrupts]
            return dict(snapshot.values), pending, usage

    def history(self):
        usage = Usage(self.db, "history")
        with usage.connect() as c:
            return c.execute("SELECT id,label,created FROM runs ORDER BY created DESC").fetchall()

    def export(self, run_id):
        state, _, _ = self.snapshot(run_id)
        return export_report(state, self.data_dir / "exports" / run_id)
