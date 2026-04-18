"use client";

import React, { useEffect, useState, useRef, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  ShieldAlert,
  Terminal,
  Zap,
  Info,
  Clock,
  Eye,
  Cpu,
  HardDrive,
  Wifi,
  MemoryStick,
  Bell,
  BellOff,
  Ban
} from "lucide-react";

import { useMonitoring } from "@/context/MonitoringContext";
import type { LogEntry, AlertEntry, HealthData } from "@/context/MonitoringContext";

export default function MonitoringDashboard() {
  const {
    logs,
    alerts,
    health,
    inventory,
    isConnected,
    notificationsEnabled,
    toggleNotifications,
    clearAlerts,
    blockedIps,
    blockIp
  } = useMonitoring();

  const scrollRef = useRef<HTMLDivElement>(null);

  const handleBlockIp = async (ip: string) => {
    await blockIp(ip);
  };

  const getLayerColor = (layer: string) => {
    switch (layer) {
      case "network": return "text-cyan-400";
      case "endpoint": return "text-purple-400";
      case "application": return "text-emerald-400";
      default: return "text-white";
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "Critical": return "bg-red-500/20 text-red-500 border-red-500/50";
      case "High": return "bg-orange-500/20 text-orange-500 border-orange-500/50";
      case "Medium": return "bg-yellow-500/20 text-yellow-500 border-yellow-500/50";
      default: return "bg-blue-500/20 text-blue-500 border-blue-500/50";
    }
  };

  const formatTime = (isoString?: string) => {
    if (!isoString) return "--:--:--";
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return "--:--:--";
      return d.toLocaleTimeString();
    } catch {
      return "--:--:--";
    }
  };

  const suspiciousIps = useMemo(() => {
    const ips = alerts.map(a => a.src_ip).filter(Boolean) as string[];
    return Array.from(new Set(ips));
  }, [alerts]);

  return (
    <div className="space-y-6">
      {/* Header with status indicators */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="text-primary animate-pulse" />
            Live Threat Monitoring
          </h2>
          <p className="text-white/50 text-sm">Real-time analysis — auto-started on server boot</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Connection Status */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-xs font-bold ${isConnected
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : "bg-red-500/10 border-red-500/30 text-red-400"
            }`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`} />
            {isConnected ? "LIVE" : "CONNECTING..."}
          </div>

          {/* Notification Toggle */}
          <button
            onClick={toggleNotifications}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-xs font-bold transition-all ${notificationsEnabled
                ? "bg-primary/10 border-primary/30 text-primary"
                : "bg-white/5 border-white/10 text-white/50 hover:text-white"
              }`}
          >
            {notificationsEnabled ? <Bell size={14} /> : <BellOff size={14} />}
            {notificationsEnabled ? "Alerts ON" : "Alerts OFF"}
          </button>
        </div>
      </div>

      {/* System Health Bar */}
      {health && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="glass p-4 rounded-2xl border-white/5 flex items-center gap-3">
            <Cpu size={20} className="text-cyan-400" />
            <div>
              <p className="text-[10px] text-white/40 font-bold uppercase">CPU</p>
              <p className="text-lg font-black text-white">{health.cpu_percent}%</p>
            </div>
            <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden ml-auto">
              <div className={`h-full rounded-full transition-all ${health.cpu_percent > 80 ? 'bg-red-500' : health.cpu_percent > 50 ? 'bg-yellow-500' : 'bg-emerald-500'}`}
                style={{ width: `${health.cpu_percent}%` }} />
            </div>
          </div>
          <div className="glass p-4 rounded-2xl border-white/5 flex items-center gap-3">
            <MemoryStick size={20} className="text-purple-400" />
            <div>
              <p className="text-[10px] text-white/40 font-bold uppercase">RAM</p>
              <p className="text-lg font-black text-white">{health.memory_percent}%</p>
            </div>
            <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden ml-auto">
              <div className={`h-full rounded-full transition-all ${health.memory_percent > 80 ? 'bg-red-500' : health.memory_percent > 50 ? 'bg-yellow-500' : 'bg-emerald-500'}`}
                style={{ width: `${health.memory_percent}%` }} />
            </div>
          </div>
          <div className="glass p-4 rounded-2xl border-white/5 flex items-center gap-3">
            <HardDrive size={20} className="text-amber-400" />
            <div>
              <p className="text-[10px] text-white/40 font-bold uppercase">Disk</p>
              <p className="text-lg font-black text-white">{health.disk_percent ?? health.memory_used_gb} {health.disk_percent != null ? '%' : 'GB'}</p>
            </div>
            {health.disk_percent != null && (
              <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden ml-auto">
                <div className={`h-full rounded-full transition-all ${health.disk_percent > 85 ? 'bg-red-500' : health.disk_percent > 60 ? 'bg-yellow-500' : 'bg-emerald-500'}`}
                  style={{ width: `${health.disk_percent}%` }} />
              </div>
            )}
          </div>
          <div className="glass p-4 rounded-2xl border-white/5 flex items-center gap-3">
            <Wifi size={20} className="text-emerald-400" />
            <div>
              <p className="text-[10px] text-white/40 font-bold uppercase">Connections</p>
              <p className="text-lg font-black text-white">{health.active_connections}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Terminal / Live Logs */}
        <div className="lg:col-span-2 glass rounded-[32px] overflow-hidden flex flex-col h-[500px]">
          <div className="bg-white/5 px-6 py-3 border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Terminal size={16} className="text-primary" />
              <span className="text-xs font-bold uppercase tracking-widest text-white/50">Global Telemetry Stream</span>
            </div>
            <div className="flex gap-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
              <div className="w-2 h-2 rounded-full bg-yellow-500" />
              <div className="w-2 h-2 rounded-full bg-green-500" />
            </div>
          </div>

          <div className="px-4 py-2 bg-white/[0.02] border-b border-white/5 text-[10px] text-white/30 font-mono">
            Real-time correlation across Network and Endpoint layers
          </div>

          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto font-mono text-[11px] bg-black/40"
          >
            {logs.length === 0 && (
              <div className="h-full flex items-center justify-center text-white/20">
                Connecting to live telemetry stream...
              </div>
            )}
            {logs.map((log) => {
              const logAction = log.label === 'malicious' ? 'ANOMALOUS_ACTIVITY' : (log.action ? log.action.toUpperCase() : 'FLOW_EVENT');
              const logDetail = log.detail ? log.detail.toUpperCase() : '';

              const borderColor = log.layer === 'network' ? 'border-l-yellow-500' : (log.layer === 'endpoint' ? 'border-l-blue-500' : 'border-l-emerald-500');
              const rawDate = typeof log.timestamp === 'string' ? log.timestamp.replace('T', ' ').replace('Z', '') : log.timestamp;

              return (
                <div key={log.id} className={`border-l-2 ${borderColor} px-4 py-3 border-b border-white/5 hover:bg-white/5 transition-colors`}>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 text-white/60">
                      <span>{rawDate}</span>
                      <span className="text-white/20">|</span>
                      <div className="flex items-center gap-2">
                        <span className={`font-black tracking-tight ${log.label === 'malicious' ? 'text-red-400' : 'text-primary'}`}>
                          {logAction}
                        </span>
                        {logDetail && (
                          <span className="text-[9px] px-1.5 py-0.5 bg-white/5 rounded border border-white/10 text-white/40 font-bold">
                            {logDetail}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-white/80">
                      <span className="text-white/40">{log.src_ip}</span>
                      <span className="text-blue-500/50">→</span>
                      <span className="text-white/80 font-bold">{log.dst_ip}</span>
                      {log.process && <span className="text-white/30 text-[10px] ml-2">[{log.process}]</span>}
                    </div>

                    <div className="flex items-center gap-2 text-white/30 text-[10px]">
                      <span>Sensor: {log.sensor || 'psutil_engine'}</span>
                      <span>|</span>
                      <span>Status: {String(log.status || 'success')}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Active Threats Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* Active Task Inventory */}
          <div className="glass rounded-[32px] flex flex-col h-[400px]">
            <div className="bg-white/5 px-6 py-4 border-b border-white/10 flex items-center gap-3">
              <HardDrive size={18} className="text-primary" />
              <span className="text-sm font-bold uppercase tracking-widest text-white/50">Active Task Inventory</span>
              <span className="ml-auto bg-primary/20 text-primary text-[10px] px-2 py-0.5 rounded-full font-bold">
                {inventory.length}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {inventory.length === 0 ? (
                <div className="h-full flex items-center justify-center text-white/10 italic text-xs">
                  Scanning active tasks...
                </div>
              ) : (
                inventory.map((task) => (
                  <div key={task.pid} className="flex items-center justify-between p-3 bg-white/[0.03] border border-white/5 rounded-2xl hover:bg-white/[0.05] transition-colors group">
                    <div className="flex flex-col">
                      <span className="text-[11px] font-black tracking-tight text-white group-hover:text-primary transition-colors">{task.name}</span>
                      <div className="flex items-center gap-2 text-[9px] text-white/30 uppercase">
                        <span>PID: {task.pid}</span>
                        <span>•</span>
                        <span>{task.user}</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <div className="flex gap-2">
                        <span className="text-[9px] px-1 bg-blue-500/10 text-blue-400 rounded">CPU {task.cpu}%</span>
                        <span className="text-[9px] px-1 bg-emerald-500/10 text-emerald-400 rounded">RAM {task.memory}%</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Active Alerts List */}
          <div className="glass rounded-[32px] flex flex-col flex-1 h-[400px]">
            <div className="bg-white/5 px-6 py-4 border-b border-white/10 flex items-center gap-3">
              <ShieldAlert size={18} className="text-red-500" />
              <span className="text-sm font-bold uppercase tracking-widest text-white/50">Active Alerts</span>
              <span className="bg-red-500 text-white text-[10px] px-2 py-0.5 rounded-full font-bold">
                {alerts.length}
              </span>
              {alerts.length > 0 && (
                <button
                  onClick={() => clearAlerts()}
                  className="ml-auto text-[10px] font-bold text-white/30 hover:text-white transition-colors uppercase tracking-tighter"
                >
                  Clear All
                </button>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {alerts.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                  <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                    <Zap className="text-emerald-500" />
                  </div>
                  <p className="text-sm text-white/40">No threats detected. System is currently healthy.</p>
                </div>
              ) : (
                alerts.map((alert, idx) => (
                  <div
                    key={alert.timestamp + idx}
                    className={`p-4 rounded-2xl border ${getSeverityColor(alert.severity)} space-y-2`}
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-bold text-xs uppercase tracking-wider">{alert.type}</span>
                      <span className="text-[10px] opacity-60">[{formatTime(alert.timestamp)}]</span>
                    </div>
                    <p className="text-xs leading-relaxed opacity-90">{alert.reason}</p>
                    <div className="flex items-center justify-between pt-1 border-t border-current/10">
                      <div className="flex items-center gap-2">
                        <Zap size={12} />
                        <span className="text-[10px] font-bold">Confidence: {Math.round(alert.confidence * 100)}%</span>
                      </div>
                      {alert.src_ip && !blockedIps.includes(alert.src_ip) && (
                        <button
                          onClick={() => handleBlockIp(alert.src_ip!)}
                          className="flex items-center gap-1 text-[10px] font-bold px-2 py-1 bg-red-500/20 rounded-lg hover:bg-red-500/30 transition-colors"
                        >
                          <Ban size={10} /> Block IP
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Suspicious IP War Rooms */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold flex items-center gap-2 pt-6">
          <Eye className="text-primary" />
          Priority Surveillance Units (War Rooms)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {suspiciousIps.length === 0 ? (
            <div className="col-span-2 glass border-dashed p-12 rounded-[32px] text-center text-white/20 uppercase tracking-[0.2em]">
              Waiting for high-confidence suspicious activity...
            </div>
          ) : (
            suspiciousIps.map(ip => {
              const ipAlerts = alerts.filter(a => a.src_ip === ip);
              const lastAlert = ipAlerts[0];
              const isBlocked = blockedIps.includes(ip);
              return (
                <div
                  key={ip}
                  className={`glass p-8 rounded-[40px] transition-all space-y-6 ${isBlocked ? "border-emerald-500/20" : "border-red-500/20 hover:border-red-500/40"
                    }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="flex items-center gap-3">
                        <span className={`text-2xl font-black font-mono tracking-tighter ${isBlocked ? "text-emerald-500 line-through" : "text-red-500"}`}>{ip}</span>
                        <span className={`text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase ${isBlocked ? "bg-emerald-500" : "bg-red-500"
                          }`}>
                          {isBlocked ? "Blocked" : "Under Surveillance"}
                        </span>
                      </div>
                      <p className="text-xs text-white/50">First detected: {formatTime(lastAlert?.timestamp)}</p>
                    </div>
                    <ShieldAlert className={`${isBlocked ? "text-emerald-500" : "text-red-500 animate-pulse"}`} size={24} />
                  </div>

                  <div className="space-y-4">
                    <div className="p-4 bg-white/5 rounded-2xl space-y-3">
                      <div className="flex items-center gap-2 text-warning">
                        <Info size={14} />
                        <span className="text-xs font-bold uppercase tracking-widest">Detection Explainability</span>
                      </div>
                      <p className="text-sm text-white/70 leading-relaxed italic">
                        &quot;{lastAlert?.reason}&quot;
                      </p>
                    </div>

                    <div className="p-4 bg-primary/10 border border-primary/20 rounded-2xl space-y-3">
                      <div className="flex items-center gap-2 text-primary">
                        <Zap size={14} />
                        <span className="text-xs font-bold uppercase tracking-widest">Recommended Playbook</span>
                      </div>
                      <p className="text-sm text-white/90">
                        {lastAlert?.playbook}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-white/40 mb-2">
                        <Clock size={14} />
                        <span className="text-xs font-bold uppercase tracking-widest">Activity Timeline</span>
                      </div>
                      <div className="space-y-2">
                        {lastAlert?.history?.map((event: any, i: number) => (
                          <div key={i} className="flex items-center gap-3 text-[10px] bg-white/5 p-2 rounded-lg border border-white/5">
                            <span className="text-white/30 whitespace-nowrap">{formatTime(event.timestamp)}</span>
                            <span className={`font-bold uppercase ${getLayerColor(event.layer)}`}>{event.layer}</span>
                            <span className="text-white/70 truncate flex-1">{event.action || event.endpoint || "FLOW DETECTED"}</span>
                            {event.label === 'malicious' && <AlertTriangle size={10} className="text-red-500" />}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 flex items-center justify-between">
                    <div className="flex -space-x-2">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="w-8 h-8 rounded-full border border-background bg-zinc-800 flex items-center justify-center">
                          <ShieldAlert size={12} className="text-white/40" />
                        </div>
                      ))}
                      <div className="w-8 h-8 rounded-full border border-background bg-zinc-700 flex items-center justify-center text-[10px] font-bold">
                        +{ipAlerts.length}
                      </div>
                    </div>
                    {!isBlocked ? (
                      <button
                        onClick={() => handleBlockIp(ip)}
                        className="px-6 py-2 bg-red-600 text-white font-bold rounded-xl text-xs hover:bg-red-700 transition-colors flex items-center gap-2"
                      >
                        <Ban size={12} /> Execute Isolation
                      </button>
                    ) : (
                      <span className="px-6 py-2 bg-emerald-600/20 text-emerald-400 font-bold rounded-xl text-xs border border-emerald-500/30">
                        ✓ IP Isolated
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
