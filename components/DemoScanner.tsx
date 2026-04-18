"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ShieldAlert, AlertCircle, CheckCircle, ExternalLink, ShieldCheck } from "lucide-react";

const DemoScanner = () => {
  const [input, setInput] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [showResult, setShowResult] = useState(false);

  const handleScan = () => {
    if (!input) return;
    setIsScanning(true);
    setShowResult(false);
    
    // Simulate API call
    setTimeout(() => {
      setIsScanning(false);
      setShowResult(true);
    }, 2000);
  };

  return (
    <section id="demo" className="py-16 md:py-20 relative">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-3xl mx-auto mb-12 md:mb-16 space-y-4">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight">
            Live Detection <span className="text-primary">Demo</span>
          </h2>
          <p className="text-base md:text-lg text-white/60">
            Paste a suspicious email header, link, or URL to see our AI in action.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <div className="glass rounded-[24px] md:rounded-[32px] overflow-hidden p-6 md:p-8 shadow-2xl relative">
            {/* Decoration */}
            <div className="absolute top-0 right-0 w-[40%] h-[40%] bg-primary/10 blur-[60px] md:blur-[80px] -z-10 pointer-events-none" />
            
            <div className="flex flex-col md:flex-row items-center space-y-4 md:space-y-0 md:space-x-4 mb-6 md:mb-8">
               <div className="flex-1 w-full relative group">
                  <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-white/30 group-focus-within:text-primary transition-colors">
                    <Search className="w-5 h-5" />
                  </div>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Paste suspicious email or URL"
                    className="w-full pl-12 pr-4 py-4 md:py-5 bg-white/5 border border-white/10 rounded-xl md:rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all text-white placeholder-white/30 text-sm md:text-base"
                  />
               </div>
               <button
                 onClick={handleScan}
                 disabled={isScanning || !input}
                 className="w-full md:w-auto px-10 py-4 md:py-5 bg-primary text-background font-bold rounded-xl md:rounded-2xl flex items-center justify-center space-x-2 hover:neon-glow-cyan disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm md:text-base"
               >
                 {isScanning ? (
                   <div className="flex items-center space-x-2">
                     <div className="w-5 h-5 border-4 border-background border-t-transparent rounded-full animate-spin" />
                     <span>Analyzing...</span>
                   </div>
                 ) : (
                   <>
                     <span>Analyze Threat</span>
                     <ExternalLink className="w-5 h-5" />
                   </>
                 )}
               </button>
            </div>

            <AnimatePresence mode="wait">
              {showResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="space-y-6"
                >
                  <div className="p-4 md:p-6 rounded-2xl bg-danger/10 border border-danger/30 flex flex-col md:flex-row items-start md:items-center space-y-4 md:space-y-0 md:space-x-4">
                    <div className="p-3 bg-danger/20 rounded-xl">
                      <ShieldAlert className="w-6 h-6 md:w-8 md:h-8 text-danger" />
                    </div>
                    <div className="flex-1">
                      <h4 className="text-lg md:text-xl font-bold text-danger mb-1 flex flex-col md:flex-row md:items-center gap-2">
                         ⚠ Suspicious Email Detected
                         <span className="w-fit text-[10px] md:text-sm font-normal bg-danger/20 px-3 py-1 rounded-full border border-danger/30 text-white">Confidence: 96%</span>
                      </h4>
                      <p className="text-xs md:text-sm text-white/70">
                        This content contains high-risk elements commonly found in phishing campaigns.
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
                     {[
                       { label: "Suspicious link", icon: AlertCircle, color: "text-danger" },
                       { label: "Urgency language", icon: AlertCircle, color: "text-warning" },
                       { label: "Sender mismatch", icon: AlertCircle, color: "text-danger" }
                     ].map((item, i) => (
                       <div key={i} className="p-3 md:p-4 glass rounded-xl flex items-center space-x-3">
                         <item.icon className="w-4 h-4 md:w-5 md:h-5 text-danger" />
                         <span className="font-medium text-white/80 text-xs md:text-sm">{item.label}</span>
                       </div>
                     ))}
                  </div>

                  <div className="p-4 md:p-6 glass rounded-xl md:rounded-2xl border-white/5 space-y-4">
                     <h5 className="font-bold flex items-center text-primary text-sm md:text-base">
                        <CheckCircle className="w-4 h-4 md:w-5 md:h-5 mr-2" /> 
                        Recommendations
                     </h5>
                     <ul className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 text-xs md:text-sm text-white/60">
                        <li className="flex items-start space-x-2">
                           <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5" />
                           <span>Do not click on any links in this email.</span>
                        </li>
                        <li className="flex items-start space-x-2">
                           <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5" />
                           <span>Verify the sender identity via a different channel.</span>
                        </li>
                        <li className="flex items-start space-x-2">
                           <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5" />
                           <span>Report this to your IT security department.</span>
                        </li>
                        <li className="flex items-start space-x-2">
                           <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5" />
                           <span>Delete the email from your inbox immediately.</span>
                        </li>
                     </ul>
                  </div>
                </motion.div>
              )}
              
              {!showResult && !isScanning && (
                 <div className="py-20 text-center space-y-4 opacity-50">
                    <ShieldCheck className="w-16 h-16 mx-auto text-white/20" />
                    <p>Enter an email or URL to perform threat analysis</p>
                 </div>
              )}
              
              {isScanning && (
                 <div className="py-20 text-center space-y-6">
                    <div className="w-24 h-24 mx-auto relative">
                       <div className="absolute inset-0 border-4 border-primary/20 rounded-full" />
                       <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                    <p className="animate-pulse text-primary font-mono tracking-widest uppercase">Initializing Neural Analysis...</p>
                 </div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
};

export default DemoScanner;
