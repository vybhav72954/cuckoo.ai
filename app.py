"""
Pharma AI - Streamlit Web Application

An Agentic AI System for Rapid Pharmaceutical Opportunity Assessment
"""
import streamlit as st
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents import MasterAgent, ResearchQuery, SynthesizedReport
from config import COLORS, AGENTS

# Page configuration
st.set_page_config(
    page_title="Cuckoo.ai",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(135deg, #0F1419 0%, #1A1F2E 100%);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1E3A5F 0%, #2C5282 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border-left: 4px solid #F7931E;
    }
    
    .main-header h1 {
        color: #FFFFFF;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    
    .main-header p {
        color: #B0C4DE;
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
    }
    
    /* Score cards */
    .score-card {
        background: linear-gradient(145deg, #1A2332 0%, #232D3F 100%);
        border: 1px solid #3D4A5C;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .score-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    
    .score-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #F7931E;
    }
    
    .score-label {
        font-size: 0.9rem;
        color: #8899A6;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Agent cards */
    .agent-card {
        background: #1A2332;
        border: 1px solid #3D4A5C;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .agent-card.running {
        border-color: #F7931E;
        animation: pulse 1.5s infinite;
    }
    
    .agent-card.completed {
        border-color: #28A745;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Finding cards */
    .finding-card {
        background: linear-gradient(145deg, #1E2A3A 0%, #263445 100%);
        border-left: 4px solid #17A2B8;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .finding-category {
        color: #17A2B8;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .finding-text {
        color: #E8E8E8;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* Recommendation badge */
    .recommendation-badge {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-weight: 700;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .badge-proceed {
        background: linear-gradient(90deg, #28A745 0%, #20C997 100%);
        color: white;
    }
    
    .badge-caution {
        background: linear-gradient(90deg, #FFC107 0%, #FFB300 100%);
        color: #1A1F2E;
    }
    
    .badge-reconsider {
        background: linear-gradient(90deg, #DC3545 0%, #C82333 100%);
        color: white;
    }
    
    /* Progress indicator */
    .progress-step {
        display: flex;
        align-items: center;
        padding: 0.5rem 0;
        color: #8899A6;
    }
    
    .progress-step.active {
        color: #F7931E;
    }
    
    .progress-step.done {
        color: #28A745;
    }
    
    /* Sidebar styling */
    .sidebar-title {
        color: #F7931E;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    /* Input styling */
    .stTextArea textarea {
        background: #1A2332 !important;
        border: 1px solid #3D4A5C !important;
        color: #E8E8E8 !important;
        border-radius: 8px !important;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #F7931E 0%, #FF6B00 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.7rem 2rem !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 20px rgba(247, 147, 30, 0.4) !important;
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background: #1A2332;
        border: 1px solid #3D4A5C;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #1A2332;
        border-radius: 8px 8px 0 0;
        color: #8899A6;
        border: 1px solid #3D4A5C;
    }
    
    .stTabs [aria-selected="true"] {
        background: #263445 !important;
        color: #F7931E !important;
        border-bottom: 2px solid #F7931E !important;
    }
</style>
""", unsafe_allow_html=True)


def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>Cuckoo.ai</h1>
        <p>Your Research Assistant to go through Journal and Database and create detailed reports</>
        <p>Agentic AI System with Institutional Knowledge Memory</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with controls and info"""
    with st.sidebar:
        st.markdown('<p class="sidebar-title">Research Configuration</p>', unsafe_allow_html=True)
        
        # Quick molecule selection
        molecule = st.selectbox(
            "Select Molecule",
            ["Metformin", "Aspirin", "Atorvastatin", "Other"],
            index=0
        )
        
        if molecule == "Other":
            molecule = st.text_input("Enter molecule name")
        
        # Indication selection
        indication = st.selectbox(
            "Target Indication",
            ["Anti-inflammatory", "Oncology", "Cardiovascular", "NASH/NAFLD", "Anti-aging", "Other"],
            index=0
        )
        
        if indication == "Other":
            indication = st.text_input("Enter indication")
        
        # Geography
        geography = st.selectbox(
            "Target Geography",
            ["Global", "North America", "Europe", "Asia Pacific"],
            index=0
        )
        
        st.markdown("---")
        
        # Agent selection
        st.markdown('<p class="sidebar-title">Agent Selection</p>', unsafe_allow_html=True)
        
        agents_selected = {}
        for agent_id, agent_info in AGENTS.items():
            if agent_id != 'master':
                agents_selected[agent_id] = st.checkbox(
                    f"{agent_info['icon']} {agent_info['name']}",
                    value=True,
                    key=f"agent_{agent_id}"
                )
        
        st.markdown("---")
        
        # Info panel
        st.markdown('<p class="sidebar-title">ℹ️ About</p>', unsafe_allow_html=True)
        st.info("""
        **Team Trikala**
        
        This PoC demonstrates an Agentic AI system 
        that reduces pharmaceutical opportunity 
        evaluation from 8-12 weeks to 5-10 days.
        
        **Key Features:**
        - Institutional Memory
        - Multi-Agent Research
        - Delta Refresh Logic
        - Automated Synthesis
        """)
        
        return molecule, indication, geography, agents_selected


def render_score_cards(report: SynthesizedReport):
    """Render the score cards"""
    cols = st.columns(6)
    
    scores = [
        ("Overall", report.overall_score),
        ("Market", report.market_attractiveness),
        ("Competitive", report.competitive_intensity),
        ("Regulatory", report.regulatory_feasibility),
        ("Scientific", report.scientific_rationale),
        ("Supply", report.supply_chain_feasibility),
    ]
    
    for col, (label, score, icon) in zip(cols, scores):
        with col:
            color = "#28A745" if score >= 7.5 else "#FFC107" if score >= 5.5 else "#DC3545"
            st.markdown(f"""
            <div class="score-card">
                <div style="font-size: 1.5rem;">{icon}</div>
                <div class="score-value" style="color: {color};">{score:.1f}</div>
                <div class="score-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_recommendation_badge(score: float):
    """Render the recommendation badge"""
    if score >= 7.5:
        badge_class = "badge-proceed"
        text = "PROCEED"
    elif score >= 5.5:
        badge_class = "badge-caution"
        text = "PROCEED WITH CAUTION"
    else:
        badge_class = "badge-reconsider"
        text = "RECONSIDER"
    
    st.markdown(f"""
    <div style="text-align: center; margin: 1.5rem 0;">
        <span class="recommendation-badge {badge_class}">{text}</span>
    </div>
    """, unsafe_allow_html=True)


def render_key_findings(findings: list):
    """Render key findings"""
    for finding in findings:
        category_colors = {
            "Clinical Evidence": "#17A2B8",
            "IP Landscape": "#6F42C1",
            "Market Intelligence": "#28A745",
            "Scientific Literature": "#FD7E14",
            "Supply Chain": "#20C997"
        }
        color = category_colors.get(finding.get("category", ""), "#17A2B8")
        
        st.markdown(f"""
        <div class="finding-card" style="border-left-color: {color};">
            <div class="finding-category" style="color: {color};">{finding.get('category', 'Finding')}</div>
            <div class="finding-text">{finding.get('finding', '')}</div>
            <div style="color: #6B7280; font-size: 0.8rem; margin-top: 0.5rem;">
                Source: {finding.get('source', 'N/A')} | Confidence: {finding.get('confidence', 0)*100:.0f}%
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_agent_progress(agent_updates: list):
    """Render agent execution progress"""
    for update in agent_updates:
        agent_info = AGENTS.get(update['agent'], {'icon': '🔄', 'name': update['agent']})
        status = update['status']
        
        if status == 'completed':
            status_icon = '✅'
            status_class = 'done'
        elif status == 'running':
            status_icon = '⏳'
            status_class = 'active'
        else:
            status_icon = '📋'
            status_class = ''
        
        st.markdown(f"""
        <div class="progress-step {status_class}">
            <span style="margin-right: 0.5rem;">{status_icon}</span>
            <span style="margin-right: 0.5rem;">{agent_info.get('icon', '🔄')}</span>
            <span>{agent_info.get('name', update['agent'])}: {update['message']}</span>
        </div>
        """, unsafe_allow_html=True)


async def run_research(query: ResearchQuery, progress_container):
    """Run the research and update progress"""
    master = MasterAgent()
    updates = []
    
    def callback(update):
        updates.append(update)
        with progress_container:
            render_agent_progress(updates)
    
    report = await master.execute_research(query, callback=callback)
    return report


def main():
    """Main application"""
    render_header()
    
    # Sidebar
    molecule, indication, geography, agents_selected = render_sidebar()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Research Query")
        
        # Build natural language query
        default_query = f"Evaluate {molecule} for {indication} indication in {geography} market"
        
        query_text = st.text_area(
            "Enter your research question",
            value=default_query,
            height=100,
            placeholder="E.g., 'Evaluate Metformin for anti-inflammatory indications'"
        )
        
        run_button = st.button("Start Research", use_container_width=True)
    
    with col2:
        st.markdown("### Quick Stats")
        st.metric("Agents Selected", sum(agents_selected.values()))
        st.metric("Estimated Time", "~30 seconds")
        st.metric("Data Sources", "10+")
    
    st.markdown("---")
    
    # Run research
    if run_button and query_text:
        query = ResearchQuery.from_natural_language(query_text)
        query.molecule = molecule
        query.indication = indication
        query.geography = geography
        
        # Progress section
        st.markdown("### Research Progress")
        progress_container = st.empty()
        
        with st.spinner("Executing research agents..."):
            report = asyncio.run(run_research(query, progress_container))
        
        # Store report in session state
        st.session_state['report'] = report
        st.success("✅ Research complete!")
    
    # Display results
    if 'report' in st.session_state:
        report = st.session_state['report']
        
        st.markdown("---")
        st.markdown("## 📊 Assessment Results")
        
        # Recommendation badge
        render_recommendation_badge(report.overall_score)
        
        # Score cards
        render_score_cards(report)
        
        st.markdown("---")
        
        # Tabs for detailed results
        tabs = st.tabs(["Summary", "Key Findings", "Recommendations", "Agent Details", "Export"])
        
        with tabs[0]:
            st.markdown("### Executive Summary")
            st.markdown(report.executive_summary)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sources", report.total_sources)
            with col2:
                st.metric("Execution Time", f"{report.execution_time_ms/1000:.1f}s")
            with col3:
                st.metric("Data Freshness", report.data_freshness)
        
        with tabs[1]:
            st.markdown("### Key Findings")
            render_key_findings(report.key_findings)
        
        with tabs[2]:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Recommendations")
                for rec in report.recommendations:
                    st.markdown(f"- {rec}")
                
                st.markdown("### Opportunities")
                for opp in report.opportunities:
                    st.markdown(f"- {opp}")
            
            with col2:
                st.markdown("### Risks")
                for risk in report.risks:
                    st.markdown(f"- {risk}")
                
                st.markdown("### Next Steps")
                for step in report.next_steps:
                    st.markdown(f"- {step}")
        
        with tabs[3]:
            st.markdown("### Agent Execution Details")
            
            for agent_id, result in report.agent_results.items():
                with st.expander(f"{AGENTS.get(agent_id, {}).get('icon', '🔄')} {result.get('agent_name', agent_id)}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Sources", result.get('source_count', 0))
                    with col2:
                        st.metric("Confidence", f"{result.get('confidence_score', 0)*100:.0f}%")
                    with col3:
                        st.metric("Time", f"{result.get('execution_time_ms', 0):.0f}ms")
                    
                    if result.get('data'):
                        st.json(result.get('data', {}))
        
        with tabs[4]:
            st.markdown("### Export Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                report_json = json.dumps(report.to_dict(), indent=2, default=str)
                st.download_button(
                    "Download JSON",
                    report_json,
                    file_name=f"report_{report.report_id}.json",
                    mime="application/json"
                )
            
            with col2:
                st.button("Generate PDF Report", disabled=True, help="Coming soon!")
            
            with col3:
                st.button("Export to Excel", disabled=True, help="Coming soon!")


if __name__ == "__main__":
    main()
