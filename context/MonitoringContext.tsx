"use client";

import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "./AuthContext";

export interface LogEntry {
  id: string;
  timestamp: string;
  layer: "network" | "endpoint" | "application";
  src_ip: string;
  dst_ip: string;
  label: string;
  action?: string;
  process?: string;
  sensor?: string;
  status?: string;
  [key: string]: any;
}

export interface AlertEntry {
  type: string;
  severity: "Low" | "Medium" | "High" | "Critical";
  confidence: number;
  reason: string;
  playbook: string;
  timestamp: string;
  src_ip?: string;
  history?: any[];
}

export interface HealthData {
  cpu_percent: number;
  memory_percent: number;
  memory_used_gb: number;
  active_connections: number;
  disk_percent?: number;
  net_sent_mb?: number;
  net_recv_mb?: number;
  timestamp: string;
}

interface MonitoringContextType {
  logs: LogEntry[];
  alerts: AlertEntry[];
  health: HealthData | null;
  inventory: any[];
  isConnected: boolean;
  notificationsEnabled: boolean;
  clearAlerts: () => void;
  toggleNotifications: () => Promise<void>;
  blockedIps: string[];
  blockIp: (ip: string) => Promise<void>;
}

const MonitoringContext = createContext<MonitoringContextType | undefined>(undefined);

export const MonitoringProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [alerts, setAlerts] = useState<AlertEntry[]>([]);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [inventory, setInventory] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [blockedIps, setBlockedIps] = useState<string[]>([]);
  
  const logBuffer = useRef<LogEntry[]>([]);
  const alertBuffer = useRef<AlertEntry[]>([]);
  const activeNotificationsRef = useRef<Notification[]>([]);
  const notificationsRef = useRef(false);

  // Persistence logic
  useEffect(() => {
    const saved = localStorage.getItem("hf_notifications_enabled");
    const isEnabled = saved === "true";
    setNotificationsEnabled(isEnabled);
    notificationsRef.current = isEnabled;

    const syncState = () => {
      const s = localStorage.getItem("hf_notifications_enabled");
      const en = s === "true";
      setNotificationsEnabled(en);
      notificationsRef.current = en;
    };
    window.addEventListener("storage", syncState);
    return () => window.removeEventListener("storage", syncState);
  }, []);

  useEffect(() => {
    notificationsRef.current = notificationsEnabled;
  }, [notificationsEnabled]);

  // Notification helper
  const sendNotification = useCallback((alert: AlertEntry) => {
    if (notificationsRef.current && "Notification" in window && Notification.permission === "granted") {
      try {
        const n = new Notification(`🚨 ${alert.severity} THREAT`, {
          body: `${alert.type}\n${alert.reason}`,
          icon: "/favicon.ico",
          tag: alert.timestamp
        });
        activeNotificationsRef.current.push(n);
        n.onclose = () => {
          activeNotificationsRef.current = activeNotificationsRef.current.filter(item => item !== n);
        };
        setTimeout(() => n.close(), 10000);
      } catch (err) {
        console.error("Context notification failed:", err);
      }
    }
  }, []);

  // WebSocket management
  useEffect(() => {
    if (!user) {
      setIsConnected(false);
      return;
    }

    let socket: WebSocket;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      const host = window.location.hostname === "localhost" ? "127.0.0.1" : window.location.hostname;
      socket = new WebSocket(`ws://${host}:8000/ws/traffic`);

      socket.onopen = () => setIsConnected(true);
      socket.onclose = () => {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connect, 3000);
      };

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "log") {
            logBuffer.current.push(msg.data);
          } else if (msg.type === "alert") {
            alertBuffer.current.push(msg.data);
            if (notificationsRef.current && (msg.data.severity === "High" || msg.data.severity === "Critical")) {
              sendNotification(msg.data);
            }
          } else if (msg.type === "health") {
            setHealth(msg.data);
          } else if (msg.type === "inventory") {
            setInventory(msg.data);
          }
        } catch (e) {}
      };
    };

    connect();

    // Throttled state updates
    const interval = setInterval(() => {
      if (logBuffer.current.length > 0) {
        // Prepend new logs to the top
        setLogs(prev => [...logBuffer.current.reverse(), ...prev].slice(0, 500));
        logBuffer.current = [];
      }
      if (alertBuffer.current.length > 0) {
        setAlerts(prev => [...alertBuffer.current, ...prev].slice(0, 100));
        alertBuffer.current = [];
      }
    }, 200);

    return () => {
      if (socket) socket.close();
      clearTimeout(reconnectTimeout);
      clearInterval(interval);
    };
  }, [user, sendNotification]);

  const toggleNotifications = async () => {
    if (!notificationsEnabled) {
      if ("Notification" in window) {
        const perm = await Notification.requestPermission();
        if (perm === "granted") {
          setNotificationsEnabled(true);
          localStorage.setItem("hf_notifications_enabled", "true");
          new Notification("Human Firewall", { body: "Monitoring active in background." });
        }
      }
    } else {
      setNotificationsEnabled(false);
      localStorage.setItem("hf_notifications_enabled", "false");
      activeNotificationsRef.current.forEach(n => n.close());
      activeNotificationsRef.current = [];
    }
  };

  const clearAlerts = () => setAlerts([]);

  const blockIp = async (ip: string) => {
    try {
      const host = window.location.hostname === "localhost" ? "127.0.0.1" : window.location.hostname;
      await fetch(`http://${host}:8000/api/threat-intel/block-ip`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip })
      });
      setBlockedIps(prev => [...prev, ip]);
    } catch (e) {}
  };

  return (
    <MonitoringContext.Provider value={{ 
      logs, alerts, health, inventory, isConnected, notificationsEnabled, 
      clearAlerts, toggleNotifications, blockedIps, blockIp 
    }}>
      {children}
    </MonitoringContext.Provider>
  );
};

export const useMonitoring = () => {
  const context = useContext(MonitoringContext);
  if (context === undefined) {
    throw new Error("useMonitoring must be used within a MonitoringProvider");
  }
  return context;
};
