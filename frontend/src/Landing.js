import React, { useEffect, useState } from 'react';

const Landing = ({ onLaunch }) => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-[#060608] text-[#e0e0e0] font-sans selection:bg-red-500/30 selection:text-white overflow-x-hidden">
      
      {/* Global CSS for custom animations (marquee, slow spin) */}
      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0%); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee {
          display: flex;
          width: 200%;
          animation: marquee 20s linear infinite;
        }
        .hover-pause:hover {
          animation-play-state: paused;
        }
        .bento-card {
          background: rgba(31, 33, 40, 0.4);
          border: 1px solid rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-radius: 24px;
          transition: transform 0.3s ease, background 0.3s ease, border-color 0.3s ease;
        }
        .bento-card:hover {
          background: rgba(31, 33, 40, 0.8);
          border-color: rgba(255, 255, 255, 0.1);
          transform: translateY(-5px);
        }
        .glass-nav {
          background: rgba(6, 6, 8, 0.7);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .glow-text {
          text-shadow: 0 0 30px rgba(239, 68, 68, 0.5);
        }
      `}</style>

      {/* Ambient Backgrounds */}
      <div className="fixed top-[-20%] left-[-10%] w-[50vw] h-[50vw] bg-red-600/10 blur-[120px] rounded-full pointer-events-none z-0" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[40vw] h-[40vw] bg-orange-600/5 blur-[120px] rounded-full pointer-events-none z-0" />
      <div className="fixed top-[40%] left-[30%] w-[30vw] h-[30vw] bg-blue-600/5 blur-[120px] rounded-full pointer-events-none z-0" />

      {/* Navigation */}
      <nav className={`fixed top-0 left-0 w-full z-50 transition-all duration-300 ${scrolled ? 'glass-nav py-4' : 'bg-transparent py-6'}`}>
        <div className="max-w-[1400px] mx-auto px-6 md:px-12 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-600 to-red-900 flex items-center justify-center shadow-[0_0_15px_rgba(220,38,38,0.4)]">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">
              Aadhaar <span className="text-red-500">DRISHTI</span>
            </span>
          </div>
          
          <div className="hidden md:flex items-center gap-10 text-sm font-medium text-gray-400">
            <a href="#vision" className="hover:text-white transition-colors">Vision</a>
            <a href="#intelligence" className="hover:text-white transition-colors">Intelligence</a>
            <a href="#infrastructure" className="hover:text-white transition-colors">Infrastructure</a>
          </div>

          <button 
            onClick={onLaunch}
            className="px-6 py-2.5 rounded-full bg-white text-black font-semibold text-sm hover:bg-gray-200 hover:scale-105 transition-all duration-300 flex items-center gap-2"
          >
            Access Terminal
            <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          </button>
        </div>
      </nav>

      {/* ──────────────── HERO SECTION ──────────────── */}
      <section className="relative z-10 pt-[20vh] pb-[10vh] px-6 md:px-12 max-w-[1400px] mx-auto flex flex-col items-center justify-center text-center min-h-screen">

        
        <h1 className="text-[12vw] md:text-[7vw] font-black tracking-tighter text-white mb-6 leading-[0.9] uppercase overflow-hidden">
          Identity <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 via-orange-500 to-red-700 glow-text">
            Intelligence
          </span>
        </h1>
        
        <p className="text-lg md:text-2xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed font-light">
          Scale your demographic analysis. Instantly unearth <strong className="text-white font-medium">infiltration</strong>, <strong className="text-white font-medium">identity laundering</strong>, and <strong className="text-white font-medium">synthetic personas</strong> across 1.4 billion records.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center gap-6 w-full sm:w-auto">
          <button 
            onClick={onLaunch}
            className="px-10 py-5 rounded-full bg-red-600 hover:bg-red-500 text-white font-bold text-lg shadow-[0_0_30px_rgba(220,38,38,0.3)] hover:shadow-[0_0_50px_rgba(220,38,38,0.5)] hover:-translate-y-1 transition-all duration-300 flex items-center gap-3 w-full sm:w-auto justify-center group"
          >
            Initialize Environment
            <svg className="w-5 h-5 flex-shrink-0 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
          </button>
        </div>

        {/* Scroll indicator down */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-500 tracking-widest text-xs uppercase animate-bounce">
          <span>Discover</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>
        </div>
      </section>

      {/* ──────────────── TICKER SECTION ──────────────── */}
      <div className="w-full border-y border-white/5 bg-white/[0.02] py-6 relative z-10 overflow-hidden flex whitespace-nowrap">
        <div className="animate-marquee hover-pause flex items-center text-4xl font-bold tracking-tighter text-gray-700 uppercase">
          <span className="mx-8">Analyzing Demographics</span>
          <span className="mx-8 text-red-900">•</span>
          <span className="mx-8">Detecting Proxies</span>
          <span className="mx-8 text-red-900">•</span>
          <span className="mx-8 text-white">99.9% Precision</span>
          <span className="mx-8 text-red-900">•</span>
          <span className="mx-8">Mapping Subversion</span>
          <span className="mx-8 text-red-900">•</span>
          <span className="mx-8 text-white">1.4 Billion Nodes</span>
          <span className="mx-8 text-red-900">•</span>
          <span className="mx-8">Analyzing Demographics</span>
          <span className="mx-8 text-red-900">•</span>
          <span className="mx-8">Detecting Proxies</span>
          <span className="mx-8 text-red-900">•</span>
          <span className="mx-8 text-white">99.9% Precision</span>
          <span className="mx-8 text-red-900">•</span>
          <span className="mx-8">Mapping Subversion</span>
          <span className="mx-8 text-red-900">•</span>
          <span className="mx-8 text-white">1.4 Billion Nodes</span>
          <span className="mx-8 text-red-900">•</span>
        </div>
      </div>

      {/* ──────────────── BENTO GRID FEATURES ──────────────── */}
      <section id="intelligence" className="relative z-10 py-32 px-6 md:px-12 max-w-[1400px] mx-auto">
        <div className="mb-20">
          <h2 className="text-4xl md:text-6xl font-black tracking-tight text-white mb-6 uppercase">
            Threat <br className="md:hidden"/> Topology
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl leading-relaxed">
            A tripartite shield engineered to expose anomalies hiding in plain sight. Uncover the invisible networks of demographic manipulation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-[400px]">
          
          {/* Card 1: Migration Radar (Large) */}
          <div className="bento-card md:col-span-2 p-10 flex flex-col justify-between group overflow-hidden relative">
            {/* Visual element */}
            <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-bl from-orange-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="absolute -right-20 -top-20 w-80 h-80 border-[1px] border-white/5 rounded-full opacity-50 block group-hover:scale-110 transition-transform duration-700" />
            <div className="absolute -right-10 -top-10 w-60 h-60 border-[1px] border-orange-500/20 rounded-full opacity-50 block group-hover:scale-105 transition-transform duration-700" />
            
            <div className="relative z-10">
              <div className="w-14 h-14 rounded-2xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center mb-6">
                <svg className="w-7 h-7 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              </div>
              <h3 className="text-3xl font-bold text-white mb-3 tracking-tight">Migration Radar</h3>
              <p className="text-gray-400 max-w-md text-lg leading-relaxed">
                Tracks unnatural spikes in adult enrolments in border districts. Identifies potential infiltration routes via spatial velocity modeling.
              </p>
            </div>
            <div className="relative z-10 self-start inline-flex items-center gap-2 text-orange-400 font-semibold tracking-wider text-sm hover:text-orange-300 cursor-pointer transition-colors mt-auto">
              Explore Module <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
            </div>
          </div>

          {/* Card 2: Laundering Detector */}
          <div className="bento-card p-10 flex flex-col justify-between group overflow-hidden relative">
            <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-bl from-yellow-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative z-10">
              <div className="w-14 h-14 rounded-2xl bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center mb-6">
                <svg className="w-7 h-7 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              </div>
              <h3 className="text-2xl font-bold text-white mb-3 tracking-tight">Laundering Net</h3>
              <p className="text-gray-400 text-md leading-relaxed">
                Flags districts where biometric updates vastly outpace demographic changes, revealing identity washing.
              </p>
            </div>
            <div className="relative z-10 w-full h-1 bg-white/5 rounded-full mt-8 overflow-hidden">
              <div className="w-3/4 h-full bg-yellow-500 rounded-full group-hover:origin-left group-hover:scale-x-110 transition-transform" />
            </div>
          </div>

          {/* Card 3: Ghost Scanner */}
          <div className="bento-card p-10 flex flex-col justify-between group overflow-hidden relative">
            <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-bl from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative z-10">
              <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-6">
                <svg className="w-7 h-7 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" /></svg>
              </div>
              <h3 className="text-2xl font-bold text-white mb-3 tracking-tight">Ghost Scanner</h3>
              <p className="text-gray-400 text-md leading-relaxed">
                Detects severe demographic imbalance—such as missing children—indicating potentially synthetic or manufactured datasets.
              </p>
            </div>
            <div className="relative z-10 w-full rounded-lg border border-white/5 bg-white/5 p-4 mt-8 flex items-center justify-between">
              <span className="text-xs text-gray-500 uppercase tracking-wider">Anomalies</span>
              <span className="text-white font-bold font-mono">24,105</span>
            </div>
          </div>

          {/* Card 4: Action/Stat (Wide) */}
          <div className="bento-card md:col-span-2 p-10 flex flex-col md:flex-row items-center justify-between group overflow-hidden relative bg-[#ef4444]/5 hover:bg-[#ef4444]/10 border-red-500/20">
            <div className="relative z-10 mb-8 md:mb-0">
              <h3 className="text-3xl font-bold text-white mb-2">Automated Dossiers</h3>
              <p className="text-red-200/60 max-w-sm">
                Generate executive-ready PDF reports with full geospatial context and evidence logs in one click.
              </p>
            </div>
            <button 
              onClick={onLaunch}
              className="relative z-10 w-full md:w-auto px-8 py-4 rounded-xl bg-white text-black font-bold hover:scale-105 transition-transform duration-300"
            >
              Start Analysis &rarr;
            </button>
          </div>

        </div>
      </section>

      {/* ──────────────── HOW IT WORKS ──────────────── */}
      <section id="infrastructure" className="relative z-10 py-32 px-6 md:px-12 max-w-[1400px] mx-auto border-t border-white/5">
        <div className="flex flex-col md:flex-row justify-between items-start gap-12">
          <div className="md:sticky md:top-40 md:w-1/3">
            <h2 className="text-5xl md:text-6xl font-black tracking-tight text-white mb-6 uppercase">
              Pipeline <br/> Protocol
            </h2>
            <p className="text-xl text-gray-400 leading-relaxed">
              We process millions of rows of encrypted dataset fragments in milliseconds, fusing them into a singular threat narrative.
            </p>
          </div>

          <div className="md:w-1/2 space-y-20">
            {/* Step 1 */}
            <div className="group">
              <div className="text-7xl font-black text-white/5 group-hover:text-red-500/20 transition-colors mb-4 block leading-none">01</div>
              <h3 className="text-2xl font-bold text-white mb-4">Ingest & Sanitize</h3>
              <p className="text-gray-400 text-lg leading-relaxed">
                Drop your Enrolment, Biometric, and Demographic CSVs securely into the ingestion portal. Local-first parsing ensures no sensitive data leaks during the formatting phase.
              </p>
            </div>

            {/* Step 2 */}
            <div className="group">
              <div className="text-7xl font-black text-white/5 group-hover:text-red-500/20 transition-colors mb-4 block leading-none">02</div>
              <h3 className="text-2xl font-bold text-white mb-4">Algorithmic Fusion</h3>
              <p className="text-gray-400 text-lg leading-relaxed">
                Data streams are normalized and assessed against baseline state metrics. The tripartite shield (Migration, Laundering, Ghost) executes concurrently across all districts.
              </p>
            </div>

            {/* Step 3 */}
            <div className="group">
              <div className="text-7xl font-black text-white/5 group-hover:text-red-500/20 transition-colors mb-4 block leading-none">03</div>
              <h3 className="text-2xl font-bold text-white mb-4">Geospatial Triage</h3>
              <p className="text-gray-400 text-lg leading-relaxed">
                Red flags are instantly projected onto the national heatmap. High-risk zones illuminate immediately, guiding investigative resources to the critical nodes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ──────────────── FOOTER CALL TO ACTION ──────────────── */}
      <section className="relative z-10 py-32 px-6 border-t border-white/5 bg-gradient-to-b from-transparent to-[#0a0000]">
        <div className="max-w-[1000px] mx-auto text-center flex flex-col items-center">
          <h2 className="text-5xl md:text-[6vw] font-black tracking-tighter text-white mb-8 leading-[0.9] uppercase">
            Deploy the <br className="hidden md:block" /> System Now
          </h2>
          <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto">
            Access restricted environment. Ensure you have the authorized datasets ready for ingestion.
          </p>
          <button 
            onClick={onLaunch}
            className="px-12 py-6 rounded-full bg-white text-black font-black text-xl hover:scale-105 hover:bg-red-500 hover:text-white hover:shadow-[0_0_50px_rgba(239,68,68,0.5)] transition-all duration-300 flex items-center gap-4 group"
          >
            Launch DRISHTI Console
            <svg className="w-6 h-6 group-hover:translate-x-2 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
          </button>
        </div>
      </section>

      {/* ──────────────── FOOTER BOTTOM ──────────────── */}
      <footer className="relative z-10 py-8 px-6 md:px-12 border-t border-white/5 flex flex-col md:flex-row items-center justify-between text-xs font-semibold tracking-wider uppercase text-gray-500 max-w-[1400px] mx-auto">
        <div>&copy; 2026 Aadhaar DRISHTI. All rights reserved.</div>
        <div className="flex gap-6 mt-4 md:mt-0">
          <a href="/" className="hover:text-white transition-colors">Documentation</a>
          <a href="/" className="hover:text-white transition-colors">System Protocol</a>
          <a href="/" className="hover:text-white transition-colors">Security</a>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
