"use client";

import React from "react";
import { motion } from "framer-motion";
import { 
  Search, 
  BrainCircuit, 
  ShieldAlert 
} from "lucide-react";
import { useTranslations } from "next-intl";

const HowItWorks = () => {
  const t = useTranslations("HowItWorks");

  const stepIcons = [Search, BrainCircuit, ShieldAlert];
  const stepColors = [
    "from-primary/40 to-primary/10",
    "from-secondary/40 to-secondary/10",
    "from-accent/40 to-accent/10"
  ];

  const steps = [0, 1, 2].map((i) => ({
    id: i + 1,
    title: t(`steps.${i}.title`),
    description: t(`steps.${i}.desc`),
    icon: stepIcons[i],
    color: stepColors[i],
  }));

  return (
    <section id="how-it-works" className="py-24 relative overflow-hidden">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-3xl mx-auto mb-20 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
            {t("title")} <span className="text-primary">{t("highlight")}</span>
          </h2>
          <p className="text-lg text-white/60">
            {t("subtitle")}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 relative">
          {/* Connector lines (Desktop) */}
          <div className="hidden md:block absolute top-[60px] left-[15%] right-[15%] h-[2px] bg-white/5 -z-10" />
          
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group text-center space-y-8"
            >
              <div className="relative mx-auto">
                <div className={`w-24 h-24 rounded-3xl mx-auto flex items-center justify-center bg-gradient-to-br ${step.color} border border-white/10 group-hover:scale-110 group-hover:neon-glow-cyan transition-all duration-300 shadow-2xl`}>
                  {step.icon && React.createElement(step.icon, { className: "w-10 h-10 text-white" })}
                </div>
                <div className="absolute -top-3 -right-3 w-10 h-10 rounded-full bg-background border border-white/10 flex items-center justify-center font-bold text-primary">
                  {step.id}
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="text-2xl font-bold group-hover:text-primary transition-colors">
                  {step.title}
                </h3>
                <p className="text-white/50 leading-relaxed max-w-xs mx-auto">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
