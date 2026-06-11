import React, { useState, useEffect, useRef } from 'react';

// UI Icon components drawn as inline SVGs for maximum reliability
const Icons = {
  Zap: () => (
    <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  Shield: () => (
    <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  Trophy: () => (
    <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
    </svg>
  ),
  Clock: () => (
    <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Sparkles: () => (
    <svg className="w-5 h-5 text-pink-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  ),
  Check: () => (
    <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
  Terminal: () => (
    <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  )
};

export default function App() {
  const [activeTab, setActiveTab] = useState('moat');
  
  // Custom Project State
  const [project, setProject] = useState({
    title: 'Titan Defend Protocol',
    description: 'An AI-powered zero-knowledge firewall running at the edge, utilizing decentralized state channels to coordinate defense strategies dynamically.',
    targetHackathon: 'Global ETH & AI Superhack 2026',
    // 5 Hackathon Moat Metric Factors (0 to 100)
    metrics: {
      technicalComplexity: 85,
      wowFactor: 75,
      sponsorIntegration: 90,
      executionSpeed: 80,
      pitchCharisma: 70
    },
    bounties: [
      { id: 1, sponsor: 'Base Network', title: 'Best L2 Implementation', prize: 5000, prob: 45, chosen: true },
      { id: 2, sponsor: 'Galadriel AI', title: 'Smartest On-chain Agent', prize: 3500, prob: 30, chosen: true },
      { id: 3, sponsor: 'Sign Protocol', title: 'Best Attestation Hook', prize: 2000, prob: 60, chosen: false },
      { id: 4, sponsor: 'Pyth Network', title: 'Most Innovative Oracle Integration', prize: 4000, prob: 25, chosen: true }
    ]
  });

  // Presentation Timer State
  const [pitchTimeLeft, setPitchTimeLeft] = useState(180); // 3 minutes standard
  const [timerRunning, setTimerRunning] = useState(false);
  const [pitchStep, setPitchStep] = useState(0); // 5 key parts of 3 mins

  // Gemini AI Generation State
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiFeedback, setAiFeedback] = useState({
    pitchHook: '',
    vulnerabilityAnalysis: '',
    suggestedMoatImprovements: ''
  });
  const [customPrompt, setCustomPrompt] = useState('Critique my tech moat and provide 3 high-impact feature shortcuts to stun the jury.');
  const [consoleLogs, setConsoleLogs] = useState([
    'System initialized: Titan Engine ready.',
    'Loaded preset: Global ETH & AI Superhack parameters successfully imported.'
  ]);

  const logMessage = (msg) => {
    setConsoleLogs(prev => [ `[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 8) ]);
  };

  // Helper calculation for overall Moat score
  const moatScore = Math.round(
    (project.metrics.technicalComplexity * 0.25) +
    (project.metrics.wowFactor * 0.25) +
    (project.metrics.sponsorIntegration * 0.20) +
    (project.metrics.executionSpeed * 0.15) +
    (project.metrics.pitchCharisma * 0.15)
  );

  // Expected Value calculation
  const totalPrizeMoney = project.bounties.filter(b => b.chosen).reduce((acc, curr) => acc + curr.prize, 0);
  const expectedValue = Math.round(
    project.bounties.filter(b => b.chosen).reduce((acc, curr) => acc + (curr.prize * (curr.prob / 100)), 0)
  );

  // Pitch Steps Config
  const steps = [
    { name: "The Hook & Impact", duration: 30, desc: "Capture the jury's attention immediately. Show, don't tell, the major problem." },
    { name: "The Core Solution", duration: 45, desc: "Introduce your app. Explain how your core concept solves this problem beautifully." },
    { name: "The Wow Live Demo", duration: 60, desc: "Step through your absolute best frontend flow. Keep delay times at 0; fake what you must." },
    { name: "The Unfair Tech Moat", duration: 30, desc: "Detail your architectural choices, cryptography secrets, or unique integrations." },
    { name: "Q&A Readiness", duration: 15, desc: "Wrap up clean and hand over seamlessly. State exactly how you will capture the market." }
  ];

  // Radar chart helper points
  const getRadarPoints = () => {
    const center = 150;
    const maxRadius = 110;
    const angles = [0, 72, 144, 216, 288];
    const keys = ['technicalComplexity', 'wowFactor', 'sponsorIntegration', 'executionSpeed', 'pitchCharisma'];
    
    return keys.map((key, i) => {
      const value = project.metrics[key];
      const radius = (value / 100) * maxRadius;
      const rad = (angles[i] - 90) * (Math.PI / 180);
      return {
        x: center + radius * Math.cos(rad),
        y: center + radius * Math.sin(rad),
        label: key.replace(/([A-Z])/g, ' $1').trim()
      };
    });
  };

  const points = getRadarPoints();
  const polygonPoints = points.map(p => `${p.x},${p.y}`).join(' ');

  // Live countdown timer logic
  useEffect(() => {
    let interval = null;
    if (timerRunning && pitchTimeLeft > 0) {
      interval = setInterval(() => {
        setPitchTimeLeft(prev => {
          const nextTime = prev - 1;
          // Determine pitch step based on time passed
          let timeElapsed = 180 - nextTime;
          let cumulativeTime = 0;
          let currentStep = 0;
          for (let i = 0; i < steps.length; i++) {
            cumulativeTime += steps[i].duration;
            if (timeElapsed <= cumulativeTime) {
              currentStep = i;
              break;
            }
          }
          setPitchStep(currentStep);
          return nextTime;
        });
      }, 1000);
    } else if (pitchTimeLeft === 0) {
      setTimerRunning(false);
      logMessage("Presentation rehearsal timer finished!");
    }
    return () => clearInterval(interval);
  }, [timerRunning, pitchTimeLeft]);

  // Adjust specific metric slider
  const handleMetricChange = (metric, value) => {
    setProject(prev => ({
      ...prev,
      metrics: {
        ...prev.metrics,
        [metric]: Number(value)
      }
    }));
    logMessage(`Adjusted ${metric} level to ${value}%`);
  };

  // Toggle dynamic bounty selection
  const toggleBounty = (id) => {
    setProject(prev => ({
      ...prev,
      bounties: prev.bounties.map(b => b.id === id ? { ...b, chosen: !b.chosen } : b)
    }));
    logMessage(`Updated target bounty pipeline profile.`);
  };

  const updateBountyProp = (id, field, val) => {
    setProject(prev => ({
      ...prev,
      bounties: prev.bounties.map(b => b.id === id ? { ...b, [field]: val } : b)
    }));
  };

  const addNewBounty = () => {
    const newB = {
      id: Date.now(),
      sponsor: 'Sponsor X',
      title: 'Best General Use Track',
      prize: 3000,
      prob: 50,
      chosen: true
    };
    setProject(prev => ({
      ...prev,
      bounties: [...prev.bounties, newB]
    }));
    logMessage(`Created custom tactical bounty tracker.`);
  };

  const removeBounty = (id) => {
    setProject(prev => ({
      ...prev,
      bounties: prev.bounties.filter(b => b.id !== id)
    }));
    logMessage(`Pruned bounty target.`);
  };

  // Exponential backoff runner for native Google Gemini
  const askTitanAI = async () => {
    setAiGenerating(true);
    logMessage("Initiating secure tunnel to Gemini 2.5 Flash...");
    
    const apiKey = ""; // Filled transparently at runtime inside current framework 
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;
    
    const prompt = `
      You are the ultimate Hackathon Strategist Judge (Titan). Critique this hackathon concept and provide structured tactical gameplans to turn it into an immediate winner.
      
      HACKATHON IDEA:
      Project Name: ${project.title}
      Description: ${project.description}
      Targeting: ${project.targetHackathon}
      
      Metric Self-Assessments:
      - Technical Complexity: ${project.metrics.technicalComplexity}/100
      - Wow Factor / Slick Demo Potential: ${project.metrics.wowFactor}/100
      - Sponsor Integration Density: ${project.metrics.sponsorIntegration}/100
      
      USER'S DIRECTIVE:
      "${customPrompt}"
      
      Respond STRICTLY in valid JSON format ONLY. Do not wrap in markdown blocks, just raw JSON with these precise keys:
      {
        "pitchHook": "An incredibly compelling, high-converting 1-sentence hook that instantly frames this project for maximum jury wow factor.",
        "vulnerabilityAnalysis": "Honest critique of what could make this project crash and burn on the judge's table (e.g. backend fakes exposed, too complex to explain).",
        "suggestedMoatImprovements": "3 concrete hacks to shortcut development, double down on the 'moat illusion', and swipe all target sponsor tracks."
      }
    `;

    const systemPrompt = "You are a highly analytical technical director and pitch coach with 50+ global hackathon wins. You provide brutally honest, brilliant shortcut strategies.";

    let baseDelay = 1000;
    let responseText = "";
    let success = false;

    for (let attempt = 1; attempt <= 5; attempt++) {
      try {
        const payload = {
          contents: [{ parts: [{ text: prompt }] }],
          systemInstruction: { parts: [{ text: systemPrompt }] },
          generationConfig: { 
            responseMimeType: "application/json" 
          }
        };

        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const data = await res.json();
          responseText = data.candidates?.[0]?.content?.parts?.[0]?.text;
          success = true;
          break;
        }
      } catch (e) {
        // Continue loop for retry
      }
      logMessage(`Retrying connection to Gemini model (Attempt ${attempt}/5)...`);
      await new Promise(resolve => setTimeout(resolve, baseDelay));
      baseDelay *= 2;
    }

    if (!success) {
      logMessage("Critical API response failure. Generating fallback simulated strategist feedback.");
      // Fallback fallback if keys or connection limits interrupt
      setTimeout(() => {
        setAiFeedback({
          pitchHook: `"${project.title} is not just another app—it is a secure, high-performance middleware architecture safeguarding edge queries without sacrificing user latency."`,
          vulnerabilityAnalysis: "A 36-hour window is too short to construct true decentralized states. If your Web3 network or edge wallet setup fails to resolve during the presentation, your entire demo is instantly bricked.",
          suggestedMoatImprovements: "1. Build an offline mock mode with instant preset success triggers. 2. Implement a local-first service fallback so you can demo completely isolated from internet dropouts. 3. Prioritize clean visual dashboards above complex protocol logic."
        });
        setAiGenerating(false);
      }, 1500);
      return;
    }

    try {
      const parsed = JSON.parse(responseText.trim());
      setAiFeedback({
        pitchHook: parsed.pitchHook || "Unable to formulate hook",
        vulnerabilityAnalysis: parsed.vulnerabilityAnalysis || "No obvious vulnerabilities detected.",
        suggestedMoatImprovements: parsed.suggestedMoatImprovements || "N/A"
      });
      logMessage("Strategic intelligence analysis compiled successfully!");
    } catch (err) {
      logMessage("Error compiling structured feedback. Using safe raw parser format.");
      setAiFeedback({
        pitchHook: "Failed raw format extraction.",
        vulnerabilityAnalysis: responseText,
        suggestedMoatImprovements: "Please attempt another query."
      });
    }
    setAiGenerating(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased selection:bg-indigo-500 selection:text-white">
      {/* Premium Cyber Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-4 flex flex-col md:flex-row justify-between items-center gap-4 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold shadow-lg shadow-indigo-500/20">
            Ω
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-indigo-300">
              TITAN HACKATHON ENGINE
            </h1>
            <p className="text-xs text-slate-400 font-mono">SECURE THE DEFENSIVE HACKATHON MOAT v4.1</p>
          </div>
        </div>

        {/* Global Score Panel */}
        <div className="flex items-center gap-6">
          <div className="text-center md:text-right bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-2 flex items-center gap-4">
            <div>
              <div className="text-[10px] text-slate-400 font-mono tracking-wider">PROJECT DEFENSE INDEX</div>
              <div className="text-2xl font-black text-indigo-400 font-mono">
                {moatScore} <span className="text-xs text-slate-500">/100</span>
              </div>
            </div>
            <div className={`h-8 w-2 rounded-full ${moatScore > 80 ? 'bg-emerald-500' : moatScore > 60 ? 'bg-amber-400' : 'bg-red-500 animate-pulse'}`} />
          </div>
        </div>
      </header>

      {/* Main Grid Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Control Deck: Info Box & Controls (4 Cols) */}
        <section className="lg:col-span-4 flex flex-col gap-6">
          
          {/* Concept Profile */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm shadow-xl flex flex-col gap-4">
            <h2 className="text-sm font-semibold text-slate-300 tracking-wider font-mono flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500" />
              PROJECT IDENTITY
            </h2>

            <div className="flex flex-col gap-3">
              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">Project Concept Title</label>
                <input 
                  type="text" 
                  value={project.title}
                  onChange={(e) => setProject({ ...project, title: e.target.value })}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-mono transition-colors"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">Target Hackathon Ecosystem</label>
                <input 
                  type="text" 
                  value={project.targetHackathon}
                  onChange={(e) => setProject({ ...project, targetHackathon: e.target.value })}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-mono transition-colors"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">Elevator Description & Core Moat</label>
                <textarea 
                  rows={3}
                  value={project.description}
                  onChange={(e) => setProject({ ...project, description: e.target.value })}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-indigo-500 transition-colors resize-none"
                  placeholder="Describe your architecture & key competitive moat..."
                />
              </div>
            </div>
          </div>

          {/* Interactive Logs Terminal */}
          <div className="bg-slate-950 border border-slate-800/60 rounded-2xl p-4 flex-1 flex flex-col">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs text-indigo-400 font-mono flex items-center gap-2">
                <Icons.Terminal /> SYSTEM LOGS
              </span>
              <button 
                onClick={() => setConsoleLogs(['Terminal cleared.'])}
                className="text-[10px] text-slate-500 hover:text-slate-300 font-mono"
              >
                CLEAR
              </button>
            </div>
            <div className="flex-1 max-h-[160px] lg:max-h-none overflow-y-auto font-mono text-[11px] leading-relaxed text-slate-400 flex flex-col gap-1.5 scrollbar-thin scrollbar-thumb-slate-800">
              {consoleLogs.map((log, index) => (
                <div key={index} className="border-l border-slate-800 pl-2 py-0.5">
                  {log}
                </div>
              ))}
            </div>
          </div>

        </section>

        {/* Right Active Interface: Tabs & Analytical Tools (8 Cols) */}
        <section className="lg:col-span-8 flex flex-col gap-6">
          
          {/* Tab Selection */}
          <nav className="flex bg-slate-900/60 p-1 rounded-xl border border-slate-800 gap-1">
            <button 
              onClick={() => setActiveTab('moat')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-semibold rounded-lg transition-all ${activeTab === 'moat' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
            >
              <Icons.Shield />
              Moat Architect
            </button>
            <button 
              onClick={() => setActiveTab('bounty')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-semibold rounded-lg transition-all ${activeTab === 'bounty' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
            >
              <Icons.Trophy />
              Bounty Strategist
            </button>
            <button 
              onClick={() => setActiveTab('pitch')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-semibold rounded-lg transition-all ${activeTab === 'pitch' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
            >
              <Icons.Clock />
              3-Min Pitch Matrix
            </button>
            <button 
              onClick={() => setActiveTab('copilot')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-semibold rounded-lg transition-all ${activeTab === 'copilot' ? 'bg-indigo-600 text-white shadow hover:shadow-indigo-500/20' : 'text-slate-400 hover:text-slate-200'}`}
            >
              <Icons.Sparkles />
              Gemini Co-Pilot
            </button>
          </nav>

          {/* Tab Contents */}
          <div className="flex-1 bg-slate-900/20 border border-slate-800 rounded-2xl p-6 min-h-[420px] shadow-2xl relative overflow-hidden">
            
            {/* Tab 1: MOAT ARCHITECT */}
            {activeTab === 'moat' && (
              <div className="flex flex-col gap-6 animate-fadeIn">
                <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white">The Hackathon Defense Radar</h3>
                    <p className="text-xs text-slate-400">Balance your project across 5 distinct points of evaluation to guarantee points from technical judges.</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                  
                  {/* Metric Sliders */}
                  <div className="flex flex-col gap-4">
                    {Object.entries(project.metrics).map(([key, val]) => (
                      <div key={key} className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3">
                        <div className="flex justify-between text-xs font-semibold mb-1">
                          <span className="capitalize text-slate-300">
                            {key.replace(/([A-Z])/g, ' $1').trim()}
                          </span>
                          <span className="text-indigo-400 font-mono">{val}%</span>
                        </div>
                        <input 
                          type="range" 
                          min="10" 
                          max="100" 
                          value={val}
                          onChange={(e) => handleMetricChange(key, e.target.value)}
                          className="w-full accent-indigo-500 h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer"
                        />
                        <span className="text-[10px] text-slate-500 mt-1 block">
                          {key === 'technicalComplexity' && 'How hard is this build to replicate under 36 hours?'}
                          {key === 'wowFactor' && 'Will judges raise eyebrows in the first 10 seconds of use?'}
                          {key === 'sponsorIntegration' && 'How heavily are you utilizing key sponsor platform APIs?'}
                          {key === 'executionSpeed' && 'Your speed of delivering a functional, bug-free dashboard/UI.'}
                          {key === 'pitchCharisma' && 'The narrative hook, performance delivery, and confidence.'}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* SVG Drawn Dynamic Radar Chart */}
                  <div className="flex flex-col items-center justify-center p-4 bg-slate-950/60 rounded-2xl border border-slate-800/80">
                    <svg width="240" height="240" viewBox="0 0 300 300" className="drop-shadow-lg">
                      {/* Concentric helper grids */}
                      <circle cx="150" cy="150" r="110" fill="none" stroke="#334155" strokeWidth="1" strokeDasharray="4 4" />
                      <circle cx="150" cy="150" r="82.5" fill="none" stroke="#334155" strokeWidth="1" strokeDasharray="4 4" />
                      <circle cx="150" cy="150" r="55" fill="none" stroke="#334155" strokeWidth="1" strokeDasharray="4 4" />
                      <circle cx="150" cy="150" r="27.5" fill="none" stroke="#334155" strokeWidth="1" strokeDasharray="4 4" />
                      
                      {/* Axis Lines */}
                      {points.map((p, i) => {
                        const angles = [0, 72, 144, 216, 288];
                        const rad = (angles[i] - 90) * (Math.PI / 180);
                        const endX = 150 + 110 * Math.cos(rad);
                        const endY = 150 + 110 * Math.sin(rad);
                        return (
                          <line key={i} x1="150" y1="150" x2={endX} y2={endY} stroke="#1e293b" strokeWidth="2" />
                        );
                      })}

                      {/* Filled Defense Polygon */}
                      <polygon points={polygonPoints} fill="rgba(99, 102, 241, 0.25)" stroke="#6366f1" strokeWidth="2.5" />
                      
                      {/* Active points on radar */}
                      {points.map((p, i) => (
                        <circle key={i} cx={p.x} cy={p.y} r="5" fill="#a5b4fc" className="transition-all duration-300" />
                      ))}

                      {/* Radar labels (Clean overlay placements) */}
                      <text x="150" y="24" textAnchor="middle" fill="#94a3b8" fontSize="9" fontWeight="bold">TECH DEPTH</text>
                      <text x="268" y="112" textAnchor="start" fill="#94a3b8" fontSize="9" fontWeight="bold">WOW DEMO</text>
                      <text x="215" y="260" textAnchor="start" fill="#94a3b8" fontSize="9" fontWeight="bold">SPONSOR API</text>
                      <text x="85" y="260" textAnchor="end" fill="#94a3b8" fontSize="9" fontWeight="bold">EXEC VELOCITY</text>
                      <text x="32" y="112" textAnchor="end" fill="#94a3b8" fontSize="9" fontWeight="bold">STORY PITCH</text>
                    </svg>
                    
                    <div className="text-[11px] text-indigo-400 font-mono mt-3">
                      Dynamic Defense Profile: <span className="text-white font-bold">{moatScore > 75 ? 'UNASSILABLE' : 'IMPROVABLE'}</span>
                    </div>
                  </div>

                </div>
              </div>
            )}

            {/* Tab 2: BOUNTY STRATEGIST */}
            {activeTab === 'bounty' && (
              <div className="flex flex-col gap-6 animate-fadeIn">
                <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white">Multi-Bounty Strategy Pipeline</h3>
                    <p className="text-xs text-slate-400">Professional hackathon hunters stack sponsor tracks to spread variance and secure multiple cash prize payouts.</p>
                  </div>
                  <button 
                    onClick={addNewBounty}
                    className="bg-indigo-600/30 hover:bg-indigo-600 text-indigo-300 hover:text-white px-3 py-1.5 text-xs font-semibold rounded-lg border border-indigo-500/50 transition-all flex items-center gap-1"
                  >
                    + ADD TARGET
                  </button>
                </div>

                {/* Dashboard Metrics summary */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 text-center">
                    <span className="text-[10px] text-slate-400 font-mono block">PIPELINE GRAND TOTAL</span>
                    <span className="text-xl font-black text-white font-mono">${totalPrizeMoney}</span>
                  </div>
                  <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 text-center">
                    <span className="text-[10px] text-slate-400 font-mono block">PROBABILISTIC EXPECTED VALUE</span>
                    <span className="text-xl font-black text-emerald-400 font-mono">${expectedValue}</span>
                  </div>
                  <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 text-center col-span-2 md:col-span-1">
                    <span className="text-[10px] text-slate-400 font-mono block">DENSITY COEFFICIENT</span>
                    <span className="text-xl font-black text-amber-400 font-mono">
                      {Math.round((project.bounties.filter(b => b.chosen).length / project.bounties.length) * 100)}%
                    </span>
                  </div>
                </div>

                {/* List of active targets */}
                <div className="flex flex-col gap-3">
                  {project.bounties.map(b => (
                    <div 
                      key={b.id} 
                      className={`flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border transition-all ${b.chosen ? 'bg-indigo-950/20 border-indigo-500/40 shadow-md shadow-indigo-500/5' : 'bg-slate-950/40 border-slate-800 opacity-60'}`}
                    >
                      <div className="flex items-start gap-3">
                        <input 
                          type="checkbox" 
                          checked={b.chosen}
                          onChange={() => toggleBounty(b.id)}
                          className="w-4 h-4 text-indigo-600 rounded mt-1 accent-indigo-500 cursor-pointer"
                        />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs bg-slate-800 text-slate-300 font-mono px-1.5 py-0.5 rounded">
                              {b.sponsor}
                            </span>
                          </div>
                          <input 
                            type="text" 
                            value={b.title} 
                            onChange={(e) => updateBountyProp(b.id, 'title', e.target.value)}
                            className="bg-transparent text-sm font-semibold text-slate-200 border-b border-transparent hover:border-slate-800 focus:border-indigo-500 focus:outline-none focus:bg-slate-950 px-1 mt-1 font-sans"
                          />
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        {/* Prize amount input */}
                        <div>
                          <span className="text-[10px] text-slate-400 block mb-0.5 font-mono">PRIZE ($)</span>
                          <input 
                            type="number" 
                            value={b.prize} 
                            onChange={(e) => updateBountyProp(b.id, 'prize', Number(e.target.value))}
                            className="w-20 bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-xs text-white font-mono"
                          />
                        </div>

                        {/* Win Probability slider */}
                        <div className="w-24">
                          <span className="text-[10px] text-slate-400 block mb-0.5 font-mono">PROBABILITY ({b.prob}%)</span>
                          <input 
                            type="range" 
                            min="5" 
                            max="95" 
                            value={b.prob} 
                            onChange={(e) => updateBountyProp(b.id, 'prob', Number(e.target.value))}
                            className="w-full accent-indigo-500 h-1 bg-slate-950 rounded-lg appearance-none cursor-pointer"
                          />
                        </div>

                        {/* Action buttons */}
                        <button 
                          onClick={() => removeBounty(b.id)}
                          className="text-slate-500 hover:text-red-400 text-xs font-bold transition-colors p-1"
                          title="Remove bounty target"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab 3: PITCH MATRIX */}
            {activeTab === 'pitch' && (
              <div className="flex flex-col gap-6 animate-fadeIn">
                <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white">3-Minute Demo Matrix Pitch Coach</h3>
                    <p className="text-xs text-slate-400">At the judging table, you have exactly 180 seconds. Break down your delivery cleanly to secure standard presentation points.</p>
                  </div>
                </div>

                {/* Main Timer Display */}
                <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-6">
                  <div className="flex items-center gap-4">
                    <div className="w-20 h-20 rounded-full border-4 border-indigo-500/20 flex items-center justify-center relative">
                      <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin" style={{ animationDuration: '4s' }} />
                      <span className="text-2xl font-black font-mono text-white">
                        {Math.floor(pitchTimeLeft / 60)}:{(pitchTimeLeft % 60).toString().padStart(2, '0')}
                      </span>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono tracking-wider text-indigo-400">REHEARSAL MASTER</div>
                      <div className="text-lg font-bold text-slate-200">
                        {steps[pitchStep]?.name || 'Rehearsal Terminated'}
                      </div>
                      <div className="text-xs text-slate-400 max-w-[280px]">
                        {steps[pitchStep]?.desc || 'Demo Complete. Await QA panel.'}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button 
                      onClick={() => setTimerRunning(!timerRunning)}
                      className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${timerRunning ? 'bg-amber-600 hover:bg-amber-500 text-white' : 'bg-indigo-600 hover:bg-indigo-500 text-white'}`}
                    >
                      {timerRunning ? 'PAUSE CLOCK' : 'START TIMER'}
                    </button>
                    <button 
                      onClick={() => {
                        setTimerRunning(false);
                        setPitchTimeLeft(180);
                        setPitchStep(0);
                      }}
                      className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 text-xs font-semibold rounded-lg transition-all"
                    >
                      RESET
                    </button>
                  </div>
                </div>

                {/* Progress breakdown visualization */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  {steps.map((s, idx) => (
                    <div 
                      key={idx}
                      className={`p-3 rounded-xl border flex flex-col justify-between h-24 transition-all ${pitchStep === idx ? 'bg-indigo-950/30 border-indigo-500 shadow' : 'bg-slate-950/50 border-slate-800'}`}
                    >
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-[10px] text-slate-400 font-mono">PART 0{idx + 1}</span>
                          <span className="text-[10px] text-indigo-400 font-mono font-bold">{s.duration}s</span>
                        </div>
                        <span className="text-xs font-bold block text-slate-200 leading-tight">
                          {s.name}
                        </span>
                      </div>
                      {/* Interactive indicator */}
                      <div className="h-1 w-full bg-slate-900 rounded-full overflow-hidden mt-2">
                        <div 
                          className={`h-full ${pitchStep === idx ? 'bg-indigo-500 animate-pulse' : pitchStep > idx ? 'bg-emerald-500' : 'bg-slate-800'}`}
                          style={{ width: pitchStep === idx ? `${(1 - (pitchTimeLeft % s.duration) / s.duration) * 100}%` : pitchStep > idx ? '100%' : '0%' }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab 4: GEMINI CO-PILOT */}
            {activeTab === 'copilot' && (
              <div className="flex flex-col gap-6 animate-fadeIn">
                <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Icons.Sparkles /> Titan Strategy AI Co-Pilot
                    </h3>
                    <p className="text-xs text-slate-400">Leverage the intelligence of a multi-turn hackathon veteran to design architectural workarounds, clean features, and pitch hooks.</p>
                  </div>
                </div>

                {/* Input Prompt Control Box */}
                <div className="flex flex-col gap-3">
                  <div className="flex gap-2">
                    <input 
                      type="text" 
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      placeholder="Ask Titan anything (e.g. 'Critique our project moat', 'Explain zero-knowledge proof integrations simply')"
                      className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono transition-colors"
                    />
                    <button 
                      onClick={askTitanAI}
                      disabled={aiGenerating}
                      className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs px-4 py-2 rounded-lg transition-all flex items-center gap-1 shrink-0"
                    >
                      {aiGenerating ? 'PROBING...' : 'RUN ANALYST'}
                    </button>
                  </div>
                  
                  {/* Prompt Quick Tags */}
                  <div className="flex flex-wrap gap-2">
                    <button 
                      onClick={() => setCustomPrompt("Critique my project’s technical moat and expose vulnerabilities.")}
                      className="text-[10px] bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded-md border border-slate-800 font-mono transition-colors"
                    >
                      # Critique Moat
                    </button>
                    <button 
                      onClick={() => setCustomPrompt("Produce an incredible 1-sentence hook to capture immediate attention.")}
                      className="text-[10px] bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded-md border border-slate-800 font-mono transition-colors"
                    >
                      # Pitch Hook
                    </button>
                    <button 
                      onClick={() => setCustomPrompt("Invent 3 high-impact sponsor integrations to sweep bounties.")}
                      className="text-[10px] bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded-md border border-slate-800 font-mono transition-colors"
                    >
                      # Sponsor Hacks
                    </button>
                  </div>
                </div>

                {/* AI Outputs Panel */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
                  
                  {/* Generated Pitch Hook Card */}
                  <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 flex flex-col gap-2">
                    <div className="text-[10px] text-pink-400 font-mono tracking-wider font-bold">1-SENTENCE HOOK PRESET</div>
                    {aiGenerating ? (
                      <div className="h-20 flex items-center justify-center">
                        <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                      </div>
                    ) : (
                      <p className="text-xs text-slate-300 italic leading-relaxed">
                        {aiFeedback.pitchHook || '"Build real defensibility into hackathon pitches before presenting. Connect with high value sponsor APIs."'}
                      </p>
                    )}
                  </div>

                  {/* Generated Vulnerabilities Card */}
                  <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 flex flex-col gap-2">
                    <div className="text-[10px] text-amber-400 font-mono tracking-wider font-bold">VULNERABILITY ANALYSIS</div>
                    {aiGenerating ? (
                      <div className="h-20 flex items-center justify-center">
                        <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                      </div>
                    ) : (
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {aiFeedback.vulnerabilityAnalysis || 'No vulnerabilities detected yet. Run the strategy analyst to map risk.'}
                      </p>
                    )}
                  </div>

                  {/* Suggested Improvements Card */}
                  <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 flex flex-col gap-2">
                    <div className="text-[10px] text-indigo-400 font-mono tracking-wider font-bold">SUGGESTED MOAT SHORTCUTS</div>
                    {aiGenerating ? (
                      <div className="h-20 flex items-center justify-center">
                        <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                      </div>
                    ) : (
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {aiFeedback.suggestedMoatImprovements || 'Run the AI agent tool to populate priority execution recommendations.'}
                      </p>
                    )}
                  </div>

                </div>
              </div>
            )}

          </div>

        </section>

      </main>

      {/* Defensive Checklist Bottom Ticker */}
      <footer className="border-t border-slate-800 bg-slate-950/80 px-6 py-3 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-slate-400 font-mono">
        <div className="flex items-center gap-4 flex-wrap">
          <span className="text-indigo-400 font-bold">TITAN MOAT CHECKLIST:</span>
          <span className="flex items-center gap-1 text-slate-300">
            <Icons.Check /> Mock Backend Safe Mode
          </span>
          <span className="flex items-center gap-1 text-slate-300">
            <Icons.Check /> Front-end Demo Flow Solid
          </span>
          <span className="flex items-center gap-1 text-slate-300">
            <Icons.Check /> Multi-API Stacked
          </span>
        </div>
        <div>
          © 2026 Titan Hackathon Moat Engine. Engineered for Elite Developers.
        </div>
      </footer>
    </div>
  );
}
