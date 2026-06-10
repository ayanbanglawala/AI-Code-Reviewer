import streamlit as st
import time
from tools.diff_tool import get_diff_lines, get_summary_stats
from agents import performance_chain, security_chain, style_chain, merge_chain

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="AI Code Reviewer",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────
# THEME STATE
# ─────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "results" not in st.session_state:
    st.session_state.results = None
if "pipeline_log" not in st.session_state:
    st.session_state.pipeline_log = []

dark = st.session_state.dark_mode

# ─────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────
if dark:
    BG        = "#0d0d0f"
    SURFACE   = "#161618"
    BORDER    = "#2a2a2e"
    TEXT_PRI  = "#f0f0f2"
    TEXT_SEC  = "#8a8a96"
    ACCENT    = "#7c6dfa"        # violet — the signature
    ACCENT2   = "#3ecfcf"        # teal highlight
    ADD_BG    = "#0d2b1e"
    ADD_FG    = "#3ecf8e"
    REM_BG    = "#2b0d0d"
    REM_FG    = "#e87070"
    UN_BG     = "#1a1a1c"
    UN_FG     = "#6e6e7a"
    PILL_BG   = "#1e1a38"
    BADGE_DONE = "#1a3a2a"
    BADGE_DONE_FG = "#3ecf8e"
    BADGE_WAIT_FG = "#8a8a96"
    TOGGLE_BG = "#2a2a2e"
    SHADOW    = "0 4px 32px rgba(0,0,0,0.6)"
else:
    BG        = "#f5f5f7"
    SURFACE   = "#ffffff"
    BORDER    = "#e0e0e6"
    TEXT_PRI  = "#111114"
    TEXT_SEC  = "#6e6e7a"
    ACCENT    = "#5b4ef0"
    ACCENT2   = "#0da5a5"
    ADD_BG    = "#eafaf2"
    ADD_FG    = "#0e7a4c"
    REM_BG    = "#faeaea"
    REM_FG    = "#b83030"
    UN_BG     = "#f9f9fb"
    UN_FG     = "#9898a6"
    PILL_BG   = "#eeecfc"
    BADGE_DONE = "#ddf5ea"
    BADGE_DONE_FG = "#0e7a4c"
    BADGE_WAIT_FG = "#9898a6"
    TOGGLE_BG = "#e0e0e6"
    SHADOW    = "0 4px 32px rgba(0,0,0,0.10)"

# ─────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  /* ── Reset & base ── */
  html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif !important;
    background-color: {BG} !important;
    color: {TEXT_PRI} !important;
  }}
  .block-container {{
    padding: 2rem 3rem 4rem 3rem !important;
    max-width: 1200px !important;
  }}
  section[data-testid="stSidebar"] {{ display: none !important; }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: {BG}; }}
  ::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}

  /* ── Textarea override ── */
  textarea {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    background-color: {SURFACE} !important;
    color: {TEXT_PRI} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 10px !important;
    transition: border-color .2s;
  }}
  textarea:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {ACCENT}28 !important;
  }}

  /* ── Buttons ── */
  .stButton > button {{
    background: linear-gradient(135deg, {ACCENT}, {ACCENT2}) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: .55rem 1.6rem !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: .88rem !important;
    letter-spacing: .02em !important;
    transition: opacity .2s, transform .15s !important;
    box-shadow: 0 2px 16px {ACCENT}44 !important;
  }}
  .stButton > button:hover {{
    opacity: .88 !important;
    transform: translateY(-1px) !important;
  }}
  .stButton > button:active {{
    transform: translateY(0px) !important;
  }}

  /* ── Cards ── */
  .cr-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: {SHADOW};
  }}
  .cr-card-title {{
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: {TEXT_SEC};
    margin-bottom: .7rem;
  }}

  /* ── Pipeline track ── */
  .pipeline-wrap {{
    display: flex;
    align-items: center;
    gap: 0;
    margin: 1.4rem 0 1.8rem 0;
    overflow-x: auto;
    padding-bottom: .4rem;
  }}
  .pipe-step {{
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    min-width: 130px;
  }}
  .pipe-connector {{
    flex: 1;
    height: 2px;
    background: {BORDER};
    margin-top: -24px;
    min-width: 24px;
    max-width: 60px;
    transition: background .4s;
  }}
  .pipe-connector.done {{ background: linear-gradient(90deg, {ACCENT}, {ACCENT2}); }}
  .pipe-dot {{
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 2px solid {BORDER};
    background: {SURFACE};
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    transition: all .35s;
    position: relative;
    z-index: 1;
  }}
  .pipe-dot.active {{
    border-color: {ACCENT};
    background: {PILL_BG};
    box-shadow: 0 0 0 5px {ACCENT}22;
    animation: pulse-dot 1.2s infinite;
  }}
  .pipe-dot.done {{
    border-color: {ACCENT2};
    background: {BADGE_DONE};
  }}
  .pipe-label {{
    font-size: .72rem;
    font-weight: 500;
    color: {TEXT_SEC};
    margin-top: .45rem;
    text-align: center;
    letter-spacing: .02em;
  }}
  .pipe-label.active {{ color: {ACCENT}; font-weight: 700; }}
  .pipe-label.done   {{ color: {ACCENT2}; }}

  @keyframes pulse-dot {{
    0%, 100% {{ box-shadow: 0 0 0 4px {ACCENT}22; }}
    50%       {{ box-shadow: 0 0 0 9px {ACCENT}10; }}
  }}

  /* ── Log stream ── */
  .log-wrap {{
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: .78rem;
    color: {TEXT_SEC};
    max-height: 200px;
    overflow-y: auto;
    line-height: 1.7;
  }}
  .log-done  {{ color: {ADD_FG}; }}
  .log-run   {{ color: {ACCENT}; }}
  .log-info  {{ color: {TEXT_SEC}; }}

  /* ── Review content ── */
  .review-body {{
    font-size: .88rem;
    line-height: 1.75;
    color: {TEXT_PRI};
    white-space: pre-wrap;
  }}

  /* ── Diff table ── */
  .diff-table {{
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace;
    font-size: .78rem;
  }}
  .diff-table td {{
    padding: .18rem .7rem;
    white-space: pre;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 520px;
  }}
  .diff-add  {{ background: {ADD_BG}; color: {ADD_FG}; }}
  .diff-rem  {{ background: {REM_BG}; color: {REM_FG}; }}
  .diff-un   {{ background: {UN_BG};  color: {UN_FG};  }}
  .diff-sym  {{ width: 28px; text-align: center; font-weight: 700; }}

  /* ── Stat pill ── */
  .stat-pill {{
    display: inline-flex;
    align-items: center;
    gap: .35rem;
    padding: .25rem .75rem;
    border-radius: 999px;
    font-size: .78rem;
    font-weight: 600;
    margin-right: .5rem;
  }}
  .pill-add {{ background: {ADD_BG}; color: {ADD_FG}; }}
  .pill-rem {{ background: {REM_BG}; color: {REM_FG}; }}
  .pill-unch {{ background: {PILL_BG}; color: {ACCENT}; }}

  /* ── Header ── */
  .cr-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 1.4rem;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 2rem;
  }}
  .cr-wordmark {{
    display: flex;
    align-items: center;
    gap: .65rem;
  }}
  .cr-hex {{
    width: 34px;
    height: 34px;
    background: linear-gradient(135deg, {ACCENT}, {ACCENT2});
    clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
  }}
  .cr-brand {{
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -.02em;
    color: {TEXT_PRI};
  }}
  .cr-brand span {{ color: {ACCENT}; }}

  /* ── Toggle ── */
  .toggle-btn {{
    background: {TOGGLE_BG};
    border: 1px solid {BORDER};
    border-radius: 20px;
    padding: .3rem .85rem;
    font-size: .8rem;
    font-weight: 500;
    color: {TEXT_SEC};
    cursor: pointer;
    letter-spacing: .03em;
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    transition: all .2s;
  }}

  /* ── Section label ── */
  .section-eyebrow {{
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: {ACCENT};
    margin-bottom: .5rem;
  }}
  .section-title {{
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: -.02em;
    margin-bottom: .35rem;
    color: {TEXT_PRI};
  }}
  .section-sub {{
    font-size: .88rem;
    color: {TEXT_SEC};
    margin-bottom: 1.6rem;
    line-height: 1.5;
  }}

  /* ── Tab strip ── */
  .tab-strip {{
    display: flex;
    gap: .4rem;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 1.2rem;
    padding-bottom: 0;
  }}
  .tab-btn {{
    padding: .45rem 1rem;
    border-radius: 8px 8px 0 0;
    font-size: .82rem;
    font-weight: 600;
    color: {TEXT_SEC};
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    letter-spacing: .01em;
    transition: color .2s, border-color .2s;
  }}
  .tab-btn.active {{
    color: {ACCENT};
    border-bottom-color: {ACCENT};
    background: {PILL_BG};
  }}

  /* ── Streamlit overrides ── */
  [data-testid="stDecoration"] {{ display: none; }}
  div[data-testid="stVerticalBlock"] > div {{ gap: 0 !important; }}
  .stTabs [role="tab"] {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: .83rem !important;
  }}
  .stTabs [aria-selected="true"] {{
    color: {ACCENT} !important;
    border-bottom-color: {ACCENT} !important;
  }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
hcol1, hcol2 = st.columns([1, 0.12])
with hcol1:
    st.markdown(f"""
    <div class="cr-wordmark">
      <div class="cr-hex"></div>
      <div class="cr-brand">code<span>review</span>.ai</div>
    </div>
    """, unsafe_allow_html=True)
with hcol2:
    theme_label = "☀ Light" if dark else "🌙 Dark"
    if st.button(theme_label, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

st.markdown(f"<hr style='border:none;border-top:1px solid {BORDER};margin:.6rem 0 2rem 0;'>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# HERO INPUT SECTION
# ─────────────────────────────────────────
st.markdown(f"""
<div class="section-eyebrow">Multi-agent pipeline</div>
<div class="section-title">Review your code instantly</div>
<div class="section-sub">Security · Performance · Style — all three agents run in parallel,<br>then a merger agent synthesizes the final refactored output.</div>
""", unsafe_allow_html=True)

code_input = st.text_area(
    label="",
    placeholder="# Paste your Python code here…\ndef example():\n    pass",
    height=280,
    key="code_input",
    label_visibility="collapsed",
)

run_col, hint_col = st.columns([0.18, 0.82])
with run_col:
    run_clicked = st.button("⬡  Run Review", key="run_btn", use_container_width=True)
with hint_col:
    st.markdown(f"<div style='color:{TEXT_SEC};font-size:.82rem;padding-top:.6rem;'>Runs 4 agents sequentially — Security → Performance → Style → Merger</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# PIPELINE RUNNER
# ─────────────────────────────────────────
STAGES = [
    {"id": "security",    "icon": "🔒", "label": "Security"},
    {"id": "performance", "icon": "⚡", "label": "Performance"},
    {"id": "style",       "icon": "✦",  "label": "Style"},
    {"id": "merger",      "icon": "⬡",  "label": "Merger"},
]

def render_pipeline(current_idx: int, done_ids: set):
    dots_html = ""
    for i, stage in enumerate(STAGES):
        state = "done" if stage["id"] in done_ids else ("active" if i == current_idx else "idle")
        dot_cls   = f"pipe-dot {state}"
        label_cls = f"pipe-label {state}"
        icon = "✓" if state == "done" else stage["icon"]
        dots_html += f'<div class="pipe-step"><div class="{dot_cls}">{icon}</div><div class="{label_cls}">{stage["label"]}</div></div>'
        if i < len(STAGES) - 1:
            conn_cls = "pipe-connector done" if stage["id"] in done_ids else "pipe-connector"
            dots_html += f'<div class="{conn_cls}"></div>'
    return f'<div class="pipeline-wrap">{dots_html}</div>'


def render_log(logs: list):
    rows = ""
    for entry in logs[-14:]:
        cls = {"done": "log-done", "run": "log-run"}.get(entry["type"], "log-info")
        rows += f'<div class="{cls}">{entry["msg"]}</div>'
    return f'<div class="log-wrap">{rows}</div>'


def strip_code_fences(text: str) -> str:
    """Remove markdown code fences like ```python ... ``` from LLM output."""
    import re
    # Remove opening fence with optional language tag
    text = re.sub(r"^```[\w]*\n?", "", text.strip(), flags=re.MULTILINE)
    # Remove closing fence
    text = re.sub(r"^```\s*$", "", text.strip(), flags=re.MULTILINE)
    return text.strip()

def safe_html(text: str) -> str:
    """Escape HTML special chars for safe rendering inside markdown divs."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

if run_clicked and code_input.strip():
    st.session_state.results = None
    st.session_state.pipeline_log = []

    st.markdown(f"<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:.72rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{ACCENT};margin-bottom:.6rem;'>Pipeline status</div>", unsafe_allow_html=True)

    pipe_ph  = st.empty()
    log_ph   = st.empty()
    status_ph = st.empty()

    logs = []
    done_ids = set()

    def add_log(msg, typ="info"):
        ts = time.strftime("%H:%M:%S")
        logs.append({"msg": f"[{ts}]  {msg}", "type": typ})

    def update(current_idx):
        pipe_ph.markdown(render_pipeline(current_idx, done_ids), unsafe_allow_html=True)
        log_ph.markdown(render_log(logs), unsafe_allow_html=True)

    def invoke_safe(chain, inputs, label):
        """Invoke a LangChain chain and always return a plain non-empty string."""
        try:
            result = chain.invoke(inputs)
            if result is None:
                return f"[{label}] Agent returned no output."
            if not isinstance(result, str):
                result = str(result)
            return result.strip() or f"[{label}] Agent returned empty string."
        except Exception as exc:
            return f"[{label}] Agent error: {exc}"

    try:
        # ── Stage 0: Security ──
        add_log("Starting Security agent…", "run")
        update(0)
        status_ph.info("🔒 Running security analysis…")
        sec_result = invoke_safe(security_chain, {"code": code_input}, "Security")
        done_ids.add("security")
        add_log("Security review complete.", "done")

        # ── Stage 1: Performance ──
        add_log("Starting Performance agent…", "run")
        update(1)
        status_ph.info("⚡ Running performance analysis…")
        perf_result = invoke_safe(performance_chain, {"code": code_input}, "Performance")
        done_ids.add("performance")
        add_log("Performance review complete.", "done")

        # ── Stage 2: Style ──
        add_log("Starting Style agent…", "run")
        update(2)
        status_ph.info("✦  Running style analysis…")
        style_result = invoke_safe(style_chain, {"code": code_input}, "Style")
        done_ids.add("style")
        add_log("Style review complete.", "done")

        # ── Stage 3: Merger ──
        add_log("Synthesizing all reviews → Merger agent…", "run")
        update(3)
        status_ph.info("⬡  Merging reviews and generating refactored code…")
        merged_result = invoke_safe(merge_chain, {
            "code":               code_input,
            "security_review":    sec_result,
            "performance_review": perf_result,
            "style_review":       style_result,
        }, "Merger")
        done_ids.add("merger")
        add_log("Merger complete. Refactored code ready.", "done")
        update(4)
        status_ph.success("✓  All agents finished.")

        # ── Strip markdown fences & ensure string before diffing ──
        merged_clean = strip_code_fences(merged_result)
        if not merged_clean.strip():
            merged_clean = code_input
            add_log("⚠ Merger returned empty — diff shows original.", "info")

        # ── Diff ──
        diff_lines = get_diff_lines(str(code_input), str(merged_clean))
        stats      = get_summary_stats(diff_lines)

        st.session_state.results = {
            "security":    sec_result,
            "performance": perf_result,
            "style":       style_result,
            "merged":      merged_clean,
            "diff_lines":  diff_lines,
            "stats":       stats,
        }
        st.session_state.pipeline_log = logs

    except Exception as pipeline_err:
        status_ph.error(f"Pipeline failed: {pipeline_err}")
        add_log(f"Fatal: {pipeline_err}", "info")
        log_ph.markdown(render_log(logs), unsafe_allow_html=True)
        st.stop()

    st.rerun()

elif run_clicked and not code_input.strip():
    st.warning("Paste some code first, then hit Run Review.")

# ─────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────
if st.session_state.results:
    r = st.session_state.results

    st.markdown(f"<div style='height:1.8rem'></div>", unsafe_allow_html=True)
    st.markdown(f"<hr style='border:none;border-top:1px solid {BORDER};margin:0 0 1.8rem 0;'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="section-eyebrow">Results</div>
    <div class="section-title">Review complete</div>
    """, unsafe_allow_html=True)

    # ── Restored pipeline (all done) ──
    done_all = {"security", "performance", "style", "merger"}
    st.markdown(render_pipeline(99, done_all), unsafe_allow_html=True)

    # ── Tabs ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⬡  Merged Output",
        "🔒 Security",
        "⚡ Performance",
        "✦  Style",
        "⇄  Diff",
    ])

    with tab1:
        st.markdown(f"<div class='cr-card'><div class='cr-card-title'>Refactored Code</div>", unsafe_allow_html=True)
        st.code(r["merged"], language="python")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown(f"<div class='cr-card'><div class='cr-card-title'>Security Analysis</div><div class='review-body'>{safe_html(r['security'])}</div></div>", unsafe_allow_html=True)

    with tab3:
        st.markdown(f"<div class='cr-card'><div class='cr-card-title'>Performance Analysis</div><div class='review-body'>{safe_html(r['performance'])}</div></div>", unsafe_allow_html=True)

    with tab4:
        st.markdown(f"<div class='cr-card'><div class='cr-card-title'>Style Analysis</div><div class='review-body'>{safe_html(r['style'])}</div></div>", unsafe_allow_html=True)

    with tab5:
        s = r["stats"]
        st.markdown(f"""
        <div style='margin-bottom:1rem;'>
          <span class='stat-pill pill-add'>+{s['lines_added']} added</span>
          <span class='stat-pill pill-rem'>-{s['lines_removed']} removed</span>
          <span class='stat-pill pill-unch'>{s['lines_unchanged']} unchanged</span>
        </div>
        """, unsafe_allow_html=True)

        # Build diff table
        rows = ""
        for line in r["diff_lines"]:
            t = line["type"]
            if t == "added":
                sym, cls = "+", "diff-add"
            elif t == "removed":
                sym, cls = "−", "diff-rem"
            else:
                sym, cls = " ", "diff-un"
            content = line["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            rows += f'<tr class="{cls}"><td class="diff-sym">{sym}</td><td>{content}</td></tr>'

        st.markdown(f"""
        <div class='cr-card' style='overflow-x:auto;'>
          <div class='cr-card-title'>Line-by-line diff — original → refactored</div>
          <table class='diff-table'><tbody>{rows}</tbody></table>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────
if not st.session_state.results and not run_clicked:
    st.markdown(f"""
    <div style='text-align:center;padding:3.5rem 0;color:{TEXT_SEC};'>
      <div style='font-size:2.5rem;margin-bottom:.8rem;opacity:.35;'>⬡</div>
      <div style='font-size:.9rem;font-weight:500;'>Paste code above and hit <strong style="color:{ACCENT}">Run Review</strong></div>
      <div style='font-size:.8rem;margin-top:.35rem;opacity:.7;'>Security · Performance · Style · Merger — all four agents, one click</div>
    </div>
    """, unsafe_allow_html=True)
