# 🧬 Cuckoo.ai — Agentic AI for Rapid Pharmaceutical Opportunity Assessment

> Ask, in plain English, whether to pursue a drug molecule for a new indication. Cuckoo.ai runs a panel of research agents over institutional memory and (planned) external sources, then returns a scored, recommendation-bearing report you can download as PDF or JSON.

**Status:** Working prototype — currently runs on bundled **mock data** (no live API/LLM calls yet). Built for **EY Techathon 6.0 · Round 2** and being developed toward a production system (see *Limitations & Roadmap*).

---

## The Problem

Pharmaceutical teams burn time and money re-evaluating drug opportunities by hand:

| Metric | Today |
|--------|-------|
| Evaluation time | 8–12 weeks per molecule |
| Cost per evaluation | $38K–$52K |
| Rework (no institutional memory) | ~35% |
| Disconnected data sources | 6+ |

With a **$236B patent cliff (2025–2030)**, finding differentiated opportunities faster is existential.

---

## The Solution

An **agentic AI system with institutional-knowledge memory**. Its differentiator is **Read-Before-Write**: it checks what the organization already knows *before* spending effort on fresh research, and only refreshes what has gone stale.

**Target outcomes** (value proposition):

- Evaluation time from **8–12 weeks → 5–10 days**
- **~3×** annual throughput (10–12 → 24–36 evaluations/year)
- **<5%** rework via institutional memory (vs ~35%)
- Standardized, auditable, **confidence-scored** reports

---

## Key Features

- **Read-Before-Write + delta refresh** — checks the archive first, reuses still-fresh prior findings, and only re-runs agents whose data is stale (per-domain freshness thresholds).
- **6 specialized agents** — institutional knowledge, clinical trials, patents, market (IQVIA), supply chain (EXIM), and web/regulatory intelligence.
- **Weighted, confidence-scored recommendation** — five sub-scores roll up into an overall score and a clear **PROCEED / PROCEED WITH CAUTION / RECONSIDER** verdict.
- **Conservative scoring** — missing data is scored low, so a molecule we know nothing about can never look falsely attractive.
- **Selectable agents** — choose which agents to run from the sidebar.
- **One-click export** — download the report as **PDF** or **JSON**.
- **Two entry points** — an interactive **Streamlit** web app or a **CLI** demo.

---

## How It Works

Every run flows through `MasterAgent.execute_research()`:

1. **Parse** the natural-language query into a molecule + indication.
2. **Read-Before-Write** — the Internal Knowledge agent searches archived reports for prior research.
3. **Delta refresh** — compare the prior research's age against per-domain freshness thresholds; reuse what's fresh, re-run what's stale.
4. **Research** — run the selected agents; each returns a structured, confidence-scored `AgentResult`.
5. **Synthesize** — aggregate into a scored report: executive summary, key findings, recommendations, risks, opportunities, and next steps.

### The agents

| Agent | Focus | Sources (simulated today) |
|-------|-------|---------------------------|
| Internal Knowledge | Prior reports / institutional memory | Archived reports |
| Clinical Trials | Trial landscape & phases | ClinicalTrials.gov, WHO ICTRP, EudraCT |
| Patent Landscape | IP status, expiry, freedom-to-operate | USPTO, WIPO, EPO, Orange Book |
| IQVIA Insights | Market size, growth, competition | IQVIA MIDAS, Symphony Health |
| EXIM Trends | API supply chain & trade | EXIM trade data, supplier DB |
| Web Intelligence | Literature, news, regulatory | PubMed, FDA, EMA, industry news |

> The sources above are what each agent *will* query in production; today they are served from `mock_data/`.

### Scoring

| Dimension | Weight |
|-----------|--------|
| Market attractiveness | 0.25 |
| Scientific rationale | 0.25 |
| Competitive intensity | 0.20 |
| Regulatory feasibility | 0.20 |
| Supply-chain feasibility | 0.10 |

Overall **≥ 7.5** → PROCEED · **≥ 5.5** → PROCEED WITH CAUTION · otherwise → RECONSIDER.

---

## Quick Start

Requires **Python 3.10+**. Runtime dependencies are just `streamlit` and `reportlab`.

```bash
# 1. Install runtime dependencies
pip install -r requirements.txt

# 2a. Launch the web app
streamlit run app.py

# 2b. ...or run the CLI demo (writes a PDF + JSON to ./reports/)
python demo_run.py
```

Run the orchestrator directly (prints the synthesized report as JSON):

```bash
python -m src.agents.master_agent
```

For development and tests:

```bash
pip install -r requirements-dev.txt   # adds pytest, pytest-asyncio
```

---

## Example

Query: *"Evaluate Metformin for anti-inflammatory indications"*

| | |
|--|--|
| Overall score | **7.4 / 10** |
| Verdict | ⚠️ PROCEED WITH CAUTION |
| Sources analyzed | 24 |
| Prior reports found | 2 |

---

## Project Structure

```
app.py                    # Streamlit web app
demo_run.py               # CLI demo (PDF + JSON output)
config.py                 # config, palette, agent metadata, score thresholds
src/agents/
  base_agent.py           # BaseAgent, AgentResult, ResearchQuery, AgentStatus
  research_agents.py      # the 6 agents + factory
  master_agent.py         # orchestration, delta refresh, scoring, report
src/reports/
  pdf_generator.py        # ReportLab PDF report
mock_data/                # pharma_data.json, archived_reports.json
reports/                  # generated RPT-*.json / .pdf
docs/                     # guide, roadmap, architecture
```

---

## Limitations & Roadmap

This is a working prototype, not production:

- **Mock-backed** — agents read from `mock_data/` and simulate network latency; there are **no real API or LLM calls** yet, and only Metformin has seeded data.
- **No persistence** — the institutional "archive" is a static JSON file.

Planned next: real data connectors (ClinicalTrials.gov, patents, market, trade), LLM-driven query parsing and synthesis, a persistent institutional-memory store, geography-aware analysis, and a test suite.

---

## Team

| Name | Role |
|------|------|
| Pranav Taneja | Prompt Engineering |
| Sneha Yadav | Data Preparation & Visualization |
| Vybhav Chaturvedi | Solution Architect |

---

## License

Released under the MIT License — see [LICENSE](LICENSE).
