"""
Master Agent - Orchestrates research and synthesizes findings
EY Techathon 6.0 - Round 2
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json

from .base_agent import BaseAgent, AgentResult, AgentStatus, ResearchQuery, AgentOrchestrator
from .research_agents import create_all_agents

# Score assigned to a dimension when the underlying agent returned no usable data.
# Intentionally low so "no information" cannot read as a favorable result.
NO_DATA_SCORE = 2.0


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
                "reused_from_archive": self.reused_from_archive
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
        self.orchestrator = AgentOrchestrator()
        self.agents = create_all_agents()
        
        # Register all agents
        for agent_id, agent in self.agents.items():
            self.orchestrator.register_agent(agent_id, agent)
        
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
        
        # Step 2: Determine which agents need fresh research
        agents_to_run = self._determine_agents_to_run(internal_result, query)
        if selected_agents is not None:
            agents_to_run = [a for a in agents_to_run if a in selected_agents]
        update_progress("master", "planning",
                       f"Running {len(agents_to_run)} agents for fresh research")
        
        # Step 3: Execute research agents in parallel
        results = {"internal_knowledge": internal_result}
        
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
                                  query: ResearchQuery) -> List[str]:
        """
        Smart agent selection based on institutional memory
        
        If we have recent, relevant research, we may skip some agents
        """
        # For PoC, we run all agents but this shows the logic
        all_agents = ["clinical_trials", "patent_landscape", "iqvia_insights", 
                      "exim_trends", "web_intelligence"]
        
        # Check what areas need refresh
        areas_needing_refresh = internal_result.data.get("areas_needing_refresh", [])
        
        if not internal_result.data.get("prior_research_exists"):
            # No prior research - run everything
            return all_agents
        
        # In production, we would be smarter about which agents to skip
        # For now, run all to demonstrate full capability
        return all_agents
    
    def _synthesize_report(self, query: ResearchQuery, 
                           results: Dict[str, AgentResult],
                           start_time: datetime) -> SynthesizedReport:
        """Synthesize all agent results into a cohesive report"""
        
        # Calculate scores
        scores = self._calculate_scores(results)
        
        # Generate executive summary
        summary = self._generate_executive_summary(query, results, scores)
        
        # Extract key findings from each agent
        key_findings = self._extract_key_findings(results)
        
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
            reused_from_archive=results.get("internal_knowledge", AgentResult(
                agent_name="", status=AgentStatus.IDLE, data={}
            )).data.get("prior_research_exists", False)
        )
        
        return report
    
    def _calculate_scores(self, results: Dict[str, AgentResult]) -> Dict[str, float]:
        """Calculate opportunity scores based on agent findings"""
        scores = {}
        
        # Each dimension scores only when its agent actually returned data; otherwise
        # NO_DATA_SCORE, so a molecule we know nothing about can't look favorable.

        # Market attractiveness (from IQVIA)
        iqvia = results.get("iqvia_insights")
        if iqvia and iqvia.status == AgentStatus.COMPLETED and iqvia.data.get("market_size_2024", 0) > 0:
            scores["market"] = iqvia.data.get("opportunity_score", 5.0)
        else:
            scores["market"] = NO_DATA_SCORE

        # Competitive intensity (from Patents)
        patent = results.get("patent_landscape")
        if patent and patent.status == AgentStatus.COMPLETED and patent.data.get("total_patents", 0) > 0:
            active_patents = patent.data.get("active_patents", 0)
            scores["competitive"] = 10 - min(active_patents * 2, 5)
        else:
            scores["competitive"] = NO_DATA_SCORE

        # Regulatory feasibility (from Web Intelligence)
        web = results.get("web_intelligence")
        if web and web.status == AgentStatus.COMPLETED and (web.data.get("regulatory_guidelines") or web.data.get("literature")):
            guidelines = web.data.get("regulatory_guidelines", [])
            scores["regulatory"] = 8.0 if guidelines else 6.0
        else:
            scores["regulatory"] = NO_DATA_SCORE

        # Scientific rationale (from Clinical Trials + Literature)
        clinical = results.get("clinical_trials")
        if clinical and clinical.status == AgentStatus.COMPLETED and clinical.data.get("total_trials", 0) > 0:
            phase3_trials = clinical.data.get("phase_distribution", {}).get("Phase 3", 0)
            scores["scientific"] = min(6 + phase3_trials, 10)
        else:
            scores["scientific"] = NO_DATA_SCORE

        # Supply chain feasibility (from EXIM)
        exim = results.get("exim_trends")
        if exim and exim.status == AgentStatus.COMPLETED and exim.data.get("api_sources"):
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
                                     scores: Dict[str, float]) -> str:
        """Generate executive summary based on findings"""
        
        overall = scores["overall"]
        recommendation = "PROCEED" if overall >= 7.5 else "PROCEED WITH CAUTION" if overall >= 6 else "RECONSIDER"
        
        # Get key stats
        clinical = results.get("clinical_trials")
        trial_count = clinical.data.get("total_trials", 0) if clinical else 0
        
        iqvia = results.get("iqvia_insights")
        market_size = iqvia.data.get("market_size_2024", 0) if iqvia else 0
        
        summary = f"""
**Opportunity Assessment: {query.molecule} for {query.indication}**

**Recommendation: {recommendation}** (Score: {overall:.1f}/10)

{query.molecule} presents a {"promising" if overall >= 7 else "moderate"} opportunity for {query.indication} indication expansion. 

Key highlights:
- {trial_count} relevant clinical trials identified, indicating {"strong" if trial_count > 3 else "growing"} research interest
- Current market size: ${market_size/1e9:.1f}B with expansion potential
- Regulatory pathway: {"Clear via 505(b)(2)" if scores["regulatory"] >= 7 else "Requires further assessment"}
- Supply chain: {"Well-established" if scores["supply"] >= 7 else "Manageable with planning"}

The analysis draws from {sum(r.source_count for r in results.values())} sources across clinical trials, patents, market data, and literature.
        """.strip()
        
        return summary
    
    def _extract_key_findings(self, results: Dict[str, AgentResult]) -> List[Dict[str, Any]]:
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
        
        return findings
    
    def _compile_recommendations(self, results: Dict[str, AgentResult], 
                                  scores: Dict[str, float]) -> tuple:
        """Compile recommendations, risks, and opportunities"""
        recommendations = []
        risks = []
        opportunities = []
        
        # Based on scores
        if scores["overall"] >= 7.5:
            recommendations.append("Proceed with detailed feasibility study")
            recommendations.append("Engage regulatory affairs for pathway confirmation")
        elif scores["overall"] >= 6:
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
        
        if scores["overall"] >= 7:
            steps = [
                f"Schedule pre-IND meeting with FDA for {query.indication} indication",
                "Initiate Phase 2 clinical study design",
                "Develop formulation strategy for differentiation",
                "Conduct detailed commercial assessment"
            ]
        elif scores["overall"] >= 5.5:
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
