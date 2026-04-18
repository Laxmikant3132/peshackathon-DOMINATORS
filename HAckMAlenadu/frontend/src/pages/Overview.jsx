import React from 'react';
import useXDRStore from '../store/useXDRStore';
import { Activity, ShieldAlert, Target, Globe, ArrowUpRight } from 'lucide-react';

const MetricCard = ({ title, value, subtext, icon: Icon, color }) => (
  <div className="glass-card flex flex-col gap-4">
    <div className="flex justify-between items-start">
      <div>
        <p className="text-[10px] font-extrabold text-slate-500 uppercase tracking-widest">{title}</p>
        <p className="text-3xl font-black mt-1 text-[#e6edf3]">{value}</p>
      </div>
      <div className={`p-2 rounded-lg bg-${color}/10 border border-${color}/20`}>
        <Icon className={`text-${color}`} size={20} />
      </div>
    </div>
    <div className="flex items-center gap-1">
      <ArrowUpRight size={14} className="text-safe" />
      <span className="text-[10px] font-bold text-safe uppercase tracking-tighter">{subtext}</span>
    </div>
  </div>
);

const Overview = () => {
  const { stats } = useXDRStore();
  
  return (
    <div className="animate-fade-in space-y-8">
      <div>
        <h2 className="text-3xl font-black tracking-tight">GLOBAL SECURITY OVERVIEW</h2>
        <p className="text-slate-500 font-medium">Real-time enterprise-wide detection and response matrix.</p>
      </div>

      {/* KPI GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          title="Telemetry Pulse" 
          value={stats.processed_count} 
          subtext="+12% VS PREV HOUR" 
          icon={Activity} 
          color="info" 
        />
        <MetricCard 
          title="Active Threats" 
          value={stats.incident_count} 
          subtext="PRIORITY CORRELATION" 
          icon={ShieldAlert} 
          color="critical" 
        />
        <MetricCard 
          title="Reputation Score" 
          value="98.2" 
          subtext="TRUST BASELINE" 
          icon={Target} 
          color="safe" 
        />
        <MetricCard 
          title="Monitored Entities" 
          value="1,420" 
          subtext="LIVE NODES" 
          icon={Globe} 
          color="info" 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* RISK GAUGE */}
        <div className="glass-card lg:col-span-1 flex flex-col justify-between">
          <div>
            <h4 className="font-bold text-sm mb-4">SYSTEM RISK INDICATOR</h4>
            <div className="relative h-48 flex items-center justify-center">
              <div className="absolute inset-0 flex items-center justify-center">
                <p className="text-6xl font-black text-neon-blue">
                  {Math.min(100, stats.incident_count * 35)}
                </p>
                <p className="absolute bottom-10 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Risk Score</p>
              </div>
              {/* Circular placeholder for Gauge */}
              <div className="w-40 h-40 rounded-full border-[10px] border-white/5 border-t-info shadow-[0_0_20px_rgba(0,163,255,0.2)] animate-spin" style={{ animationDuration: '3s' }} />
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-[10px] font-bold">
              <span className="text-slate-500">SEVERITY BREAKDOWN</span>
              <span className="text-info">4 ACTIVE CHAINS</span>
            </div>
            <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden flex">
              <div className="h-full bg-critical" style={{ width: '20%' }} />
              <div className="h-full bg-warning" style={{ width: '30%' }} />
              <div className="h-full bg-info" style={{ width: '50%' }} />
            </div>
          </div>
        </div>

        {/* THREAT TRENDS (Placeholder) */}
        <div className="glass-card lg:col-span-2 min-h-[300px] flex flex-col">
          <h4 className="font-bold text-sm mb-4 uppercase tracking-widest">Attack Distribution (Live)</h4>
          <div className="flex-1 flex items-center justify-center border border-dashed border-white/10 rounded-lg">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Waiting for Graph Intelligence Analytics...</p>
          </div>
        </div>
      </div>

      {/* RECENT ALERTS FEED */}
      <div className="glass-card">
        <h4 className="font-bold text-sm mb-6 uppercase tracking-widest">Global Security Posture Snapshot</h4>
        <div className="space-y-4">
          <div className="flex items-center gap-4 p-4 bg-safe/5 border-l-4 border-safe rounded-r-lg">
            <div className="h-2 w-2 bg-safe rounded-full animate-pulse" />
            <p className="text-xs font-bold font-mono">14:55:02 | NORMALIZATION_ENGINE | Heartbeat successful across 14 sensors | STABLE</p>
          </div>
          <div className="flex items-center gap-4 p-4 bg-info/5 border-l-4 border-info rounded-r-lg">
            <div className="h-2 w-2 bg-info rounded-full animate-pulse" />
            <p className="text-xs font-bold font-mono">14:54:12 | GRAPH_ENGINE | Detected multi-entity overlap on cluster entity.inc.22 | INVESTIGATING</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;
