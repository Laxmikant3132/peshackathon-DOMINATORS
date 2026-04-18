"use client";

import React, { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { motion } from "framer-motion";
import { 
  Cpu, 
  MemoryStick, 
  HardDrive, 
  Wifi, 
  Activity, 
  Clock, 
  Server,
  Zap,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";

interface HealthData {
  cpu: { percent: number; cores: number; physical_cores: number; freq_mhz: number };
  memory: { total_gb: number; used_gb: number; available_gb: number; percent: number };
  disk: { total_gb: number; used_gb: number; free_gb: number; percent: number };
  network: { bytes_sent_mb: number; bytes_recv_mb: number; packets_sent: number; packets_recv: number; active_connections: number };
  system: { hostname: string; platform: string; platform_version: string; uptime_hours: number; boot_time: string };
  top_processes: any[];
  timestamp: string;
}

export default function SystemHealthPage() {
  const [data, setData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/system-health`);
      if (response.ok) {
        const healthData = await response.json();
        setData(healthData);
        setError(null);
      } else {
        setError("Backend services are currently unresponsive.");
      }
    } catch (error) {
      console.error("Error fetching system health:", error);
      setError("Unable to connect to security backend. Please ensure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 5000); // 5s refresh
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <RefreshCw className="w-12 h-12 text-primary animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  if (error || !data) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6 text-center max-w-md mx-auto">
          <div className="w-20 h-20 rounded-3xl bg-danger/10 flex items-center justify-center border border-danger/20">
            <Server className="text-danger w-10 h-10" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-black text-white">System Offline</h2>
            <p className="text-white/50 text-sm">{error || "No telemetry data available at this time."}</p>
          </div>
          <button 
            onClick={fetchHealth}
            className="px-8 py-3 bg-white text-background font-black rounded-2xl hover:bg-primary transition-all uppercase tracking-widest text-xs"
          >
            Retry Connection
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-1">
            <h1 className="text-3xl md:text-5xl font-black tracking-tighter">
              SYSTEM <span className="text-primary">HEALTH</span>
            </h1>
            <p className="text-white/40 text-lg max-w-2xl font-medium">
              Real-time resource telemetry and hardware performance metrics.
            </p>
          </div>
          <div className="glass px-6 py-3 rounded-2xl flex items-center gap-4 bg-emerald-500/5 border-emerald-500/10">
            <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-emerald-400 font-bold text-sm tracking-widest uppercase">System Online</span>
          </div>
        </header>

        {/* Primary Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard 
            title="CPU Usage" 
            value={`${data.cpu.percent}%`} 
            subValue={`${data.cpu.cores} Cores @ ${data.cpu.freq_mhz}MHz`}
            icon={Cpu}
            color="text-cyan-400"
            percent={data.cpu.percent}
          />
          <MetricCard 
            title="Memory" 
            value={`${data.memory.percent}%`} 
            subValue={`${data.memory.used_gb}GB / ${data.memory.total_gb}GB`}
            icon={MemoryStick}
            color="text-purple-400"
            percent={data.memory.percent}
          />
          <MetricCard 
            title="Disk Space" 
            value={`${data.disk.percent}%`} 
            subValue={`${data.disk.used_gb}GB Used`}
            icon={HardDrive}
            color="text-amber-400"
            percent={data.disk.percent}
          />
          <MetricCard 
            title="Network" 
            value={`${data.network.active_connections}`} 
            subValue="Active Connections"
            icon={Wifi}
            color="text-emerald-400"
            percent={Math.min(100, (data.network.active_connections / 200) * 100)}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
           {/* System Details */}
           <div className="lg:col-span-1 glass rounded-[40px] p-8 border-white/5 space-y-8">
              <h3 className="text-xl font-bold flex items-center gap-3">
                 <Server className="text-primary" size={24} />
                 Inventory Details
              </h3>
              
              <div className="space-y-6">
                 <DetailItem label="Hostname" value={data.system.hostname} />
                 <DetailItem label="OS / Platform" value={data.system.platform} />
                 <DetailItem label="Uptime" value={`${data.system.uptime_hours} Hours`} />
                 <DetailItem label="Network Traffic" value={
                    <div className="flex gap-4">
                       <span className="text-emerald-400 flex items-center gap-1"><ArrowDownRight size={14}/> {data.network.bytes_recv_mb}MB</span>
                       <span className="text-blue-400 flex items-center gap-1"><ArrowUpRight size={14}/> {data.network.bytes_sent_mb}MB</span>
                    </div>
                 } />
              </div>

              <div className="pt-4">
                 <div className="p-6 bg-primary/5 rounded-3xl border border-primary/10">
                    <p className="text-xs text-white/30 uppercase font-black tracking-widest mb-2">Last Update</p>
                    <div className="flex justify-between items-center">
                       <p className="font-mono text-sm">{new Date(data.timestamp).toLocaleTimeString()}</p>
                       <RefreshCw size={14} className="text-primary animate-spin-slow" />
                    </div>
                 </div>
              </div>
           </div>

           {/* Top Processes */}
           <div className="lg:col-span-2 glass rounded-[40px] p-8 border-white/5 space-y-6">
              <div className="flex items-center justify-between">
                 <h3 className="text-xl font-bold flex items-center gap-3">
                    <Activity className="text-primary" size={24} />
                    High-Res Load Analysis
                 </h3>
                 <span className="text-[10px] font-black uppercase tracking-widest text-white/30">Top 10 Processes</span>
              </div>

              <div className="overflow-x-auto">
                 <table className="w-full text-left font-mono text-sm">
                    <thead>
                       <tr className="text-white/20 border-b border-white/5">
                          <th className="pb-4 font-bold">PID</th>
                          <th className="pb-4 font-bold">PROCESS NAME</th>
                          <th className="pb-4 font-bold text-right">CPU %</th>
                          <th className="pb-4 font-bold text-right">MEM %</th>
                       </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.02]">
                       {data.top_processes.map((proc, i) => (
                          <tr key={i} className="group hover:bg-white/[0.02]">
                             <td className="py-4 text-white/40">{proc.pid}</td>
                             <td className="py-4 font-bold text-white group-hover:text-primary transition-colors">{proc.name}</td>
                             <td className="py-4 text-right">{proc.cpu_percent?.toFixed(1) || "0.0"}%</td>
                             <td className="py-4 text-right">{proc.memory_percent?.toFixed(1) || "0.0"}%</td>
                          </tr>
                       ))}
                    </tbody>
                 </table>
              </div>
           </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

function MetricCard({ title, value, subValue, icon: Icon, color, percent }: any) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-8 rounded-[40px] border-white/5 space-y-6 group hover:border-white/10 transition-all cursor-default"
    >
      <div className="flex justify-between items-start">
         <div className={`p-4 rounded-2xl bg-white/5 border border-white/10 group-hover:scale-110 transition-transform ${color}`}>
            <Icon size={24} />
         </div>
         <Zap size={16} className="text-white/10 group-hover:text-primary transition-colors" />
      </div>
      <div>
         <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-1">{title}</h3>
         <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black">{value}</span>
            <span className="text-xs text-white/40 font-bold">{subValue}</span>
         </div>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
         <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${percent}%` }}
            className={`h-full rounded-full bg-current ${color.replace('text-', 'bg-')}`} 
         />
      </div>
    </motion.div>
  );
}

function DetailItem({ label, value }: any) {
   return (
      <div className="flex justify-between items-center">
         <span className="text-xs font-bold text-white/30 uppercase tracking-widest">{label}</span>
         <div className="text-sm font-bold">{value}</div>
      </div>
   );
}
