import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Play, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Database, 
  Cpu, 
  FileText, 
  Lock, 
  Unlock, 
  FileCode, 
  History, 
  Copy, 
  Check, 
  Trash2, 
  Binary, 
  HelpCircle 
} from 'lucide-react';
import { fallbackScenarios, Scenario } from './data/scenarios';

const API_BASE_URL = 'http://localhost:8000';

interface RuleMatch {
  id: string;
  name: string;
  pattern: string;
  severity: string;
  description: string;
}

interface ComparisonResult {
  is_match: boolean;
  diff: string | null;
  size_diff_bytes: number;
  run_1_hash: string;
  run_2_hash: string;
}

interface LedgerRecord {
  timestamp: string;
  original_code_hash: string;
  rule_id: string | null;
  template_id: string | null;
  patch_run_1_hash: string | null;
  patch_run_2_hash: string | null;
  gate_decision: string;
  ledger_hash: string;
}

interface ScanResponse {
  original_code: string;
  matched_rule: RuleMatch | null;
  applied_template_id: string | null;
  patch_run_1: string | null;
  patch_run_2: string | null;
  comparison: ComparisonResult;
  ledger_record: LedgerRecord;
  gate_decision: string;
}

// Quick helper to generate a realistic mock SHA-256 hash for local simulation
const generateMockHash = (str: string): string => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  const hex = Math.abs(hash).toString(16).padStart(8, '0');
  // Extend it to look like a full 64-char SHA-256
  return (hex + '8f7a9c3e5d1b4a6c2e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d').substring(0, 64);
};

export default function App() {
  const [scenarios, setScenarios] = useState<Scenario[]>(fallbackScenarios);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>(fallbackScenarios[0].id);
  const [code, setCode] = useState<string>(fallbackScenarios[0].code);
  const [simulateNonDeterminism, setSimulateNonDeterminism] = useState<boolean>(false);
  
  const [loading, setLoading] = useState<boolean>(false);
  const [activeStep, setActiveStep] = useState<number>(0);
  const [response, setResponse] = useState<ScanResponse | null>(null);
  const [ledgerHistory, setLedgerHistory] = useState<LedgerRecord[]>([]);
  const [copiedText, setCopiedText] = useState<string | null>(null);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch scenarios and initial check
  useEffect(() => {
    const initFetch = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/scenarios`);
        if (res.ok) {
          const data = await res.json();
          setScenarios(data);
          setIsBackendOnline(true);
        } else {
          setIsBackendOnline(false);
        }
      } catch (err) {
        setIsBackendOnline(false);
      }
      fetchLedger();
    };

    initFetch();
  }, []);

  // Update editor when scenario changes
  const handleScenarioChange = (id: string) => {
    setSelectedScenarioId(id);
    const scen = scenarios.find(s => s.id === id);
    if (scen) {
      setCode(scen.code);
    }
  };

  const fetchLedger = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/ledger`);
      if (res.ok) {
        const data = await res.json();
        setLedgerHistory(data);
      }
    } catch (err) {
      // If backend is offline, load from local storage
      const local = localStorage.getItem('replayguard_ledger_history');
      if (local) {
        setLedgerHistory(JSON.parse(local));
      }
    }
  };

  const clearLedger = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/ledger/clear`, { method: 'POST' });
      setLedgerHistory([]);
    } catch (err) {
      setLedgerHistory([]);
      localStorage.removeItem('replayguard_ledger_history');
    }
  };

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    setTimeout(() => setCopiedText(null), 2000);
  };

  const runPipeline = async () => {
    setLoading(true);
    setErrorMsg(null);
    setResponse(null);
    
    // Animate through pipeline steps for visual engagement
    setActiveStep(1); // Scanning
    await new Promise(r => setTimeout(r, 600));
    setActiveStep(2); // Normalizing
    await new Promise(r => setTimeout(r, 600));
    setActiveStep(3); // Replaying
    await new Promise(r => setTimeout(r, 800));
    setActiveStep(4); // Comparing & Ledgering
    await new Promise(r => setTimeout(r, 600));

    if (isBackendOnline) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/scan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            code,
            language: 'python',
            simulate_non_determinism: simulateNonDeterminism
          })
        });

        if (res.ok) {
          const data: ScanResponse = await res.json();
          setResponse(data);
          fetchLedger();
        } else {
          throw new Error("Failed to process scan API");
        }
      } catch (err) {
        runLocalSimulation();
      }
    } else {
      runLocalSimulation();
    }
    
    setLoading(false);
  };

  // Pure frontend simulation engine in case backend isn't available
  const runLocalSimulation = () => {
    // 1. Detect matching rules
    let matchedRule: RuleMatch | null = null;
    let templateId: string | null = null;
    let patch1: string | null = null;
    let patch2: string | null = null;

    if (code.includes('SELECT') && code.includes('WHERE') && code.includes('+')) {
      matchedRule = {
        id: "rule_sql_injection",
        name: "SQL Injection Detection",
        pattern: "query\\s*=\\s*[\"']SELECT\\s+.*\\s+WHERE\\s+(\\w+)\\s*=\\s*[\"']\\s*\\+\\s*(\\w+)",
        severity: "CRITICAL",
        description: "SQL query built using string concatenation. Risk of SQL injection."
      };
      templateId = "template_sql_injection";
      patch1 = code.replace(
        /^([ \t]*)query\s*=\s*["']SELECT\s+(.*)\s+WHERE\s+(\w+)\s*=\s*["']\s*\+\s*(\w+)/m,
        '$1query = "SELECT $2 WHERE $3 = ?"\n$1params = ($4,)'
      );
    } else if (code.includes('API_KEY') && code.includes('=')) {
      matchedRule = {
        id: "rule_hardcoded_secret",
        name: "Hardcoded API Key Detection",
        pattern: "([A-Z_]+_KEY)\\s*=\\s*[\"']([a-zA-Z0-9_]{6,})[\"']",
        severity: "CRITICAL",
        description: "Hardcoded API key detected in plaintext code."
      };
      templateId = "template_hardcoded_secret";
      patch1 = `import os\n\n` + code.replace(
        /API_KEY\s*=\s*["']([a-zA-Z0-9_]{6,})["']/,
        'API_KEY = os.getenv("API_KEY")'
      );
    } else if (code.includes('subprocess.run') && code.includes('shell=True')) {
      matchedRule = {
        id: "rule_unsafe_shell",
        name: "Unsafe Shell Command Detection",
        pattern: "subprocess\\.run\\([\"'](\\w+)\\s+([a-zA-Z0-9_\\-]+)\\s*[\"']\\s*\\+\\s*(\\w+),\\s*shell=True\\)",
        severity: "HIGH",
        description: "Subprocess execution using shell=True with dynamic arguments. Risk of shell injection."
      };
      templateId = "template_unsafe_shell";
      patch1 = code.replace(
        /subprocess\.run\(["'](\w+)\s+([a-zA-Z0-9_\-]+)\s*["']\s*\+\s*(\w+),\s*shell=True\)/,
        'subprocess.run(["$1", "$2", $3], shell=False)'
      );
    } else if (code.includes('eval(')) {
      matchedRule = {
        id: "rule_unsafe_eval",
        name: "Unsafe Eval Execution Detection",
        pattern: "eval\\(.*\\)",
        severity: "CRITICAL",
        description: "Unsafe use of eval() detected, allowing execution of arbitrary code strings."
      };
      templateId = null;
      patch1 = null;
      patch2 = null;
    }

    // Prepare Run 2 (Simulate mismatch if toggled)
    if (patch1) {
      patch2 = patch1;
      const isMismatchScenario = code.trim() === 'query = "SELECT * FROM users WHERE id = " + user_id';
      if (simulateNonDeterminism || isMismatchScenario) {
        const randToken = Math.random().toString(36).substring(2, 10);
        patch2 = patch1 + `\n\n# ReplayGuard Non-Deterministic Seed: ${randToken}`;
      }
    }

    // Determine decisions
    let gateDecision = "REVIEW";
    let isMatch = true;
    let sizeDiff = 0;
    let diff: string | null = null;

    if (matchedRule && templateId && patch1 && patch2) {
      isMatch = !simulateNonDeterminism;
      const isMismatchScenario = code.trim() === 'query = "SELECT * FROM users WHERE id = " + user_id';
      if (isMismatchScenario) {
        isMatch = false;
      }
      
      if (isMatch) {
        gateDecision = "ALLOW";
      } else {
        gateDecision = "BLOCK";
        sizeDiff = patch2.length - patch1.length;
        diff = `--- patch_run_1.py\n+++ patch_run_2.py\n@@ -5,6 +5,8 @@\n     with open(filepath, 'r') as f:\n         return f.read()\n+\n+# ReplayGuard Non-Deterministic Seed: ${patch2.split('Seed: ')[1]}`;
      }
    } else if (matchedRule && !templateId) {
      gateDecision = "REVIEW";
      isMatch = false;
      diff = "One or both patch runs failed to generate.";
    }

    const origHash = generateMockHash(code);
    const p1Hash = patch1 ? generateMockHash(patch1) : "";
    const p2Hash = patch2 ? generateMockHash(patch2) : "";
    const combinedPayload = `${origHash}|${matchedRule?.id || ''}|${templateId || ''}|${p1Hash}|${p2Hash}|${gateDecision}`;
    const ledgerHash = generateMockHash(combinedPayload);

    const record: LedgerRecord = {
      timestamp: new Date().toISOString(),
      original_code_hash: origHash,
      rule_id: matchedRule?.id || null,
      template_id: templateId,
      patch_run_1_hash: patch1 ? p1Hash : null,
      patch_run_2_hash: patch2 ? p2Hash : null,
      gate_decision: gateDecision,
      ledger_hash: ledgerHash
    };

    let explanation = "";
    if (gateDecision === "ALLOW") {
      if (matchedRule) {
        if (matchedRule.id === "rule_sql_injection") {
          explanation = "Deterministic SQL parameterization applied to prevent SQL injection.";
        } else if (matchedRule.id === "rule_hardcoded_secret") {
          explanation = "Hardcoded credential replaced with environment variable loading via os.getenv.";
        } else if (matchedRule.id === "rule_unsafe_shell") {
          explanation = "Unsafe shell=True subprocess run replaced with safe list-based execution.";
        }
      } else {
        explanation = "No issues detected. Code is safe.";
      }
    } else if (gateDecision === "BLOCK") {
      const isMismatchScenario = code.trim() === 'query = "SELECT * FROM users WHERE id = " + user_id';
      if (isMismatchScenario) {
        explanation = "Replay mismatch detected. Merge blocked because remediation output was not reproducible.";
      } else {
        explanation = "Safety Violation: Replay verification detected non-deterministic patch generation. Merging blocked.";
      }
    } else {
      if (matchedRule) {
        explanation = "Violation detected, but no deterministic remediation template is available. Human review required.";
      } else {
        explanation = "No matching deterministic remediation template available. Code routed to manual security review.";
      }
    }

    const simulatedResponse: ScanResponse = {
      original_code: code,
      remediated_code: patch1,
      matched_rule: matchedRule,
      applied_template_id: templateId,
      patch_run_1: patch1,
      patch_run_2: patch2,
      comparison: {
        is_match: isMatch,
        diff: diff,
        size_diff_bytes: sizeDiff,
        run_1_hash: p1Hash,
        run_2_hash: p2Hash
      },
      ledger_record: record,
      gate_decision: gateDecision,
      explanation: explanation
    };

    setResponse(simulatedResponse);

    // Save locally
    const localHistory = localStorage.getItem('replayguard_ledger_history');
    let history: LedgerRecord[] = localHistory ? JSON.parse(localHistory) : [];
    history.unshift(record);
    history = history.slice(0, 50);
    localStorage.setItem('replayguard_ledger_history', JSON.stringify(history));
    setLedgerHistory(history);
  };

  return (
    <div className="min-h-screen pb-16">
      {/* Top Premium Header */}
      <header className="border-b border-slate-800 bg-[#0d1425] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-tr from-blue-600 to-indigo-500 p-2 rounded-lg text-white shadow-lg shadow-blue-500/10">
              <Shield className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white font-sans">ReplayGuard</h1>
                <span className="text-[10px] uppercase font-bold tracking-widest bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded border border-blue-500/30">
                  Patent-Backed Prototype
                </span>
              </div>
              <p className="text-xs text-slate-400">Deterministic Code Remediation with Replay Verification</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Status indicator */}
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${isBackendOnline ? 'bg-emerald-500 shadow-emerald-500/50' : 'bg-amber-500 shadow-amber-500/50'} shadow-lg`}></span>
              <span className="text-xs text-slate-400">
                {isBackendOnline ? 'Backend API Active' : 'Simulation Fallback Mode'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <section className="trust-gate-hero" aria-label="Where ReplayGuard sits">
        <div className="trust-gate-kicker">WHERE REPLAYGUARD SITS</div>

        <h2>ReplayGuard separates fix generation from fix trust.</h2>

        <p className="trust-gate-summary">
          AI agents, scanners, internal scripts, or developers may propose a patch.
          ReplayGuard does not trust the patch until it is replayed, compared, evidenced, and gated.
        </p>

        <div className="trust-gate-flow">
          <div className="trust-gate-sources">
            <div className="trust-gate-chip">AI Agent</div>
            <div className="trust-gate-chip">SAST Scanner</div>
            <div className="trust-gate-chip">Internal Script</div>
            <div className="trust-gate-chip">Human Patch</div>
          </div>

          <div className="trust-gate-arrow">→</div>

          <div className="trust-gate-core">
            <div className="trust-gate-core-title">ReplayGuard Trust Gate</div>
            <div className="trust-gate-core-subtitle">
              Replay • Byte-Compare • Record Evidence • Gate
            </div>
          </div>

          <div className="trust-gate-arrow">→</div>

          <div className="trust-gate-outcomes">
            <div className="trust-gate-outcome allow">ALLOW</div>
            <div className="trust-gate-outcome block">BLOCK</div>
            <div className="trust-gate-outcome review">REVIEW</div>
          </div>
        </div>
      </section>


      {/* Product Explanation Banner */}
      <div className="bg-[#0b0e17] border-b border-slate-800/80 py-3 px-4 text-center">
        <p className="text-xs text-slate-300 font-medium tracking-wide">
          Automated remediation should not move forward on confidence alone. ReplayGuard requires replay evidence before a gate decision is allowed.
        </p>
      </div>

      {/* Main Grid */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Code Input & Controls */}
        <section className="lg:col-span-5 flex flex-col gap-6">
          <div className="glass-panel rounded-xl p-6 shadow-xl flex flex-col gap-5">
            <h2 className="text-lg font-semibold flex items-center gap-2 text-blue-400">
              <FileCode className="w-5 h-5" /> Remediation Verification Input
            </h2>

            {/* Selector */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Load Verification Scenario
              </label>
              <select
                value={selectedScenarioId}
                onChange={(e) => handleScenarioChange(e.target.value)}
                className="w-full bg-[#080c14] border border-slate-700 hover:border-slate-600 rounded-lg py-2 px-3 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
              >
                {scenarios.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              {scenarios.map(s => s.id === selectedScenarioId && (
                <p key={s.id} className="text-xs text-slate-400 mt-2 italic leading-relaxed">
                  {s.description}
                </p>
              ))}
            </div>

            {/* Editor */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Source Code Editor
              </label>
              <div className="relative rounded-lg overflow-hidden border border-slate-800 bg-[#06080d]">
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  rows={9}
                  className="w-full bg-transparent p-4 text-xs font-mono text-slate-300 focus:outline-none resize-none leading-relaxed"
                  placeholder="# Write or paste your python code here..."
                />
              </div>
            </div>

            {/* Simulator Switches */}
            <div className="bg-[#0f1526]/50 border border-slate-800/80 rounded-lg p-4">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                <Binary className="w-4 h-4 text-blue-400" /> Simulation Settings
              </h3>
              
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="non-deterministic"
                  checked={simulateNonDeterminism}
                  onChange={(e) => setSimulateNonDeterminism(e.target.checked)}
                  className="mt-1 h-4.5 w-4.5 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-900"
                />
                <div className="text-xs">
                  <label htmlFor="non-deterministic" className="font-semibold text-slate-200 hover:cursor-pointer">
                    Simulate Non-Determinism (Replay Mismatch)
                  </label>
                  <p className="text-slate-400 mt-1 leading-relaxed">
                    Injects a randomized identifier comment on Run 2. This forces a byte-level mismatch, which triggers a Merge Gate <strong>BLOCK</strong>.
                  </p>
                </div>
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={runPipeline}
              disabled={loading}
              className={`w-full py-3 px-4 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 shadow-lg transition-all ${
                loading 
                  ? 'bg-blue-600/30 text-blue-300 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-500 hover:scale-[1.01] hover:shadow-blue-500/20 active:scale-[0.99] text-white'
              }`}
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing Verification Replays...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Run ReplayGuard Pipeline</span>
                </>
              )}
            </button>
          </div>
        </section>

        {/* Right Column: Pipeline Execution & Results */}
        <section className="lg:col-span-7 flex flex-col gap-6">
          
          {/* Stepper loader */}
          {loading && (
            <div className="glass-panel rounded-xl p-8 shadow-xl flex flex-col gap-6 animate-pulse">
              <h3 className="text-center font-semibold text-slate-300">Executing Replay Verification Pipeline</h3>
              <div className="grid grid-cols-4 gap-4 relative">
                <div className="absolute top-4 left-0 right-0 h-1 bg-slate-800 -z-10"></div>
                
                <div className="flex flex-col items-center text-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${activeStep >= 1 ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400'}`}>
                    1
                  </div>
                  <span className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-wider">Detection</span>
                </div>

                <div className="flex flex-col items-center text-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${activeStep >= 2 ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400'}`}>
                    2
                  </div>
                  <span className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-wider">Normalize</span>
                </div>

                <div className="flex flex-col items-center text-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${activeStep >= 3 ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400'}`}>
                    3
                  </div>
                  <span className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-wider">Dual Run</span>
                </div>

                <div className="flex flex-col items-center text-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${activeStep >= 4 ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400'}`}>
                    4
                  </div>
                  <span className="text-[10px] text-slate-400 mt-2 font-bold uppercase tracking-wider">Ledger Gate</span>
                </div>
              </div>
            </div>
          )}

          {/* Empty Welcome State */}
          {!loading && !response && (
            <div className="glass-panel rounded-xl p-12 shadow-xl flex flex-col items-center text-center gap-6 justify-center min-h-[450px]">
              <div className="bg-[#0f1627] p-4 rounded-full border border-slate-800">
                <Database className="w-12 h-12 text-slate-500" />
              </div>
              <div className="max-w-md">
                <h3 className="text-lg font-semibold text-slate-200">Awaiting Trust Gate Run</h3>
                <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                  Select a remediation verification scenario on the left, set simulation properties, and run the trust gate. The system will demonstrate deterministic detection, dual independent remediation replays, byte-level comparison, evidence recording, and gate decisioning.
                </p>
              </div>
              
              <div className="grid grid-cols-3 gap-4 w-full max-w-lg mt-4 text-xs">
                <div className="border border-slate-800/80 bg-[#0b0e17] rounded-lg p-3">
                  <span className="text-emerald-500 font-bold block mb-1">ALLOW Gate</span>
                  Replay matched. Evidence recorded.
                </div>
                <div className="border border-slate-800/80 bg-[#0b0e17] rounded-lg p-3">
                  <span className="text-rose-500 font-bold block mb-1">BLOCK Gate</span>
                  Replay failed. Change stopped.
                </div>
                <div className="border border-slate-800/80 bg-[#0b0e17] rounded-lg p-3">
                  <span className="text-amber-500 font-bold block mb-1">REVIEW Gate</span>
                  No deterministic path. Human review required.
                </div>
              </div>
            </div>
          )}

          {/* Response Results Display */}
          {!loading && response && (
            <div className="flex flex-col gap-6">
              
              {/* Decision Gate Banner */}
              <div className={`rounded-xl border p-6 flex items-center justify-between shadow-xl ${
                response.gate_decision === 'ALLOW' 
                  ? 'bg-gradient-to-r from-emerald-950/45 to-teal-950/20 border-emerald-500/40 text-emerald-200'
                  : response.gate_decision === 'BLOCK'
                  ? 'bg-gradient-to-r from-rose-950/45 to-red-950/20 border-rose-500/40 text-rose-200'
                  : 'bg-gradient-to-r from-amber-950/45 to-orange-950/20 border-amber-500/40 text-amber-200'
              }`}>
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-full border ${
                    response.gate_decision === 'ALLOW'
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                      : response.gate_decision === 'BLOCK'
                      ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                      : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                  }`}>
                    {response.gate_decision === 'ALLOW' && <Unlock className="w-8 h-8" />}
                    {response.gate_decision === 'BLOCK' && <Lock className="w-8 h-8" />}
                    {response.gate_decision === 'REVIEW' && <AlertTriangle className="w-8 h-8" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2.5">
                      <span className="text-xs uppercase font-extrabold tracking-widest text-slate-300">
                        Merge Gate Decision
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-black ${
                        response.gate_decision === 'ALLOW'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : response.gate_decision === 'BLOCK'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}>
                        {response.gate_decision}
                      </span>
                    </div>
                    <h3 className="text-2xl font-black mt-0.5">
                      {response.gate_decision === 'ALLOW' && 'Merge Gate: ALLOW'}
                      {response.gate_decision === 'BLOCK' && 'Merge Gate: BLOCK'}
                      {response.gate_decision === 'REVIEW' && 'Merge Gate: REVIEW'}
                    </h3>
                    <p className="text-slate-300 text-xs mt-1 font-medium">
                      {response.gate_decision === 'ALLOW' && 'Replay verified. Ledger evidence committed.'}
                      {response.gate_decision === 'BLOCK' && 'Replay mismatch detected. Change cannot proceed.'}
                      {response.gate_decision === 'REVIEW' && 'No deterministic remediation template available. Human review required.'}
                    </p>
                  </div>
                </div>
              </div>

              {/* What Happened Summary Card */}
              <div className="bg-[#0f1423]/60 border border-slate-800 rounded-xl p-5 shadow-md">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Database className="w-4 h-4 text-blue-400" /> What Happened
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed font-normal">
                  {response.gate_decision === 'ALLOW' && 
                    'ReplayGuard detected the issue, applied a deterministic remediation template, replayed the patch twice, verified both outputs matched, and committed ledger evidence.'}
                  {response.gate_decision === 'BLOCK' && 
                    'ReplayGuard detected a replay mismatch. Since the second patch output did not match the first one, the merge gate blocked the change.'}
                  {response.gate_decision === 'REVIEW' && 
                    'ReplayGuard detected an issue, but no deterministic remediation template was available. The change was routed to human review.'}
                </p>
              </div>

              {/* Before/After Code Comparison Section */}
              <div className="glass-panel rounded-xl p-5 shadow-md">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5 border-b border-slate-800 pb-2">
                  <FileCode className="w-4 h-4 text-blue-400" /> Proposed Remediation Comparison
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Left: Original Code */}
                  <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Original Vulnerable Code
                    </span>
                    <div className="bg-[#06080d] p-3 rounded-lg border border-slate-800 overflow-x-auto min-h-[120px]">
                      <pre className="text-[11px] text-slate-300 font-mono leading-relaxed whitespace-pre">
                        {response.original_code}
                      </pre>
                    </div>
                  </div>

                  {/* Right: Remediated Code */}
                  <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Deterministic Remediated Code
                    </span>
                    <div className="bg-[#06080d] p-3 rounded-lg border border-slate-800 overflow-x-auto min-h-[120px] flex items-start">
                      {response.remediated_code ? (
                        <pre className="text-[11px] text-slate-300 font-mono leading-relaxed whitespace-pre w-full">
                          {response.remediated_code}
                        </pre>
                      ) : (
                        <span className="text-[11px] text-slate-500 italic mt-2">
                          No deterministic remediation generated.
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 1: Detector output */}
              <div className="glass-panel rounded-xl p-5 shadow-md">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5 border-b border-slate-800 pb-2">
                  <Cpu className="w-4 h-4 text-blue-400" /> Pipeline Stage 1: Vulnerability Detection
                </h4>
                {response.matched_rule ? (
                  <div className="flex justify-between items-start gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-slate-200">{response.matched_rule.name}</span>
                        <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                          response.matched_rule.severity === 'CRITICAL' 
                            ? 'bg-rose-950 border border-rose-500/30 text-rose-400' 
                            : 'bg-amber-950 border border-amber-500/30 text-amber-400'
                        }`}>
                          {response.matched_rule.severity}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">{response.matched_rule.description}</p>
                      <div className="text-[10px] font-mono text-slate-500 mt-2 bg-[#090d16] py-1 px-2 rounded inline-block">
                        Match Signature: {response.matched_rule.pattern}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] font-bold bg-emerald-500/10 text-emerald-400 py-1 px-2 rounded border border-emerald-500/20">
                        MATCHED
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="text-xs text-slate-400">No vulnerability signature matched.</span>
                      <p className="text-[10px] text-slate-500 mt-1">Code structure is deemed safe or unknown to local policies.</p>
                    </div>
                    <span className="text-[10px] font-bold bg-slate-800/80 text-slate-400 py-1 px-2 rounded border border-slate-700">
                      NO MATCH
                    </span>
                  </div>
                )}
              </div>

              {/* Step 2: Template selection */}
              {response.matched_rule && (
                <div className="glass-panel rounded-xl p-5 shadow-md">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5 border-b border-slate-800 pb-2">
                    <FileText className="w-4 h-4 text-blue-400" /> Pipeline Stage 2: Remediation Mapping
                  </h4>
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400 font-semibold uppercase">Applied Template:</span>
                        <code className="text-xs font-mono text-blue-400 bg-blue-950/20 py-0.5 px-2 rounded border border-blue-500/10">
                          {response.applied_template_id}
                        </code>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-1.5">
                        Selected deterministic substitution schema from local database.
                      </p>
                    </div>
                    <span className="text-[10px] font-bold bg-emerald-500/10 text-emerald-400 py-1 px-2 rounded border border-emerald-500/20">
                      RESOLVED
                    </span>
                  </div>
                </div>
              )}

              {/* Step 3: Replay & Code comparison diff */}
              {response.patch_run_1 && response.patch_run_2 && (
                <div className="glass-panel rounded-xl p-5 shadow-md">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5 border-b border-slate-800 pb-2">
                    <Binary className="w-4 h-4 text-blue-400" /> Pipeline Stage 3: Replay Verification & Byte Comparison
                  </h4>
                  
                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4 mb-4 text-xs">
                    <div className="bg-[#080d16] p-3 rounded-lg border border-slate-800/80">
                      <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">Patch Run 1 Hash</span>
                      <code className="font-mono text-[10px] text-slate-300 break-all select-all">{response.comparison.run_1_hash}</code>
                    </div>
                    <div className="bg-[#080d16] p-3 rounded-lg border border-slate-800/80">
                      <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">Patch Run 2 Hash</span>
                      <code className={`font-mono text-[10px] break-all select-all ${response.comparison.is_match ? 'text-slate-300' : 'text-rose-400 font-bold'}`}>
                        {response.comparison.run_2_hash}
                      </code>
                    </div>
                  </div>

                  {/* Code Panel Display */}
                  {response.comparison.is_match ? (
                    <div className="flex flex-col gap-2">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] text-emerald-400 font-bold uppercase flex items-center gap-1">
                          <CheckCircle className="w-3.5 h-3.5" /> Byte-Level Comparison: MATCH
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {response.patch_run_1.split('\n').length} lines • {new Blob([response.patch_run_1]).size} bytes
                        </span>
                      </div>
                      <div className="bg-[#06080d] p-4 rounded-lg border border-slate-800 overflow-x-auto">
                        <pre className="text-[11px] text-slate-300 font-mono leading-relaxed whitespace-pre">
                          {response.patch_run_1}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-3">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] text-rose-400 font-bold uppercase flex items-center gap-1">
                          <XCircle className="w-3.5 h-3.5" /> Byte-Level Comparison: MISMATCH
                        </span>
                        <span className="text-[10px] text-rose-400 font-mono font-bold bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                          Size Diff: {response.comparison.size_diff_bytes > 0 ? `+${response.comparison.size_diff_bytes}` : response.comparison.size_diff_bytes} bytes
                        </span>
                      </div>
                      
                      {/* Diff output block */}
                      <div className="bg-rose-950/20 border border-rose-900/60 rounded-lg overflow-hidden">
                        <div className="bg-rose-950/35 border-b border-rose-900/60 px-4 py-2 flex justify-between items-center">
                          <span className="text-[10px] font-bold text-rose-300 uppercase tracking-widest font-mono">
                            Comparison Unified Diff
                          </span>
                        </div>
                        <div className="p-4 bg-[#06080d] overflow-x-auto">
                          <pre className="text-[11px] font-mono leading-relaxed whitespace-pre text-slate-400">
                            {response.comparison.diff?.split('\n').map((line, idx) => {
                              const isAddition = line.startsWith('+') && !line.startsWith('+++');
                              const isDeletion = line.startsWith('-') && !line.startsWith('---');
                              const isHeader = line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++');
                              
                              let color = 'text-slate-400';
                              let bg = '';
                              if (isAddition) {
                                color = 'text-emerald-400';
                                bg = 'bg-emerald-950/10';
                              } else if (isDeletion) {
                                color = 'text-rose-400';
                                bg = 'bg-rose-950/10';
                              } else if (isHeader) {
                                color = 'text-indigo-400 font-bold';
                              }
                              
                              return (
                                <div key={idx} className={`${bg} ${color} px-1 rounded-sm`}>
                                  {line}
                                </div>
                              );
                            })}
                          </pre>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Step 4: Cryptographic ledger details */}
              <div className="glass-panel rounded-xl p-5 shadow-md">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-1.5 border-b border-slate-800 pb-2">
                  <Database className="w-4 h-4 text-blue-400" /> Pipeline Stage 4: Cryptographic Ledger Entry
                </h4>

                <div className="flex flex-col gap-4">
                  {/* Ledger Record Hash Chain */}
                  <div className="flex flex-col gap-2 bg-[#080d16] p-4 rounded-lg border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                      Immutable Record Receipt Hash
                    </span>
                    <div className="flex items-center justify-between gap-3">
                      <code className="font-mono text-xs text-blue-400 break-all select-all font-bold">
                        {response.ledger_record.ledger_hash}
                      </code>
                      <button 
                        onClick={() => handleCopy(response.ledger_record.ledger_hash, 'receipt')}
                        className="p-1.5 bg-slate-800 hover:bg-slate-700 hover:text-white rounded border border-slate-700 transition"
                      >
                        {copiedText === 'receipt' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {/* Hash breakdown list */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 text-xs leading-relaxed">
                    <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-400 font-medium">Original Hash:</span>
                      <code className="font-mono text-[10px] text-slate-300 bg-slate-900 px-1.5 py-0.5 rounded">
                        {response.ledger_record.original_code_hash.substring(0, 16)}...
                      </code>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-400 font-medium">Rule Match:</span>
                      <span className="text-slate-300 font-mono text-[10px] bg-slate-900 px-1.5 py-0.5 rounded">
                        {response.ledger_record.rule_id || 'NONE'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-400 font-medium">Applied Template:</span>
                      <span className="text-slate-300 font-mono text-[10px] bg-slate-900 px-1.5 py-0.5 rounded">
                        {response.ledger_record.template_id || 'NONE'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-400 font-medium">Status Flag:</span>
                      <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${
                        response.ledger_record.gate_decision === 'ALLOW' ? 'text-emerald-400 bg-emerald-950/20' : response.ledger_record.gate_decision === 'BLOCK' ? 'text-rose-400 bg-rose-950/20' : 'text-amber-400 bg-amber-950/20'
                      }`}>
                        {response.ledger_record.gate_decision}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          )}
        </section>

      </main>

      {/* Section Bottom: Ledger History Table */}
      <footer className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8 mt-6">
        <div className="glass-panel rounded-xl p-6 shadow-xl">
          <div className="flex justify-between items-center border-b border-slate-800 pb-4 mb-4">
            <h3 className="text-md font-semibold flex items-center gap-2 text-slate-200">
              <History className="w-5 h-5 text-indigo-400" /> Cryptographic Audit Ledger Trail
            </h3>
            {ledgerHistory.length > 0 && (
              <button 
                onClick={clearLedger}
                className="text-xs text-rose-400 hover:text-rose-300 font-medium flex items-center gap-1.5 py-1 px-3 bg-rose-500/10 hover:bg-rose-500/20 rounded border border-rose-500/10 transition"
              >
                <Trash2 className="w-3.5 h-3.5" /> Clear Audit Ledger History
              </button>
            )}
          </div>

          {ledgerHistory.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-400">
              No audit ledger transactions recorded yet. Run the pipeline to populate the ledger.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-slate-800 bg-[#06080d]/60">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-[#0c1221] text-slate-400 border-b border-slate-800 font-bold uppercase tracking-wider text-[10px]">
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Rule Applied</th>
                    <th className="py-3 px-4">Patch Runs Hashed</th>
                    <th className="py-3 px-4">Gate Decision</th>
                    <th className="py-3 px-4">Ledger Transaction Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {ledgerHistory.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/10 transition">
                      <td className="py-3.5 px-4 font-mono text-[10px] text-slate-400">
                        {new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}{' '}
                        <span className="text-[8px] text-slate-600 block">
                          {new Date(item.timestamp).toLocaleDateString()}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        {item.rule_id ? (
                          <div className="flex flex-col gap-1">
                            <span className="font-semibold text-slate-200">{item.rule_id.split('rule_')[1].toUpperCase().replace('_', ' ')}</span>
                            <span className="text-[9px] font-mono text-slate-500 bg-slate-900 py-0.2 px-1 rounded border border-slate-800 inline-block w-fit">
                              {item.template_id}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-500 font-mono text-[10px]">No Matching Rule (Bypass)</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        {item.patch_run_1_hash ? (
                          <div className="flex flex-col gap-1 text-[10px] font-mono">
                            <span className="text-slate-400">Run 1: {item.patch_run_1_hash.substring(0, 8)}...</span>
                            <span className={item.gate_decision === 'BLOCK' ? 'text-rose-400 font-bold' : 'text-slate-400'}>
                              Run 2: {item.patch_run_2_hash?.substring(0, 8)}...
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-500 font-mono text-[10px]">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-black tracking-wider inline-block ${
                          item.gate_decision === 'ALLOW'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : item.gate_decision === 'BLOCK'
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}>
                          {item.gate_decision}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[10px] max-w-[200px] truncate select-all text-slate-400 hover:text-blue-400 transition" title={item.ledger_hash}>
                        {item.ledger_hash}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </footer>
    </div>
  );
}
