"""MarketMate AI: competitor research and a practical first-week plan."""
import streamlit as st
from pydantic import ValidationError
from market_research.config import load_settings
from market_research.market_schemas import BusinessBrief, BusinessProfile
from market_research.market_service import MarketService
from market_research.market_reporting import basis_claims
from market_research.reporting import render_report
from market_research.runtime import ServiceError

st.set_page_config(page_title="MarketMate AI", page_icon=":material/storefront:", layout="wide")

@st.cache_resource
def get_service():
    return MarketService()

service = get_service()
st.session_state.setdefault("market_run", None)

def execute(run_id, answer=None):
    try:
        with st.status("Researching your marketÃ¢â‚¬Â¦", expanded=True) as status:
            def progress(stage, update):
                labels = {"discovery":"Discovering competitors", "research":"Reading public sources",
                          "analyze":"Checking competitor facts", "compile":"Preparing experiments and content ideas",
                          "orchestrate":"Checking evidence coverage", "review":"Saving your review"}
                if stage in labels:
                    st.write(labels[stage])
            result = service.execute(run_id, answer, progress)
            status.update(label="Research saved Ã‚Â· "+result.get("status","paused").replace("_"," "),
                          state="complete", expanded=False)
    except (ServiceError, ValidationError):
        st.error("Research paused. Check configuration or resume the saved run.")
    except Exception:
        st.error("Research stopped unexpectedly. The last checkpoint is saved; try resuming.")

with st.sidebar:
    st.header("Your workspace")
    if st.button("New business brief", icon=":material/add:", width="stretch"):
        st.session_state.market_run = None
        st.rerun()
    history = service.history()
    if history:
        selected = st.selectbox("Saved research", [r[0] for r in history],
            format_func=lambda rid: next(r[1] for r in history if r[0]==rid))
        if st.button("Open research", width="stretch"):
            st.session_state.market_run = selected
            st.rerun()
    st.caption("Local research workspace. Review your briefing before exporting.")

st.title("MarketMate AI")
st.markdown("### Understand your market. Plan your next move.")
st.caption("Explore competing brands, find ideas worth testing, and leave with a practical action plan.")

try:
    load_settings()
except ValidationError:
    st.error("Add YDC_API_KEY and OPENAI_API_KEY to your local .env file, then reload.")
    st.stop()

run_id = st.session_state.market_run
if not run_id:
    with st.container(border=True):
        st.subheader("What business are you building?")
        presets = {
            "Healthy snacks": ("Launch an online healthy-snack brand for office workers", "Office workers looking for convenient snacks", "The Whole Truth", "https://thewholetruthfoods.com"),
            "Home coffee": ("Launch a beginner-friendly specialty coffee brand for home brewing", "First-time home coffee brewers", "Blue Tokai", "https://bluetokaicoffee.com"),
            "Regional drinks": ("Launch a regional fruit drink brand for young adults", "Young adults looking for convenient fruit drinks", "Paper Boat", "https://www.hectorbeverages.com"),
        }
        example = st.selectbox("Start with an example, then edit", list(presets))
        defaults = presets[example]
        with st.form("business_brief"):
            goal = st.text_area("Business idea", defaults[0], max_chars=1000)
            audience = st.text_input("Who is it for?", defaults[1], max_chars=500)
            left, right = st.columns(2)
            with left:
                anchor = st.text_input("Reference brand", defaults[2], max_chars=100)
                country = st.text_input("Target market", "India", max_chars=80)
            with right:
                url = st.text_input("Reference brand website", defaults[3])
                days = st.slider("News lookback (days)", 7, 180, 90)
            st.caption("We research this brand and discover three competitors. Public facts support ideas to test; they do not prove demand.")
            submitted = st.form_submit_button("Research my market", type="primary", icon=":material/search:")
        if submitted:
            try:
                brief = BusinessBrief(goal=goal, audience=audience, anchor_name=anchor,
                                      anchor_url=url, country=country, news_days=days)
                run_id = service.new_run(brief)
                st.session_state.market_run = run_id
                execute(run_id)
                st.rerun()
            except ValidationError:
                st.error("Enter your business idea, audience, market, and a valid public brand website.")
    with st.container(horizontal=True):
        st.info("01 Ã‚Â· Sourced competitor facts")
        st.info("02 Ã‚Â· Differentiation experiments")
        st.info("03 Ã‚Â· Content ideas and a first-week plan")
    st.stop()

state, pending, usage = service.snapshot(run_id)
if not state:
    st.warning("This run has no saved state. Start a new brief.")
    st.stop()
brief = BusinessBrief.model_validate(state["brief"])
st.subheader(brief.goal)
st.caption(f"{brief.audience} Ã‚Â· {brief.country} Ã‚Â· Research from {state['created_at'][:10]}")

def show_claim(claim, prefix=""):
    st.write(prefix + claim.text)
    source = state.get("sources", {}).get(claim.source_id)
    if source:
        st.caption("Source: " + source["title"])
        st.link_button("Read supporting source", source["url"])
        with st.expander("Supporting passage"):
            st.text(claim.quote)

def show_basis(refs):
    with st.expander("Why this idea: research basis"):
        for company, claim in basis_claims(refs, state.get("profiles", {})):
            show_claim(claim, company + ": ")

profiles = state.get("profiles", {})
plan = state.get("recommendation", {})
a,b,c = st.columns(3)
a.metric("Brands researched", len(profiles))
b.metric("Sources collected", len(state.get("sources", {})))
c.metric("Status", state.get("status", "ready").replace("_"," ").title())
overview, ideas, content, actions, evidence = st.tabs(
    ["Competitor landscape", "Ideas to test", "Content studio", "First-week plan", "Sources and activity"])

with overview:
    st.write(plan.get("explanation", "Research is in progress. Completed findings appear here."))
    rows = []
    for raw in profiles.values():
        p = BusinessProfile.model_validate(raw)
        rows.append({"Brand":p.name, "Positioning":p.positioning.text if p.positioning else "Still researching",
                     "Products / services":"; ".join(c.text for c in p.products),
                     "Supported claims":len(p.products)+len(p.messaging)+len(p.pricing)+bool(p.positioning)+len(p.news)})
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
    for raw in profiles.values():
        p = BusinessProfile.model_validate(raw)
        with st.expander(p.name, expanded=False):
            st.link_button("Brand website", p.url)
            if p.positioning:
                show_claim(p.positioning)
            for heading, claims in (("Products and services",p.products),("Brand messaging",p.messaging),("Published price examples",p.pricing)):
                if claims:
                    st.markdown("**"+heading+"**")
                    for claim in claims:
                        show_claim(claim)
            if p.news:
                st.markdown("**Dated news**")
                for item in p.news:
                    show_claim(item.evidence, item.published_date+" Ã‚Â· ")
            if not p.pricing:
                st.caption("No supported price example collected. Other findings remain usable.")
            if not p.news:
                st.caption("No dated news verified in this window.")
            for gap in p.gaps:
                st.caption("Research gap: "+gap)
    if state.get("errors"):
        with st.expander("Run history and limitations"):
            st.caption("Includes earlier errors recovered during this run. Completed findings are retained.")
            for error in dict.fromkeys(state["errors"]):
                st.warning(error)

with ideas:
    st.subheader("Differentiation experiments")
    st.caption("Proposals to validate with customers. These are not claims of proven demand or empty market niches.")
    for item in plan.get("opportunities", []):
        with st.container(border=True):
            st.markdown("#### "+item["title"])
            st.write(item["proposal"])
            st.write("**Try this:** "+item["test"])
            st.write("**Look for:** "+item["success_signal"])
            show_basis(item["basis"])
    if not plan.get("opportunities"):
        st.info("Experiments appear after enough competitor evidence has been collected.")

with content:
    st.subheader("Content ideas you can adapt")
    st.caption("Draft concepts. Check any product, ingredient, or performance claim before using it.")
    for item in plan.get("content_ideas", []):
        with st.container(border=True):
            st.markdown("#### "+item["title"])
            st.caption(item["format"])
            st.write(item["outline"])
            st.write("**Call to action:** "+item["call_to_action"])
            show_basis(item["basis"])

with actions:
    st.subheader("Your proposed first week")
    for item in sorted(plan.get("actions", []), key=lambda x:x["day"]):
        with st.container(border=True):
            st.markdown(f"**Day {item['day']} Ã‚Â· {item['task']}**")
            st.write("Deliverable: "+item["deliverable"])
    if plan.get("questions"):
        st.markdown("### Assumptions to validate")
        for question in plan["questions"]:
            st.write("Ã¢â‚¬Â¢ "+question)

with evidence:
    st.caption("Public source snapshots. Brand messaging is attributed, not independently proven.")
    for source in state.get("sources", {}).values():
        with st.expander(source["title"]+" Ã‚Â· "+source["id"]):
            st.link_button("Read source", source["url"], key="source_"+source["id"])
            st.caption(f"Retrieved {source['retrieved_at']} Ã‚Â· Published {source.get('published_at') or 'not supplied'}")
            st.text(source["text"][:5000])
    counts = usage.counts()
    st.caption(f"Search/page requests: {counts.get('search',0)}/30 Ã‚Â· Model requests: {counts.get('model',0)}/36")
    st.dataframe([{"Step":k,"Detail":d,"Time":t} for k,d,t in usage.events() if k not in ("search","model")], hide_index=True)
    st.caption("Run ID: "+run_id)
    with st.expander("Full draft briefing"):
        st.code(render_report(state), language="markdown")

if pending:
    request = pending[0]
    with st.container(border=True):
        st.subheader("Review your briefing" if request["type"]=="review" else "Your input is needed")
        st.write(request["message"])
        if request["type"]=="review":
            target = st.selectbox("Brand to research again", list(profiles))
            feedback = st.text_input("What should we investigate?", placeholder="Find more evidence about their product range")
            with st.container(horizontal=True):
                approve = st.button("Approve briefing", type="primary")
                revise = st.button("Research this question", disabled=not feedback.strip() or state.get("revision_count",0)>=2)
                cancel = st.button("Cancel run")
            if approve or revise or cancel:
                execute(run_id, {"action":"approve" if approve else ("revise" if revise else "cancel"),
                                 "target_name":target,"feedback":feedback})
                st.rerun()
        elif request["type"]=="clarification":
            feedback = st.text_area("Clarify the market or reference brand")
            with st.container(horizontal=True):
                clarify = st.button("Update scope", disabled=not feedback.strip())
                partial = st.button("Continue with available competitors")
                cancel = st.button("Cancel run")
            if clarify or partial or cancel:
                execute(run_id, {"action":"clarify" if clarify else ("partial" if partial else "cancel"),"feedback":feedback})
                st.rerun()
        else:
            with st.container(horizontal=True):
                retry = st.button("Retry failed step")
                partial = st.button("Prepare partial briefing")
                cancel = st.button("Cancel run")
            if retry or partial or cancel:
                execute(run_id, {"action":"retry" if retry else ("partial" if partial else "cancel")})
                st.rerun()
elif state.get("status")=="approved":
    location = service.export(run_id)
    st.success("Briefing approved. Your report is ready.")
    with st.container(horizontal=True):
        st.download_button("Download briefing", (location/"briefing.md").read_text(encoding="utf-8"),
                           file_name="marketmate-briefing.md", mime="text/markdown")
        st.download_button("Download research JSON", (location/"briefing.json").read_text(encoding="utf-8"),
                           file_name="marketmate-research.json", mime="application/json")
elif state.get("status")!="cancelled":
    if st.button("Resume saved research", type="primary"):
        execute(run_id)
        st.rerun()
