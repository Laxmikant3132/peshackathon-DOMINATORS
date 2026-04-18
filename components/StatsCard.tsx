"use client";

import React from "react";
import type { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color: string;
  trend?: string;
}

const StatsCard = ({ title, value, icon: Icon, color, trend }: StatsCardProps) => {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="glass p-6 rounded-3xl border-white/5 relative overflow-hidden group"
    >
      <div className={`absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-10 group-hover:opacity-20 transition-opacity ${color}`} />
      
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-xl ${color}/20 text-white`}>
          <Icon className="w-6 h-6" />
        </div>
        {trend && (
           <span className={`text-xs font-bold px-2 py-1 rounded-full ${trend.startsWith("+") ? "bg-secondary/10 text-secondary" : "bg-danger/10 text-danger"}`}>
              {trend}
           </span>
        )}
      </div>

      <div className="space-y-1">
        <div className="text-3xl font-extrabold tracking-tight">{value}</div>
        <div className="text-sm font-medium text-white/50 tracking-wide uppercase text-[10px]">{title}</div>
      </div>
    </motion.div>
  );
};

export default StatsCard;
