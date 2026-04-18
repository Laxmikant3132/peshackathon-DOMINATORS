"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldAlert, Mail, AlertTriangle, CheckCircle2, XCircle, Reply, Flag, Trophy, Target, Sparkles, Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { saveUserAction } from "@/services/firebaseService";

const trainingEmails = [
  {
    id: 1,
    sender: "Microsoft Support <support@microsft-office-365.online>",
    subject: "Action Required: Your password expires in 2 hours",
    body: "Dear User, your account password is set to expire in 2 hours. Click the link below to verify your current credentials and extend your password life for another 90 days. Failure to comply will result in immediate account lockout.",
    link: "http://verify-microsoft-login.net/secure-auth",
    indicators: ["Sender Mismatch", "Urgent Language", "Suspicious URL"]
  },
  {
    id: 2,
    sender: "Internal Payroll <payroll@humanfirewall.ai>",
    subject: "Q3 Bonus Structure Update",
    body: "Hi Team, please find the updated Q3 bonus calculation spreadsheet attached for your review. Let us know if you have any questions before the processing deadline next Friday.",
    link: "View bonus_structure.pdf",
    indicators: []
  }
];

export default function TrainingSimulator() {
  const [emails, setEmails] = useState<any[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [showFeedback, setShowFeedback] = useState(false);
  const [userAction, setUserAction] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [loading, setLoading] = useState(true);
  const { profile } = useAuth();

  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/training/scenarios");
        if (response.ok) {
          const data = await response.json();
          setEmails(data.length > 0 ? data : trainingEmails);
        } else {
          setEmails(trainingEmails);
        }
      } catch (err) {
        console.error("Failed to fetch scenarios, using defaults:", err);
        setEmails(trainingEmails);
      } finally {
        setLoading(false);
      }
    };
    fetchScenarios();
  }, []);

  const handleAction = async (action: string) => {
    setUserAction(action);
    setShowFeedback(true);
    
    const isPhishing = emails[currentStep]?.indicators.length > 0;
    const isCorrect = (action === "Report Phishing" && isPhishing) || (action === "Mark Safe" && !isPhishing);
    
    if (isCorrect) setScore(score + 100);

    if (profile && emails[currentStep]) {
      await saveUserAction(profile.uid, {
        trainingId: emails[currentStep].id,
        action,
        isCorrect,
        timestamp: new Date()
      });
    }
  };

  const nextQuestion = () => {
    if (currentStep < emails.length - 1) {
      setCurrentStep(currentStep + 1);
      setShowFeedback(false);
      setUserAction(null);
    } else {
      // Completed simulation
      alert(`Simulation completed! Total Score: ${score}`);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="w-12 h-12 text-primary animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  const currentEmail = emails[currentStep];

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto space-y-12">
        <header className="flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left">
          <div className="space-y-1">
             <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-[10px] font-bold tracking-widest text-accent uppercase mb-2 mx-auto md:mx-0">
                <Target className="w-3 h-3" />
                <span>Security Awareness Training</span>
             </div>
             <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">Training <span className="text-primary">Simulator</span></h1>
             <p className="text-white/50 text-base md:text-lg">Test your ability to identify and report phishing threats.</p>
          </div>
          
          <div className="flex items-center space-x-4 w-full md:w-auto justify-center">
             <div className="glass p-4 md:p-6 rounded-2xl md:rounded-3xl border-primary/20 flex flex-col items-center min-w-[100px] md:min-w-[120px] flex-1 md:flex-none">
                <span className="text-[10px] md:text-xs font-bold text-white/50 uppercase tracking-widest">Score</span>
                <span className="text-2xl md:text-3xl font-black text-primary">{score}</span>
             </div>
             <div className="glass p-4 md:p-6 rounded-2xl md:rounded-3xl border-accent/20 flex flex-col items-center min-w-[100px] md:min-w-[120px] flex-1 md:flex-none">
                <span className="text-[10px] md:text-xs font-bold text-white/50 uppercase tracking-widest">Rank</span>
                <span className="text-2xl md:text-3xl font-black text-accent">Lvl 1</span>
             </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
           <div className="lg:col-span-2 space-y-6">
              <motion.div 
                 key={currentStep}
                 initial={{ opacity: 0, x: -20 }}
                 animate={{ opacity: 1, x: 0 }}
                 className="glass rounded-[32px] md:rounded-[40px] border-white/5 overflow-hidden flex flex-col min-h-[400px] md:min-h-[500px] shadow-2xl relative"
              >
                 <div className="p-6 md:p-8 border-b border-white/5 bg-white/5 space-y-4">
                    <div className="flex items-center space-x-4">
                       <div className="w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl bg-white/5 flex items-center justify-center p-0.5 border border-white/10">
                          <Mail className="w-5 h-5 md:w-6 md:h-6 text-primary" />
                       </div>
                       <div className="min-w-0">
                          <h4 className="font-bold text-white text-sm md:text-base truncate">{currentEmail?.sender}</h4>
                          <p className="text-[10px] text-white/40 uppercase tracking-widest font-black">To: me@humanfirewall.ai</p>
                       </div>
                    </div>
                    <h2 className="text-xl md:text-2xl font-black italic tracking-tight text-primary leading-tight">Subject: {currentEmail?.subject}</h2>
                 </div>

                 <div className="p-6 md:p-10 flex-1 text-white/70 leading-relaxed text-base md:text-lg space-y-6">
                    <p>{currentEmail?.body}</p>
                    {currentEmail?.link && (
                       <a href="#" className="inline-block p-4 rounded-xl md:rounded-2xl bg-primary/10 border border-primary/20 text-primary font-bold hover:bg-primary/20 transition-all text-sm md:text-base break-words w-full md:w-auto text-center">
                          {currentEmail.link}
                       </a>
                    )}
                 </div>

                 <div className="p-6 md:p-8 bg-white/5 border-t border-white/5 grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4">
                    <button 
                       onClick={() => handleAction("Mark Safe")}
                       disabled={showFeedback}
                       className="py-3 md:py-4 rounded-xl md:rounded-2xl bg-secondary/10 border border-secondary/20 text-secondary font-bold hover:bg-secondary/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 text-sm md:text-base"
                    >
                       <CheckCircle2 className="w-4 h-4 md:w-5 md:h-5" />
                       <span>Mark Safe</span>
                    </button>
                    <button 
                       onClick={() => handleAction("Report Phishing")}
                       disabled={showFeedback}
                       className="py-3 md:py-4 rounded-xl md:rounded-2xl bg-danger/10 border border-danger/20 text-danger font-bold hover:bg-danger/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 shadow-[0_0_20px_rgba(239,68,68,0.1)] text-sm md:text-base"
                    >
                       <Flag className="w-4 h-4 md:w-5 md:h-5" />
                       <span>Report Phishing</span>
                    </button>
                    <button 
                       onClick={() => handleAction("Reply")}
                       disabled={showFeedback}
                       className="py-3 md:py-4 rounded-xl md:rounded-2xl bg-accent/10 border border-accent/20 text-accent font-bold hover:bg-accent/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 text-sm md:text-base"
                    >
                       <Reply className="w-4 h-4 md:w-5 md:h-5" />
                       <span>Reply</span>
                    </button>
                 </div>
              </motion.div>
           </div>

           <div className="space-y-6">
              <AnimatePresence>
                 {showFeedback && (
                    <motion.div 
                       initial={{ opacity: 0, scale: 0.9 }}
                       animate={{ opacity: 1, scale: 1 }}
                       className="glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 md:space-y-8 relative overflow-hidden"
                    >
                       {/* Result Icon background decoration */}
                       <div className={`absolute -top-10 -right-10 w-40 h-40 rounded-full blur-3xl opacity-20 ${
                          (userAction === "Report Phishing" && currentEmail?.indicators.length! > 0) || (userAction === "Mark Safe" && currentEmail?.indicators.length === 0)
                          ? "bg-secondary" : "bg-danger"
                       }`} />

                       <div className="flex flex-col items-center text-center space-y-4 relative z-10">
                          <div className={`p-5 md:p-6 rounded-[24px] md:rounded-[32px] ${
                             (userAction === "Report Phishing" && currentEmail?.indicators.length! > 0) || (userAction === "Mark Safe" && currentEmail?.indicators.length === 0)
                             ? "bg-secondary/20 text-secondary" : "bg-danger/20 text-danger"
                          }`}>
                             {(userAction === "Report Phishing" && currentEmail?.indicators.length! > 0) || (userAction === "Mark Safe" && currentEmail?.indicators.length === 0) 
                                ? <Trophy className="w-12 h-12 md:w-16 md:h-16" /> : <ShieldAlert className="w-12 h-12 md:w-16 md:h-16" />}
                          </div>
                          <h3 className={`text-2xl md:text-3xl font-black uppercase tracking-tighter ${
                             (userAction === "Report Phishing" && currentEmail?.indicators.length! > 0) || (userAction === "Mark Safe" && currentEmail?.indicators.length === 0)
                             ? "text-secondary" : "text-danger"
                          }`}>
                             {(userAction === "Report Phishing" && currentEmail?.indicators.length! > 0) || (userAction === "Mark Safe" && currentEmail?.indicators.length === 0)
                                ? "Success!" : "Security Failure"}
                          </h3>
                          <p className="text-white/70 text-base md:text-lg">
                             {(userAction === "Report Phishing" && currentEmail?.indicators.length! > 0) || (userAction === "Mark Safe" && currentEmail?.indicators.length === 0)
                                ? "Excellent identification skills! You spotted the threat vectors correctly."
                                : "You missed critical indicators. Let&apos;s analyze what went wrong."}
                          </p>
                       </div>

                       <div className="space-y-4 relative z-10">
                          <h4 className="font-bold text-[10px] uppercase tracking-widest text-white/30">Identified Indicators</h4>
                          <div className="flex flex-wrap gap-2">
                             {currentEmail?.indicators.length! > 0 ? (currentEmail?.indicators as string[]).map((ind: string) => (
                                <span key={ind} className="px-3 md:px-4 py-1.5 md:py-2 bg-danger/10 border border-danger/20 rounded-xl text-[10px] md:text-xs font-bold text-danger">{ind}</span>
                             )) : (
                                <span className="px-3 md:px-4 py-1.5 md:py-2 bg-secondary/10 border border-secondary/20 rounded-xl text-[10px] md:text-xs font-bold text-secondary">Verified Safe Content</span>
                             )}
                          </div>
                       </div>

                       <button 
                          onClick={nextQuestion}
                          className="w-full py-4 md:py-5 bg-white text-background font-black rounded-2xl md:rounded-3xl hover:bg-primary hover:text-background transition-all text-sm md:text-base"
                       >
                          Proceed to Next Simulation
                       </button>
                    </motion.div>
                 )}

                 {!showFeedback && (
                    <div className="glass p-6 md:p-8 rounded-[32px] md:rounded-[40px] border-white/5 space-y-6 text-center">
                       <div className="w-16 h-16 md:w-20 md:h-20 rounded-full bg-primary/10 mx-auto flex items-center justify-center">
                          <AlertTriangle className="w-8 h-8 md:w-10 md:h-10 text-primary animate-pulse" />
                       </div>
                       <div className="space-y-2">
                          <h4 className="text-lg md:text-xl font-bold">Threat Assessment</h4>
                          <p className="text-xs md:text-sm text-white/50">Analyze the email carefully before taking action. Your risk score depends on accuracy.</p>
                       </div>
                    </div>
                 )}
              </AnimatePresence>
           </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
