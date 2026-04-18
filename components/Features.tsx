"use client";

import React from "react";
import { motion } from "framer-motion";
import { 
  ShieldCheck, 
  Globe, 
  Wallet, 
  Monitor, 
  Mail, 
  GraduationCap 
} from "lucide-react";
import { useTranslations } from "next-intl";

const Features = () => {
  const t = useTranslations("Features");
  
  const featureIcons = [ShieldCheck, Globe, Wallet, Monitor, Mail, GraduationCap];
  const featureColors = [
    "bg-primary",
    "bg-secondary",
    "bg-accent",
    "bg-warning",
    "bg-danger",
    "bg-primary"
  ];

  const features = [0, 1, 2, 3, 4, 5].map((i) => ({
    title: t(`items.${i}.title`),
    description: t(`items.${i}.desc`),
    icon: featureIcons[i],
    color: featureColors[i],
  }));

  return (
    <section id="features" className="py-24">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-3xl mx-auto mb-16 md:mb-20 space-y-4">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-bold tracking-tight"
          >
            {t("title")} <span className="text-primary">{t("highlight")}</span>
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-lg text-white/60"
          >
            {t("subtitle")}
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group p-8 glass rounded-[32px] border border-white/10 hover:border-primary/50 transition-all duration-300 relative overflow-hidden"
            >
              <div className={`absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-10 group-hover:opacity-30 transition-opacity ${feature.color}`} />
              
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-6 border border-white/10 group-hover:scale-110 transition-transform ${feature.color}/20 text-white`}>
                {feature.icon && React.createElement(feature.icon, { className: "w-7 h-7" })}
              </div>
              
              <h3 className="text-2xl font-bold mb-4 group-hover:text-primary transition-colors">
                {feature.title}
              </h3>
              
              <p className="text-white/60 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
