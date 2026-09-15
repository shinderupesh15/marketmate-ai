from streamlit.testing.v1 import AppTest
from test_marketmate import factory

from market_research.market_service import MarketService


def test_new_brief_and_review_ui(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key")
    monkeypatch.setenv("YDC_API_KEY", "fake-you-key")
    # Replace service construction so this UI test never makes network requests.
    monkeypatch.setattr(
        "market_research.market_service.MarketService", lambda: MarketService(tmp_path, factory)
    )
    import streamlit as st

    st.cache_resource.clear()
    app = AppTest.from_file("../streamlit_app.py", default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value == "MarketMate AI"
    examples = next(w for w in app.selectbox if w.label.startswith("Start with"))
    examples.select("Your own idea").run()
    assert next(w for w in app.text_input if w.label == "Business idea").value == ""
    next(w for w in app.selectbox if w.label.startswith("Start with")).select("Home coffee").run()
    assert "coffee" in next(w for w in app.text_input if w.label == "Business idea").value
    next(b for b in app.button if b.label == "Research my market").click().run(timeout=20)
    assert not app.exception
    assert any(b.label == "Approve briefing" for b in app.button)
    assert not app.get("download_button")
    next(w for w in app.selectbox if w.label == "Explore a brand").select("Beta").run()
    assert not app.exception
    next(w for w in app.text_input if w.label == "Search sources").set_value("no-match-xyz").run()
    assert any("No matching sources" in w.value for w in app.info)
    next(w for w in app.text_input if w.label == "Search sources").set_value("roasted").run()
    assert any(w.label == "Choose a source" for w in app.selectbox)
    assert not app.exception
    next(b for b in app.button if b.label == "Approve briefing").click().run(timeout=20)
    assert not app.exception
    assert app.get("download_button")
    st.cache_resource.clear()


def test_ui_text_has_no_encoding_damage():
    from pathlib import Path

    source = (Path(__file__).parent.parent / "streamlit_app.py").read_text(encoding="utf-8")
    for marker in ("\u00c3", "\u00c2", "\ufffd"):
        assert marker not in source
