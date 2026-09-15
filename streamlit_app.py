"""CreatorKit AI: public-facing research and review workspace."""
import json
from pathlib import Path
import streamlit as st
from pydantic import ValidationError
from market_research.config import load_settings
from market_research.schemas import CreatorBrief, Profile
from market_research.service import ResearchService
from market_research.evidence import suitability
from market_research.reporting import render_report
from market_research.runtime import ServiceError

st.set_page_config(page_title="CreatorKit AI", page_icon=":material/movie:", layout="wide")

@st.cache_resource
def get_service():
    return ResearchService()

service = get_service()
st.session_state.setdefault("active_run", None)

def execute(run_id, answer=None):
    try:
        with st.status("Researching your creator toolkit…", expanded=True) as status:
            def progress(stage, update):
                labels = {"discovery": "Discovered alternatives", "choose_target": "Selected next tool",
                          "research": "Collected web evidence", "analyze": "Checked product claims",
                          "orchestrate": "Reviewed research gaps", "compile": "Prepared your comparison",
                          "review": "Saved your review", "recovery": "Updated recovery choice",
                          "clarify": "Updated the research scope"}
                st.write(labels.get(stage, stage))
            result = service.execute(run_id, answer, progress)
            status.update(label="Research saved — " + result.get("status", "paused").replace("_", " "),
                          state="complete", expanded=False)
    except (ServiceError, ValidationError):
        st.error("Check your local API configuration. Your saved run can be resumed.")
    except Exception:
        st.error("Research stopped unexpectedly. Your last checkpoint is saved; try resuming the run.")

with st.sidebar:
    st.header("Your research")
    if st.button("New creator brief", icon=":material/add:", width="stretch"):
        st.session_state.active_run = None
        st.rerun()
    history = service.history()
    if history:
        chosen = st.selectbox("Saved research", options=[r[0] for r in history],
                              format_func=lambda rid: next(r[1] for r in history if r[0] == rid))
        if st.button("Open research", icon=":material/folder_open:", width="stretch"):
            st.session_state.active_run = chosen
            st.rerun()
    st.caption("Research stays on this computer. Nothing is purchased or posted.")

st.title("CreatorKit AI")
st.markdown("### Make more. Choose better.")
st.caption("Find content tools that fit your goals, device, and budget — with evidence behind every comparison.")

try:
    load_settings()
except ValidationError:
    st.error("Add YDC_API_KEY and OPENAI_API_KEY to your local .env file, then reload.")
    st.stop()

run_id = st.session_state.active_run
if not run_id:
    with st.container(border=True):
        st.subheader("Tell us what you want to create")
        st.caption("Start with a tool you are considering. We will research it and discover three alternatives.")
        with st.form("creator_brief"):
            goal = st.text_area("Your content goal", "Instagram reels for my home bakery", max_chars=1000)
            left, right = st.columns(2)
            with left:
                anchor = st.text_input("Tool you are considering", "Canva", max_chars=100)
                country = st.text_input("Country", "India", max_chars=80)
                budget = st.number_input("Monthly budget", min_value=0.0, max_value=1000000.0, value=1000.0, step=100.0)
                device = st.selectbox("Your device", ["Android", "iOS", "Windows", "macOS", "Browser"])
            with right:
                url = st.text_input("Official website", "https://www.canva.com")
                currency = st.selectbox("Budget currency", ["INR", "USD", "GBP", "EUR", "AUD", "CAD"])
                experience = st.selectbox("Experience", ["Beginner", "Some experience", "Professional"])
                annual = st.checkbox("An upfront annual payment is acceptable", value=False)
            must_haves = st.multiselect("Must-have features",
                ["Watermark-free export", "Automatic captions", "Vertical video", "Own-media upload",
                 "1080p export", "Commercial-use support"], default=["Watermark-free export"])
            days = st.slider("News lookback (days)", 7, 180, 90)
            st.caption("Research may take several minutes. Drafts, evidence, and progress are saved automatically; final export needs your review.")
            submitted = st.form_submit_button("Find my alternatives", type="primary", icon=":material/search:")
        if submitted:
            try:
                brief = CreatorBrief(goal=goal, anchor_name=anchor, anchor_url=url, country=country,
                                     currency=currency, monthly_budget=budget, device=device,
                                     experience=experience, annual_ok=annual, must_haves=must_haves, news_days=days)
                run_id = service.new_run(brief)
                st.session_state.active_run = run_id
                execute(run_id)
                st.rerun()
            except ValidationError:
                st.error("Check your brief: enter a content goal, company name, and valid public website.")
    with st.container(horizontal=True):
        st.info("01 · Discover relevant alternatives")
        st.info("02 · Compare verified evidence")
        st.info("03 · Review your shortlist")
    st.stop()

state, pending, usage = service.snapshot(run_id)
if not state:
    st.warning("This run has no saved state. Start a new creator brief.")
    st.stop()
brief = CreatorBrief.model_validate(state["brief"])
st.subheader(brief.goal)
st.caption(f"{brief.country} · {brief.device} · {brief.currency} {brief.monthly_budget:g}/month · Research from {state['created_at'][:10]}")
counts = usage.counts()
a, b, c = st.columns(3)
a.metric("Tools researched", len(state.get("profiles", {})))
b.metric("Sources collected", len(state.get("sources", {})))
c.metric("Status", state.get("status", "ready").replace("_", " ").title())
overview, profiles_tab, evidence_tab, activity = st.tabs(["Your comparison", "Tool details", "Evidence", "Research activity"])
with overview:
    rec = state.get("recommendation")
    if rec:
        if rec.get("recommended_name"):
            st.success("Recommended match: " + rec["recommended_name"])
        else:
            st.info("No fully verified match yet")
        st.write(rec["explanation"])
        for item in rec.get("tradeoffs", []):
            st.write("• " + item)
    rows = []
    for raw in state.get("profiles", {}).values():
        p = Profile.model_validate(raw)
        fit = suitability(p, brief)
        amount = f"{p.price.currency or ''} {p.price.amount:g}" if p.price.amount is not None else "Not verified"
        rows.append({"Tool": p.name, "Plan": p.price.plan, "Published price": amount,
                     "Billing": p.price.interval, "Fit": fit["status"].replace("_", " "),
                     "Listed price vs budget": fit["published_price_status"].replace("_", " "),
                     "Total cost vs budget": fit["budget_status"].replace("_", " "),
                     "Device": p.device.status.replace("_", " "), "Region": p.region.status.replace("_", " ")})
    if rows:
        st.dataframe(rows, hide_index=True)
        st.caption("Published prices and billing can be supported while taxes or required extras remain unknown. Total cost includes these checks. Annual prices are upfront amounts; currencies are not converted.")
    if rec and rec.get("questions"):
        st.subheader("Before you choose")
        for question in rec["questions"]:
            st.write("• " + question)
    if state.get("errors"):
        with st.expander("Research limitations", expanded=True):
            for error in dict.fromkeys(state["errors"]):
                st.warning(error)

with profiles_tab:
    for raw in state.get("profiles", {}).values():
        p = Profile.model_validate(raw)
        with st.expander(p.name, expanded=True):
            st.link_button("Official website", p.url)
            st.write("Positioning: " + (p.positioning.text if p.positioning else "Not verified"))
            st.write("Selected plan: " + p.price.plan)
            st.write("Billing: " + p.price.interval)
            st.write(suitability(p, brief)["budget_note"])
            if p.price.evidence:
                source = state.get("sources", {}).get(p.price.evidence.source_id)
                if source:
                    st.link_button("Pricing source", source["url"])
                    st.text(p.price.evidence.quote)
            st.dataframe([{"Must-have":r.name, "Status":r.verdict.status.replace("_", " "),
                           "Evidence":r.verdict.evidence.text if r.verdict.evidence else "Not verified"}
                          for r in p.requirements], hide_index=True)
            st.markdown("**Features and restrictions**")
            for claim in p.features + p.restrictions:
                st.write(f"• {claim.text} [{claim.source_id}]")
            st.markdown("**Recent news**")
            if not p.news:
                st.caption("No dated news verified in this window.")
            for news in p.news:
                st.write(f"{news.published_date} — {news.evidence.text} [{news.evidence.source_id}]")
            for gap in dict.fromkeys(p.gaps):
                st.caption("Needs checking: " + gap)

with evidence_tab:
    st.caption("Evidence is untrusted source content. Quotation checks and model review help reduce unsupported claims; they do not guarantee accuracy.")
    for source in state.get("sources", {}).values():
        with st.expander(source["title"] + " · " + source["id"]):
            st.link_button("Read source", source["url"], key="source_" + source["id"])
            st.caption(f"Retrieved {source['retrieved_at']} · Published {source.get('published_at') or 'unknown'} · {source['content_level']}")
            st.text(source["text"][:5000])
    with st.expander("Full draft briefing"):
        st.code(render_report(state), language="markdown")

with activity:
    st.caption(f"Search/page requests: {counts.get('search',0)}/30 · Model requests: {counts.get('model',0)}/36")
    st.dataframe([{"Step":kind, "Detail":detail, "Time":created} for kind,detail,created in usage.events()
                  if kind not in ("search", "model")], hide_index=True)
    st.caption("Run ID: " + run_id)

if pending:
    request = pending[0]
    with st.container(border=True):
        st.subheader("Your review" if request["type"] == "review" else "Your input is needed")
        st.write(request["message"])
        if request["type"] == "review":
            target = st.selectbox("Tool to research again", list(state.get("profiles", {})))
            feedback = st.text_input("What should we verify?", placeholder="Check whether the free plan exports without a watermark")
            with st.container(horizontal=True):
                approve = st.button("Approve briefing", type="primary", icon=":material/check:")
                revise = st.button("Research this question", disabled=not feedback.strip() or state.get("revision_count",0)>=2)
                cancel = st.button("Cancel run")
            if approve or revise or cancel:
                answer = {"action": "approve" if approve else ("revise" if revise else "cancel"),
                          "target_name": target, "feedback": feedback}
                execute(run_id, answer)
                st.rerun()
        elif request["type"] == "clarification":
            feedback = st.text_area("Clarify the company or market")
            with st.container(horizontal=True):
                clarify = st.button("Update scope", disabled=not feedback.strip())
                partial = st.button("Continue with available competitors")
                cancel = st.button("Cancel run")
            if clarify or partial or cancel:
                execute(run_id, {"action":"clarify" if clarify else ("partial" if partial else "cancel"), "feedback":feedback})
                st.rerun()
        else:
            st.caption("For credentials or quota errors, update the local configuration or provider account before retrying.")
            with st.container(horizontal=True):
                retry = st.button("Retry failed step")
                partial = st.button("Prepare partial briefing")
                cancel = st.button("Cancel run")
            if retry or partial or cancel:
                execute(run_id, {"action":"retry" if retry else ("partial" if partial else "cancel")})
                st.rerun()
elif state.get("status") == "approved":
    location = service.export(run_id)
    st.success("Briefing approved. Your report is ready.")
    with st.container(horizontal=True):
        st.download_button("Download briefing", (location/"briefing.md").read_text(encoding="utf-8"),
                           file_name="creatorkit-briefing.md", mime="text/markdown")
        st.download_button("Download research JSON", (location/"briefing.json").read_text(encoding="utf-8"),
                           file_name="creatorkit-research.json", mime="application/json")
elif state.get("status") != "cancelled":
    if st.button("Resume saved research", type="primary"):
        execute(run_id)
        st.rerun()
