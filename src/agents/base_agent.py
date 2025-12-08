"""
Base Agent Framework for Pharma AI System
EY Techathon 6.0 - Round 2
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import json
import uuid

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"

@dataclass
class AgentResult:
    """Result from an agent execution"""
    agent_name: str
    status: AgentStatus
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time_ms: float = 0
    data_freshness_date: Optional[str] = None
    confidence_score: float = 0.0
    source_count: int = 0
    cached: bool = False
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "data_freshness_date": self.data_freshness_date,
            "confidence_score": self.confidence_score,
            "source_count": self.source_count,
            "cached": self.cached,
            "error_message": self.error_message
        }

@dataclass
class ResearchQuery:
    """Structured research query"""
    query_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    molecule: str = ""
    indication: str = ""
    geography: str = "Global"
    raw_query: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_natural_language(cls, query: str) -> 'ResearchQuery':
        """Parse natural language query into structured format"""
        # Simple parsing - in production, use NLP/LLM
        query_lower = query.lower()
        
        # Extract molecule (look for common patterns)
        molecule = ""
        indication = ""
        
        # Common molecules
        molecules = ["metformin", "aspirin", "ibuprofen", "atorvastatin", "omeprazole"]
        for mol in molecules:
            if mol in query_lower:
                molecule = mol.capitalize()
                break
        
        # Common indications/therapeutic areas
        indications = {
            "inflammation": "Inflammation",
            "anti-inflammatory": "Anti-inflammatory",
            "diabetes": "Diabetes",
            "cancer": "Oncology",
            "aging": "Anti-aging",
            "alzheimer": "Alzheimer's Disease",
            "cardiovascular": "Cardiovascular",
            "nash": "NASH/NAFLD",
            "nafld": "NASH/NAFLD"
        }
        
        for key, value in indications.items():
            if key in query_lower:
                indication = value
                break
        
        return cls(
            molecule=molecule,
            indication=indication,
            raw_query=query
        )

class BaseAgent(ABC):
    """Abstract base class for all research agents"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.last_run: Optional[datetime] = None
        
    @abstractmethod
    async def execute(self, query: ResearchQuery) -> AgentResult:
        """Execute the agent's research task"""
        pass
    
    @abstractmethod
    def get_data_sources(self) -> List[str]:
        """Return list of data sources this agent uses"""
        pass
    
    def check_cache(self, query: ResearchQuery) -> Optional[AgentResult]:
        """Check if we have cached results for this query"""
        # In production, implement actual cache check
        return None
    
    def _create_result(self, data: Dict[str, Any], 
                       execution_time: float,
                       confidence: float = 0.8,
                       sources: int = 0,
                       cached: bool = False,
                       freshness_date: str = None) -> AgentResult:
        """Helper to create standardized result"""
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            data=data,
            execution_time_ms=execution_time,
            confidence_score=confidence,
            source_count=sources,
            cached=cached,
            data_freshness_date=freshness_date or datetime.now().strftime("%Y-%m-%d")
        )


class AgentOrchestrator:
    """Master orchestrator that coordinates all agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.execution_log: List[Dict[str, Any]] = []
        
    def register_agent(self, agent_id: str, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent_id] = agent
        
    async def execute_query(self, query: ResearchQuery, 
                           selected_agents: Optional[List[str]] = None) -> Dict[str, AgentResult]:
        """Execute research query across all or selected agents"""
        results = {}
        agents_to_run = selected_agents or list(self.agents.keys())
        
        execution_start = datetime.now()
        
        for agent_id in agents_to_run:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                try:
                    result = await agent.execute(query)
                    results[agent_id] = result
                except Exception as e:
                    results[agent_id] = AgentResult(
                        agent_name=agent.name,
                        status=AgentStatus.FAILED,
                        data={},
                        error_message=str(e)
                    )
        
        # Log execution
        self.execution_log.append({
            "query_id": query.query_id,
            "timestamp": execution_start.isoformat(),
            "agents_executed": agents_to_run,
            "duration_ms": (datetime.now() - execution_start).total_seconds() * 1000
        })
        
        return results
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents"""
        return {
            agent_id: {
                "name": agent.name,
                "status": agent.status.value,
                "last_run": agent.last_run.isoformat() if agent.last_run else None,
                "description": agent.description
            }
            for agent_id, agent in self.agents.items()
        }
