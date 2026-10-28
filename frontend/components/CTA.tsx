"use client";

import React from "react";
import { Link } from "../navigation";
import { motion } from "framer-motion";
import { ArrowRight, UserPlus, LogIn } from "lucide-react";
import { useTranslations } from "next-intl";

const CTA = () => {
  const t = useTranslations("CTA");

  return (
    <section className="py-24 relative overflow-hidden">
      <div className="absolute inset-0 bg-primary/5 blur-[150px] -z-10 rounded-full pointer-events-none" />
      
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        className="max-w-6xl mx-auto glass rounded-[48px] overflow-hidden p-12 md:p-24 text-center space-y-10 border-white/10 relative"
      >
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
        
        <div className="space-y-6">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-7xl font-extrabold tracking-tight"
          >
            {t("title")} <span className="text-primary">{t("highlight")}</span>
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-xl text-white/50 max-w-3xl mx-auto leading-relaxed"
          >
            {t("subtitle")}
          </motion.p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-8">
          <Link
            href="/signup"
            className="w-full sm:w-auto px-12 py-5 bg-primary text-background font-black rounded-2xl flex items-center justify-center space-x-3 hover:neon-glow-cyan transition-all group text-lg"
          >
            <UserPlus className="w-6 h-6" />
            <span>{t("signup")}</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="/login"
            className="w-full sm:w-auto px-12 py-5 glass border-white/20 font-black rounded-2xl flex items-center justify-center space-x-3 hover:bg-white/10 transition-all text-lg"
          >
            <LogIn className="w-6 h-6" />
            <span>{t("login")}</span>
          </Link>
        </div>

        <div className="pt-12 flex flex-wrap justify-center items-center gap-x-12 gap-y-6 opacity-30 grayscale hover:grayscale-0 transition-all duration-700">
           {[0, 1, 2, 3].map(i => (
              <span key={i} className="text-2xl font-black uppercase tracking-[0.2em]">{t(`brands.${i}`)}</span>
           ))}
        </div>
      </motion.div>
    </section>
  );
};

export default CTA;
