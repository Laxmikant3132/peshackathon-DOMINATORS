"use client";

import React, { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { 
  Users, 
  Search, 
  Plus, 
  X, 
  Mail, 
  Building2, 
  Lock, 
  Loader2, 
  MoreVertical,
  ShieldAlert,
  AlertTriangle,
  ShieldCheck,
  Building
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "../../../../navigation";
import { db } from "@/services/firebaseConfig";
import { collection, query, where, onSnapshot, orderBy } from "firebase/firestore";
import { registerEmployee } from "@/services/firebaseService";

export default function EmployeeDirectory() {
  const { profile, loading } = useAuth();
  const router = useRouter();
  const [employees, setEmployees] = useState<any[]>([]);
  const [emailLogs, setEmailLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Form State
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    organization: "",
    password: ""
  });
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState("");

  useEffect(() => {
    if (!loading && profile && profile.role !== "admin") {
      router.push("/dashboard");
    }
  }, [profile, loading, router]);

  useEffect(() => {
    if (!profile || profile.role !== "admin") return;

    setIsLoading(true);

    const employeesQuery = query(collection(db, "users"), where("role", "==", "employee"));
    const unsubscribeEmployees = onSnapshot(employeesQuery, (snapshot) => {
      const empList = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setEmployees(empList);
      setIsLoading(false);
    });

    const logsQuery = query(collection(db, "email_logs"), orderBy("analyzedAt", "desc"));
    const unsubscribeLogs = onSnapshot(logsQuery, (snapshot) => {
      const logs = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setEmailLogs(logs);
    });

    return () => {
      unsubscribeEmployees();
      unsubscribeLogs();
    };
  }, [profile]);

  const handleAddEmployee = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError("");
    try {
      await registerEmployee(
        formData.name,
        formData.email,
        formData.password,
        formData.organization
      );
      setIsModalOpen(false);
      setFormData({ name: "", email: "", organization: "", password: "" });
    } catch (err: any) {
      setFormError(err.message || "Failed to create employee account");
    } finally {
      setFormLoading(false);
    }
  };

  const employeeMetrics = employees.map(emp => {
    const empLogs = emailLogs.filter(log => log.employeeEmail === emp.email);
    const dangerousHits = empLogs.filter(log => log.safety?.toLowerCase() === "dangerous").length;
    
    let riskLevel = "LOW";
    if (dangerousHits >= 4) riskLevel = "HIGH";
    else if (dangerousHits >= 1) riskLevel = "MEDIUM";

    return {
      ...emp,
      scans: empLogs.length,
      dangerousHits,
      riskLevel
    };
  }).filter(emp => 
    emp.name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
    emp.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    emp.organization?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading || isLoading || (profile && profile.role !== "admin")) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="w-12 h-12 text-primary animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-1">
            <h1 className="text-4xl font-extrabold tracking-tight flex items-center space-x-3">
              <Users className="w-8 h-8 text-primary" />
              <span>Employee <span className="text-primary">Directory</span></span>
            </h1>
            <p className="text-white/50 text-lg">Manage and monitor employee security profiles.</p>
          </div>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="px-6 py-3 bg-primary text-background font-black rounded-2xl flex items-center space-x-2 hover:neon-glow-cyan transition-all group shadow-[0_0_20px_rgba(0,255,255,0.2)]"
          >
            <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform" />
            <span>Add New Employee</span>
          </button>
        </header>

        {/* Search and Filters */}
        <div className="glass p-4 rounded-3xl flex items-center space-x-4">
          <div className="relative flex-1 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-primary transition-colors" />
            <input 
              type="text" 
              placeholder="Search employees by name, email or organization..."
              className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/50 transition-all text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Employee List */}
        <div className="glass rounded-[40px] border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-separate border-spacing-0">
              <thead>
                <tr className="bg-white/5 text-white/30 text-[10px] font-black uppercase tracking-widest">
                  <th className="px-8 py-6">Employee</th>
                  <th className="px-6 py-6">Organization</th>
                  <th className="px-6 py-6 text-center">Emails Scanned</th>
                  <th className="px-6 py-6 text-center">Dangerous Emails</th>
                  <th className="px-6 py-6 text-center">Risk Level</th>
                  <th className="px-8 py-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {employeeMetrics.map((emp) => (
                  <tr key={emp.id} className="group hover:bg-white/[0.04] transition-all">
                    <td className="py-6 px-8">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center font-bold text-primary border border-white/10 group-hover:scale-110 transition-transform">
                          {emp.name?.charAt(0)}
                        </div>
                        <div>
                          <div className="text-sm font-bold text-white">{emp.name}</div>
                          <div className="text-xs text-white/30">{emp.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-6 px-6">
                      <div className="flex items-center space-x-2 text-white/70">
                        <Building className="w-4 h-4 text-white/20" />
                        <span className="text-sm font-medium">{emp.organization || "N/A"}</span>
                      </div>
                    </td>
                    <td className="py-6 px-6 text-center">
                      <div className="inline-flex items-center space-x-2 px-3 py-1 bg-white/5 rounded-full border border-white/10">
                        <span className="text-sm font-bold text-primary">{emp.scans}</span>
                      </div>
                    </td>
                    <td className="py-6 px-6 text-center">
                      <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full border ${
                        emp.dangerousHits > 0 ? "bg-danger/10 border-danger/20 text-danger" : "bg-white/5 border-white/10 text-white/30"
                      }`}>
                        <span className="text-sm font-bold">{emp.dangerousHits}</span>
                      </div>
                    </td>
                    <td className="py-6 px-6 text-center">
                      <div className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border inline-block ${
                        emp.riskLevel === "LOW" ? "bg-secondary/10 border-secondary/20 text-secondary" : 
                        emp.riskLevel === "MEDIUM" ? "bg-warning/10 border-warning/20 text-warning" : "bg-danger/10 border-danger/20 text-danger"
                      }`}>
                        {emp.riskLevel}
                      </div>
                    </td>
                    <td className="py-6 px-8 text-right">
                      <button className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-xs font-bold hover:bg-white/10 hover:text-primary transition-all">
                        Profile
                      </button>
                    </td>
                  </tr>
                ))}
                {employeeMetrics.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-20 text-center">
                      <div className="flex flex-col items-center justify-center space-y-4 opacity-30">
                        <Users className="w-16 h-16" />
                        <p className="text-lg font-bold">No employees found</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Add Employee Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsModalOpen(false)}
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-lg glass rounded-[40px] border-white/10 p-8 relative z-10"
            >
              <div className="flex items-center justify-between mb-8">
                <div className="space-y-1">
                  <h3 className="text-2xl font-bold flex items-center space-x-3">
                    <Plus className="w-6 h-6 text-primary" />
                    <span>Add New <span className="text-primary">Employee</span></span>
                  </h3>
                  <p className="text-white/50 text-sm">Create a new secure employee profile.</p>
                </div>
                <button 
                  onClick={() => setIsModalOpen(false)}
                  className="p-3 hover:bg-white/5 rounded-2xl text-white/30 hover:text-white transition-all"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <form onSubmit={handleAddEmployee} className="space-y-6">
                <div className="space-y-4">
                  <div className="relative group">
                    <Users className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-primary transition-colors" />
                    <input 
                      type="text" 
                      required
                      placeholder="Full Name"
                      className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/50 transition-all"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    />
                  </div>
                  
                  <div className="relative group">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-primary transition-colors" />
                    <input 
                      type="email" 
                      required
                      placeholder="Email Address"
                      className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/50 transition-all"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    />
                  </div>

                  <div className="relative group">
                    <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-primary transition-colors" />
                    <input 
                      type="text" 
                      required
                      placeholder="Organization"
                      className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/50 transition-all"
                      value={formData.organization}
                      onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
                    />
                  </div>

                  <div className="relative group">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-primary transition-colors" />
                    <input 
                      type="password" 
                      required
                      placeholder="Password"
                      className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/50 transition-all"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    />
                  </div>
                </div>

                {formError && (
                  <div className="p-4 bg-danger/10 border border-danger/20 rounded-2xl flex items-center space-x-3 text-danger text-sm">
                    <ShieldAlert className="w-5 h-5 flex-shrink-0" />
                    <span>{formError}</span>
                  </div>
                )}

                <button 
                  type="submit"
                  disabled={formLoading}
                  className="w-full py-4 bg-primary text-background font-black rounded-2xl hover:neon-glow-cyan transition-all shadow-[0_0_20px_rgba(0,255,255,0.2)] disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  {formLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Creating Account...</span>
                    </>
                  ) : (
                    <>
                      <Plus className="w-5 h-5" />
                      <span>Add Employee</span>
                    </>
                  )}
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </DashboardLayout>
  );
}
