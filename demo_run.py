#!/usr/bin/env python3
"""
Demo Runner for Pharma AI PoC
EY Techathon 6.0 - Round 2

This script demonstrates a complete end-to-end research flow:
1. Parse natural language query
2. Check institutional memory
3. Execute research agents
4. Synthesize findings
5. Generate PDF report
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents import MasterAgent, ResearchQuery
from src.reports.pdf_generator import generate_pdf_report
from config import recommendation_for

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_agent(agent_name, status, message):
    icon = "✅" if status == "completed" else "⏳" if status == "running" else "📋"
    color = Colors.GREEN if status == "completed" else Colors.YELLOW if status == "running" else Colors.CYAN
    print(f"{icon} {color}[{agent_name}]{Colors.ENDC} {message}")

def print_score(name, score, max_score=10):
    bar_length = 20
    filled = int((score / max_score) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    if score >= 7.5:
        color = Colors.GREEN
    elif score >= 5.5:
        color = Colors.YELLOW
    else:
        color = Colors.RED
    
    print(f"  {name:25} {color}{bar} {score:.1f}/{max_score}{Colors.ENDC}")


async def run_demo():
    """Run the complete demo flow"""
    
    print_header("PHARMA AI - Opportunity Assessment Demo")
    print(f"{Colors.CYAN}EY Techathon 6.0 - Round 2{Colors.ENDC}")
    print(f"{Colors.CYAN}Demonstrating: Agentic AI with Institutional Memory{Colors.ENDC}\n")
    
    # Demo query
    query_text = "Evaluate Metformin for anti-inflammatory indications"
    
    print(f"{Colors.BOLD}Research Query:{Colors.ENDC}")
    print(f"  '{query_text}'\n")
    
    # Parse query
    print(f"{Colors.BOLD}Step 1: Parsing Query...{Colors.ENDC}")
    query = ResearchQuery.from_natural_language(query_text)
    print(f"  Molecule: {query.molecule}")
    print(f"  Indication: {query.indication}")
    print(f"  Query ID: {query.query_id}\n")
    
    # Initialize master agent
    print(f"{Colors.BOLD}Step 2: Initializing Research Agents...{Colors.ENDC}")
    master = MasterAgent()
    
    agent_count = len(master.agents)
    print(f"  Registered {agent_count} research agents")
    for agent_id, agent in master.agents.items():
        print(f"    - {agent.name}")
    print()
    
    # Execute research
    print(f"{Colors.BOLD}Step 3: Executing Research Workflow...{Colors.ENDC}")
    print(f"  {Colors.YELLOW}(Institutional Memory: Read-Before-Write enabled){Colors.ENDC}\n")
    
    progress_updates = []
    
    def progress_callback(update):
        progress_updates.append(update)
        print_agent(update['agent'], update['status'], update['message'])
    
    # Run research
    report = await master.execute_research(query, callback=progress_callback)
    
    print()
    print_header("RESEARCH COMPLETE")
    
    # Display scores
    print(f"{Colors.BOLD}Assessment Scores:{Colors.ENDC}\n")
    print_score("Overall Score", report.overall_score)
    print_score("Market Attractiveness", report.market_attractiveness)
    print_score("Competitive Intensity", report.competitive_intensity)
    print_score("Regulatory Feasibility", report.regulatory_feasibility)
    print_score("Scientific Rationale", report.scientific_rationale)
    print_score("Supply Chain", report.supply_chain_feasibility)
    
    print()
    
    # Recommendation
    rec = recommendation_for(report.overall_score)
    rec_color = {
        "PROCEED": Colors.GREEN,
        "PROCEED WITH CAUTION": Colors.YELLOW,
        "RECONSIDER": Colors.RED,
    }[rec]

    print(f"{Colors.BOLD}Recommendation:{Colors.ENDC} {rec_color}{Colors.BOLD}{rec}{Colors.ENDC}")
    
    print()
    print(f"{Colors.BOLD}Key Findings:{Colors.ENDC}")
    for i, finding in enumerate(report.key_findings[:5], 1):
        print(f"  {i}. [{finding['category']}] {finding['finding'][:80]}...")
    
    print()
    print(f"{Colors.BOLD}Recommended Next Steps:{Colors.ENDC}")
    for i, step in enumerate(report.next_steps[:4], 1):
        print(f"  {i}. {step}")
    
    # Generate PDF
    print()
    print(f"{Colors.BOLD}Step 4: Generating PDF Report...{Colors.ENDC}")
    
    # Create reports directory
    reports_dir = Path("./reports")
    reports_dir.mkdir(exist_ok=True)
    
    pdf_path = reports_dir / f"{report.report_id}.pdf"
    
    try:
        generate_pdf_report(report.to_dict(), str(pdf_path))
        print(f"  {Colors.GREEN}✅ PDF generated: {pdf_path}{Colors.ENDC}")
    except Exception as e:
        print(f"  {Colors.RED}❌ PDF generation failed: {e}{Colors.ENDC}")
    
    # Save JSON
    json_path = reports_dir / f"{report.report_id}.json"
    with open(json_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2, default=str)
    print(f"  {Colors.GREEN}✅ JSON saved: {json_path}{Colors.ENDC}")
    
    # Summary
    print()
    print_header("EXECUTION SUMMARY")
    print(f"  Report ID:        {report.report_id}")
    print(f"  Total Sources:    {report.total_sources}")
    print(f"  Execution Time:   {report.execution_time_ms/1000:.2f} seconds")
    print(f"  Data Freshness:   {report.data_freshness}")
    print(f"  Archive Reuse:    {'Yes' if report.reused_from_archive else 'No'}")
    
    print()
    print(f"{Colors.GREEN}{Colors.BOLD}Demo Complete!{Colors.ENDC}")
    print(f"Check the ./reports directory for generated outputs.\n")
    
    return report


def main():
    """Main entry point"""
    try:
        report = asyncio.run(run_demo())
        return 0
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user.{Colors.ENDC}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
