"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Globe, ShieldAlert, AlertCircle, ShieldCheck, Loader2, Link2, LayoutGrid, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "../../../navigation";
import { addDoc, collection, Timestamp } from "firebase/firestore";
import { db } from "@/services/firebaseConfig";

export default function URLScanner() {
  const [url, setUrl] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const { user, profile, loading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        router.push("/login");
      }
    }
  }, [user, profile, authLoading, router]);

  const handleScan = async () => {
    if (!url) return;
    setIsScanning(true);
    setResult(null);

    try {
      const response = await fetch("https://humanfirewall-backend.onrender.com/api/classify-url", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        throw new Error("Failed to scan URL");
      }

      const data = await response.json();
      
      const scanResult = {
        status: data.safety === "safe" ? "Safe Link" : data.safety === "suspicious" ? "Suspicious Link Detected" : "Phishing Detected",
        confidence: data.confidence,
        domainAge: data.details.domain_age,
        ssl: data.details.ssl_status === "valid" ? "Valid" : "Invalid",
        indicators: data.indicators,
      };

      if (profile) {
        await addDoc(collection(db, "reports"), {
          uid: profile.uid,
          type: "url-scan",
          url,
          ...scanResult,
          timestamp: Timestamp.now()
        });
      }
      
      setResult(scanResult);
    } catch (error) {
      console.error("Scan error:", error);
      // Fallback or error state could be added here, but keeping UI unchanged
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-12">
        <header className="text-center space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-[10px] font-bold tracking-widest text-accent uppercase">
            <Globe className="w-3 h-3" />
            <span>URL Reputation Engine</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">URL <span className="text-primary">Scanner</span></h1>
          <p className="text-white/50 text-base md:text-lg">Real-time analysis of domain reputation and landing page integrity.</p>
        </header>

        <motion.div 
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           className="glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 md:space-y-8 shadow-2xl"
        >
          <div className="flex flex-col md:flex-row items-center space-y-4 md:space-y-0 md:space-x-4">
             <div className="relative group flex-1 w-full">
                <Link2 className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-white/30 group-focus-within:text-primary transition-colors" />
                <input
                  type="text"
                  placeholder="Paste suspicious website URL here..."
                  className="w-full pl-16 pr-6 py-4 md:py-6 bg-white/5 border border-white/10 rounded-[24px] md:rounded-[32px] focus:outline-none focus:border-primary/50 transition-all text-base md:text-lg"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                />
             </div>
             <button
               onClick={handleScan}
               disabled={isScanning || !url}
               className="w-full md:w-auto px-12 py-4 md:py-6 bg-primary text-background font-black rounded-[24px] md:rounded-[32px] hover:neon-glow-cyan transition-all disabled:opacity-50 flex items-center justify-center space-x-3 text-base md:text-lg"
             >
               {isScanning ? (
                 <>
                   <Loader2 className="w-6 h-6 animate-spin" />
                   <span>Scanning...</span>
                 </>
               ) : (
                 <>
                   <span>Scan URL</span>
                   <Globe className="w-6 h-6" />
                 </>
               )}
             </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 opacity-50">
             {["HTTPS Check", "Domain Age", "IP Reputation", "Social Engineering"].map(test => (
                <div key={test} className="p-3 glass rounded-2xl text-[10px] font-bold uppercase tracking-widest text-center border-white/5">
                   {test}
                </div>
             ))}
          </div>
        </motion.div>

        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-1 md:grid-cols-3 gap-6"
            >
              <div className={`md:col-span-2 glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 flex flex-col md:flex-row items-center space-y-6 md:space-y-0 md:space-x-8 ${
                 result.status.includes("Detected") ? "border-danger/20 bg-danger/5" : "border-secondary/20 bg-secondary/5"
              }`}>
                 <div className={`p-6 rounded-3xl ${
                    result.status.includes("Detected") ? "bg-danger/20 text-danger" : "bg-secondary/20 text-secondary"
                 }`}>
                    {result.status.includes("Detected") ? <ShieldAlert className="w-12 h-12 md:w-16 md:h-16" /> : <ShieldCheck className="w-12 h-12 md:w-16 md:h-16" />}
                 </div>
                 <div className="space-y-2 text-center md:text-left">
                    <h3 className={`text-2xl md:text-4xl font-black ${
                       result.status.includes("Detected") ? "text-danger" : "text-secondary"
                    }`}>
                       {result.status}
                    </h3>
                    <p className="text-white/50 text-base md:text-lg">AI Confidence: <span className="text-white">{result.confidence}%</span></p>
                 </div>
              </div>

              <div className="glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6">
                 <h4 className="font-bold text-white/50 uppercase tracking-widest text-[10px] md:text-xs">Security Details</h4>
                 <div className="space-y-4">
                    <div className="flex justify-between items-center text-sm">
                       <span className="text-white/50">Domain Age</span>
                       <span className="font-bold">{result.domainAge}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                       <span className="text-white/50">SSL Certificate</span>
                       <span className={`font-bold ${result.ssl === "Valid" ? "text-secondary" : "text-danger"}`}>{result.ssl}</span>
                    </div>
                 </div>
              </div>

              <div className="md:col-span-3 glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6">
                 <h4 className="font-bold text-white/50 uppercase tracking-widest text-[10px] md:text-xs">Threat Indicators</h4>
                 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {result.indicators.length > 0 ? result.indicators.map((indicator: string) => (
                       <div key={indicator} className="p-4 bg-danger/10 border border-danger/20 rounded-2xl flex items-center space-x-3">
                          <AlertCircle className="w-5 h-5 text-danger" />
                          <span className="text-sm font-bold text-danger/80">{indicator}</span>
                       </div>
                    )) : (
                       <div className="col-span-full p-6 bg-secondary/10 border border-secondary/20 rounded-[24px] md:rounded-[32px] flex flex-col md:flex-row items-center justify-center md:space-x-4 text-secondary font-black text-lg md:text-xl text-center md:text-left space-y-4 md:space-y-0">
                          <CheckCircle2 className="w-8 h-8" />
                          <span>No malicious patterns identified for this domain</span>
                       </div>
                    )}
                 </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </DashboardLayout>
  );
}
