#!/usr/bin/env python3
"""
Demo Runner for Pharma AI PoC
EY Techathon 6.0 - Round 2

This script demonstrates the full workflow of the Agentic AI system.
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents import MasterAgent, ResearchQuery, SynthesizedReport


def print_header():
    """Print demo header"""
    print("\n" + "="*70)
    print("🧬 PHARMA AI - Agentic Opportunity Assessment System")
    print("   EY Techathon 6.0 - Round 2 PoC Demo")
    print("="*70 + "\n")


def print_section(title: str):
    """Print section header"""
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


def format_score(score: float) -> str:
    """Format score with color indicator"""
    if score >= 7.5:
        indicator = "🟢"
    elif score >= 5.5:
        indicator = "🟡"
    else:
        indicator = "🔴"
    return f"{indicator} {score:.1f}/10"


async def run_demo():
    """Run the full demo workflow"""
    print_header()
    
    # Demo query
    query_text = "Evaluate Metformin for anti-inflammatory indications"
    
    print_section("📝 Research Query")
    print(f"  Query: {query_text}")
    
    # Parse query
    query = ResearchQuery.from_natural_language(query_text)
    query.molecule = "Metformin"
    query.indication = "Anti-inflammatory"
    
    print(f"  Molecule: {query.molecule}")
    print(f"  Indication: {query.indication}")
    print(f"  Query ID: {query.query_id}")
    
    # Initialize Master Agent
    master = MasterAgent()
    
    print_section("🤖 Agent Execution")
    
    # Progress callback
    def progress_callback(update):
        status_icons = {
            "running": "⏳",
            "completed": "✅",
            "planning": "📋",
            "synthesizing": "🔄"
        }
        icon = status_icons.get(update['status'], "📌")
        print(f"  {icon} [{update['agent']}] {update['message']}")
    
    # Execute research
    start_time = datetime.now()
    report = await master.execute_research(query, callback=progress_callback)
    execution_time = (datetime.now() - start_time).total_seconds()
    
    print_section("📊 Assessment Results")
    
    # Overall recommendation
    if report.overall_score >= 7.5:
        rec = "✅ PROCEED"
        rec_desc = "Strong opportunity - proceed with detailed planning"
    elif report.overall_score >= 5.5:
        rec = "⚠️  PROCEED WITH CAUTION"
        rec_desc = "Moderate opportunity - additional analysis recommended"
    else:
        rec = "❌ RECONSIDER"
        rec_desc = "Weak opportunity - consider alternatives"
    
    print(f"\n  Recommendation: {rec}")
    print(f"  {rec_desc}")
    
    print("\n  Scores:")
    print(f"    Overall Score:          {format_score(report.overall_score)}")
    print(f"    Market Attractiveness:  {format_score(report.market_attractiveness)}")
    print(f"    Competitive Intensity:  {format_score(report.competitive_intensity)}")
    print(f"    Regulatory Feasibility: {format_score(report.regulatory_feasibility)}")
    print(f"    Scientific Rationale:   {format_score(report.scientific_rationale)}")
    print(f"    Supply Chain:           {format_score(report.supply_chain_feasibility)}")
    
    print_section("🔍 Key Findings")
    for i, finding in enumerate(report.key_findings[:4], 1):
        print(f"\n  {i}. {finding.get('category', 'Finding')}")
        print(f"     {finding.get('finding', 'N/A')}")
        print(f"     Confidence: {finding.get('confidence', 0)*100:.0f}%")
    
    print_section("💡 Recommendations")
    for rec in report.recommendations:
        print(f"  • {rec}")
    
    print_section("⚠️  Risks & ✅ Opportunities")
    print("\n  Opportunities:")
    for opp in report.opportunities:
        print(f"    ✓ {opp}")
    print("\n  Risks:")
    for risk in report.risks:
        print(f"    ⚠ {risk}")
    
    print_section("📋 Next Steps")
    for i, step in enumerate(report.next_steps, 1):
        print(f"  {i}. {step}")
    
    print_section("📈 Execution Metrics")
    print(f"  Report ID:       {report.report_id}")
    print(f"  Total Sources:   {report.total_sources}")
    print(f"  Execution Time:  {execution_time:.2f} seconds")
    print(f"  Data Freshness:  {report.data_freshness}")
    print(f"  Reused Archive:  {'Yes' if report.reused_from_archive else 'No'}")
    
    # Save report
    print_section("💾 Saving Report")
    
    output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON
    json_path = output_dir / f"report_{report.report_id}.json"
    with open(json_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2, default=str)
    print(f"  JSON: {json_path}")
    
    # Generate PDF
    try:
        from src.reports.pdf_generator import generate_pdf_report
        pdf_path = output_dir / f"report_{report.report_id}.pdf"
        generate_pdf_report(report.to_dict(), str(pdf_path))
        print(f"  PDF:  {pdf_path}")
    except Exception as e:
        print(f"  PDF generation skipped: {e}")
    
    print("\n" + "="*70)
    print("✅ Demo Complete!")
    print("="*70 + "\n")
    
    return report


def main():
    """Main entry point"""
    try:
        report = asyncio.run(run_demo())
        return 0
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
