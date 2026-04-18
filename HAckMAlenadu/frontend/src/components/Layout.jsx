import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { 
  Shield, Activity, List, Share2, Info, Eye, 
  Play, Settings, Terminal, Users, BarChart3, Crosshair, HeartPulse, Search, Map
} from 'lucide-react';
import useXDRStore from '../store/useXDRStore';

const NavItem = ({ to, icon: Icon, label }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
        isActive 
          ? 'bg-info/20 text-info border-r-4 border-info' 
          : 'text-slate-400 hover:bg-white/5 hover:text-slate-100'
      }`
    }
  >
    <Icon size={20} />
    <span className="text-sm font-semibold">{label}</span>
  </NavLink>
);

const Layout = () => {
  const { stats } = useXDRStore();
  const threatColor = stats.threat_level === 'CRITICAL' ? 'text-critical' : 'text-safe';

  return (
    <div className="flex h-screen bg-[#0a0b10] overflow-hidden">
      {/* SIDEBAR NAVIGATION */}
      <aside className="w-64 bg-[#0c0d16] border-r border-white/10 flex flex-col">
        <div className="p-6 flex items-center gap-3 border-b border-white/10">
          <Shield className="text-info" size={32} />
          <div>
            <h1 className="font-extrabold text-lg tracking-tight">SENTINEL AI</h1>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-none">Enterprise XDR</p>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-4 space-y-1">
          <p className="text-[10px] px-4 py-2 font-bold text-slate-500 uppercase tracking-widest">Main Dashboard</p>
          <NavItem to="/" icon={BarChart3} label="Overview" />
          <NavItem to="/monitoring" icon={Activity} label="Live Monitoring" />
          
          <p className="text-[10px] px-4 py-6 font-bold text-slate-500 uppercase tracking-widest">Intelligence</p>
          <NavItem to="/incidents" icon={List} label="Incident Center" />
          <NavItem to="/graph" icon={Share2} label="Graph Explorer" />
          <NavItem to="/intel" icon={Crosshair} label="Threat Intelligence" />
          
          <p className="text-[10px] px-4 py-6 font-bold text-slate-500 uppercase tracking-widest">Forensics</p>
          <NavItem to="/explainability" icon={Info} label="Explainability" />
          <NavItem to="/replay" icon={Eye} label="Forensics & Replay" />
          <NavItem to="/playbooks" icon={Play} label="SOAR Playbooks" />
        </nav>

        <div className="p-4 bg-white/5 m-4 rounded-xl border border-white/5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold text-slate-400">STATUS</span>
            <div className={`h-2 w-2 rounded-full bg-current ${threatColor} animate-pulse`} />
          </div>
          <p className={`text-xs font-bold ${threatColor}`}>{stats.threat_level}</p>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        <header className="h-16 border-b border-white/10 bg-[#0a0b10]/50 backdrop-blur-md flex items-center justify-between px-8 z-20">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 bg-info rounded-full animate-pulse" />
            <span className="text-xs font-bold text-slate-400">PIPELINE ACTIVE - 45 EPS</span>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-[10px] text-slate-500 font-bold">ACTIVE INCIDENTS</p>
              <p className="text-sm font-bold text-critical leading-none">{stats.incident_count}</p>
            </div>
            <div className="h-8 w-8 rounded-lg bg-info/10 border border-info/20 flex items-center justify-center">
              <Settings size={18} className="text-info" />
            </div>
          </div>
        </header>

        <section className="flex-1 overflow-y-auto p-8 relative">
          <Outlet />
        </section>
      </main>
    </div>
  );
};

export default Layout;
