import React, { useState, useEffect } from 'react';

const PharmaAIDashboard = () => {
  const [activeAgent, setActiveAgent] = useState(null);
  const [queryRunning, setQueryRunning] = useState(false);
  const [progress, setProgress] = useState([]);
  const [report, setReport] = useState(null);
  const [step, setStep] = useState(0);

  const agents = [
    { id: 'internal', name: 'Internal Knowledge', icon: '📚', color: '#28A745' },
    { id: 'clinical', name: 'Clinical Trials', icon: '🔬', color: '#17A2B8' },
    { id: 'patent', name: 'Patent Landscape', icon: '📜', color: '#6F42C1' },
    { id: 'iqvia', name: 'IQVIA Insights', icon: '📊', color: '#FD7E14' },
    { id: 'exim', name: 'EXIM Trends', icon: '🚢', color: '#20C997' },
    { id: 'web', name: 'Web Intelligence', icon: '🌐', color: '#007BFF' },
  ];

  const mockResults = {
    overall: 7.4,
    market: 7.5,
    competitive: 6.0,
    regulatory: 8.0,
    scientific: 8.0,
    supply: 7.0,
    recommendation: 'PROCEED WITH CAUTION',
    findings: [
      { category: 'Clinical Evidence', text: 'Late-stage trials indicate mature evidence base' },
      { category: 'IP Landscape', text: 'Novel formulation could provide differentiation' },
      { category: 'Market Intelligence', text: 'Global market size: $3.2B with 4.2% CAGR' },
    ],
  };

  const runDemo = async () => {
    setQueryRunning(true);
    setProgress([]);
    setReport(null);
    setStep(1);

    // Simulate agent execution
    for (let i = 0; i < agents.length; i++) {
      setActiveAgent(agents[i].id);
      setProgress(prev => [...prev, { agent: agents[i].name, status: 'running' }]);
      await new Promise(r => setTimeout(r, 400));
      setProgress(prev => 
        prev.map((p, idx) => idx === i ? { ...p, status: 'completed' } : p)
      );
    }

    setActiveAgent(null);
    setStep(2);
    await new Promise(r => setTimeout(r, 500));
    setReport(mockResults);
    setQueryRunning(false);
    setStep(3);
  };

  const ScoreCard = ({ label, value, icon }) => {
    const color = value >= 7.5 ? '#28A745' : value >= 5.5 ? '#FFC107' : '#DC3545';
    const width = (value / 10) * 100;
    return (
      <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
        <div className="flex justify-between items-center mb-2">
          <span className="text-gray-400 text-sm">{icon} {label}</span>
          <span className="font-bold" style={{ color }}>{value.toFixed(1)}</span>
        </div>
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${width}%`, backgroundColor: color }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900 to-blue-800 rounded-xl p-6 mb-6 border-l-4 border-orange-500">
        <h1 className="text-3xl font-bold mb-2">🧬 Pharma AI | Opportunity Assessment</h1>
        <p className="text-blue-200">Agentic AI System with Institutional Knowledge Memory</p>
        <div className="mt-2 inline-block bg-yellow-500 text-gray-900 px-3 py-1 rounded-full text-sm font-bold">
          EY Techathon 6.0 - Round 2 PoC
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Query */}
        <div className="lg:col-span-1">
          <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
            <h2 className="text-lg font-bold mb-4 text-orange-400">💬 Research Query</h2>
            <div className="bg-gray-900 rounded-lg p-4 mb-4 border border-gray-600">
              <p className="text-gray-300 italic">
                "Evaluate Metformin for anti-inflammatory indications"
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
              <div className="bg-gray-700 rounded p-2">
                <span className="text-gray-400">Molecule:</span>
                <span className="ml-2 text-white font-medium">Metformin</span>
              </div>
              <div className="bg-gray-700 rounded p-2">
                <span className="text-gray-400">Indication:</span>
                <span className="ml-2 text-white font-medium">Anti-inflammatory</span>
              </div>
            </div>
            <button
              onClick={runDemo}
              disabled={queryRunning}
              className={`w-full py-3 rounded-lg font-bold text-lg transition-all ${
                queryRunning 
                  ? 'bg-gray-600 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 hover:shadow-lg hover:shadow-orange-500/20'
              }`}
            >
              {queryRunning ? '⏳ Running...' : '🚀 Start Research'}
            </button>
          </div>

          {/* Agent Status */}
          <div className="bg-gray-800 rounded-xl p-5 border border-gray-700 mt-6">
            <h2 className="text-lg font-bold mb-4 text-orange-400">🤖 Agent Status</h2>
            <div className="space-y-2">
              {agents.map(agent => {
                const prog = progress.find(p => p.agent === agent.name);
                const isActive = activeAgent === agent.id;
                const isCompleted = prog?.status === 'completed';
                return (
                  <div 
                    key={agent.id}
                    className={`flex items-center p-2 rounded-lg transition-all ${
                      isActive ? 'bg-orange-900/30 border border-orange-500' : 
                      isCompleted ? 'bg-green-900/20 border border-green-500/50' :
                      'bg-gray-700/50'
                    }`}
                  >
                    <span className="text-xl mr-3">{agent.icon}</span>
                    <span className="flex-1 text-sm">{agent.name}</span>
                    {isActive && <span className="text-orange-400">⏳</span>}
                    {isCompleted && <span className="text-green-400">✅</span>}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Panel - Results */}
        <div className="lg:col-span-2">
          {!report ? (
            <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 h-full flex flex-col items-center justify-center text-gray-500">
              <div className="text-6xl mb-4">🔬</div>
              <p className="text-xl">Click "Start Research" to run the demo</p>
              <p className="text-sm mt-2">Watch as 6 AI agents analyze the opportunity</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Recommendation Banner */}
              <div className={`rounded-xl p-6 text-center ${
                report.overall >= 7.5 ? 'bg-gradient-to-r from-green-800 to-green-700' :
                report.overall >= 5.5 ? 'bg-gradient-to-r from-yellow-700 to-yellow-600' :
                'bg-gradient-to-r from-red-800 to-red-700'
              }`}>
                <div className="text-4xl mb-2">
                  {report.overall >= 7.5 ? '✅' : report.overall >= 5.5 ? '⚠️' : '❌'}
                </div>
                <h2 className="text-2xl font-bold">{report.recommendation}</h2>
                <p className="text-lg mt-1">Overall Score: {report.overall.toFixed(1)} / 10</p>
              </div>

              {/* Score Cards */}
              <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h3 className="text-lg font-bold mb-4 text-orange-400">📊 Assessment Scores</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <ScoreCard label="Market" value={report.market} icon="📈" />
                  <ScoreCard label="Competitive" value={report.competitive} icon="⚔️" />
                  <ScoreCard label="Regulatory" value={report.regulatory} icon="📋" />
                  <ScoreCard label="Scientific" value={report.scientific} icon="🔬" />
                  <ScoreCard label="Supply Chain" value={report.supply} icon="🚚" />
                  <ScoreCard label="Overall" value={report.overall} icon="🎯" />
                </div>
              </div>

              {/* Key Findings */}
              <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h3 className="text-lg font-bold mb-4 text-orange-400">🔍 Key Findings</h3>
                <div className="space-y-3">
                  {report.findings.map((finding, idx) => (
                    <div key={idx} className="bg-gray-700/50 rounded-lg p-4 border-l-4 border-cyan-500">
                      <div className="text-cyan-400 text-sm font-bold mb-1">{finding.category}</div>
                      <p className="text-gray-200">{finding.text}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Execution Stats */}
              <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h3 className="text-lg font-bold mb-4 text-orange-400">⚡ Execution Summary</h3>
                <div className="grid grid-cols-4 gap-4 text-center">
                  <div className="bg-gray-700 rounded-lg p-3">
                    <div className="text-2xl font-bold text-green-400">24</div>
                    <div className="text-xs text-gray-400">Sources</div>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-3">
                    <div className="text-2xl font-bold text-blue-400">2.6s</div>
                    <div className="text-xs text-gray-400">Time</div>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-3">
                    <div className="text-2xl font-bold text-purple-400">6</div>
                    <div className="text-xs text-gray-400">Agents</div>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-3">
                    <div className="text-2xl font-bold text-orange-400">Yes</div>
                    <div className="text-xs text-gray-400">Archive Used</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 text-center text-gray-500 text-sm">
        <p>Built for EY Techathon 6.0 | Agentic AI with Institutional Memory</p>
        <p className="mt-1">Reducing pharmaceutical opportunity evaluation from 8-12 weeks to 5-10 days</p>
      </div>
    </div>
  );
};

export default PharmaAIDashboard;
