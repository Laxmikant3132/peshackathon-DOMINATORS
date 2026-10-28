"use client";

import React from "react";
import { motion } from "framer-motion";
import { Shield, ArrowRight, ShieldCheck, Zap } from "lucide-react";
import { useTranslations } from "next-intl";

const Hero3D = () => {
  const t = useTranslations("Hero");

  return (
    <section className="relative min-h-screen pt-32 pb-20 overflow-hidden flex items-center">
      {/* Background elements */}
      <div className="absolute top-0 left-0 w-full h-full -z-10">
        <div className="absolute top-[10%] left-[-5%] w-[40%] h-[40%] bg-primary/20 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-[10%] right-[-5%] w-[40%] h-[40%] bg-accent/20 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-[0.03] pointer-events-none" />
      </div>

      <div className="container mx-auto px-4 md:px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* Left Content */}
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="space-y-8"
        >
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-primary text-xs font-mono uppercase tracking-widest">
            <Zap className="w-3 h-3" />
            <span>{t("badge")}</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold leading-tight tracking-tight">
            {t("titlePart1")} <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary via-blue-400 to-accent">
              {t("titlePart2")}
            </span> <br />
            {t("titlePart3")}
          </h1>
          
          <p className="text-lg md:text-xl text-white/60 max-w-xl leading-relaxed">
            {t("subtitle")}
          </p>
          
          <div className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-6">
            <button 
              onClick={() => document.getElementById('analyzer')?.scrollIntoView({ behavior: 'smooth' })}
              className="w-full sm:w-auto px-8 py-4 bg-primary text-background font-bold rounded-2xl flex items-center justify-center space-x-2 hover:neon-glow-cyan transition-all group"
            >
              <span>{t("ctaStart")}</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button className="w-full sm:w-auto px-8 py-4 bg-white/5 text-white font-bold rounded-2xl border border-white/10 hover:bg-white/10 transition-all">
              {t("ctaLearn")}
            </button>
          </div>

          <div className="flex items-center space-x-8 pt-4">
            <div className="flex -space-x-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="w-10 h-10 rounded-full border-2 border-background bg-zinc-800" />
              ))}
            </div>
            <p className="text-sm text-white/40">
              <span className="text-white font-bold">10k+</span> {t("stats")}
            </p>
          </div>
        </motion.div>

        {/* Right Content - 3D Visualization */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1 }}
          className="relative perspective-1000 hidden lg:block"
        >
          <div className="relative w-full aspect-square flex items-center justify-center">
            {/* Animated Shield / Core */}
            <motion.div
              animate={{ 
                rotateY: [0, 360],
                y: [0, -20, 0]
              }}
              transition={{ 
                rotateY: { duration: 20, repeat: Infinity, ease: "linear" },
                y: { duration: 4, repeat: Infinity, ease: "easeInOut" }
              }}
              className="relative z-10 w-64 h-64 flex items-center justify-center"
              style={{ transformStyle: "preserve-3d" }}
            >
              <div className="absolute inset-0 bg-primary/20 rounded-full blur-3xl animate-pulse" />
              <Shield className="w-48 h-48 text-primary drop-shadow-[0_0_30px_rgba(0,255,255,0.5)]" />
              
              {/* Orbital Rings */}
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="absolute border border-primary/30 rounded-full"
                  style={{
                    width: `${100 + i * 60}%`,
                    height: `${100 + i * 60}%`,
                    transform: `rotateX(${45 + i * 15}deg) rotateY(${i * 20}deg)`,
                    animation: `spin ${10 + i * 5}s linear infinite`
                  }}
                />
              ))}
            </motion.div>

            {/* Particles / Network Grid (Simplified) */}
            <div className="absolute inset-0 overflow-hidden">
               {Array.from({ length: 20 }).map((_, i) => (
                 <motion.div
                   key={i}
                   initial={{ 
                     x: Math.random() * 100 + "%", 
                     y: Math.random() * 100 + "%",
                     opacity: Math.random()
                   }}
                   animate={{ 
                     y: [null, Math.random() * 100 + "%"],
                     opacity: [0.2, 0.5, 0.2]
                   }}
                   transition={{ 
                     duration: 5 + Math.random() * 5, 
                     repeat: Infinity,
                     ease: "linear"
                   }}
                   className="absolute w-1 h-1 bg-primary rounded-full shadow-[0_0_5px_#00ffff]"
                 />
               ))}
            </div>

            {/* Floating Security Cards */}
            <motion.div
              animate={{ y: [0, 20, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              className="absolute top-0 right-0 p-4 glass rounded-2xl border border-white/10 flex items-center space-x-3 shadow-2xl"
            >
              <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-secondary" />
              </div>
              <div>
                <p className="text-xs font-bold">{t("threatBlocked")}</p>
                <p className="text-[10px] text-white/50">{t("phishingDetected")}</p>
              </div>
            </motion.div>

            <motion.div
              animate={{ y: [0, -25, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 1 }}
              className="absolute bottom-10 left-0 p-4 glass rounded-2xl border border-white/10 flex items-center space-x-3 shadow-2xl"
            >
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                <Zap className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-xs font-bold">{t("aiAnalysis")}</p>
                <p className="text-[10px] text-white/50">{t("scanning")}</p>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>

      <style jsx>{`
        .perspective-1000 {
          perspective: 1000px;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </section>
  );
};

export default Hero3D;
