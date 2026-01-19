import React, { useState, useCallback, useMemo } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, Cell, 
  AreaChart, Area, PieChart, Pie 
} from 'recharts';
import { SVGMap } from "react-svg-map";
import India from "@svg-maps/india";
import { Tooltip as ReactTooltip } from 'react-tooltip';

const API_BASE_URL = 'http://localhost:8000';

// Helper: Normalize state names
const normalizeStateName = (name) => {
  if (!name) return "";
  return name.toLowerCase().replace(/[^a-z0-9]/g, '').replace("state", "").trim();
};

const Dashboard = () => {
  const [files, setFiles] = useState([]);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloadingPDF, setDownloadingPDF] = useState(false);
  const [warnings, setWarnings] = useState([]);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'details'
  const [tooltipContent, setTooltipContent] = useState("");

  // File Upload
  const onDrop = useCallback((acceptedFiles) => {
    setFiles(prev => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: true
  });

  const handleAnalyze = async () => {
    if (files.length === 0) return;
    setLoading(true);
    setWarnings([]);
    try {
      const formData = new FormData();
      files.forEach((file) => formData.append('files', file));
      const response = await axios.post(`${API_BASE_URL}/analyze_trishield`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (response.data.success) {
        setAnalysisResults(response.data.data);
        setWarnings(response.data.warnings || []);
      }
    } catch (err) {
      console.error(err);
      alert("Analysis failed. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async (mode = 'simple') => {
    if (!analysisResults) return;
    setDownloadingPDF(true);
    try {
      const endpoint = mode === 'detailed' ? '/generate_report_detailed' : '/generate_report';
      const response = await axios.post(`${API_BASE_URL}${endpoint}`, analysisResults, {
        responseType: 'blob', headers: { 'Content-Type': 'application/json' }
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `DRISHTI_Report_${mode}_${Date.now()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
    } finally {
      setDownloadingPDF(false);
    }
  };

  const handleReset = () => {
    setFiles([]);
    setAnalysisResults(null);
    setWarnings([]);
  };

  // --- Data Prep for Widgets ---
  const chartData = useMemo(() => {
    if (!analysisResults) return [];
    const all = [
      ...analysisResults.shield1_results.map(r => ({ ...r, type: 'Infiltration' })),
      ...analysisResults.shield2_results.map(r => ({ ...r, type: 'Laundering' })),
      ...analysisResults.shield3_results.map(r => ({ ...r, type: 'Ghost Children' }))
    ];
    const map = {};
    all.forEach(t => map[t.district] = (map[t.district] || 0) + 1);
    return Object.entries(map)
      .map(([d, c]) => ({ district: d, threats: c }))
      .sort((a, b) => b.threats - a.threats)
      .slice(0, 5);
  }, [analysisResults]);

  const mapRiskData = useMemo(() => {
    if (!analysisResults) return {};
    const risks = {};
    const process = (list, type) => {
      list.forEach(item => {
        const key = normalizeStateName(item.state || item.State);
        if (!key) return;
        if (!risks[key]) risks[key] = { level: 0, types: [], count: 0 };
        risks[key].count += 1;
        risks[key].level = item.risk_level === 'CRITICAL' ? 2 : Math.max(risks[key].level, 1);
        if (!risks[key].types.includes(type)) risks[key].types.push(type);
      });
    };
    process(analysisResults.shield1_results, 'Infiltration');
    process(analysisResults.shield2_results, 'Laundering');
    process(analysisResults.shield3_results, 'Ghost Children');
    return risks;
  }, [analysisResults]);

  // --- Components ---

  const StatCard = ({ title, value, subtext, color, icon }) => (
    <div className="dashboard-card group">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="dashboard-card-title">{title}</h3>
          <p className="dashboard-value">{value}</p>
          <p className="text-xs text-gray-500 mt-1">{subtext}</p>
        </div>
        <div className={`p-2 rounded-lg bg-${color}-500/10 text-${color}-500 group-hover:bg-${color}-500/20 transition-colors`}>
          {icon}
        </div>
      </div>
      {/* Tiny Sparkline Decoration */}
      <div className="mt-4 h-1 w-full bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full bg-${color}-500 w-[70%] rounded-full opacity-80`}></div>
      </div>
    </div>
  );

  // If no results yet, show the "Upload Mode" dashboard
  if (!analysisResults) {
    return (
      <div className="flex h-screen bg-[#0b0c10] text-white font-sans overflow-hidden">
        <Sidebar active="upload" />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <TopBar title="Data Ingestion" />
          <main className="flex-1 overflow-y-auto p-6">
            <div className="max-w-4xl mx-auto h-full flex flex-col justify-center">
              <div className="text-center mb-10">
                <h1 className="text-4xl font-bold mb-2">Aadhaar <span className="text-red-600">DRISHTI</span></h1>
                <p className="text-gray-400">Secure Government Data Analysis System</p>
              </div>
              
              <div {...getRootProps()} 
                className={`border-2 border-dashed rounded-xl h-64 flex flex-col items-center justify-center cursor-pointer transition-all
                  ${isDragActive ? 'border-red-500 bg-red-500/10' : 'border-gray-700 bg-[#1f2128] hover:border-gray-500'}
                `}>
                <input {...getInputProps()} />
                <svg className="w-12 h-12 text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                <p className="text-lg font-medium text-gray-300">Drop datasets here</p>
                <p className="text-sm text-gray-500 mt-2">Enrolment, Demographic, Biometric CSVs</p>
              </div>

              {files.length > 0 && (
                <div className="mt-6 bg-[#1f2128] rounded-xl p-4 border border-gray-800">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase">Staged Files ({files.length})</h3>
                    <button onClick={() => setFiles([])} className="text-xs text-red-400 hover:text-red-300">Clear All</button>
                  </div>
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-2 custom-scrollbar">
                    {files.map((f, i) => (
                      <div key={i} className="flex justify-between items-center p-2 bg-[#0b0c10] rounded border border-gray-800 text-sm">
                        <span className="truncate">{f.name}</span>
                        <span className="text-gray-500 text-xs">{(f.size/1024).toFixed(1)} KB</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-6">
                    <button 
                      onClick={handleAnalyze} 
                      disabled={loading}
                      className="w-full btn-primary h-12 text-lg shadow-lg shadow-red-900/20"
                    >
                      {loading ? (
                        <span className="flex items-center"><svg className="animate-spin h-5 w-5 mr-3 text-white" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg> Processing...</span>
                      ) : "Analyze Data"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    );
  }

  // --- Main Dashboard View ---
  return (
    <div className="flex h-screen bg-[#0b0c10] text-white font-sans overflow-hidden">
      <Sidebar active="dashboard" />
      
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar title="Mission Control" onReset={handleReset} />
        
        <main className="flex-1 overflow-y-auto p-6 custom-scrollbar">
          {/* Row 1: KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <StatCard 
              title="Total Threats" 
              value={analysisResults.summary.total_threats} 
              subtext="Across all shields" 
              color="red"
              icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
            />
            <StatCard 
              title="Infiltration" 
              value={analysisResults.summary.infiltration_cases} 
              subtext="Shield 1 Alerts" 
              color="orange"
              icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
            />
            <StatCard 
              title="Laundering" 
              value={analysisResults.summary.laundering_cases} 
              subtext="Shield 2 Alerts" 
              color="yellow"
              icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
            />
            <StatCard 
              title="Anomalies" 
              value={analysisResults.summary.anomaly_cases || 0} 
              subtext="ML Detected" 
              color="blue"
              icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>}
            />
          </div>

          {/* Row 2: Map & Analytics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Map Widget */}
            <div className="lg:col-span-2 dashboard-card h-[400px] flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h3 className="dashboard-card-title">Geospatial Risk Analysis</h3>
                <div className="flex space-x-2 text-[10px]">
                  <span className="flex items-center"><span className="w-2 h-2 rounded-full bg-red-500 mr-1"></span>Critical</span>
                  <span className="flex items-center"><span className="w-2 h-2 rounded-full bg-orange-500 mr-1"></span>High</span>
                </div>
              </div>
              <div className="flex-1 w-full h-full relative">
                <SVGMap
                  map={India}
                  className="w-full h-full"
                  locationClassName={(location) => {
                    const nm = normalizeStateName(location.name);
                    const risk = mapRiskData[nm];
                    if (!risk) return "map-state map-state-low"; // CSS class
                    if (risk.level === 2) return "map-state map-state-critical";
                    return "map-state map-state-high";
                  }}
                  onLocationMouseOver={(e) => {
                    const name = e.target.getAttribute("name");
                    const nm = normalizeStateName(name);
                    const risk = mapRiskData[nm];
                    setTooltipContent(risk ? `${name}: ${risk.count} Threats` : name);
                  }}
                  onLocationMouseOut={() => setTooltipContent("")}
                />
                {tooltipContent && (
                  <div className="absolute bottom-4 right-4 bg-gray-900/90 border border-gray-700 px-3 py-1 rounded text-xs text-white shadow-xl backdrop-blur-sm pointer-events-none">
                    {tooltipContent}
                  </div>
                )}
              </div>
            </div>

            {/* Top Districts Chart */}
            <div className="dashboard-card flex flex-col">
              <h3 className="dashboard-card-title">Top 5 High-Risk Districts</h3>
              <div className="flex-1 min-h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical" margin={{top: 0, right: 30, left: 40, bottom: 0}}>
                    <XAxis type="number" hide />
                    <YAxis dataKey="district" type="category" width={80} tick={{fill: '#9ca3af', fontSize: 10}} axisLine={false} tickLine={false} />
                    <RechartsTooltip contentStyle={{backgroundColor: '#1f2128', borderColor: '#374151', fontSize: '12px'}} cursor={{fill: 'transparent'}} />
                    <Bar dataKey="threats" fill="#ef4444" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Row 3: Action & Lists */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Recent Alerts List */}
            <div className="lg:col-span-2 dashboard-card h-[350px] overflow-hidden flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h3 className="dashboard-card-title">Live Threat Feed</h3>
                <span className="text-xs text-gray-500">Real-time Analysis</span>
              </div>
              <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
                <table className="w-full text-left border-collapse">
                  <thead className="sticky top-0 bg-[#1f2128] text-xs text-gray-500 uppercase">
                    <tr>
                      <th className="py-2">District</th>
                      <th className="py-2">Type</th>
                      <th className="py-2 text-right">Vol</th>
                      <th className="py-2 text-right">Risk</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y divide-gray-800">
                    {[
                      ...analysisResults.shield1_results.map(r => ({...r, type: 'Infiltration'})),
                      ...analysisResults.shield2_results.map(r => ({...r, type: 'Laundering'})),
                      ...analysisResults.shield3_results.map(r => ({...r, type: 'Ghost Child'}))
                    ].slice(0, 50).map((row, i) => (
                      <tr key={i} className="hover:bg-white/5 transition-colors">
                        <td className="py-2 font-medium text-gray-300">{row.district}</td>
                        <td className="py-2 text-gray-400">{row.type}</td>
                        <td className="py-2 text-right text-gray-400 font-mono">
                          {row.total_volume || row.child_volume || row.demographic_volume}
                        </td>
                        <td className="py-2 text-right">
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${row.risk_level === 'CRITICAL' ? 'bg-red-500/20 text-red-500' : 'bg-orange-500/20 text-orange-500'}`}>
                            {row.risk_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Reports & Actions */}
            <div className="dashboard-card flex flex-col justify-between">
              <div>
                <h3 className="dashboard-card-title">Export Intelligence</h3>
                <p className="text-sm text-gray-400 mb-6">Generate official government-grade dossiers.</p>
                
                <div className="space-y-3">
                  <button 
                    onClick={() => handleDownloadReport('simple')}
                    disabled={downloadingPDF}
                    className="w-full btn-secondary text-sm justify-between group"
                  >
                    <span>Summary Report</span>
                    <svg className="w-4 h-4 text-gray-400 group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                  </button>
                  <button 
                    onClick={() => handleDownloadReport('detailed')}
                    disabled={downloadingPDF}
                    className="w-full btn-secondary text-sm justify-between group"
                  >
                    <span>Detailed Forensic Report</span>
                    <svg className="w-4 h-4 text-gray-400 group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                  </button>
                </div>
              </div>

              {warnings.length > 0 && (
                <div className="mt-6 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded text-xs text-yellow-500">
                  <strong>System Notes:</strong>
                  <ul className="list-disc list-inside mt-1">
                    {warnings.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

// --- Static Sidebar ---
const Sidebar = ({ active }) => (
  <div className="w-16 md:w-20 bg-[#1f2128] border-r border-gray-800 flex flex-col items-center py-6 z-20">
    <div className="w-10 h-10 bg-red-600 rounded-lg flex items-center justify-center mb-8 shadow-lg shadow-red-500/30">
      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
    </div>
    
    <nav className="flex-1 space-y-6 w-full flex flex-col items-center">
      <NavItem icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>} active={active === 'dashboard'} />
      <NavItem icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>} active={false} />
      <NavItem icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" /></svg>} active={active === 'upload'} />
    </nav>

    <div className="mb-4">
      <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-300">SP</div>
    </div>
  </div>
);

const NavItem = ({ icon, active }) => (
  <div className={`p-3 rounded-xl transition-all cursor-pointer ${active ? 'bg-gray-800 text-white shadow-inner' : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/50'}`}>
    {icon}
  </div>
);

// --- Top Bar ---
const TopBar = ({ title, onReset }) => (
  <header className="h-16 border-b border-gray-800 flex items-center justify-between px-6 bg-[#0b0c10]/50 backdrop-blur sticky top-0 z-10">
    <div className="flex items-center">
      <h2 className="text-lg font-semibold text-gray-200">{title}</h2>
    </div>
    <div className="flex items-center space-x-4">
      {onReset && (
        <button onClick={onReset} className="text-sm text-gray-400 hover:text-white flex items-center transition-colors">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          New Analysis
        </button>
      )}
      <div className="h-4 w-px bg-gray-700 mx-2"></div>
      <div className="flex items-center text-xs text-green-500">
        <span className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
        System Online
      </div>
    </div>
  </header>
);

export default Dashboard;
