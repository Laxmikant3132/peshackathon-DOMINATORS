"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import StatsCard from "@/components/StatsCard";
import { 
  Search, 
  ShieldAlert, 
  AlertCircle, 
  ShieldCheck, 
  Loader2, 
  Link2, 
  MessageSquare, 
  UserX, 
  FileText, 
  BarChart3, 
  Trash2, 
  AlertTriangle,
  Zap,
  Info,
  ExternalLink,
  Flag,
  Ban,
  Download
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "../../../navigation";
import { addDoc, collection, Timestamp } from "firebase/firestore";
import { db } from "@/services/firebaseConfig";

export default function AbuseAnalyzer() {
  const [url, setUrl] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { user, profile, loading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push("/login");
      }
    }
  }, [user, profile, authLoading, router]);

  const handleAnalyze = async () => {
    if (!url) return;
    setIsAnalyzing(true);
    setResult(null);
    setError(null);

    try {
      let response = await fetch("/backend-api/analyze-abuse", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      }).catch(() => null);

      if (!response || !response.ok) {
        response = await fetch("http://localhost:8000/api/analyze-abuse", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ url }),
        });
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || "Failed to analyze URL");
      }

      const data = await response.json();
      
      setResult(data);
      setHistory(prev => [{ url, timestamp: new Date().toLocaleString(), threat: data.threat_level }, ...prev].slice(0, 5));

      if (profile) {
        await addDoc(collection(db, "reports"), {
          uid: profile.uid,
          type: "abuse-analysis",
          url,
          harmfulCount: data.harmful_detected,
          threatLevel: data.threat_level,
          timestamp: Timestamp.now()
        });
      }
    } catch (error: any) {
      console.error("Analysis error:", error);
      setError(error.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical": return "text-red-500 bg-red-500/10 border-red-500/20";
      case "high": return "text-orange-500 bg-orange-500/10 border-orange-500/20";
      case "medium": return "text-yellow-500 bg-yellow-500/10 border-yellow-500/20";
      case "low": return "text-blue-500 bg-blue-500/10 border-blue-500/20";
      default: return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
    }
  };

  const generateReport = async () => {
    const element = document.getElementById("evidence-report");
    if (!element) return;

    // Temporarily make the report visible for PDF generation
    element.classList.remove("hidden");
    element.style.display = "block";

    const html2pdf = (await import("html2pdf.js")).default;

    const options: any = {
      margin: [10, 10, 10, 10] as [number, number, number, number],
      filename: `CyberAbuse_Incident_Report_${new Date().toISOString().slice(0,10)}.pdf`,
      image: { type: "jpeg" as const, quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
      pagebreak: { mode: ["avoid-all", "css", "legacy"] }
    };

    await html2pdf().set(options).from(element).save();

    // Hide it again after generation
    element.classList.add("hidden");
    element.style.display = "";
  };

  const [playbookStatus, setPlaybookStatus] = useState<string | null>(null);
  const [showBlockGuide, setShowBlockGuide] = useState(false);
  const [blockedUsersList, setBlockedUsersList] = useState<string[]>([]);

  const handleBlockUsers = () => {
    if (!result) return;
    const offenders = (result.offender_patterns || []).map((o: any) => o.user);
    const abusiveUsers = [...new Set((result.comments || result.results || [])
      .filter((c: any) => c.severity !== "None")
      .map((c: any) => c.user))];
    const allBlocked = [...new Set([...offenders, ...abusiveUsers])] as string[];

    if (allBlocked.length === 0) {
      setPlaybookStatus("No abusive users found to block.");
      setTimeout(() => setPlaybookStatus(null), 3000);
      return;
    }

    setBlockedUsersList(allBlocked);
    setShowBlockGuide(true);
  };

  const handleMassReport = async () => {
    if (!result) return;
    const abusiveComments = (result.comments || result.results || [])
      .filter((c: any) => c.severity !== "None");

    if (abusiveComments.length === 0) {
      setPlaybookStatus("No abusive comments found to report.");
      setTimeout(() => setPlaybookStatus(null), 3000);
      return;
    }

    if (profile) {
      await addDoc(collection(db, "mass_reports"), {
        uid: profile.uid,
        sourceUrl: url,
        reportedComments: abusiveComments.map((c: any) => ({
          user: c.user,
          comment: c.comment,
          type: c.type,
          severity: c.severity
        })),
        totalReported: abusiveComments.length,
        timestamp: Timestamp.now()
      });
    }

    setPlaybookStatus(`🚩 ${abusiveComments.length} comment(s) flagged and evidence stored for reporting.`);
    setTimeout(() => setPlaybookStatus(null), 5000);
  };

  const handleCybercrimePortal = () => {
    window.open("https://cybercrime.gov.in/Webform/Accept.aspx", "_blank");
  };

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-12">
        <header className="text-center space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] font-bold tracking-widest text-primary uppercase">
            <Zap className="w-3 h-3" />
            <span>AI Moderation Engine</span>
          </div>
          <h1 className="text-3xl md:text-5xl font-black tracking-tighter uppercase">
            Online <span className="text-primary">Abuse Analyzer</span>
          </h1>
          <p className="text-white/40 text-base md:text-lg max-w-2xl mx-auto font-medium">
            Detect cyberbullying, harassment, and toxic patterns in real-time using advanced NLP forensics.
          </p>
        </header>

        {/* Input Section */}
        <motion.div 
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           className="glass p-6 md:p-10 rounded-[40px] border-white/5 space-y-8 shadow-2xl relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 p-8 opacity-5">
            <ShieldAlert size={120} />
          </div>
          
          <div className="flex flex-col md:flex-row items-center space-y-4 md:space-y-0 md:space-x-4 relative z-10">
             <div className="relative group flex-1 w-full">
                <Link2 className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-white/30 group-focus-within:text-primary transition-colors" />
                <input
                  type="text"
                  placeholder="Paste YouTube Video URL here..."
                  className="w-full pl-16 pr-6 py-5 md:py-7 bg-white/5 border border-white/10 rounded-[32px] focus:outline-none focus:border-primary/50 transition-all text-base md:text-xl font-medium"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                />
             </div>
             <button
               onClick={handleAnalyze}
               disabled={isAnalyzing || !url}
               className="w-full md:w-auto px-12 py-5 md:py-7 bg-primary text-background font-black rounded-[32px] hover:neon-glow-cyan transition-all disabled:opacity-50 flex items-center justify-center space-x-3 text-base md:text-xl uppercase tracking-widest"
             >
               {isAnalyzing ? (
                 <>
                   <Loader2 className="w-6 h-6 animate-spin" />
                   <span>Fetching Comments...</span>
                 </>
               ) : (
                 <>
                   <span>Analyze YouTube</span>
                   <Search className="w-6 h-6" />
                 </>
               )}
             </button>
          </div>

          {history.length > 0 && (
            <div className="pt-4 space-y-3">
              <h4 className="text-[10px] font-black uppercase tracking-widest text-white/20">Recent Analysis History</h4>
              <div className="flex flex-wrap gap-3">
                {history.map((h, i) => (
                  <button 
                    key={i} 
                    onClick={() => setUrl(h.url)}
                    className="flex items-center space-x-2 px-4 py-2 glass rounded-xl border-white/5 text-xs hover:bg-white/10 transition-all"
                  >
                    <Info size={12} className="text-primary" />
                    <span className="text-white/50 truncate max-w-[150px]">{h.url}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-4 bg-danger/10 border border-danger/20 rounded-2xl flex items-center space-x-3 text-danger"
            >
              <AlertCircle size={20} />
              <span className="text-sm font-bold uppercase tracking-tight">{error}</span>
            </motion.div>
          )}
        </motion.div>

        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-8 print:block"
            >
              {/* Stats Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatsCard title="Total Analyzed" value={(result?.total_comments ?? 0).toString()} icon={MessageSquare} color="bg-blue-500" />
                <StatsCard title="Abuse Detected" value={(result?.harmful_detected ?? 0).toString()} icon={AlertTriangle} color="bg-red-500" />
                <StatsCard title="Repeat Offenders" value={(result?.repeat_offenders_found ?? 0).toString()} icon={UserX} color="bg-orange-500" />
                <StatsCard title="Safety Score" value={`${result?.safety_score ?? 100}%`} icon={ShieldCheck} color="bg-emerald-500" />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Table */}
                <div className="lg:col-span-2 glass rounded-[40px] p-8 border-white/5 space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold flex items-center space-x-3">
                      <BarChart3 className="text-primary" />
                      <span>Analysis Forensic Stream</span>
                    </h3>
                    <button 
                      onClick={generateReport}
                      className="flex items-center space-x-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-xs font-bold transition-all border border-white/10"
                    >
                      <Download size={14} />
                      <span>EXPORT PDF</span>
                    </button>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="text-[10px] font-black uppercase tracking-[0.2em] text-white/20 border-b border-white/5">
                          <th className="pb-4 px-4">User Identity</th>
                          <th className="pb-4 px-4">Forensic Comment</th>
                          <th className="pb-4 px-4 text-center">Threat Type</th>
                          <th className="pb-4 px-4 text-right">Severity</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/[0.03]">
                        {(result.comments || result.results || []).map((c: any) => (
                          <tr key={c.id} className="group hover:bg-white/[0.02] transition-all">
                            <td className="py-5 px-4">
                              <div className="flex items-center space-x-3">
                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs ${c.is_repeat_offender ? 'bg-red-500/20 text-red-500' : 'bg-white/5 text-white/50'}`}>
                                  {c.user.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                  <div className="text-sm font-bold flex items-center space-x-2">
                                    <span>{c.user}</span>
                                    {c.is_repeat_offender && <AlertCircle size={12} className="text-red-500 animate-pulse" />}
                                  </div>
                                  <div className="text-[9px] text-white/20 uppercase font-bold tracking-tighter">ID: {c.id.substring(0,8)}</div>
                                </div>
                              </div>
                            </td>
                            <td className="py-5 px-4 max-w-xs">
                              <p className="text-sm text-white/70 italic leading-relaxed">&quot;{c.comment}&quot;</p>
                            </td>
                            <td className="py-5 px-4 text-center">
                              <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded-lg bg-white/5 text-white/40 border border-white/5">
                                {c.type}
                              </span>
                            </td>
                            <td className="py-5 px-4 text-right">
                              <div className={`inline-block px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${getSeverityColor(c.severity)}`}>
                                {c.severity}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Sidebar: Offenders & Suggestions */}
                <div className="space-y-8">
                  {/* Repeat Offenders */}
                  <div className="glass rounded-[40px] p-8 border-white/5 space-y-6">
                    <h3 className="text-lg font-bold flex items-center space-x-3">
                      <UserX className="text-red-500" />
                      <span>Repeat Offenders</span>
                    </h3>
                    <div className="space-y-4">
                      {(result.offender_patterns || []).map((off: any, i: number) => (
                        <div key={i} className="p-4 rounded-3xl bg-red-500/5 border border-red-500/10 space-y-3 group hover:border-red-500/30 transition-all">
                          <div className="flex justify-between items-start">
                            <span className="font-bold text-red-500 text-sm">{off.user}</span>
                            <span className="text-[10px] bg-red-500 text-white px-2 py-0.5 rounded-full font-black uppercase">{off.count} Hits</span>
                          </div>
                          <div className="space-y-1">
                            <p className="text-xs font-bold text-white/80 uppercase tracking-tighter">{off.pattern}</p>
                            <p className="text-[10px] text-white/40 italic">{off.behavior}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Preventive Suggestions */}
                  <div className="glass rounded-[40px] p-8 border-white/5 space-y-6">
                    <h3 className="text-lg font-bold flex items-center space-x-3 text-primary">
                      <ShieldCheck />
                      <span>Security Playbook</span>
                    </h3>

                    {playbookStatus && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="p-4 bg-primary/10 border border-primary/20 rounded-2xl text-xs font-bold text-primary"
                      >
                        {playbookStatus}
                      </motion.div>
                    )}

                    <div className="space-y-3">
                      <button onClick={handleBlockUsers} className="w-full flex items-center space-x-4 p-4 bg-white/5 rounded-3xl border border-white/5 hover:border-red-500/30 hover:bg-red-500/5 transition-all text-left group">
                        <div className="p-2 rounded-xl bg-white/5 group-hover:text-red-500">
                          <Ban size={18} />
                        </div>
                        <div>
                          <div className="text-xs font-bold text-white">Block Targeted Users</div>
                          <div className="text-[10px] text-white/30">Instantly restrict interaction access.</div>
                        </div>
                      </button>


                      <button onClick={generateReport} className="w-full flex items-center space-x-4 p-4 bg-white/5 rounded-3xl border border-white/5 hover:border-primary/20 hover:bg-primary/5 transition-all text-left group">
                        <div className="p-2 rounded-xl bg-white/5 group-hover:text-primary">
                          <FileText size={18} />
                        </div>
                        <div>
                          <div className="text-xs font-bold text-white">Generate Incident PDF</div>
                          <div className="text-[10px] text-white/30">Official documentation for legal use.</div>
                        </div>
                      </button>

                      <button onClick={handleCybercrimePortal} className="w-full flex items-center space-x-4 p-4 bg-white/5 rounded-3xl border border-white/5 hover:border-emerald-500/30 hover:bg-emerald-500/5 transition-all text-left group">
                        <div className="p-2 rounded-xl bg-white/5 group-hover:text-emerald-500">
                          <ExternalLink size={18} />
                        </div>
                        <div>
                          <div className="text-xs font-bold text-white">Cybercrime Portal</div>
                          <div className="text-[10px] text-white/30">Escalate to national authorities.</div>
                        </div>
                      </button>
                    </div>
                  </div>

                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {/* Evidence Report Overlay (Hidden by default, used for print) */}
      <div id="evidence-report" className="hidden print:block p-12 bg-white text-black min-h-screen">
        <div className="border-b-4 border-black pb-8 mb-8 flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-black uppercase tracking-tighter">Cyberbullying Incident Report</h1>
            <p className="text-gray-500 font-mono mt-2 uppercase text-xs">Generated by Human Firewall AI Forensics Engine</p>
          </div>
          <div className="text-right">
             <p className="font-bold uppercase text-xs">Report ID: {Math.random().toString(36).substring(7).toUpperCase()}</p>
             <p className="font-mono text-[10px]">{new Date().toISOString()}</p>
          </div>
        </div>

        {result && (
          <div className="space-y-8">
            <div className="grid grid-cols-2 gap-8">
              <div className="p-6 bg-gray-100 rounded-2xl">
                 <h2 className="font-black uppercase text-xs mb-4 text-gray-500">Source Investigation</h2>
                 <p className="font-bold text-lg break-all">{result?.url || url}</p>
              </div>
              <div className="p-6 bg-gray-100 rounded-2xl">
                 <h2 className="font-black uppercase text-xs mb-4 text-gray-500">Threat Assessment</h2>
                 <div className="flex items-center space-x-4">
                    <span className="text-4xl font-black">{result?.threat_level || "Unknown"}</span>
                    <span className="text-gray-400">/ 100% confidence</span>
                 </div>
              </div>
            </div>

            <div className="space-y-4">
              <h2 className="font-black uppercase text-sm border-b pb-2">Abuse Evidence Log</h2>
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-200 text-[10px] font-black uppercase">
                    <th className="p-3 border">Timestamp</th>
                    <th className="p-3 border">Username</th>
                    <th className="p-3 border">Comment Content</th>
                    <th className="p-3 border">Classification</th>
                  </tr>
                </thead>
                <tbody>
                  {(result.comments || result.results || []).map((c: any, i: number) => (
                    <tr key={i} className="text-xs">
                      <td className="p-3 border font-mono">{c.timestamp.substring(11,19)}</td>
                      <td className="p-3 border font-bold">{c.user}</td>
                      <td className="p-3 border italic">&quot;{c.comment}&quot;</td>
                      <td className="p-3 border uppercase font-black text-[10px]">{c.type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pt-12 border-t mt-12 text-center text-[10px] text-gray-400 uppercase font-mono">
              This document is generated for forensic evidence collection purposes.
              All classifications are performed by AI models and should be verified by legal authorities.
            </div>
          </div>
        )}
      </div>

      {/* Block Users Guide Modal */}
      <AnimatePresence>
        {showBlockGuide && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-6 bg-background/80 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="w-full max-w-2xl glass rounded-[32px] md:rounded-[40px] border-white/10 overflow-hidden flex flex-col max-h-[90vh] shadow-2xl"
            >
              <div className="p-6 md:p-8 border-b border-white/5 flex items-start justify-between bg-red-500/5">
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-xl bg-red-500/10 border border-red-500/20">
                      <Ban className="w-6 h-6 text-red-500" />
                    </div>
                    <h2 className="text-xl md:text-2xl font-bold text-white">Block Abusive Users on YouTube</h2>
                  </div>
                  <p className="text-xs text-white/40">Follow these steps to block each flagged user from your channel.</p>
                </div>
                <button onClick={() => setShowBlockGuide(false)} className="p-2 hover:bg-white/10 rounded-xl transition-all">
                  <AlertCircle className="w-5 h-5 rotate-45" />
                </button>
              </div>

              <div className="p-6 md:p-8 overflow-y-auto space-y-6">
                {/* Detected Users */}
                <div className="space-y-3">
                  <h3 className="text-[10px] font-black uppercase tracking-widest text-red-500">Flagged Users ({blockedUsersList.length})</h3>
                  <div className="flex flex-wrap gap-2">
                    {blockedUsersList.map((user, i) => (
                      <span key={i} className="px-3 py-1.5 bg-red-500/10 border border-red-500/20 text-red-500 rounded-full text-xs font-bold">
                        @{user}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Steps */}
                <div className="space-y-4">
                  <h3 className="text-[10px] font-black uppercase tracking-widest text-white/30">Steps to Block a User on YouTube</h3>
                  {[
                    { step: 1, title: "Go to the Video", desc: "Open the YouTube video using the link provided below." },
                    { step: 2, title: "Find the Abusive Comment", desc: "Scroll through the comments section and locate the comment from the flagged user." },
                    { step: 3, title: "Click the Three-Dot Menu", desc: "Hover over the abusive comment and click the ⋮ (three dots) icon on the right side." },
                    { step: 4, title: "Select 'Report'", desc: "Click 'Report' from the dropdown menu and choose the appropriate reason (e.g., Harassment, Hate Speech)." },
                    { step: 5, title: "Block the User", desc: "Click on the user's profile picture → Go to their channel → Click the Flag icon → Select 'Block User'." },
                    { step: 6, title: "Hide from Your Channel", desc: "If you're the channel owner, go to YouTube Studio → Settings → Community → Hidden Users, and add their username." }
                  ].map((item) => (
                    <div key={item.step} className="flex items-start space-x-4 p-4 bg-white/[0.03] rounded-2xl border border-white/5">
                      <div className="w-8 h-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-black text-sm flex-shrink-0">
                        {item.step}
                      </div>
                      <div>
                        <div className="text-sm font-bold text-white">{item.title}</div>
                        <div className="text-xs text-white/40 mt-0.5">{item.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Video Link */}
                <div className="p-5 bg-primary/5 border border-primary/20 rounded-2xl space-y-3">
                  <h3 className="text-[10px] font-black uppercase tracking-widest text-primary">Go to the Analyzed Video</h3>
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-3 text-primary hover:underline break-all"
                  >
                    <ExternalLink className="w-5 h-5 flex-shrink-0" />
                    <span className="text-sm font-bold">{url}</span>
                  </a>
                </div>
              </div>

              <div className="p-6 md:p-8 border-t border-white/5 bg-white/5 flex justify-end gap-3">
                <button
                  onClick={() => setShowBlockGuide(false)}
                  className="px-6 py-3 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition-all font-bold text-sm"
                >
                  Close
                </button>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-3 bg-primary text-background rounded-2xl hover:scale-105 transition-all font-bold text-sm shadow-[0_0_20px_rgba(0,255,255,0.2)]"
                >
                  Open YouTube Video
                </a>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <style jsx global>{`
        @media print {
          body * {
            visibility: hidden;
          }
          #evidence-report, #evidence-report * {
            visibility: visible;
          }
          #evidence-report {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
          }
        }
      `}</style>
    </DashboardLayout>
  );
}
