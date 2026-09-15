from streamlit.testing.v1 import AppTest
from market_research.service import ResearchService
from test_research import factory

def test_new_brief_and_review_ui(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","fake-openai-key")
    monkeypatch.setenv("YDC_API_KEY","fake-you-key")
    # Replace service construction so this UI test never makes network requests.
    monkeypatch.setattr("market_research.service.ResearchService", lambda:ResearchService(tmp_path,factory))
    import streamlit as st
    st.cache_resource.clear()
    app=AppTest.from_file("../streamlit_app.py",default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value=="CreatorKit AI"
    next(b for b in app.button if b.label=="Find my alternatives").click().run(timeout=20)
    assert not app.exception
    assert any(b.label=="Approve briefing" for b in app.button)
    assert not app.get("download_button")
    next(b for b in app.button if b.label=="Approve briefing").click().run(timeout=20)
    assert not app.exception
    assert app.get("download_button")
    st.cache_resource.clear()
