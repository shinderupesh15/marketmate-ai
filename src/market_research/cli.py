"""Run live research: uv run python -m market_research.cli [--run-id ID]."""
import argparse
from market_research.market_schemas import BusinessBrief
from market_research.market_service import MarketService

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    args = parser.parse_args()
    service = MarketService()
    run_id = args.run_id or service.new_run(BusinessBrief())
    print("RUN_ID=" + run_id, flush=True)
    state = service.execute(run_id, progress=lambda stage, _: print(stage, flush=True))
    print("STATUS=" + state.get("status", "unknown"))
    print("PROFILES=" + str(len(state.get("profiles", {}))))
    print("Open the Streamlit app and select this run to review it.")

if __name__ == "__main__":
    main()
