import React, { useState, useCallback, useMemo } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend as RechartsLegend,
} from 'recharts';
import { SVGMap } from "react-svg-map";
import India from "@svg-maps/india";

// Resolved at build time by Create React App. In local dev this is
// unset and falls back to `http://localhost:8000`. On Vercel set it to
// the backend service's routePrefix (e.g. `/_/backend`) so requests go
// through the same domain — no CORS, no mixed content.
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const ZONE_LABELS = { 3: 'CRITICAL', 2: 'HIGH', 1: 'MODERATE', 0: 'SAFE' };
const ZONE_BADGE = {
  3: 'bg-red-500/20 text-red-400 border border-red-500/30',
  2: 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
  1: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
};

const normalizeStateName = (name) => {
  if (!name) return "";
  return name.toLowerCase().replace(/[^a-z0-9]/g, '').replace("state", "").trim();
};

const classifyFile = (file) => {
  const n = file.name.toLowerCase();
  if (n.includes('enrol')) return 'enrol';
  if (n.includes('bio'))   return 'bio';
  if (n.includes('demo'))  return 'demo';
  return null;
};

const Dashboard = () => {
  const [files, setFiles] = useState([]);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [warnings, setWarnings] = useState([]);
  const [tooltipContent, setTooltipContent] = useState("");
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    setFiles(prev => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: true
  });

  const classified = useMemo(() => {
    const result = { enrol: null, bio: null, demo: null };
    files.forEach(f => {
      const type = classifyFile(f);
      if (type && !result[type]) result[type] = f;
    });
    return result;
  }, [files]);

  const allThreePresent = classified.enrol && classified.bio && classified.demo;

  const handleAnalyze = async () => {
    if (!allThreePresent) return;
    setLoading(true);
    setWarnings([]);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('enrol_file', classified.enrol);
      formData.append('bio_file', classified.bio);
      formData.append('demo_file', classified.demo);

      const response = await axios.post(`${API_BASE_URL}/api/v1/ingest`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const { summary, red_flags } = response.data;

      const shield1 = red_flags
        .filter(f => f.modules_triggered.includes('migration_radar'))
        .map(f => ({
          district: f.district,
          state: f.state,
          total_volume: f.total_enrollments,
          adult_ratio: f.enrollment_velocity,
          risk_level: f.severity === 'HIGH' ? 'CRITICAL' : 'HIGH',
          threat_type: 'Infiltration',
          anomaly_score: f.anomaly_score,
        }));

      const shield2 = red_flags
        .filter(f => f.modules_triggered.includes('laundering_detector'))
        .map(f => ({
          district: f.district,
          state: f.state,
          demographic_volume: f.demo_age_5_17 + f.demo_age_17_,
          biometric_volume: f.bio_age_5_17 + f.bio_age_17_,
          laundering_ratio: f.bio_demo_ratio_17_,
          risk_level: f.severity === 'HIGH' ? 'CRITICAL' : 'HIGH',
          threat_type: 'Identity Laundering',
          anomaly_score: f.anomaly_score,
        }));

      const shield3 = red_flags
        .filter(f => f.modules_triggered.includes('ghost_scanner'))
        .map(f => ({
          district: f.district,
          state: f.state,
          child_volume: f.age_0_5 + f.age_5_17,
          adult_volume: f.age_18_greater,
          ghost_child_ratio: f.ghost_child_ratio,
          risk_level: f.severity === 'HIGH' ? 'CRITICAL' : 'HIGH',
          threat_type: 'Ghost Children Fraud',
          anomaly_score: f.anomaly_score,
        }));

      setAnalysisResults({
        shield1_results: shield1,
        shield2_results: shield2,
        shield3_results: shield3,
        raw_flags: red_flags,
        summary: {
          total_threats: summary.flagged_count,
          infiltration_cases: summary.module_breakdown.migration_radar,
          laundering_cases: summary.module_breakdown.laundering_detector,
          ghost_children_cases: summary.module_breakdown.ghost_scanner,
          unclassified_cases: summary.module_breakdown.isolation_forest_only || 0,
          multi_module_cases: summary.module_breakdown.multi_module || 0,
          anomaly_cases: summary.flagged_count,
          total_records: summary.total_records,
          processing_time_ms: summary.processing_time_ms,
        },
      });

      const w = [];
      if (shield1.length === 0) w.push("No infiltration patterns detected by Migration Radar.");
      if (shield2.length === 0) w.push("No laundering patterns detected.");
      if (shield3.length === 0) w.push("No ghost children patterns detected.");
      setWarnings(w);
    } catch (err) {
      console.error(err);
      const detail = err.response?.data?.detail || err.message;
      setError(`Analysis failed: ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async (flag) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/reports/generate`,
        flag,
        { responseType: 'blob', headers: { 'Content-Type': 'application/json' } }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `drishti_report_${flag.district || 'flag'}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
      alert("Report generation failed.");
    }
  };

  const handleDownloadTopReport = async () => {
    if (!analysisResults?.raw_flags?.length) return;
    const top = analysisResults.raw_flags[0];
    await handleDownloadReport(top);
  };

  const handleReset = () => {
    setFiles([]);
    setAnalysisResults(null);
    setWarnings([]);
    setError(null);
  };

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

  // Module-breakdown pie data — shows how the total flagged pool
  // distributes across the four categories (the "what about the
  // remaining N?" answer in chart form).
  const moduleBreakdownData = useMemo(() => {
    if (!analysisResults) return [];
    const s = analysisResults.summary;
    return [
      { name: 'Ghost Children', value: s.ghost_children_cases, color: '#3b82f6' },
      { name: 'Laundering',    value: s.laundering_cases,      color: '#eab308' },
      { name: 'Infiltration',  value: s.infiltration_cases,    color: '#f97316' },
      { name: 'Unclassified',  value: s.unclassified_cases,    color: '#a855f7' },
    ].filter(d => d.value > 0);
  }, [analysisResults]);

  // Severity-distribution pie data — HIGH / MEDIUM / LOW split of all
  // flagged records.
  const severityData = useMemo(() => {
    if (!analysisResults) return [];
    const buckets = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    (analysisResults.raw_flags || []).forEach((f) => {
      if (f.severity && buckets[f.severity] !== undefined) buckets[f.severity] += 1;
    });
    const palette = { HIGH: '#ef4444', MEDIUM: '#f97316', LOW: '#22c55e' };
    return Object.entries(buckets)
      .filter(([, v]) => v > 0)
      .map(([k, v]) => ({ name: k, value: v, color: palette[k] }));
  }, [analysisResults]);

  const renderPieLabel = ({ name, percent }) =>
    `${name} ${(percent * 100).toFixed(0)}%`;

  const mapRiskData = useMemo(() => {
    if (!analysisResults) return {};
    const risks = {};
    const process = (list, type) => {
      list.forEach(item => {
        const key = normalizeStateName(item.state || item.State);
        if (!key) return;
        if (!risks[key]) risks[key] = { level: 0, types: [], count: 0, hasCritical: false, originalName: item.state || item.State };
        risks[key].count += 1;
        if (item.risk_level === 'CRITICAL') risks[key].hasCritical = true;
        if (!risks[key].types.includes(type)) risks[key].types.push(type);
      });
    };
    process(analysisResults.shield1_results, 'Infiltration');
    process(analysisResults.shield2_results, 'Laundering');
    process(analysisResults.shield3_results, 'Ghost Children');

    Object.values(risks).forEach(r => {
      if (r.hasCritical || r.count >= 5) r.level = 3;
      else if (r.count >= 3)             r.level = 2;
      else if (r.count >= 1)             r.level = 1;
    });
    return risks;
  }, [analysisResults]);

  const highlightedStatesList = useMemo(() => {
    if (!mapRiskData || Object.keys(mapRiskData).length === 0) return [];
    return Object.entries(mapRiskData)
      .filter(([, d]) => d.count > 0)
      .map(([key, d]) => ({
        name: d.originalName || key,
        count: d.count,
        level: d.level,
        label: ZONE_LABELS[d.level] || 'SAFE',
        types: d.types.join(', ')
      }))
      .sort((a, b) => b.level - a.level || b.count - a.count);
  }, [mapRiskData]);

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
      <div className="mt-4 h-1 w-full bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full bg-${color}-500 w-[70%] rounded-full opacity-80`}></div>
      </div>
    </div>
  );

  // ── Upload view ──────────────────────────────────────────────────────────
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
                    {files.map((f, i) => {
                      const type = classifyFile(f);
                      const label = type === 'enrol' ? 'Enrolment' : type === 'bio' ? 'Biometric' : type === 'demo' ? 'Demographic' : 'Unknown';
                      const labelColor = type ? 'text-green-400' : 'text-yellow-400';
                      return (
                        <div key={i} className="flex justify-between items-center p-2 bg-[#0b0c10] rounded border border-gray-800 text-sm">
                          <span className="truncate flex-1">{f.name}</span>
                          <span className={`text-xs mx-2 font-medium ${labelColor}`}>{label}</span>
                          <span className="text-gray-500 text-xs">{(f.size/1024).toFixed(1)} KB</span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Classification status */}
                  <div className="mt-4 flex gap-3 text-xs">
                    <span className={classified.enrol ? 'text-green-400' : 'text-gray-600'}>
                      {classified.enrol ? '✓' : '○'} Enrolment
                    </span>
                    <span className={classified.bio ? 'text-green-400' : 'text-gray-600'}>
                      {classified.bio ? '✓' : '○'} Biometric
                    </span>
                    <span className={classified.demo ? 'text-green-400' : 'text-gray-600'}>
                      {classified.demo ? '✓' : '○'} Demographic
                    </span>
                  </div>

                  {!allThreePresent && files.length > 0 && (
                    <p className="mt-2 text-xs text-yellow-500">
                      Upload all 3 file types to enable analysis. Files are identified by name
                      (must contain "enrol", "bio", or "demo").
                    </p>
                  )}

                  {error && (
                    <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400">
                      {error}
                    </div>
                  )}

                  <div className="mt-6">
                    <button
                      onClick={handleAnalyze}
                      disabled={loading || !allThreePresent}
                      className="w-full btn-primary h-12 text-lg shadow-lg shadow-red-900/20 disabled:opacity-40"
                    >
                      {loading ? (
                        <span className="flex items-center justify-center">
                          <svg className="animate-spin h-5 w-5 mr-3 text-white" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
                          Processing...
                        </span>
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

  // ── Results dashboard ────────────────────────────────────────────────────
  return (
    <div className="flex h-screen bg-[#0b0c10] text-white font-sans overflow-hidden">
      <Sidebar active="dashboard" />

      <div className="flex-1 flex flex-col min-w-0">
        <TopBar title="Mission Control" onReset={handleReset} />

        <main className="flex-1 overflow-y-auto p-6 custom-scrollbar">
          {/* Row 1: KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-6">
            <StatCard
              title="Total Threats"
              value={analysisResults.summary.total_threats}
              subtext={`of ${analysisResults.summary.total_records} records`}
              color="red"
              icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
            />
            <StatCard
              title="Infiltration"
              value={analysisResults.summary.infiltration_cases}
              subtext="Migration Radar"
              color="orange"
              icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
            />
            <StatCard
              title="Laundering"
              value={analysisResults.summary.laundering_cases}
              subtext="Laundering Detector"
              color="yellow"
              icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
            />
            <StatCard
              title="Ghost Children"
              value={analysisResults.summary.ghost_children_cases}
              subtext="Ghost Scanner"
              color="blue"
              icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>}
            />
            <StatCard
              title="Unclassified"
              value={analysisResults.summary.unclassified_cases}
              subtext="ML-only anomaly"
              color="purple"
              icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
            />
          </div>

          {/* Row 2: Map & Analytics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-2 dashboard-card flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h3 className="dashboard-card-title">Geospatial Risk Analysis</h3>
                <div className="flex space-x-3 text-[10px]">
                  <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-sm mr-1" style={{background:'#f87171'}}></span>Critical</span>
                  <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-sm mr-1" style={{background:'#fb923c'}}></span>High</span>
                  <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-sm mr-1" style={{background:'#fde047'}}></span>Moderate</span>
                  <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-sm mr-1" style={{background:'#86efac'}}></span>Safe</span>
                </div>
              </div>
              <div className="flex-1 w-full h-[400px] relative rounded-lg overflow-hidden bg-[#0f172a]">
                <SVGMap
                  map={India}
                  className="w-full h-full"
                  locationClassName={(location) => {
                    const nm = normalizeStateName(location.name);
                    const risk = mapRiskData[nm];
                    const base = "svg-map__location";
                    if (!risk || risk.count === 0) return `${base} map-zone-safe`;
                    if (risk.level >= 3) return `${base} map-zone-red`;
                    if (risk.level === 2) return `${base} map-zone-orange`;
                    return `${base} map-zone-yellow`;
                  }}
                  onLocationMouseOver={(e) => {
                    const name = e.target.getAttribute("name");
                    const nm = normalizeStateName(name);
                    const risk = mapRiskData[nm];
                    if (risk && risk.count > 0) {
                      setTooltipContent(`${name}: ${risk.count} threat${risk.count > 1 ? 's' : ''} (${risk.types.join(', ')})`);
                    } else {
                      setTooltipContent(`${name}: Safe`);
                    }
                  }}
                  onLocationMouseOut={() => setTooltipContent("")}
                />
                {tooltipContent && (
                  <div className="absolute bottom-3 right-3 bg-gray-900/95 border border-gray-600 px-3 py-1.5 rounded text-xs text-white shadow-md pointer-events-none z-10 font-medium">
                    {tooltipContent}
                  </div>
                )}
              </div>

              {highlightedStatesList.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-800">
                  <h4 className="text-xs font-semibold text-gray-400 uppercase mb-3">Highlighted States ({highlightedStatesList.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {highlightedStatesList.map((state, idx) => (
                      <div
                        key={idx}
                        className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-2 ${
                          ZONE_BADGE[state.level] || 'bg-green-500/20 text-green-400 border border-green-500/30'
                        }`}
                      >
                        <span className="font-bold">{state.name}</span>
                        <span className="text-gray-500">&bull;</span>
                        <span>{state.count} threat{state.count > 1 ? 's' : ''}</span>
                        <span className="text-gray-500">&bull;</span>
                        <span className="font-bold">{state.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

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

          {/* Row 2.5: Pie charts — category mix & severity mix */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="dashboard-card flex flex-col">
              <div className="flex justify-between items-center mb-2">
                <h3 className="dashboard-card-title">Threat Category Mix</h3>
                <span className="text-xs text-gray-500">
                  {moduleBreakdownData.reduce((s, d) => s + d.value, 0)} flagged
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-2">
                How the flagged records split across the four detection categories.
                <span className="text-purple-400"> Unclassified</span> = flagged by
                the ML model without any single Tri-Shield rule firing.
              </p>
              <div className="flex-1 min-h-[260px]">
                {moduleBreakdownData.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-sm text-gray-600">
                    No threats to chart
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={moduleBreakdownData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={90}
                        paddingAngle={2}
                        label={renderPieLabel}
                        labelLine={false}
                      >
                        {moduleBreakdownData.map((d, i) => (
                          <Cell key={i} fill={d.color} stroke="#0b0c10" strokeWidth={2} />
                        ))}
                      </Pie>
                      <RechartsTooltip
                        contentStyle={{ backgroundColor: '#1f2128', borderColor: '#374151', fontSize: '12px' }}
                        formatter={(v, n) => [`${v} flag${v === 1 ? '' : 's'}`, n]}
                      />
                      <RechartsLegend
                        verticalAlign="bottom"
                        iconType="circle"
                        wrapperStyle={{ fontSize: '11px', color: '#9ca3af' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            <div className="dashboard-card flex flex-col">
              <div className="flex justify-between items-center mb-2">
                <h3 className="dashboard-card-title">Severity Distribution</h3>
                <span className="text-xs text-gray-500">
                  {severityData.reduce((s, d) => s + d.value, 0)} flagged
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-2">
                HIGH = 2+ signals aligned or deeply anomalous ML score.
                MEDIUM = single signal. LOW = marginal outlier.
              </p>
              <div className="flex-1 min-h-[260px]">
                {severityData.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-sm text-gray-600">
                    No threats to chart
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={severityData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={90}
                        paddingAngle={2}
                        label={renderPieLabel}
                        labelLine={false}
                      >
                        {severityData.map((d, i) => (
                          <Cell key={i} fill={d.color} stroke="#0b0c10" strokeWidth={2} />
                        ))}
                      </Pie>
                      <RechartsTooltip
                        contentStyle={{ backgroundColor: '#1f2128', borderColor: '#374151', fontSize: '12px' }}
                        formatter={(v, n) => [`${v} flag${v === 1 ? '' : 's'}`, n]}
                      />
                      <RechartsLegend
                        verticalAlign="bottom"
                        iconType="circle"
                        wrapperStyle={{ fontSize: '11px', color: '#9ca3af' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </div>

          {/* Row 3: Threat Feed & Actions */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 dashboard-card h-[350px] overflow-hidden flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h3 className="dashboard-card-title">Live Threat Feed</h3>
                <span className="text-xs text-gray-500">{analysisResults.summary.total_threats} flags</span>
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
                          {row.total_volume || row.child_volume || row.demographic_volume || '—'}
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

            <div className="dashboard-card flex flex-col justify-between">
              <div>
                <h3 className="dashboard-card-title">Export Intelligence</h3>
                <p className="text-sm text-gray-400 mb-6">Generate official investigation dossiers.</p>

                <div className="space-y-3">
                  <button
                    onClick={handleDownloadTopReport}
                    className="w-full btn-secondary text-sm justify-between group"
                  >
                    <span>Top Flag Report (PDF)</span>
                    <svg className="w-4 h-4 text-gray-400 group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                  </button>
                </div>

                <p className="text-xs text-gray-600 mt-4">
                  Processed {analysisResults.summary.total_records.toLocaleString()} records
                  in {analysisResults.summary.processing_time_ms}ms
                </p>
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
