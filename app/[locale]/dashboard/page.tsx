"use client";

import React, { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import StatsCard from "@/components/StatsCard";
import { Mail, ShieldCheck, AlertCircle, AlertTriangle, TrendingUp, BarChart3, PieChart as PieChartIcon, RefreshCw } from "lucide-react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { collection, query, where, getDocs, orderBy, Timestamp } from "firebase/firestore";
import { db } from "@/services/firebaseConfig";
import { useRouter } from "../../../navigation";

const COLORS = ["#10b981", "#f59e0b", "#ef4444"];

export default function Dashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMobile, setIsMobile] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    safe: 0,
    suspicious: 0,
    dangerous: 0
  });

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);
  const [pieData, setPieData] = useState<any[]>([]);
  const [lineData, setLineData] = useState<any[]>([]);
  const [barData, setBarData] = useState<any[]>([]);

  const fetchDashboardData = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);

    try {
      // Removed orderBy to avoid missing index errors in Firestore
      const q = query(
        collection(db, "emails"),
        where("user_uid", "==", user.uid)
      );
      
      const querySnapshot = await getDocs(q);
      // Sort in-memory instead
      const emails = querySnapshot.docs
        .map(doc => doc.data())
        .sort((a: any, b: any) => {
          const t1 = a.timestamp?.toMillis?.() || a.timestamp?.getTime?.() || 0;
          const t2 = b.timestamp?.toMillis?.() || b.timestamp?.getTime?.() || 0;
          return t2 - t1;
        });

      const total = emails.length;
      const safe = emails.filter(e => e.classification === "Safe").length;
      const suspicious = emails.filter(e => e.classification === "Suspicious").length;
      const dangerous = emails.filter(e => e.classification === "Dangerous").length;

      setStats({ total, safe, suspicious, dangerous });

      // Pie Chart Data
      setPieData([
        { name: "Safe", value: safe },
        { name: "Suspicious", value: suspicious },
        { name: "Dangerous", value: dangerous },
      ].filter(d => d.value > 0));

      // Line Chart Data (Last 7 days scan activity)
      const last7Days = [...Array(7)].map((_, i) => {
        const d = new Date();
        d.setDate(d.getDate() - i);
        return d.toLocaleDateString('en-US', { weekday: 'short' });
      }).reverse();

      const activityMap: any = {};
      last7Days.forEach(day => activityMap[day] = 0);

      emails.forEach((email: any) => {
        const date = email.timestamp?.toDate?.() || (email.timestamp instanceof Date ? email.timestamp : new Date());
        const day = date.toLocaleDateString('en-US', { weekday: 'short' });
        if (activityMap[day] !== undefined) {
          activityMap[day]++;
        }
      });

      setLineData(last7Days.map(day => ({
        name: day,
        scans: activityMap[day]
      })));

      // Bar Chart Data (Placeholder for platforms since we only have Gmail for now)
      setBarData([
        { name: "Gmail", safe: safe, threat: suspicious + dangerous },
        { name: "Outlook", safe: 0, threat: 0 },
        { name: "Direct", safe: 0, threat: 0 },
      ]);

    } catch (err: any) {
      console.error("Error fetching dashboard data:", err);
      setError(err.message || "Failed to load security data.");
    } finally {
      setLoading(false);
    }
  };

  const [lastUpdated, setLastUpdated] = useState<string>("");

  useEffect(() => {
    fetchDashboardData();
    // Auto-refresh dashboard every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 30000);
    return () => clearInterval(interval);
  }, [user]);

  useEffect(() => {
    if (!loading) {
      setLastUpdated(new Date().toLocaleTimeString());
    }
  }, [loading]);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <RefreshCw className="w-12 h-12 text-primary animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
          <AlertCircle className="w-16 h-16 text-danger" />
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">Error Loading Dashboard</h2>
            <p className="text-white/50">{error}</p>
          </div>
          <button 
            onClick={fetchDashboardData}
            className="px-8 py-3 bg-primary text-background font-bold rounded-2xl hover:neon-glow-cyan transition-all"
          >
            Retry Fetch
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8 md:space-y-12">
        <header className="space-y-2">
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">System <span className="text-primary">Overview</span></h1>
          <p className="text-white/50 text-base md:text-lg">Real-time security analytics and threat monitoring based on your inbox.</p>
        </header>

        {/* Stats Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          <StatsCard 
             title="Emails Scanned" 
             value={stats.total.toLocaleString()} 
             icon={Mail} 
             color="bg-primary" 
          />
          <StatsCard 
             title="Safe Emails" 
             value={stats.safe.toLocaleString()} 
             icon={ShieldCheck} 
             color="bg-secondary" 
          />
          <StatsCard 
             title="Suspicious" 
             value={stats.suspicious.toLocaleString()} 
             icon={AlertTriangle} 
             color="bg-warning" 
          />
          <StatsCard 
             title="Dangerous" 
             value={stats.dangerous.toLocaleString()} 
             icon={AlertCircle} 
             color="bg-danger" 
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 md:space-y-8"
          >
            <div className="flex items-center justify-between">
               <h3 className="text-lg md:text-xl font-bold flex items-center space-x-3">
                  <TrendingUp className="w-5 h-5 text-primary" />
                  <span>Weekly Scan Activity</span>
               </h3>
            </div>
            <div className="h-[250px] md:h-[300px] w-full">
               <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={lineData}>
                     <defs>
                        <linearGradient id="colorScans" x1="0" y1="0" x2="0" y2="1">
                           <stop offset="5%" stopColor="#00ffff" stopOpacity={0.3}/>
                           <stop offset="95%" stopColor="#00ffff" stopOpacity={0}/>
                        </linearGradient>
                     </defs>
                     <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                     <XAxis dataKey="name" stroke="#ffffff50" axisLine={false} tickLine={false} />
                     <YAxis stroke="#ffffff50" axisLine={false} tickLine={false} />
                     <Tooltip 
                        contentStyle={{ backgroundColor: "#12121a", borderColor: "#ffffff10", borderRadius: "16px" }} 
                        itemStyle={{ color: "#00ffff" }}
                     />
                     <Area type="monotone" dataKey="scans" stroke="#00ffff" fillOpacity={1} fill="url(#colorScans)" strokeWidth={3} />
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
                  <PieChartIcon className="w-5 h-5 text-accent" />
                  <span>Threat Distribution</span>
               </h3>
            </div>
            <div className="h-[250px] md:h-[300px] w-full">
               <ResponsiveContainer width="100%" height="100%">
                  {pieData.length > 0 ? (
                    <PieChart>
                       <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={isMobile ? 60 : 80}
                          outerRadius={isMobile ? 80 : 100}
                          paddingAngle={5}
                          dataKey="value"
                       >
                          {pieData.map((entry, index) => (
                             <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length] || "#8884d8"} />
                          ))}
                       </Pie>
                       <Tooltip 
                          contentStyle={{ backgroundColor: "#12121a", borderColor: "#ffffff10", borderRadius: "16px" }} 
                          itemStyle={{ color: "#ffffff" }}
                       />
                       <Legend verticalAlign="bottom" height={36}/>
                    </PieChart>
                  ) : (
                    <div className="h-full flex items-center justify-center text-white/20 font-bold uppercase tracking-widest">No Threat Data Available</div>
                  )}
               </ResponsiveContainer>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 md:space-y-8 lg:col-span-2"
          >
            <div className="flex items-center justify-between">
               <h3 className="text-lg md:text-xl font-bold flex items-center space-x-3">
                  <BarChart3 className="w-5 h-5 text-secondary" />
                  <span>Email Classification by Platform</span>
               </h3>
            </div>
            <div className="h-[250px] md:h-[300px] w-full">
               <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barData}>
                     <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                     <XAxis dataKey="name" stroke="#ffffff50" axisLine={false} tickLine={false} />
                     <YAxis stroke="#ffffff50" axisLine={false} tickLine={false} />
                     <Tooltip 
                        contentStyle={{ backgroundColor: "#12121a", borderColor: "#ffffff10", borderRadius: "16px" }} 
                     />
                     <Legend />
                     <Bar dataKey="safe" fill="#10b981" radius={[10, 10, 0, 0]} />
                     <Bar dataKey="threat" fill="#ef4444" radius={[10, 10, 0, 0]} />
                  </BarChart>
               </ResponsiveContainer>
            </div>
          </motion.div>
        </div>
      </div>
    </DashboardLayout>
  );
}
