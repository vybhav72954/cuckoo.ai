"""
Specialized Research Agents for Pharma AI System
EY Techathon 6.0 - Round 2
"""
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent, AgentResult, AgentStatus, ResearchQuery

# Load mock data
def load_mock_data():
    data_path = Path(__file__).parent.parent.parent / "mock_data" / "pharma_data.json"
    if data_path.exists():
        with open(data_path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_archived_reports():
    data_path = Path(__file__).parent.parent.parent / "mock_data" / "archived_reports.json"
    if data_path.exists():
        with open(data_path, encoding="utf-8") as f:
            return json.load(f)
    return {"reports": [], "semantic_index": {}}


def _normalize_key_findings(raw):
    """Coerce an archived report's key_findings into a list of dicts so downstream
    synthesis can rely on dict access. Drops None, wraps scalars, ignores non-lists."""
    if not isinstance(raw, list):
        return []
    normalized = []
    for item in raw:
        if isinstance(item, dict):
            normalized.append(item)
        elif item is not None:
            normalized.append({"finding": str(item)})
    return normalized


class InternalKnowledgeAgent(BaseAgent):
    """Agent that searches institutional memory and archived reports"""
    
    def __init__(self):
        super().__init__(
            name="Internal Knowledge Agent",
            description="Searches archived reports and institutional memory for relevant prior research"
        )
        
    def get_data_sources(self) -> List[str]:
        return ["Archived Reports", "Institutional Memory DB", "Previous Analyses"]
    
    async def execute(self, query: ResearchQuery) -> AgentResult:
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        
        # Simulate async operation
        await asyncio.sleep(0.3)
        
        # Load archived reports
        archive = load_archived_reports()
        
        # Search for relevant reports
        relevant_reports = []
        keywords = [query.molecule.lower(), query.indication.lower()]
        
        for report in archive.get("reports", []):
            tags = [t.lower() for t in report.get("tags", [])]
            if any(kw in tags for kw in keywords if kw):
                score = report.get("score")
                if not isinstance(score, dict):
                    score = {}
                relevant_reports.append({
                    "report_id": report.get("report_id", ""),
                    "title": f"{report.get('molecule', '?')} - {report.get('indication', '?')}",
                    "date": report.get("created_date", ""),
                    "indication": report.get("indication", ""),
                    "summary": report.get("executive_summary", ""),
                    "recommendation": report.get("recommendation", ""),
                    "score": score.get("overall", 0),
                    "scores": score,
                    "key_findings": _normalize_key_findings(report.get("key_findings")),
                    "relevance": "High" if query.molecule.lower() in [t.lower() for t in report.get("tags", [])] else "Medium"
                })
        
        # Determine if we have reusable findings
        reusable_findings = []
        outdated_areas = []
        
        for report in relevant_reports:
            reusable_findings.append({
                "source": report["report_id"],
                "finding": report["summary"][:200],
                "freshness": "Recent" if "2024" in report["date"] else "May need refresh"
            })
        
        # Domains flagged as stale -> MasterAgent force-refreshes these regardless of
        # age. Emitted as agent ids so the orchestrator can act on them directly.
        if query.indication.lower() in ("inflammation", "anti-inflammatory"):
            outdated_areas = ["clinical_trials", "iqvia_insights"]

        # How stale is the prior research? Drives delta-refresh in MasterAgent.
        last_research_date = None
        days_since_last_research = None
        report_dates = []
        for r in relevant_reports:
            raw_date = (r.get("date") or "")[:10]
            try:
                report_dates.append(datetime.strptime(raw_date, "%Y-%m-%d"))
            except ValueError:
                continue
        if report_dates:
            most_recent = max(report_dates)
            last_research_date = most_recent.strftime("%Y-%m-%d")
            days_since_last_research = (datetime.now() - most_recent).days

        execution_time = (time.time() - start_time) * 1000
        self.status = AgentStatus.COMPLETED
        self.last_run = datetime.now()
        
        return self._create_result(
            data={
                "relevant_reports": relevant_reports,
                "reusable_findings": reusable_findings,
                "areas_needing_refresh": outdated_areas,
                "recommendation": "PARTIAL_REUSE" if relevant_reports else "FULL_RESEARCH",
                "prior_research_exists": len(relevant_reports) > 0,
                "last_research_date": last_research_date,
                "days_since_last_research": days_since_last_research,
                "estimated_time_saved": f"{len(relevant_reports) * 15}%" if relevant_reports else "0%"
            },
            execution_time=execution_time,
            confidence=0.9 if relevant_reports else 0.5,
            sources=len(relevant_reports),
            freshness_date=datetime.now().strftime("%Y-%m-%d")
        )


class ClinicalTrialsAgent(BaseAgent):
    """Agent that analyzes clinical trial landscape"""
    
    def __init__(self):
        super().__init__(
            name="Clinical Trials Agent",
            description="Analyzes clinical trial landscape from ClinicalTrials.gov and WHO ICTRP"
        )
        
    def get_data_sources(self) -> List[str]:
        return ["ClinicalTrials.gov", "WHO ICTRP", "EudraCT"]
    
    async def execute(self, query: ResearchQuery) -> AgentResult:
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        
        await asyncio.sleep(0.5)  # Simulate API call
        
        mock_data = load_mock_data()
        
        # Get trials for the molecule-indication pair
        key = f"{query.molecule.lower()}_{query.indication.lower().replace('-', '_').replace(' ', '_')}"
        trials = mock_data.get("clinical_trials", {}).get(key, [])
        
        # If no exact match, try molecule + inflammation
        if not trials and query.molecule.lower() == "metformin":
            trials = mock_data.get("clinical_trials", {}).get("metformin_inflammation", [])
        
        # Analyze trials
        phase_distribution = {"Phase 1": 0, "Phase 2": 0, "Phase 3": 0, "Phase 4": 0}
        status_distribution = {"Completed": 0, "Recruiting": 0, "Active": 0, "Not yet recruiting": 0}

        # Exact (normalized) status->bucket map. Substring matching previously
        # miscounted "Active, not recruiting" and "Not yet recruiting" as Recruiting.
        status_buckets = {
            "completed": "Completed",
            "recruiting": "Recruiting",
            "active, not recruiting": "Active",
            "not yet recruiting": "Not yet recruiting",
        }

        for trial in trials:
            phase = trial.get("phase", "Unknown")
            if phase in phase_distribution:
                phase_distribution[phase] += 1

            status = trial.get("status")
            status = status.strip().lower() if isinstance(status, str) else ""
            bucket = status_buckets.get(status)
            if bucket:
                status_distribution[bucket] += 1
        
        # Generate insights
        insights = []
        if phase_distribution["Phase 3"] > 0:
            insights.append("Late-stage trials indicate mature evidence base")
        if status_distribution["Recruiting"] > 0:
            insights.append(f"{status_distribution['Recruiting']} trials actively recruiting - competitive landscape evolving")
        if status_distribution["Completed"] > 0:
            insights.append(f"{status_distribution['Completed']} completed trials provide efficacy/safety data")
        
        execution_time = (time.time() - start_time) * 1000
        self.status = AgentStatus.COMPLETED
        self.last_run = datetime.now()
        
        return self._create_result(
            data={
                "total_trials": len(trials),
                "trials": trials[:5],  # Top 5 most relevant
                "phase_distribution": phase_distribution,
                "status_distribution": status_distribution,
                "insights": insights,
                "key_endpoints": ["CRP reduction", "Inflammatory markers", "Disease activity scores"],
                "largest_trial": max(trials, key=lambda x: x.get("enrollment", 0)) if trials else None
            },
            execution_time=execution_time,
            confidence=0.85,
            sources=len(trials),
            freshness_date=datetime.now().strftime("%Y-%m-%d")
        )


class PatentLandscapeAgent(BaseAgent):
    """Agent that evaluates patent status and IP landscape"""
    
    def __init__(self):
        super().__init__(
            name="Patent Landscape Agent",
            description="Evaluates patent status, expiry dates, and IP opportunities"
        )
        
    def get_data_sources(self) -> List[str]:
        return ["USPTO", "WIPO", "EPO", "Orange Book"]
    
    async def execute(self, query: ResearchQuery) -> AgentResult:
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        
        await asyncio.sleep(0.4)
        
        mock_data = load_mock_data()
        patents = mock_data.get("patents", {}).get(query.molecule.lower(), [])
        
        # Analyze patents
        active_patents = [p for p in patents if p.get("status") == "Active"]
        expired_patents = [p for p in patents if p.get("status") == "Expired"]
        
        # Find opportunities
        opportunities = []
        risks = []
        
        if not active_patents:
            opportunities.append("Base compound is off-patent - generic entry possible")
        
        # Check for method of use patents
        method_patents = [p for p in active_patents if p.get("type") == "Method of Use"]
        if method_patents:
            risks.append(f"{len(method_patents)} active method-of-use patents may block new indication")
        
        formulation_patents = [p for p in active_patents if p.get("type") == "Formulation"]
        if formulation_patents:
            opportunities.append("Novel formulation could provide differentiation and patent protection")
        
        # Earliest active-patent expiry = patent cliff. Parse to dates so the
        # comparison is chronological (not lexicographic) and malformed/missing
        # dates are dropped rather than skewing the result.
        active_expiries = []
        for p in active_patents:
            try:
                # .date() drops any time/tz, so mixed naive/aware values from
                # fromisoformat can't clash in min() (expiry is a calendar date).
                active_expiries.append(datetime.fromisoformat(p.get("expiry_date")).date())
            except (TypeError, ValueError):
                continue
        patent_cliff_date = (
            min(active_expiries).strftime("%Y-%m-%d") if active_expiries else "Already off-patent"
        )

        execution_time = (time.time() - start_time) * 1000
        self.status = AgentStatus.COMPLETED
        self.last_run = datetime.now()

        return self._create_result(
            data={
                "total_patents": len(patents),
                "active_patents": len(active_patents),
                "expired_patents": len(expired_patents),
                "patents": patents,
                "patent_cliff_date": patent_cliff_date,
                "opportunities": opportunities,
                "risks": risks,
                "recommendation": "FAVORABLE" if len(active_patents) <= 1 else "CHALLENGING",
                "freedom_to_operate": "High" if not method_patents else "Requires analysis"
            },
            execution_time=execution_time,
            confidence=0.9,
            sources=len(patents),
            freshness_date=datetime.now().strftime("%Y-%m-%d")
        )


class IQVIAInsightsAgent(BaseAgent):
    """Agent that analyzes market data and competitive landscape"""
    
    def __init__(self):
        super().__init__(
            name="IQVIA Insights Agent",
            description="Analyzes market data, sales trends, and competitive landscape"
        )
        
    def get_data_sources(self) -> List[str]:
        return ["IQVIA MIDAS", "Symphony Health", "Internal Sales Data"]
    
    async def execute(self, query: ResearchQuery) -> AgentResult:
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        
        await asyncio.sleep(0.6)
        
        mock_data = load_mock_data()
        market = mock_data.get("market_data", {}).get(query.molecule.lower(), {})
        
        if not market:
            market = {
                "global_market_size_2024": 0,
                "cagr_2024_2030": 0,
                "top_markets": [],
                "competition": []
            }
        
        # Calculate market opportunity
        current_size = market.get("global_market_size_2024", 0)
        cagr = market.get("cagr_2024_2030", 0)
        projected_2030 = current_size * (1 + cagr/100) ** 6 if current_size else 0
        
        # Competitive analysis
        competition = market.get("competition", [])
        market_concentration = sum([c.get("market_share", 0) for c in competition[:3]])
        
        insights = [
            f"Global market size: ${current_size/1e9:.1f}B (2024)",
            f"Projected 2030: ${projected_2030/1e9:.1f}B ({cagr}% CAGR)",
            f"Top 3 players control {market_concentration}% of market"
        ]
        
        if query.indication:
            insights.append(f"New indication ({query.indication}) could expand addressable market by 15-25%")
        
        execution_time = (time.time() - start_time) * 1000
        self.status = AgentStatus.COMPLETED
        self.last_run = datetime.now()
        
        return self._create_result(
            data={
                "market_size_2024": current_size,
                "market_size_2030_projected": projected_2030,
                "cagr": cagr,
                "top_markets": market.get("top_markets", []),
                "competition": competition,
                "pricing": market.get("pricing", {}),
                "market_concentration": market_concentration,
                "insights": insights,
                "opportunity_score": 7.5 if cagr > 3 else 5.0
            },
            execution_time=execution_time,
            confidence=0.85,
            sources=3,
            freshness_date=datetime.now().strftime("%Y-%m-%d")
        )


class EXIMTrendsAgent(BaseAgent):
    """Agent that evaluates supply chain and trade data"""
    
    def __init__(self):
        super().__init__(
            name="EXIM Trends Agent",
            description="Evaluates supply chain, trade data, and API availability"
        )
        
    def get_data_sources(self) -> List[str]:
        return ["EXIM Trade Data", "API Supplier Database", "Supply Chain Intel"]
    
    async def execute(self, query: ResearchQuery) -> AgentResult:
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        
        await asyncio.sleep(0.3)
        
        mock_data = load_mock_data()
        exim = mock_data.get("exim_data", {}).get(query.molecule.lower(), {})
        
        if not exim:
            exim = {
                "api_sources": [],
                "import_trends": {},
                "supply_risk": "Unknown",
                "lead_time_days": 60
            }
        
        # Analyze supply chain
        sources = exim.get("api_sources", [])
        primary_source = sources[0] if sources else {"country": "Unknown", "share": 0}
        
        # Risk assessment (no supplier data -> Unknown, not a falsely low risk)
        if not sources:
            concentration_risk = "Unknown"
        elif primary_source.get("share", 0) > 60:
            concentration_risk = "High"
        elif primary_source.get("share", 0) > 40:
            concentration_risk = "Medium"
        else:
            concentration_risk = "Low"
        
        insights = [
            f"Primary API source: {primary_source.get('country')} ({primary_source.get('share')}% supply)",
            f"Supplier concentration risk: {concentration_risk}",
            f"Average lead time: {exim.get('lead_time_days', 'Unknown')} days"
        ]
        
        execution_time = (time.time() - start_time) * 1000
        self.status = AgentStatus.COMPLETED
        self.last_run = datetime.now()
        
        return self._create_result(
            data={
                "api_sources": sources,
                "primary_source": primary_source,
                "import_trends": exim.get("import_trends", {}),
                "supply_risk": exim.get("supply_risk", "Unknown"),
                "lead_time_days": exim.get("lead_time_days", 60),
                "quality_certifications": exim.get("quality_certifications", []),
                "concentration_risk": concentration_risk,
                "insights": insights,
                "supply_feasibility": (
                    "Unknown" if not sources
                    else "Medium" if concentration_risk == "High"
                    else "High"
                )
            },
            execution_time=execution_time,
            confidence=0.8,
            sources=len(sources),
            freshness_date=datetime.now().strftime("%Y-%m-%d")
        )


class WebIntelligenceAgent(BaseAgent):
    """Agent that gathers latest news and regulatory updates"""
    
    def __init__(self):
        super().__init__(
            name="Web Intelligence Agent",
            description="Gathers latest news, guidelines, and regulatory updates"
        )
        
    def get_data_sources(self) -> List[str]:
        return ["PubMed", "FDA.gov", "EMA", "Reuters Health", "BioPharma Dive"]
    
    async def execute(self, query: ResearchQuery) -> AgentResult:
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        
        await asyncio.sleep(0.5)
        
        mock_data = load_mock_data()
        
        # Get literature
        lit_key = f"{query.molecule.lower()}_{query.indication.lower().replace('-', '_').replace(' ', '_')}"
        literature = mock_data.get("literature", {}).get(lit_key, [])
        
        if not literature and query.molecule.lower() == "metformin":
            literature = mock_data.get("literature", {}).get("metformin_inflammation", [])
        
        # Get regulatory guidelines
        reg_key = f"{query.molecule.lower()}_{query.indication.lower().replace('-', '_').replace(' ', '_')}"
        guidelines = mock_data.get("regulatory_guidelines", {}).get(reg_key, [])
        
        if not guidelines and query.molecule.lower() == "metformin":
            guidelines = mock_data.get("regulatory_guidelines", {}).get("metformin_inflammation", [])
        
        # Generate news items (simulated)
        news = [
            {
                "title": f"New research highlights {query.molecule}'s potential in {query.indication}",
                "source": "BioPharma Dive",
                "date": "2024-11-01",
                "sentiment": "Positive"
            },
            {
                "title": f"FDA signals openness to repurposing strategies for established drugs",
                "source": "Reuters Health",
                "date": "2024-10-28",
                "sentiment": "Positive"
            }
        ]
        
        execution_time = (time.time() - start_time) * 1000
        self.status = AgentStatus.COMPLETED
        self.last_run = datetime.now()
        
        return self._create_result(
            data={
                "literature": literature,
                "total_publications": len(literature),
                "high_impact_papers": [l for l in literature if l.get("citations", 0) > 100],
                "regulatory_guidelines": guidelines,
                "recent_news": news,
                "sentiment_summary": "Generally Positive",
                "key_opinion_leaders": ["Dr. Nir Barzilai (TAME Trial)", "Dr. David Sinclair (Aging Research)"],
                "insights": [
                    f"Found {len(literature)} relevant publications",
                    "Strong mechanistic rationale in peer-reviewed literature",
                    "Regulatory pathway appears feasible via 505(b)(2)"
                ]
            },
            execution_time=execution_time,
            confidence=0.8,
            sources=len(literature) + len(guidelines) + len(news),
            freshness_date=datetime.now().strftime("%Y-%m-%d")
        )


def create_all_agents() -> Dict[str, BaseAgent]:
    """Factory function to create all agents"""
    return {
        "internal_knowledge": InternalKnowledgeAgent(),
        "clinical_trials": ClinicalTrialsAgent(),
        "patent_landscape": PatentLandscapeAgent(),
        "iqvia_insights": IQVIAInsightsAgent(),
        "exim_trends": EXIMTrendsAgent(),
        "web_intelligence": WebIntelligenceAgent()
    }
