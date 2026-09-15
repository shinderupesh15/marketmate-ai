"""Separate MarketMate runs from existing CreatorKit snapshots."""
from contextlib import contextmanager
from langgraph.checkpoint.sqlite import SqliteSaver
from market_research.service import ResearchService
from market_research.config import PROJECT_ROOT, load_settings
from market_research.runtime import Usage
from market_research.models import Models
from market_research.tools import YouSearch
from market_research.graph import build_graph
from market_research.market_agents import MarketAgents

class MarketService(ResearchService):
    def __init__(self, data_dir=None, factory=None):
        super().__init__(data_dir or PROJECT_ROOT / "data" / "marketmate", factory)

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

    def export(self, run_id):
        from market_research.reporting import export_report
        from market_research.market_reporting import render_market_report
        state, _, _ = self.snapshot(run_id)
        return export_report(state, self.data_dir / "exports" / run_id, renderer=render_market_report)
