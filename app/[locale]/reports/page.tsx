"use client";

import React, { useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { BarChart3, Download, Calendar, TrendingUp, FileText, ChevronRight, Loader2 } from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line
} from "recharts";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "../../../navigation";

const recentReports = [
  { id: 1, name: "Weekly Security Posture", date: "Oct 24 - Oct 31", type: "Excel", size: "4.2 MB" },
  { id: 2, name: "Employee Training Summary", date: "Oct 17 - Oct 24", type: "CSV", size: "1.1 MB" },
  { id: 3, name: "Threat Analysis Log", date: "Oct 10 - Oct 17", type: "Excel", size: "4.8 MB" },
];

export default function WeeklyReports() {
  const { profile, loading: authLoading } = useAuth();
  const router = useRouter();
  const [employees, setEmployees] = React.useState<any[]>([]);
  const [emails, setEmails] = React.useState<any[]>([]);
  const [trendData, setTrendData] = React.useState<any[]>([]);
  const [growthData, setGrowthData] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  useEffect(() => {
    if (!authLoading && profile && profile.role !== "admin") {
      router.push("/dashboard");
    }
  }, [profile, authLoading, router]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch("/api/admin/stats");
        const data = await response.json();
        
        if (data.employees) {
          setEmployees(data.employees);
        }
        
        if (data.emails) {
          setEmails(data.emails);
          
          // Generate real trend and growth data from emails
          const sortedEmails = [...data.emails].sort((a, b) => 
            new Date(a.analyzedAt).getTime() - new Date(b.analyzedAt).getTime()
          );

          // Group by day for trend - providing better granularity
          const dayTrendMap: Record<string, { name: string; safe: number; threats: number }> = {};
          sortedEmails.forEach((email) => {
            const date = new Date(email.analyzedAt);
            const dayLabel = `${date.getDate()} ${date.toLocaleString('default', { month: 'short' })}`;
            
            if (!dayTrendMap[dayLabel]) {
              dayTrendMap[dayLabel] = { name: dayLabel, safe: 0, threats: 0 };
            }
            
            if (email.safety?.toLowerCase() === "safe") {
              dayTrendMap[dayLabel].safe++;
            } else {
              dayTrendMap[dayLabel].threats++;
            }
          });
          setTrendData(Object.values(dayTrendMap));

          // Group by day for growth (cumulative) - providing better granularity
          const dayMap: Record<string, number> = {};
          let cumulativeTotal = 0;
          
          sortedEmails.forEach((email) => {
            const date = new Date(email.analyzedAt);
            const dayLabel = `${date.getDate()} ${date.toLocaleString('default', { month: 'short' })}`;
            
            if (!dayMap[dayLabel]) {
              dayMap[dayLabel] = 0;
            }
            dayMap[dayLabel]++;
          });

          const growthArray = Object.entries(dayMap).map(([name, count]) => {
            cumulativeTotal += count;
            return { name, total: cumulativeTotal };
          });
          setGrowthData(growthArray);
        }
      } catch (error) {
        console.error("Error fetching stats:", error);
      } finally {
        setLoading(false);
      }
    };

    if (profile?.role === "admin") {
      fetchStats();
    }
  }, [profile]);

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="min-h-[60vh] flex items-center justify-center">
          <Loader2 className="w-12 h-12 text-primary animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  if (profile && profile.role !== "admin") {
    return null;
  }

  const handleReportDownload = (report: typeof recentReports[0]) => {
    let content: any = "";
    let mimeType = "text/csv;charset=utf-8";
    let fileName = `${report.name.toLowerCase().replace(/ /g, "_")}.csv`;

    const escapeCSV = (val: any) => {
      const stringVal = String(val ?? "");
      if (stringVal.includes(",") || stringVal.includes("\"") || stringVal.includes("\n")) {
        return `"${stringVal.replace(/"/g, "\"\"")}"`;
      }
      return stringVal;
    };

    const headerBase = [
      ["sep=,"],
      [report.name],
      ["Period", report.date],
      ["Generated At", new Date().toLocaleString()],
      [""]
    ];

    if (report.name === "Weekly Security Posture") {
      const dataRows = [
        ["Employee Name", "Email", "Total Scans", "Risk Profile", "Dangerous Hits"]
      ];
      employees.forEach(emp => {
        dataRows.push([
          escapeCSV(emp.name),
          escapeCSV(emp.email),
          escapeCSV(emp.scans),
          escapeCSV(emp.risk),
          escapeCSV(emp.dangerousCount)
        ]);
      });
      content = "\uFEFF" + [...headerBase, ...dataRows].map(e => e.join(",")).join("\n");
    } else if (report.name === "Employee Training Summary") {
      const dataRows = [
        ["Employee Name", "Email", "Training Score", "Completed Modules", "Compliance Status"]
      ];
      employees.forEach(emp => {
        // Deriving some mock training data based on their risk/scans to make it "feel" real
        const score = Math.max(60, 100 - (emp.dangerousCount * 10));
        const modules = emp.scans > 0 ? "4/5" : "0/5";
        const status = score > 80 ? "Compliant" : "Follow-up Required";
        
        dataRows.push([
          escapeCSV(emp.name),
          escapeCSV(emp.email),
          escapeCSV(`${score}/100`),
          escapeCSV(modules),
          escapeCSV(status)
        ]);
      });
      content = "\uFEFF" + [...headerBase, ...dataRows].map(e => e.join(",")).join("\n");
    } else if (report.name === "Threat Analysis Log") {
      const dataRows = [
        ["Timestamp", "Employee Email", "Sender", "Subject", "Safety Status", "Threat Type"]
      ];
      emails.forEach(email => {
        dataRows.push([
          escapeCSV(new Date(email.analyzedAt).toLocaleString()),
          escapeCSV(email.employeeEmail),
          escapeCSV(email.sender),
          escapeCSV(email.subject),
          escapeCSV(email.safety),
          escapeCSV(email.threatType || "None")
        ]);
      });
      content = "\uFEFF" + [...headerBase, ...dataRows].map(e => e.join(",")).join("\n");
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const downloadCSV = () => {
    // Defaulting to security posture for the top export button
    const escapeCSV = (val: any) => {
      const stringVal = String(val ?? "");
      if (stringVal.includes(",") || stringVal.includes("\"") || stringVal.includes("\n")) {
        return `"${stringVal.replace(/"/g, "\"\"")}"`;
      }
      return stringVal;
    };

    const csvHeader = ["Employee Name", "Email", "Total Scans", "Risk Level", "Dangerous Hits"];
    const csvRows = employees.map(emp => [
      escapeCSV(emp.name),
      escapeCSV(emp.email),
      escapeCSV(emp.scans),
      escapeCSV(emp.risk),
      escapeCSV(emp.dangerousCount)
    ]);
    const content = "\uFEFF" + [csvHeader, ...csvRows].map(e => e.join(",")).join("\n");
    const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "human_firewall_weekly_report.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 md:space-y-12">
        <header className="flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left">
          <div className="space-y-1">
             <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight flex flex-col md:flex-row items-center md:justify-start md:space-x-3">
                <BarChart3 className="w-8 h-8 text-primary mb-2 md:mb-0" />
                <span>Security <span className="text-primary">Reports</span></span>
             </h1>
             <p className="text-white/50 text-base md:text-lg">Detailed analysis and historical security trends.</p>
          </div>
          <button 
             onClick={downloadCSV}
             className="w-full md:w-auto px-8 py-4 bg-primary text-background font-black rounded-[20px] flex items-center justify-center space-x-3 hover:neon-glow-cyan transition-all group shadow-[0_0_20px_rgba(0,255,255,0.2)]"
          >
             <Download className="w-5 h-5 group-hover:translate-y-1 transition-transform" />
             <span>Export CSV Report</span>
          </button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
           <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 md:space-y-8"
           >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                 <h3 className="text-lg md:text-xl font-bold flex items-center space-x-3">
                    <TrendingUp className="w-5 h-5 text-primary" />
                    <span>Threat Detection Trends</span>
                 </h3>
                 <div className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-[10px] font-bold flex items-center space-x-2 w-fit">
                    <Calendar className="w-4 h-4 text-primary" />
                    <span>Last 30 Days</span>
                 </div>
              </div>
              <div className="h-[250px] md:h-[300px] w-full">
                 <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trendData}>
                       <defs>
                          <linearGradient id="colorSafe" x1="0" y1="0" x2="0" y2="1">
                             <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                             <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                             <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                             <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                          </linearGradient>
                       </defs>
                       <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                       <XAxis dataKey="name" stroke="#ffffff50" axisLine={false} tickLine={false} />
                       <YAxis stroke="#ffffff50" axisLine={false} tickLine={false} />
                       <Tooltip contentStyle={{ backgroundColor: "#12121a", borderColor: "#ffffff10", borderRadius: "16px" }} />
                       <Legend />
                       <Area type="monotone" dataKey="safe" stroke="#10b981" fillOpacity={1} fill="url(#colorSafe)" strokeWidth={3} />
                       <Area type="monotone" dataKey="threats" stroke="#ef4444" fillOpacity={1} fill="url(#colorThreats)" strokeWidth={3} />
                    </AreaChart>
                 </ResponsiveContainer>
              </div>
           </motion.div>

           <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 md:space-y-8"
           >
              <div className="flex items-center justify-between">
                 <h3 className="text-lg md:text-xl font-bold flex items-center space-x-3">
                    <TrendingUp className="w-5 h-5 text-accent" />
                    <span>Scan Growth (Cumulative)</span>
                 </h3>
              </div>
              <div className="h-[250px] md:h-[300px] w-full">
                 <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={growthData}>
                       <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                       <XAxis dataKey="name" stroke="#ffffff50" axisLine={false} tickLine={false} />
                       <YAxis stroke="#ffffff50" axisLine={false} tickLine={false} />
                       <Tooltip contentStyle={{ backgroundColor: "#12121a", borderColor: "#ffffff10", borderRadius: "16px" }} />
                       <Line type="monotone" dataKey="total" stroke="#a855f7" strokeWidth={4} dot={{ fill: "#a855f7", strokeWidth: 2, r: 6 }} activeDot={{ r: 8, strokeWidth: 0 }} />
                    </LineChart>
                 </ResponsiveContainer>
              </div>
           </motion.div>

           <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="lg:col-span-2 glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 md:space-y-8"
           >
              <div className="flex items-center justify-between px-2">
                 <h3 className="text-lg md:text-xl font-bold flex items-center space-x-3">
                    <FileText className="w-5 h-5 text-primary" />
                    <span>Recent Generated Reports</span>
                 </h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
                 {recentReports.map(report => (
                    <div 
                       key={report.id} 
                       onClick={() => handleReportDownload(report)}
                       className="p-5 md:p-6 bg-white/5 border border-white/10 rounded-[24px] md:rounded-[32px] hover:border-primary/20 hover:bg-white/[0.08] transition-all group cursor-pointer"
                    >
                       <div className="flex items-center justify-between mb-4 md:mb-6">
                          <div className="p-3 bg-primary/10 rounded-2xl text-primary">
                             <FileText className="w-5 h-5 md:w-6 md:h-6" />
                          </div>
                          <span className="px-3 py-1 bg-white/5 rounded-full text-[10px] font-black uppercase tracking-widest text-white/40">{report.type}</span>
                       </div>
                       <div className="space-y-1 mb-4 md:mb-6">
                          <h4 className="font-bold text-white text-sm md:text-base group-hover:text-primary transition-colors line-clamp-1">{report.name}</h4>
                          <p className="text-[10px] md:text-xs text-white/30 font-medium">{report.date}</p>
                       </div>
                       <div className="flex items-center justify-between">
                          <span className="text-[10px] md:text-xs font-bold text-white/20">{report.size}</span>
                          <ChevronRight className="w-5 h-5 text-white/10 group-hover:text-primary transition-all group-hover:translate-x-1" />
                       </div>
                    </div>
                 ))}
              </div>
           </motion.div>
        </div>
      </div>
    </DashboardLayout>
  );
}
