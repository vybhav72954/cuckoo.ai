"""
Configuration for Pharma AI PoC
EY Techathon 6.0 - Round 2
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Application configuration"""
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "demo-key")
    OPENAI_MODEL: str = "gpt-4"
    
    # Database paths (for PoC, using local files)
    DATA_DIR: str = "./mock_data"
    ARCHIVE_DIR: str = "./archive"
    REPORTS_DIR: str = "./reports"
    
    # Agent Configuration
    MAX_RETRIES: int = 3
    AGENT_TIMEOUT: int = 60
    
    # Freshness thresholds (in days)
    CLINICAL_TRIALS_FRESHNESS: int = 30
    PATENT_FRESHNESS: int = 90
    MARKET_DATA_FRESHNESS: int = 7
    LITERATURE_FRESHNESS: int = 60
    
    # Report settings
    REPORT_VERSION: str = "1.0.0"
    
    @classmethod
    def get_instance(cls) -> 'Config':
        return cls()

# Color scheme for UI
COLORS = {
    'primary': '#1E3A5F',      # Deep blue
    'secondary': '#F7931E',    # Orange accent
    'success': '#28A745',      # Green
    'warning': '#FFC107',      # Yellow
    'danger': '#DC3545',       # Red
    'info': '#17A2B8',         # Cyan
    'light': '#F8F9FA',        # Light gray
    'dark': '#343A40',         # Dark gray
    'background': '#0F1419',   # Near black
    'surface': '#1A1F2E',      # Dark surface
    'text': '#E8E8E8',         # Light text
}

# Agent definitions
AGENTS = {
    'master': {
        'name': 'Master Orchestrator',
        'description': 'Coordinates all research agents and synthesizes findings',
        'icon': '🎯'
    },
    'internal_knowledge': {
        'name': 'Internal Knowledge Agent',
        'description': 'Searches archived reports and institutional memory',
        'icon': '📚'
    },
    'clinical_trials': {
        'name': 'Clinical Trials Agent',
        'description': 'Analyzes clinical trial landscape from ClinicalTrials.gov',
        'icon': '🔬'
    },
    'patent_landscape': {
        'name': 'Patent Landscape Agent',
        'description': 'Evaluates patent status, expiry dates, and IP opportunities',
        'icon': '📜'
    },
    'iqvia_insights': {
        'name': 'IQVIA Insights Agent',
        'description': 'Analyzes market data, sales trends, and competitive landscape',
        'icon': '📊'
    },
    'exim_trends': {
        'name': 'EXIM Trends Agent',
        'description': 'Evaluates supply chain, trade data, and API availability',
        'icon': '🚢'
    },
    'web_intelligence': {
        'name': 'Web Intelligence Agent',
        'description': 'Gathers latest news, guidelines, and regulatory updates',
        'icon': '🌐'
    }
}

# Recommendation thresholds — single source of truth for the
# PROCEED / PROCEED WITH CAUTION / RECONSIDER verdict shown across the
# Streamlit UI, the PDF report, and the CLI demos. Keep all verdict logic
# routed through recommendation_for() so these never drift apart again.
PROCEED_THRESHOLD = 7.5
CAUTION_THRESHOLD = 5.5

def recommendation_for(score: float) -> str:
    """Map an overall opportunity score (0-10) to a recommendation verdict."""
    if score >= PROCEED_THRESHOLD:
        return "PROCEED"
    if score >= CAUTION_THRESHOLD:
        return "PROCEED WITH CAUTION"
    return "RECONSIDER"
