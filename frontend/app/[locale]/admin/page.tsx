"use client";

import React, { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import StatsCard from "@/components/StatsCard";
import { Users, Mail, ShieldCheck, AlertTriangle, AlertCircle, BarChart3, PieChart as PieChartIcon, Search, MoreVertical, ShieldAlert, RefreshCw } from "lucide-react";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend
} from "recharts";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "../../../navigation";
import { db } from "@/services/firebaseConfig";
import { collection, query, where, onSnapshot, orderBy } from "firebase/firestore";

const PROCESS_DESCRIPTIONS: { [key: string]: string } = {
  "SVCHOST.EXE": "System Host Process: Manages Windows services, network stacks, and background system logic.",
  "CHROME.EXE": "Google Chrome: Active web browsing session. Monitoring for suspicious URLs and data exfiltration.",
  "POWERSHELL.EXE": "Windows PowerShell: Powerful command-line shell. Monitoring for high-risk script execution.",
  "EXPLORER.EXE": "Windows Explorer: Managing file system access and user desktop interface.",
  "NODE.EXE": "Node.js Runtime: Active server-side or local script execution. Potential application backend.",
  "CONHOST.EXE": "Console Window Host: Managing terminal interface for command-line tools.",
  "PYTHON.EXE": "Python Interpreter: Executing data scripts or background applications.",
  "MSEDGE.EXE": "Microsoft Edge: Modern web browsing. Verifying security certificates and traffic origin.",
  "SMARTSCREEN.EXE": "Windows SmartScreen: Built-in security tool scanning for phishing and malware.",
  "TASKMGR.EXE": "Task Manager: Monitoring system performance and active process management.",
  "SERVICES.EXE": "Services Control Manager: Orchestrating the lifecycle of background system services."
};

const COLORS = ["#10b981", "#f59e0b", "#ef4444"];

interface EmailLog {
  id: string;
  employeeEmail?: string;
  sender?: string;
  subject?: string;
  safety?: string;
  analyzedAt: any; // Can be Timestamp or Date
}

export default function AdminPanel() {
  const { profile, loading } = useAuth();
  const router = useRouter();
  const [employees, setEmployees] = useState<any[]>([]);
  const [emailLogs, setEmailLogs] = useState<EmailLog[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  const [stats, setStats] = useState({
    totalEmails: 0,
    safeCount: 0,
    suspiciousCount: 0,
    dangerousCount: 0,
    employeesMonitored: 0
  });

  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string>("all");

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!loading && profile && profile.role !== "admin") {
      router.push("/dashboard");
    }
  }, [profile, loading, router]);

  useEffect(() => {
    if (!profile || profile.role !== "admin") return;

    setIsLoading(true);

    // 1. Listen to employees
    const employeesQuery = query(collection(db, "users"), where("role", "==", "employee"));
    const unsubscribeEmployees = onSnapshot(employeesQuery, (snapshot) => {
      const empList = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setEmployees(empList);
      setStats(prev => ({ ...prev, employeesMonitored: empList.length }));
      setIsLoading(false);
    });

    // 2. Listen to email logs
    const logsQuery = query(collection(db, "email_logs"), orderBy("analyzedAt", "desc"));
    const unsubscribeLogs = onSnapshot(logsQuery, (snapshot) => {
      const logs: EmailLog[] = snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          analyzedAt: data.analyzedAt?.toDate() || new Date()
        } as EmailLog;
      });
      setEmailLogs(logs);

      // Calculate stats
      const newStats = {
        totalEmails: logs.length,
        safeCount: logs.filter(l => l.safety?.toLowerCase() === "safe").length,
        suspiciousCount: logs.filter(l => l.safety?.toLowerCase() === "suspicious").length,
        dangerousCount: logs.filter(l => l.safety?.toLowerCase() === "dangerous").length,
        employeesMonitored: employees.length
      };
      setStats(prev => ({ ...prev, ...newStats }));
    });

    return () => {
      unsubscribeEmployees();
      unsubscribeLogs();
    };
  }, [profile, employees.length]);

  const refreshData = () => {
    // With onSnapshot, data is real-time, but we can trigger a visual refresh or just log
    console.log("Data refreshed via real-time listeners");
  };

  if (loading || isLoading || (profile && profile.role !== "admin")) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <RefreshCw className="w-12 h-12 text-primary animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  const employeeMetrics = employees.map(emp => {
    const empLogs = emailLogs.filter(log => log.employeeEmail === emp.email);
    const dangerousCount = empLogs.filter(log => log.safety?.toLowerCase() === "dangerous").length;
    
    let risk = "Low";
    if (dangerousCount >= 3) risk = "High";
    else if (dangerousCount >= 1) risk = "Medium";

    return {
      ...emp,
      scans: empLogs.length,
      risk,
      dangerousCount
    };
  });

  const pieData = [
    { name: "Safe", value: stats.safeCount },
    { name: "Suspicious", value: stats.suspiciousCount },
    { name: "Dangerous", value: stats.dangerousCount },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8 md:space-y-12 max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left">
          <div className="space-y-1">
             <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight flex flex-col md:flex-row items-center md:space-x-3">
                <Users className="w-8 h-8 text-primary mb-2 md:mb-0" />
                <span>Admin <span className="text-primary">Panel</span></span>
             </h1>
             <p className="text-white/50 text-base md:text-lg">Organization-wide security posture and employee risk metrics.</p>
          </div>
          <button 
             onClick={refreshData}
             className="w-full md:w-auto px-6 py-3 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center space-x-2 hover:bg-white/10 hover:text-primary transition-all font-bold"
          >
             <RefreshCw className="w-5 h-5" />
             <span>Refresh Data</span>
          </button>
        </header>

        {/* Admin Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 md:gap-6">
          <StatsCard title="Employees Monitored" value={stats.employeesMonitored.toString()} icon={Users} color="bg-primary" />
          <StatsCard title="Emails Analyzed" value={stats.totalEmails.toLocaleString()} icon={Mail} color="bg-accent" />
          <StatsCard title="Safe Emails" value={stats.safeCount.toLocaleString()} icon={ShieldCheck} color="bg-secondary" />
          <StatsCard title="Suspicious Emails" value={stats.suspiciousCount.toLocaleString()} icon={AlertTriangle} color="bg-warning" />
          <StatsCard title="Dangerous Emails" value={stats.dangerousCount.toLocaleString()} icon={AlertCircle} color="bg-danger" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
           {/* Employee Table */}
           <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="lg:col-span-2 glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 md:space-y-8"
           >
              <div className="flex items-center justify-between">
                 <h3 className="text-lg md:text-xl font-bold flex items-center space-x-3">
                    <BarChart3 className="w-5 h-5 text-primary" />
                    <span>Employee Security Metrics</span>
                 </h3>
              </div>

              <div className="overflow-x-auto -mx-6 md:mx-0 px-6 md:px-0">
                 {/* Desktop Table View */}
                 <table className="hidden md:table w-full text-left border-separate border-spacing-y-4">
                    <thead>
                       <tr className="text-white/30 text-[10px] font-black uppercase tracking-widest">
                          <th className="px-4">Employee</th>
                          <th className="px-4 text-center">Sync Count</th>
                          <th className="px-4 text-center">Risk Profile</th>
                          <th className="px-4 text-right">Monitoring</th>
                       </tr>
                    </thead>
                    <tbody className="space-y-4">
                       {employeeMetrics.map((emp: any) => (
                          <tr key={emp.id} className="glass-light rounded-2xl group hover:bg-white/[0.04] transition-all">
                             <td className="py-4 px-4 rounded-l-2xl">
                                <div className="flex items-center space-x-3">
                                   <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center font-bold text-primary border border-white/10">{emp.name?.charAt(0)}</div>
                                   <div className="min-w-0">
                                      <div className="text-sm font-bold text-white truncate">{emp.name}</div>
                                      <div className="text-xs text-white/30 truncate">{emp.email}</div>
                                   </div>
                                </div>
                             </td>
                             <td className="py-4 px-4 text-center font-mono font-bold text-primary">{emp.scans}</td>
                             <td className="py-4 px-4 text-center">
                                <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border inline-block ${
                                   emp.risk === "Low" ? "bg-secondary/10 border-secondary/20 text-secondary" : 
                                   emp.risk === "Medium" ? "bg-warning/10 border-warning/20 text-warning" : "bg-danger/10 border-danger/20 text-danger"
                                }`}>
                                   {emp.risk}
                                </div>
                             </td>
                             <td className="py-4 px-4 text-right rounded-r-2xl">
                                <button className="p-2 hover:bg-white/10 rounded-lg text-white/30 hover:text-white transition-all"><MoreVertical className="w-5 h-5" /></button>
                             </td>
                          </tr>
                       ))}
                    </tbody>
                 </table>

                 {/* Mobile Card View */}
                 <div className="md:hidden space-y-4">
                    {employeeMetrics.map((emp: any) => (
                       <div key={emp.id} className="glass-light p-4 rounded-2xl border border-white/5 space-y-4">
                          <div className="flex items-center justify-between">
                             <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center font-bold text-primary border border-white/10">{emp.name?.charAt(0)}</div>
                                <div className="min-w-0">
                                   <div className="text-sm font-bold text-white truncate">{emp.name}</div>
                                   <div className="text-xs text-white/30 truncate">{emp.email}</div>
                                </div>
                             </div>
                             <button className="p-2 hover:bg-white/10 rounded-lg text-white/30 transition-all"><MoreVertical className="w-5 h-5" /></button>
                          </div>
                          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                             <div>
                                <div className="text-[10px] text-white/30 uppercase font-black tracking-widest mb-1">Sync Count</div>
                                <div className="text-sm font-mono font-bold text-primary">{emp.scans}</div>
                             </div>
                             <div className="text-right">
                                <div className="text-[10px] text-white/30 uppercase font-black tracking-widest mb-1">Risk Profile</div>
                                <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border inline-block ${
                                   emp.risk === "Low" ? "bg-secondary/10 border-secondary/20 text-secondary" : 
                                   emp.risk === "Medium" ? "bg-warning/10 border-warning/20 text-warning" : "bg-danger/10 border-danger/20 text-danger"
                                }`}>
                                   {emp.risk}
                                </div>
                             </div>
                          </div>
                       </div>
                    ))}
                 </div>
              </div>
           </motion.div>

           <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 md:space-y-8 flex flex-col"
           >
              <div className="flex items-center justify-between">
                 <h3 className="text-lg md:text-xl font-bold flex items-center space-x-3">
                    <PieChartIcon className="w-5 h-5 text-accent" />
                    <span>Organization Threat Distribution</span>
                 </h3>
              </div>
              <div className="h-[250px] md:h-[300px] w-full mt-auto">
                 <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                       <Pie 
                         data={pieData} 
                         cx="50%" 
                         cy="50%" 
                         innerRadius={isMobile ? 60 : 70} 
                         outerRadius={isMobile ? 80 : 90} 
                         paddingAngle={5} 
                         dataKey="value"
                         stroke="none"
                       >
                          {pieData.map((entry, index) => (
                             <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length] || "#000"} />
                          ))}
                       </Pie>
                       <Tooltip 
                         contentStyle={{ backgroundColor: "#12121a", borderColor: "#ffffff10", borderRadius: "16px", color: "#fff" }} 
                         itemStyle={{ color: "#fff" }}
                       />
                       <Legend verticalAlign="bottom" height={36}/>
                    </PieChart>
                 </ResponsiveContainer>
              </div>
              <div className="p-6 bg-accent/10 border border-accent/20 rounded-3xl space-y-2 mt-auto">
                 <div className="flex items-center space-x-2 text-accent">
                    <ShieldAlert className="w-5 h-5" />
                    <span className="font-bold text-sm">AI Security Insight</span>
                 </div>
                 <p className="text-xs text-white/60 leading-relaxed">
                   Currently monitoring {stats.totalEmails} organization emails. 
                   {stats.dangerousCount > 0 ? ` Detected ${stats.dangerousCount} critical threats requiring immediate intervention.` : ' All synced emails are within safe parameters.'}
                 </p>
              </div>
           </motion.div>

           {/* Organization Email Log */}
           <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="lg:col-span-3 glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 md:space-y-8"
           >
              <div className="flex items-center justify-between">
                 <h3 className="text-lg md:text-xl font-bold flex items-center space-x-3">
                    <Mail className="w-5 h-5 text-primary" />
                    <span>Real-time Organization Email Log</span>
                 </h3>
              </div>

              <div className="overflow-x-auto -mx-6 md:mx-0 px-6 md:px-0">
                 {/* Desktop Table View */}
                 <table className="hidden md:table w-full text-left">
                    <thead>
                       <tr className="text-white/30 text-[10px] font-black uppercase tracking-widest border-b border-white/5">
                          <th className="pb-4 px-4">Employee</th>
                          <th className="pb-4 px-4">Sender</th>
                          <th className="pb-4 px-4">Subject</th>
                          <th className="pb-4 px-4 text-center">Classification</th>
                          <th className="pb-4 px-4 text-right">Analyzed At</th>
                       </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                       {emailLogs.map((email: EmailLog) => (
                          <tr key={email.id} className="group hover:bg-white/[0.02] transition-all">
                             <td className="py-4 px-4">
                                <div className="text-sm font-bold text-white">{email.employeeEmail}</div>
                             </td>
                             <td className="py-4 px-4 min-w-[200px]">
                                <div className="text-sm text-white/70 truncate">{email.sender}</div>
                             </td>
                             <td className="py-4 px-4 min-w-[300px]">
                                <div className="text-sm text-white/70 truncate">{email.subject}</div>
                             </td>
                             <td className="py-4 px-4 text-center">
                                <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border inline-block ${
                                   email.safety?.toLowerCase() === "safe" ? "bg-secondary/10 border-secondary/20 text-secondary" : 
                                   email.safety?.toLowerCase() === "suspicious" ? "bg-warning/10 border-warning/20 text-warning" : "bg-danger/10 border-danger/20 text-danger"
                                }`}>
                                   {email.safety}
                                </div>
                             </td>
                             <td className="py-4 px-4 text-right text-xs text-white/30 font-mono">
                                {email.analyzedAt.toLocaleString()}
                             </td>
                          </tr>
                       ))}
                    </tbody>
                 </table>

                 {/* Mobile Card View */}
                 <div className="md:hidden space-y-4">
                    {emailLogs.map((email: EmailLog) => (
                       <div key={email.id} className="glass-light p-4 rounded-2xl border border-white/5 space-y-3">
                          <div className="flex items-center justify-between">
                             <div className="text-xs font-bold text-white truncate max-w-[150px]">{email.employeeEmail}</div>
                             <div className={`px-2 py-0.5 rounded-full text-[8px] font-black uppercase tracking-widest border ${
                                email.safety?.toLowerCase() === "safe" ? "bg-secondary/10 border-secondary/20 text-secondary" : 
                                email.safety?.toLowerCase() === "suspicious" ? "bg-warning/10 border-warning/20 text-warning" : "bg-danger/10 border-danger/20 text-danger"
                             }`}>
                                {email.safety}
                             </div>
                          </div>
                          <div>
                             <div className="text-[9px] text-white/30 uppercase font-black tracking-widest mb-1">Subject</div>
                             <div className="text-xs text-primary font-bold truncate">{email.subject}</div>
                             <div className="text-[9px] text-white/50 truncate mt-0.5">{email.sender}</div>
                          </div>
                          <div className="flex items-center justify-between pt-2 border-t border-white/5">
                             <div className="text-[8px] text-white/20 font-mono italic">ID: {email.id.substring(0, 8)}...</div>
                             <div className="text-[9px] text-white/30 font-mono">{email.analyzedAt.toLocaleString()}</div>
                          </div>
                       </div>
                    ))}
                 </div>
              </div>
           </motion.div>
        </div>
      </div>
    </DashboardLayout>
  );
}
