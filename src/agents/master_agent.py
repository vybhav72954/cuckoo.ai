"""
Master Agent - Orchestrates research and synthesizes findings
EY Techathon 6.0 - Round 2
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json

from .base_agent import AgentResult, AgentStatus, ResearchQuery
from .research_agents import create_all_agents
from config import Config, recommendation_for, PROCEED_THRESHOLD, CAUTION_THRESHOLD


def _freshness_thresholds() -> Dict[str, int]:
    """Per-agent max age (days) before prior research must be refreshed (from config.py)."""
    cfg = Config.get_instance()
    return {
        "clinical_trials": cfg.CLINICAL_TRIALS_FRESHNESS,
        "patent_landscape": cfg.PATENT_FRESHNESS,
        "iqvia_insights": cfg.MARKET_DATA_FRESHNESS,
        "exim_trends": cfg.MARKET_DATA_FRESHNESS,
        "web_intelligence": cfg.LITERATURE_FRESHNESS,
    }

# Sub-score each agent "owns" in a prior report, so a reused (still-fresh) agent
# contributes its archived score instead of a neutral default. (Archived reports
# don't carry a supply-chain score, so exim_trends has no reusable score.)
PRIOR_SCORE_KEY = {
    "iqvia_insights": "market_attractiveness",
    "patent_landscape": "competitive_intensity",
    "web_intelligence": "regulatory_feasibility",
    "clinical_trials": "scientific_rationale",
    "exim_trends": None,
}


# Score assigned to a dimension when the underlying agent returned no usable data.
# Intentionally low so "no information" cannot read as a favorable result.
NO_DATA_SCORE = 2.0

# Archived reports carry qualitative confidence labels; fresh findings use a 0-1
# float. Normalize so reused findings render consistently (confidence * 100).
_CONFIDENCE_LABELS = {"high": 0.9, "medium": 0.7, "low": 0.5}

def _confidence_to_float(value, default: float = 0.6) -> float:
    if isinstance(value, (int, float)):
        v = float(value)
        if v > 1:  # percent-like (e.g. 85) -> fraction
            v /= 100
        return max(0.0, min(1.0, v))
    return _CONFIDENCE_LABELS.get(str(value).strip().lower(), default)


@dataclass
class SynthesizedReport:
    """Final synthesized report from all agents"""
    report_id: str
    query: ResearchQuery
    created_at: datetime
    version: str = "1.0"
    
    # Scores
    market_attractiveness: float = 0.0
    competitive_intensity: float = 0.0
    regulatory_feasibility: float = 0.0
    scientific_rationale: float = 0.0
    supply_chain_feasibility: float = 0.0
    overall_score: float = 0.0
    
    # Content
    executive_summary: str = ""
    key_findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    
    # Agent results
    agent_results: Dict[str, Dict] = field(default_factory=dict)
    
    # Metadata
    total_sources: int = 0
    execution_time_ms: float = 0.0
    data_freshness: str = ""
    reused_from_archive: bool = False
    agents_refreshed: List[str] = field(default_factory=list)
    agents_reused: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "query": {
                "molecule": self.query.molecule,
                "indication": self.query.indication,
                "raw_query": self.query.raw_query
            },
            "created_at": self.created_at.isoformat(),
            "version": self.version,
            "scores": {
                "market_attractiveness": self.market_attractiveness,
                "competitive_intensity": self.competitive_intensity,
                "regulatory_feasibility": self.regulatory_feasibility,
                "scientific_rationale": self.scientific_rationale,
                "supply_chain_feasibility": self.supply_chain_feasibility,
                "overall": self.overall_score
            },
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "risks": self.risks,
            "opportunities": self.opportunities,
            "next_steps": self.next_steps,
            "metadata": {
                "total_sources": self.total_sources,
                "execution_time_ms": self.execution_time_ms,
                "data_freshness": self.data_freshness,
                "reused_from_archive": self.reused_from_archive,
                "agents_refreshed": self.agents_refreshed,
                "agents_reused": self.agents_reused
            }
        }


class MasterAgent:
    """
    Master Agent that orchestrates all research agents and synthesizes findings.
    
    Implements the key differentiator: Read-Before-Write logic
    1. First checks Internal Knowledge Agent for prior research
    2. Determines which agents need fresh data
    3. Runs only necessary agents (delta refresh)
    4. Synthesizes all findings into cohesive report
    """
    
    def __init__(self):
        self.agents = create_all_agents()
        self.current_execution: Optional[Dict] = None
        self.execution_log: List[Dict] = []
        
    async def execute_research(self, query: ResearchQuery,
                               callback=None,
                               selected_agents: Optional[List[str]] = None) -> SynthesizedReport:
        """
        Execute full research workflow with institutional memory check

        Args:
            query: Structured research query
            callback: Optional callback for progress updates
            selected_agents: If provided, only these fresh-research agents run
                (internal_knowledge always runs for the Read-Before-Write step).
        """
        start_time = datetime.now()
        
        # Progress tracking
        def update_progress(agent: str, status: str, message: str):
            if callback:
                callback({
                    "agent": agent,
                    "status": status,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
        
        # Step 1: Check Institutional Memory (Read-Before-Write)
        update_progress("internal_knowledge", "running", "Checking institutional memory...")
        internal_result = await self.agents["internal_knowledge"].execute(query)
        update_progress("internal_knowledge", "completed", 
                       f"Found {len(internal_result.data.get('relevant_reports', []))} related reports")
        
        # Step 2: Delta refresh — decide which agents to re-run vs reuse from archive,
        # then drop any the caller did not select.
        agents_to_run, agents_reused = self._determine_agents_to_run(internal_result, query)
        if selected_agents is not None:
            agents_to_run = [a for a in agents_to_run if a in selected_agents]
            agents_reused = [a for a in agents_reused if a in selected_agents]
        update_progress("master", "planning",
                       f"Refreshing {len(agents_to_run)} agents, "
                       f"reusing {len(agents_reused)} from archive")

        results = {"internal_knowledge": internal_result}

        # Step 3a: Reuse still-fresh prior research without re-running those agents
        for agent_id in agents_reused:
            results[agent_id] = self._build_reused_result(agent_id, internal_result, query)
            update_progress(agent_id, "completed",
                          "Reused from institutional memory (data still fresh)")

        # Step 3b: Execute the agents whose data is stale
        for agent_id in agents_to_run:
            update_progress(agent_id, "running", f"Executing {self.agents[agent_id].name}...")
            result = await self.agents[agent_id].execute(query)
            results[agent_id] = result
            update_progress(agent_id, "completed",
                          f"Found {result.source_count} sources")
        
        # Step 4: Synthesize findings
        update_progress("master", "synthesizing", "Synthesizing findings into report...")
        report = self._synthesize_report(query, results, start_time)
        update_progress("master", "completed", "Report generation complete")
        
        return report
    
    def _determine_agents_to_run(self, internal_result: AgentResult,
                                  query: ResearchQuery) -> tuple:
        """
        Delta-refresh decision: which agents must run fresh vs. can be reused.

        Compares the age of the most relevant prior research against each domain's
        freshness threshold (config.py). Domains still within their threshold are
        reused from institutional memory; stale domains are re-run.

        Returns (agents_to_run, agents_reused).
        """
        all_agents = ["clinical_trials", "patent_landscape", "iqvia_insights",
                      "exim_trends", "web_intelligence"]

        # No prior research -> everything must be researched fresh.
        if not internal_result.data.get("prior_research_exists"):
            return all_agents, []

        days_since = internal_result.data.get("days_since_last_research")
        if days_since is None:
            # Prior research exists but we couldn't date it -> refresh everything.
            return all_agents, []

        thresholds = _freshness_thresholds()
        # Domains the knowledge agent explicitly flagged as stale must refresh
        # regardless of age. Intersect with known agents so any prose entries are
        # ignored rather than treated as agent ids.
        force_refresh = set(internal_result.data.get("areas_needing_refresh", [])) & set(all_agents)

        agents_to_run, agents_reused = [], []
        for agent_id in all_agents:
            # An agent can only be reused if its prior assessment can be carried
            # forward as a score; archives carry no supply-chain score, so
            # exim_trends (PRIOR_SCORE_KEY is None) always re-runs rather than being
            # reused-but-unscored. This keeps the reuse decision from affecting scores.
            unscorable_on_reuse = PRIOR_SCORE_KEY.get(agent_id) is None
            if days_since > thresholds[agent_id] or agent_id in force_refresh or unscorable_on_reuse:
                agents_to_run.append(agent_id)
            else:
                agents_reused.append(agent_id)
        return agents_to_run, agents_reused

    def _best_prior_report(self, internal_result: Optional[AgentResult],
                           query: ResearchQuery) -> Optional[Dict[str, Any]]:
        """
        Choose which archived report to reuse: prefer one whose indication matches
        the query, otherwise fall back to the most recent relevant report.
        """
        if internal_result is None:
            return None
        reports = internal_result.data.get("relevant_reports", [])
        if not reports:
            return None
        indication = (query.indication or "").lower()
        matches = [r for r in reports
                   if indication and indication in (r.get("indication", "") or "").lower()]
        pool = matches or reports
        return max(pool, key=lambda r: r.get("date") or "")

    def _build_reused_result(self, agent_id: str,
                             internal_result: AgentResult,
                             query: ResearchQuery) -> AgentResult:
        """
        Build a CACHED result for an agent skipped because its data is still fresh.

        Carries forward the best-matching prior sub-score for that domain so synthesis
        stays meaningful without re-running the agent.
        """
        prior = self._best_prior_report(internal_result, query)
        prior_scores = prior.get("scores", {}) if prior else {}
        score_key = PRIOR_SCORE_KEY.get(agent_id)
        reused_score = prior_scores.get(score_key) if score_key else None

        return AgentResult(
            agent_name=self.agents[agent_id].name,
            status=AgentStatus.CACHED,
            data={
                "reused": True,
                "reused_score": reused_score,
                "source": "institutional_memory",
                "archived_report_id": prior.get("report_id") if prior else None,
            },
            confidence_score=0.7,
            # Reused agents fetch no fresh sources; the backing prior reports are
            # already counted once via the internal_knowledge agent, so count 0 here
            # to avoid inflating total_sources.
            source_count=0,
            cached=True,
            data_freshness_date=internal_result.data.get("last_research_date")
        )
    
    def _synthesize_report(self, query: ResearchQuery, 
                           results: Dict[str, AgentResult],
                           start_time: datetime) -> SynthesizedReport:
        """Synthesize all agent results into a cohesive report"""
        
        # Calculate scores
        scores = self._calculate_scores(results)

        # Which fresh-research agents ran vs were reused from the archive
        fresh_agents = ["clinical_trials", "patent_landscape", "iqvia_insights",
                        "exim_trends", "web_intelligence"]
        agents_reused = [a for a in fresh_agents
                         if a in results and results[a].status == AgentStatus.CACHED]
        agents_refreshed = [a for a in fresh_agents
                            if a in results and results[a].status == AgentStatus.COMPLETED]
        # The archived report whose research is being reused (drives findings/summary
        # fallback for reused domains).
        prior_report = (self._best_prior_report(results.get("internal_knowledge"), query)
                        if agents_reused else None)

        # Generate executive summary (reuse-aware)
        summary = self._generate_executive_summary(query, results, scores, prior_report)

        # Extract key findings, surfacing prior research for reused domains
        key_findings = self._extract_key_findings(results, prior_report)

        # Compile recommendations, risks, opportunities
        recommendations, risks, opportunities = self._compile_recommendations(results, scores)

        # Generate next steps
        next_steps = self._generate_next_steps(scores, query)

        # Calculate metadata
        total_sources = sum(r.source_count for r in results.values())
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        report = SynthesizedReport(
            report_id=f"RPT-{datetime.now().strftime('%Y%m%d')}-{query.query_id}",
            query=query,
            created_at=datetime.now(),
            market_attractiveness=scores["market"],
            competitive_intensity=scores["competitive"],
            regulatory_feasibility=scores["regulatory"],
            scientific_rationale=scores["scientific"],
            supply_chain_feasibility=scores["supply"],
            overall_score=scores["overall"],
            executive_summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            opportunities=opportunities,
            next_steps=next_steps,
            agent_results={k: v.to_dict() for k, v in results.items()},
            total_sources=total_sources,
            execution_time_ms=execution_time,
            data_freshness=datetime.now().strftime("%Y-%m-%d"),
            reused_from_archive=bool(agents_reused),
            agents_refreshed=agents_refreshed,
            agents_reused=agents_reused
        )

        return report
    
    def _calculate_scores(self, results: Dict[str, AgentResult]) -> Dict[str, float]:
        """Calculate opportunity scores based on agent findings"""
        scores = {}

        # Per dimension: (1) carried-forward score if the agent was reused from
        # archive, else (2) live formula if the agent returned real data, else
        # (3) NO_DATA_SCORE so a molecule we know nothing about can't look favorable.

        def reused_score(agent_id):
            """Carried-forward prior score if this agent was reused, else None."""
            r = results.get(agent_id)
            if r is not None and r.status == AgentStatus.CACHED:
                return r.data.get("reused_score")
            return None

        # Market attractiveness (from IQVIA)
        iqvia = results.get("iqvia_insights")
        iqvia_reused = reused_score("iqvia_insights")
        if iqvia_reused is not None:
            scores["market"] = iqvia_reused
        elif iqvia and iqvia.status == AgentStatus.COMPLETED and iqvia.data.get("market_size_2024", 0) > 0:
            scores["market"] = iqvia.data.get("opportunity_score", 5.0)
        else:
            scores["market"] = NO_DATA_SCORE

        # Competitive intensity (from Patents). total_patents present (including
        # 0 = off-patent, a favorable FTO signal) is real data; only a missing/
        # failed patent agent falls back to NO_DATA_SCORE.
        patent = results.get("patent_landscape")
        patent_reused = reused_score("patent_landscape")
        if patent_reused is not None:
            scores["competitive"] = patent_reused
        elif patent and patent.status == AgentStatus.COMPLETED and patent.data.get("total_patents") is not None:
            active_patents = patent.data.get("active_patents", 0)
            scores["competitive"] = 10 - min(active_patents * 2, 5)
        else:
            scores["competitive"] = NO_DATA_SCORE

        # Regulatory feasibility (from Web Intelligence)
        web = results.get("web_intelligence")
        web_reused = reused_score("web_intelligence")
        if web_reused is not None:
            scores["regulatory"] = web_reused
        elif web and web.status == AgentStatus.COMPLETED and (web.data.get("regulatory_guidelines") or web.data.get("literature")):
            guidelines = web.data.get("regulatory_guidelines", [])
            scores["regulatory"] = 8.0 if guidelines else 6.0
        else:
            scores["regulatory"] = NO_DATA_SCORE

        # Scientific rationale (from Clinical Trials + Literature)
        clinical = results.get("clinical_trials")
        clinical_reused = reused_score("clinical_trials")
        if clinical_reused is not None:
            scores["scientific"] = clinical_reused
        elif clinical and clinical.status == AgentStatus.COMPLETED and clinical.data.get("total_trials", 0) > 0:
            phase3_trials = clinical.data.get("phase_distribution", {}).get("Phase 3", 0)
            scores["scientific"] = min(6 + phase3_trials, 10)
        else:
            scores["scientific"] = NO_DATA_SCORE

        # Supply chain feasibility (from EXIM)
        exim = results.get("exim_trends")
        exim_reused = reused_score("exim_trends")
        if exim_reused is not None:
            scores["supply"] = exim_reused
        elif exim and exim.status == AgentStatus.COMPLETED and exim.data.get("api_sources"):
            feasibility = exim.data.get("supply_feasibility", "Medium")
            scores["supply"] = 9.0 if feasibility == "High" else 7.0 if feasibility == "Medium" else 5.0
        else:
            scores["supply"] = NO_DATA_SCORE
        
        # Overall weighted score
        weights = {"market": 0.25, "competitive": 0.2, "regulatory": 0.2, 
                   "scientific": 0.25, "supply": 0.1}
        scores["overall"] = sum(scores[k] * weights[k] for k in weights)
        
        return scores
    
    def _generate_executive_summary(self, query: ResearchQuery,
                                     results: Dict[str, AgentResult],
                                     scores: Dict[str, float],
                                     prior_report: Optional[Dict[str, Any]] = None) -> str:
        """Generate executive summary based on findings"""

        overall = scores["overall"]
        recommendation = recommendation_for(overall)

        # Quote a live figure only when the agent ran fresh; for reused domains say
        # so rather than reporting "0 trials" / "$0.0B" from an absent field.
        clinical = results.get("clinical_trials")
        if clinical and clinical.status == AgentStatus.COMPLETED:
            trials = clinical.data.get("total_trials", 0)
            clinical_line = (f"- {trials} relevant clinical trials identified, indicating "
                             f"{'strong' if trials > 3 else 'growing'} research interest")
        elif clinical and clinical.status == AgentStatus.CACHED:
            clinical_line = "- Clinical evidence drawn from prior research on file"
        else:
            clinical_line = "- No clinical trial data available"

        iqvia = results.get("iqvia_insights")
        if iqvia and iqvia.status == AgentStatus.COMPLETED:
            market_size = iqvia.data.get("market_size_2024", 0)
            market_line = f"- Current market size: ${market_size/1e9:.1f}B with expansion potential"
        elif iqvia and iqvia.status == AgentStatus.CACHED:
            market_line = "- Market sizing reused from prior research on file"
        else:
            market_line = "- No market sizing data available"

        summary = f"""
**Opportunity Assessment: {query.molecule} for {query.indication}**

**Recommendation: {recommendation}** (Score: {overall:.1f}/10)

{query.molecule} presents a {"promising" if overall >= PROCEED_THRESHOLD else "moderate"} opportunity for {query.indication} indication expansion.

Key highlights:
{clinical_line}
{market_line}
- Regulatory pathway: {"Clear via 505(b)(2)" if scores["regulatory"] >= 7 else "Requires further assessment"}
- Supply chain: {"Well-established" if scores["supply"] >= 7 else "Manageable with planning"}

The analysis draws from {sum(r.source_count for r in results.values())} sources across clinical trials, patents, market data, and literature.
        """.strip()

        if prior_report:
            summary += (f"\n\nReuses institutional memory from {prior_report.get('report_id', 'archive')}"
                        f" ({(prior_report.get('date') or '')[:10]}) where prior data was still current.")

        return summary
    
    def _extract_key_findings(self, results: Dict[str, AgentResult],
                              prior_report: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Extract and prioritize key findings from all agents"""
        findings = []
        
        # Clinical trials findings
        clinical = results.get("clinical_trials")
        if clinical and clinical.status == AgentStatus.COMPLETED:
            for insight in clinical.data.get("insights", [])[:2]:
                findings.append({
                    "category": "Clinical Evidence",
                    "finding": insight,
                    "source": "Clinical Trials Agent",
                    "confidence": clinical.confidence_score
                })
        
        # Patent findings
        patent = results.get("patent_landscape")
        if patent and patent.status == AgentStatus.COMPLETED:
            for opp in patent.data.get("opportunities", [])[:2]:
                findings.append({
                    "category": "IP Landscape",
                    "finding": opp,
                    "source": "Patent Agent",
                    "confidence": patent.confidence_score
                })
        
        # Market findings
        iqvia = results.get("iqvia_insights")
        if iqvia and iqvia.status == AgentStatus.COMPLETED:
            for insight in iqvia.data.get("insights", [])[:2]:
                findings.append({
                    "category": "Market Intelligence",
                    "finding": insight,
                    "source": "IQVIA Agent",
                    "confidence": iqvia.confidence_score
                })
        
        # Literature findings
        web = results.get("web_intelligence")
        if web and web.status == AgentStatus.COMPLETED:
            for insight in web.data.get("insights", [])[:2]:
                findings.append({
                    "category": "Scientific Literature",
                    "finding": insight,
                    "source": "Web Intelligence Agent",
                    "confidence": web.confidence_score
                })

        # For reused domains, surface the prior report's findings (categories not
        # already covered by a freshly-run agent) so a reused report isn't left empty.
        if prior_report:
            covered = {f["category"] for f in findings}
            report_id = prior_report.get("report_id", "archive")
            for pf in prior_report.get("key_findings", []):
                category = pf.get("category", "Prior Research")
                if category in covered:
                    continue
                covered.add(category)
                findings.append({
                    "category": category,
                    "finding": pf.get("finding", ""),
                    "source": f"Institutional memory ({report_id})",
                    "confidence": _confidence_to_float(pf.get("confidence")),
                })

        return findings
    
    def _compile_recommendations(self, results: Dict[str, AgentResult], 
                                  scores: Dict[str, float]) -> tuple:
        """Compile recommendations, risks, and opportunities"""
        recommendations = []
        risks = []
        opportunities = []
        
        # Based on scores (tiers match the recommendation verdict thresholds)
        if scores["overall"] >= PROCEED_THRESHOLD:
            recommendations.append("Proceed with detailed feasibility study")
            recommendations.append("Engage regulatory affairs for pathway confirmation")
        elif scores["overall"] >= CAUTION_THRESHOLD:
            recommendations.append("Conduct additional competitive analysis")
            recommendations.append("Evaluate differentiation strategies")
        else:
            recommendations.append("Consider alternative indication or molecule")
        
        # Patent-based
        patent = results.get("patent_landscape")
        if patent:
            risks.extend(patent.data.get("risks", []))
            opportunities.extend(patent.data.get("opportunities", []))
        
        # Supply chain
        exim = results.get("exim_trends")
        if exim:
            if exim.data.get("concentration_risk") == "High":
                risks.append("Supply chain concentration risk - consider alternative sources")
        
        return recommendations, risks, opportunities
    
    def _generate_next_steps(self, scores: Dict[str, float], 
                              query: ResearchQuery) -> List[str]:
        """Generate actionable next steps"""
        steps = []
        
        if scores["overall"] >= PROCEED_THRESHOLD:
            steps = [
                f"Schedule pre-IND meeting with FDA for {query.indication} indication",
                "Initiate Phase 2 clinical study design",
                "Develop formulation strategy for differentiation",
                "Conduct detailed commercial assessment"
            ]
        elif scores["overall"] >= CAUTION_THRESHOLD:
            steps = [
                "Conduct deeper competitive landscape analysis",
                "Explore combination therapy opportunities",
                "Assess regional filing strategies",
                "Re-evaluate in 6 months with updated data"
            ]
        else:
            steps = [
                "Archive findings for future reference",
                "Evaluate alternative indications",
                "Monitor clinical trial outcomes",
                "Consider partnership opportunities"
            ]
        
        return steps


async def run_demo_query():
    """Demo function to test the master agent"""
    master = MasterAgent()
    
    query = ResearchQuery.from_natural_language(
        "Evaluate Metformin for anti-inflammatory indications"
    )
    
    def progress_callback(update):
        print(f"[{update['agent']}] {update['status']}: {update['message']}")
    
    report = await master.execute_research(query, callback=progress_callback)
    
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(json.dumps(report.to_dict(), indent=2, default=str))
    
    return report


if __name__ == "__main__":
    asyncio.run(run_demo_query())
