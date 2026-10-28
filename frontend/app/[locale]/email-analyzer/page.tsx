"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Mail, ShieldAlert, AlertCircle, ShieldCheck, ArrowRight, Loader2, Sparkles } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "../../../navigation";
import { saveEmailAnalysis } from "@/services/firebaseService";

export default function EmailAnalyzer() {
  const [emailContent, setEmailContent] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
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

  const handleAnalyze = async () => {
    if (!emailContent) return;
    setIsAnalyzing(true);
    setResult(null);

    try {
      let response = await fetch("/backend-api/classify-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ emailBody: emailContent }),
      }).catch(() => null);

      if (!response || !response.ok) {
        response = await fetch("https://humanfirewall-backend.onrender.com/api/classify-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ emailBody: emailContent }),
        });
      }

      if (!response || !response.ok) throw new Error("Backend connection failed");
      const data = await response.json();
      
      const analysisResult = {
        classification: data.safety === "safe" ? "Safe" : data.safety === "suspicious" ? "Suspicious" : "Dangerous",
        confidence: Math.round(data.confidence * 100),
        indicators: data.indicators || [],
        reason: data.reason
      };

      if (profile) {
        await saveEmailAnalysis(profile.uid, analysisResult);
      }
      
      setResult(analysisResult);
    } catch (err) {
      console.error("Analysis error:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-12">
        <header className="text-center space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] font-bold tracking-widest text-primary uppercase">
            <Sparkles className="w-3 h-3" />
            <span>AI Neural Analysis</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">Message <span className="text-primary">Analyzer</span></h1>
          <p className="text-white/50 text-base md:text-lg">Social engineering detection for SMS, WhatsApp, or Emails.</p>
        </header>

        <motion.div 
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           className="glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6"
        >
          <div className="space-y-4">
             <label className="text-sm font-bold text-white/50 uppercase tracking-widest px-2">Message Content</label>
             <textarea
               className="w-full h-64 bg-white/5 border border-white/10 rounded-3xl p-6 focus:outline-none focus:border-primary/30 transition-all resize-none text-white/80"
               placeholder="Paste the message content here for deep neural analysis..."
               value={emailContent}
               onChange={(e) => setEmailContent(e.target.value)}
             />
          </div>

          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing || !emailContent}
            className="w-full py-5 bg-primary text-background font-bold rounded-[20px] hover:neon-glow-cyan transition-all disabled:opacity-50 flex items-center justify-center space-x-3 text-lg"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-6 h-6 animate-spin" />
                <span>AI is scanning content...</span>
              </>
            ) : (
              <>
                <Search className="w-6 h-6" />
                <span>Analyze for Threats</span>
              </>
            )}
          </button>
        </motion.div>

        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`p-6 md:p-8 rounded-[32px] md:rounded-[40px] border relative overflow-hidden ${
                result.classification === "Safe" 
                ? "bg-secondary/5 border-secondary/20" 
                : result.classification === "Suspicious" 
                ? "bg-warning/5 border-warning/20" 
                : "bg-danger/5 border-danger/20"
              }`}
            >
              <div className="flex flex-col md:flex-row items-center justify-between gap-6 md:gap-8">
                <div className="flex flex-col md:flex-row items-center space-y-4 md:space-y-0 md:space-x-6">
                   <div className={`p-5 rounded-3xl ${
                     result.classification === "Safe" ? "bg-secondary/20 text-secondary" : 
                     result.classification === "Suspicious" ? "bg-warning/20 text-warning" : "bg-danger/20 text-danger"
                   }`}>
                      {result.classification === "Safe" ? <ShieldCheck className="w-12 h-12" /> : <ShieldAlert className="w-12 h-12" />}
                   </div>
                   <div className="space-y-1 text-center md:text-left">
                      <h3 className={`text-2xl md:text-3xl font-black ${
                        result.classification === "Safe" ? "text-secondary" : 
                        result.classification === "Suspicious" ? "text-warning" : "text-danger"
                      }`}>
                         {result.classification}
                      </h3>
                      <p className="text-white/50 font-medium text-sm md:text-base">Confidence Score: <span className="text-white">{result.confidence}%</span></p>
                   </div>
                </div>

                <div className="flex flex-wrap justify-center md:justify-end gap-2 md:gap-3 max-w-sm">
                   {result.indicators.length > 0 ? result.indicators.map((indicator: string) => (
                      <span key={indicator} className="px-4 py-2 bg-white/5 border border-white/10 rounded-full text-xs font-bold flex items-center space-x-2">
                         <AlertCircle className="w-3 h-3 text-danger" />
                         <span>{indicator}</span>
                      </span>
                   )) : (
                      <span className="px-4 py-2 bg-secondary/10 border border-secondary/20 rounded-full text-xs font-bold text-secondary flex items-center space-x-2">
                         <ShieldCheck className="w-3 h-3" />
                         <span>No threats detected</span>
                      </span>
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
