"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, useInView, useSpring, useTransform } from "framer-motion";
import { ShieldCheck, Mail, AlertTriangle, Users } from "lucide-react";

const Counter = ({ value, label, icon: Icon, suffix = "", color = "primary" }: any) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const springValue = useSpring(0, {
    stiffness: 100,
    damping: 30,
    duration: 2000,
  });

  useEffect(() => {
    if (isInView) {
      springValue.set(value);
    }
  }, [isInView, springValue, value]);

  const displayValue = useTransform(springValue, (latest) =>
    Math.floor(latest).toLocaleString()
  );

  const colors: any = {
    primary: "text-primary border-primary/20 bg-primary/10",
    secondary: "text-secondary border-secondary/20 bg-secondary/10",
    accent: "text-accent border-accent/20 bg-accent/10",
    warning: "text-warning border-warning/20 bg-warning/10",
  };

  return (
    <div ref={ref} className="group p-6 md:p-8 glass rounded-[24px] md:rounded-[32px] text-center space-y-4 md:space-y-6 relative overflow-hidden transition-all duration-500 hover:scale-105 border-white/5 hover:border-white/10">
      <div className={`w-12 h-12 md:w-16 md:h-16 rounded-xl md:rounded-2xl mx-auto flex items-center justify-center border ${colors[color]} group-hover:scale-110 transition-transform duration-500`}>
        <Icon className="w-6 h-6 md:w-8 md:h-8" />
      </div>
      
      <div className="space-y-1 md:space-y-2">
        <div className="text-3xl md:text-5xl font-extrabold flex items-center justify-center tracking-tighter">
          <motion.span>{displayValue}</motion.span>
          <span>{suffix}</span>
        </div>
        <p className="text-xs md:text-sm font-medium text-white/50 tracking-wide uppercase">
          {label}
        </p>
      </div>

      {/* Hover decoration */}
      <div className={`absolute -bottom-1 left-0 w-full h-1 bg-gradient-to-r from-transparent via-${color} to-transparent opacity-0 group-hover:opacity-100 transition-opacity`} />
    </div>
  );
};

const Stats = () => {
  return (
    <section className="py-16 md:py-20 relative">
      <div className="container mx-auto px-4 md:px-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
          <Counter 
            value={1000000} 
            suffix="+" 
            label="Emails Analyzed" 
            icon={Mail} 
            color="primary" 
          />
          <Counter 
            value={96} 
            suffix="%" 
            label="Detection Accuracy" 
            icon={ShieldCheck} 
            color="secondary" 
          />
          <Counter 
            value={5000} 
            suffix="+" 
            label="Phishing Attacks Detected" 
            icon={AlertTriangle} 
            color="warning" 
          />
          <Counter 
            value={300} 
            suffix="+" 
            label="Employees Protected" 
            icon={Users} 
            color="accent" 
          />
        </div>
      </div>
    </section>
  );
};

export default Stats;
