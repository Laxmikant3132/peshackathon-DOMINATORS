"use client";

import React from "react";
import { motion } from "framer-motion";
import { 
  Link2, 
  UserX, 
  Flame, 
  Fingerprint, 
  FileWarning, 
  Globe2 
} from "lucide-react";

const indicators = [
  {
    title: "Suspicious Links",
    description: "Links that lead to unknown domains or redirect through multiple obfuscation layers.",
    icon: Link2,
    color: "text-primary",
  },
  {
    title: "Domain Spoofing",
    description: "Look-alike domains that mimic legitimate brands by replacing characters or using different TLDs.",
    icon: Globe2,
    color: "text-accent",
  },
  {
    title: "Urgent Language",
    description: "Psychological pressure tactics designed to bypass critical thinking and force immediate action.",
    icon: Flame,
    color: "text-danger",
  },
  {
    title: "Fake Login Pages",
    description: "Pixel-perfect replicas of popular service login screens used for credential harvesting.",
    icon: Fingerprint,
    color: "text-secondary",
  },
  {
    title: "Malicious Attachments",
    description: "Infected files with embedded macros or scripts designed to install malware or ransomware.",
    icon: FileWarning,
    color: "text-warning",
  },
  {
    title: "Sender Reputation",
    description: "Analysis of the sender's domain, IP address, and historical behavior for trust metrics.",
    icon: UserX,
    color: "text-primary",
  },
];

const SecurityIndicators = () => {
  return (
    <section className="py-16 md:py-20 relative">
      <div className="container mx-auto px-4 md:px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 md:gap-16 items-center">
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="space-y-6 md:space-y-8 text-center lg:text-left"
        >
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] md:text-xs font-semibold tracking-wider text-primary uppercase mx-auto lg:mx-0">
            <span>Threat Intelligence</span>
          </div>

          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight leading-tight">
            How Our AI Identifies <br className="hidden sm:block" />
            <span className="text-primary">Phishing Indicators</span>
          </h2>

          <p className="text-base md:text-lg text-white/60 leading-relaxed max-w-xl mx-auto lg:mx-0">
            Our neural networks are trained on millions of confirmed phishing campaigns to recognize subtle patterns that human analysts might miss.
          </p>

          <div className="flex flex-col space-y-4 max-w-md mx-auto lg:mx-0">
             <div className="flex items-center space-x-4 p-4 glass rounded-2xl border-white/5">
                <div className="p-3 bg-primary/20 rounded-xl text-primary font-bold text-lg md:text-xl">
                   98%
                </div>
                <div className="flex-1 text-left">
                   <h5 className="font-bold text-white/90 text-sm md:text-base">Recall Accuracy</h5>
                   <p className="text-xs md:text-sm text-white/50">Industry-leading identification of zero-day phishing threats.</p>
                </div>
             </div>
             
             <div className="flex items-center space-x-4 p-4 glass rounded-2xl border-white/5">
                <div className="p-3 bg-secondary/20 rounded-xl text-secondary font-bold text-lg md:text-xl">
                   0.1%
                </div>
                <div className="flex-1 text-left">
                   <h5 className="font-bold text-white/90 text-sm md:text-base">False Positive Rate</h5>
                   <p className="text-xs md:text-sm text-white/50">Minimized disruption to legitimate business communication.</p>
                </div>
             </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-6 relative">
          {/* Subtle background glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-primary/5 blur-[120px] -z-10" />
          
          {indicators.map((indicator, index) => (
            <motion.div
              key={indicator.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="p-6 glass rounded-2xl glass-hover space-y-4 border-white/5 hover:border-white/10"
            >
              <div className={`p-3 w-fit rounded-xl bg-white/5 ${indicator.color}`}>
                <indicator.icon className="w-6 h-6" />
              </div>
              <h4 className="text-lg font-bold group-hover:text-primary transition-colors">
                {indicator.title}
              </h4>
              <p className="text-sm text-white/50 leading-relaxed">
                {indicator.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default SecurityIndicators;
