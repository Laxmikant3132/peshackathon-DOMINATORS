"use client";

import React from "react";
import { motion } from "framer-motion";
import { ShieldAlert, Globe, ArrowRight } from "lucide-react";

const Hero = () => {
  return (
    <section className="relative pt-24 md:pt-32 pb-16 md:pb-20 overflow-hidden min-h-[90vh] flex items-center justify-center">
      {/* Moving Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-full -z-10 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.1, 0.2, 0.1],
          }}
          transition={{ duration: 10, repeat: Infinity }}
          className="absolute -top-[20%] -left-[10%] w-[100%] md:w-[60%] h-[80%] bg-primary/20 blur-[80px] md:blur-[120px] rounded-full"
        />
        <motion.div
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.1, 0.15, 0.1],
          }}
          transition={{ duration: 12, repeat: Infinity, delay: 1 }}
          className="absolute -bottom-[20%] -right-[10%] w-[100%] md:w-[50%] h-[70%] bg-accent/20 blur-[70px] md:blur-[100px] rounded-full"
        />
      </div>

      <div className="container mx-auto px-4 md:px-6 grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-16 items-center">
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="space-y-6 md:space-y-8 text-center md:text-left"
        >
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] md:text-xs font-semibold tracking-wider text-primary uppercase mx-auto md:mx-0">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            <span>Next-Gen Security Platform</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-7xl font-extrabold tracking-tight leading-tight">
            AI-Powered Phishing <br className="hidden sm:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-secondary to-accent">
              Detection & Human Firewall
            </span>
          </h1>

          <p className="text-base md:text-xl text-white/60 max-w-lg leading-relaxed mx-auto md:mx-0">
            Protect organizations from phishing attacks using AI-powered email analysis, URL scanning, and employee awareness training.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center md:justify-start space-y-4 sm:space-y-0 sm:space-x-4">
            <button className="w-full sm:w-auto px-8 py-4 bg-primary text-background font-bold rounded-xl flex items-center justify-center space-x-2 hover:neon-glow-cyan transition-all group">
              <span>Analyze Email</span>
              <ShieldAlert className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button className="w-full sm:w-auto px-8 py-4 glass border-white/20 font-bold rounded-xl flex items-center justify-center space-x-2 hover:bg-white/10 transition-all">
              <span>Scan URL</span>
              <Globe className="w-5 h-5" />
            </button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1 }}
          className="relative hidden md:block"
        >
          {/* Main Illustration */}
          <div className="relative z-10 animate-float">
            <div className="relative w-full aspect-square max-w-[500px] mx-auto">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/30 to-accent/30 rounded-3xl blur-3xl -z-10 opacity-50" />
              <div className="w-full h-full glass rounded-[40px] flex items-center justify-center p-8 border-white/20 relative">
                 <ShieldAlert className="w-48 h-48 text-primary opacity-80" />
                 
                 {/* Floating elements */}
                 <motion.div 
                    animate={{ y: [0, -15, 0] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute -top-4 -right-4 p-4 glass rounded-2xl border-primary/30"
                 >
                    <Globe className="w-8 h-8 text-primary" />
                 </motion.div>
                 <motion.div 
                    animate={{ y: [0, 15, 0] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute -bottom-6 -left-6 p-4 glass rounded-2xl border-danger/30"
                 >
                    <div className="flex items-center space-x-3">
                       <div className="w-3 h-3 rounded-full bg-danger animate-pulse" />
                       <div className="text-[10px] font-bold text-danger uppercase tracking-widest whitespace-nowrap">Threat Detected</div>
                    </div>
                 </motion.div>
              </div>
            </div>
          </div>
          
          {/* Tech lines background decorative */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full -z-10 opacity-20 pointer-events-none">
             <div className="absolute w-[150%] h-[1px] bg-white/20 rotate-45 top-[40%]" />
             <div className="absolute w-[150%] h-[1px] bg-white/20 -rotate-45 top-[60%]" />
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default Hero;
