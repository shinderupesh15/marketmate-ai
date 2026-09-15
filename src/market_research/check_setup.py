"""Offline setup check: python -m market_research.check_setup."""

from importlib import import_module
from importlib.metadata import version
from typing import TypedDict

from pydantic import ValidationError

from market_research.config import load_settings


def main() -> int:
    try:
        settings = load_settings()
    except ValidationError as exc:
        fields = sorted({str(e["loc"][0]) for e in exc.errors(include_input=False)})
        print("Configuration needs attention: " + ", ".join(fields))
        return 1
    print("You.com and OpenAI credentials: configured (values hidden)")
    print("Model: " + settings.openai_model)
    for module, distribution in (
        ("langchain", "langchain"),
        ("langgraph.graph", "langgraph"),
        ("langchain_openai", "langchain-openai"),
        ("streamlit", "streamlit"),
        ("httpx", "httpx"),
        ("ipykernel", "ipykernel"),
    ):
        import_module(module)
        print(f"{distribution}: {version(distribution)}")

    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.graph import END, START, StateGraph

    class State(TypedDict):
        ready: bool

    with SqliteSaver.from_conn_string(":memory:") as saver:
        graph = StateGraph(State)
        graph.add_node("check", lambda state: {"ready": True})
        graph.add_edge(START, "check")
        graph.add_edge("check", END)
        compiled = graph.compile(checkpointer=saver)
        run = {"configurable": {"thread_id": "setup-check"}}
        result = compiled.invoke({"ready": False}, run)
        if not result["ready"] or not compiled.get_state(run).values["ready"]:
            raise RuntimeError("Checkpoint check failed")
    print("LangGraph execution and SQLite checkpoint round-trip: OK")
    print("Setup OK. No API requests were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
