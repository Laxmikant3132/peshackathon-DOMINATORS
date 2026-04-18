import React, { useEffect, useState } from 'react';
import useXDRStore from '../store/useXDRStore';
import { Terminal, ShieldAlert, Zap, Search, Activity, Cpu, Globe, ArrowRight } from 'lucide-react';

const Monitoring = () => {
  const { events, stats } = useXDRStore();
  const [activeTab, setActiveTab] = useState('all');

  return (
    <div className="animate-fade-in flex flex-col h-full gap-8">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-black tracking-tight uppercase">Live Traffic Monitoring</h2>
          <p className="text-slate-500 font-medium">Synchronized telemetry from 14 operational sensors.</p>
        </div>
        <div className="flex gap-2 bg-white/5 p-1 rounded-lg border border-white/10">
          <button 
            onClick={() => setActiveTab('all')}
            className={`px-4 py-1.5 rounded-md text-[10px] font-bold transition-all ${activeTab === 'all' ? 'bg-info text-white shadow-lg' : 'text-slate-500 hover:text-white'}`}
          >
            GLOBAL STREAM
          </button>
          <button 
            onClick={() => setActiveTab('critical')}
            className={`px-4 py-1.5 rounded-md text-[10px] font-bold transition-all ${activeTab === 'critical' ? 'bg-critical text-white shadow-lg' : 'text-slate-500 hover:text-white'}`}
          >
            CRITICAL ONLY
          </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-8 overflow-hidden min-h-0">
        {/* LEFT PANEL: LIVE LOG STREAM */}
        <div className="glass-card flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-4">
            <div className="flex items-center gap-2">
              <Terminal size={16} className="text-info" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-slate-300">Telemetry Ingestor</h3>
            </div>
            <span className="text-[10px] font-bold text-info animate-pulse">STREAMING_REALTIME</span>
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-2 pr-2">
            {events.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-4">
                <div className="p-4 rounded-full bg-white/5 border border-white/10 animate-pulse">
                  <Activity size={32} />
                </div>
                <p className="text-xs font-bold uppercase tracking-widest">Awaiting Live Signals</p>
              </div>
            ) : (
              events.map((event, idx) => (
                <div 
                  key={event.event_id || idx}
                  className="bg-black/40 border-l-2 border-info p-3 rounded-r-lg group hover:bg-info/5 transition-colors animate-fade-in"
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[10px] font-mono font-bold text-info">{event.timestamp}</span>
                    <span className="text-[9px] font-black uppercase text-slate-500 px-1 border border-slate-500 rounded">{event.event_type}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-mono">
                    <span className={event.priority === 'HIGH' ? 'text-critical font-bold' : 'text-slate-200'}>
                      {event.source_entity}
                    </span>
                    <ArrowRight size={10} className="text-slate-500" />
                    <span className="text-slate-400">{event.target_entity || 'LOCAL_OS'}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* RIGHT PANEL: SUSPICIOUS IP INTELLIGENCE */}
        <div className="glass-card flex flex-col min-h-0 border-info/20 shadow-[0_0_40px_rgba(0,163,255,0.05)]">
          <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-4">
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-warning" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-slate-300">Suspicious Entity Intelligence</h3>
            </div>
            <div className="flex gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-critical animate-ping" />
              <span className="text-[10px] font-black text-critical">{stats.incident_count} ACTIVE THREATS</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-6 pr-2">
            {/* DYNAMIC IP PANELS WOULD INITIALLY BE MOCKED FOR UI DESIGN */}
            {stats.incident_count > 0 ? (
              <div className="space-y-4">
                <div className="p-5 rounded-xl bg-critical/5 border border-critical/20 space-y-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-lg font-black text-critical tracking-tight">192.168.1.5</h4>
                      <p className="text-[10px] font-bold text-slate-500 uppercase">External Source Node</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-black text-critical">RISK: 94/100</p>
                      <p className="text-[8px] font-bold text-slate-500 uppercase tracking-tighter">Class: Brute Force</p>
                    </div>
                  </div>
                  
                  {/* ATTACK PATH GRAPH STUB */}
                  <div className="h-32 bg-black/50 border border-white/5 rounded-lg flex items-center justify-center relative overflow-hidden">
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,75,75,0.1),transparent)]" />
                    <div className="z-10 flex items-center gap-4">
                      <Globe size={20} className="text-slate-500" />
                      <div className="h-px w-12 bg-critical dashed" />
                      <div className="h-8 w-8 rounded-lg bg-info/20 border border-info flex items-center justify-center">
                        <Cpu size={14} className="text-info" />
                      </div>
                      <div className="h-px w-12 bg-warning shadow-[0_0_10px_orange]" />
                      <ShieldAlert size={20} className="text-critical animate-pulse" />
                    </div>
                  </div>

                  <div className="flex justify-between gap-4">
                    <button className="flex-1 bg-critical/20 hover:bg-critical/30 border border-critical/30 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all">Block IP</button>
                    <button className="flex-1 bg-white/5 hover:bg-white/10 border border-white/10 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all">Detailed Path</button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-4">
                <div className="p-4 rounded-full bg-white/5 border border-white/10">
                  <ShieldAlert size={32} />
                </div>
                <p className="text-xs font-bold uppercase tracking-widest">No Active Threat Clusters</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Monitoring;
