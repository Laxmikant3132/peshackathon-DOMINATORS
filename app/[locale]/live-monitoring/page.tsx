"use client";

import React from "react";
import DashboardLayout from "@/components/DashboardLayout";
import MonitoringDashboard from "@/components/MonitoringDashboard";
import { motion } from "framer-motion";

export default function LiveMonitoringPage() {
  return (
    <DashboardLayout>
      <div className="space-y-8">
        <header className="space-y-2">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1 className="text-3xl md:text-5xl font-black tracking-tighter">
              LIVE <span className="text-primary">TRAFFIC</span> MONITORING
            </h1>
            <p className="text-white/40 text-lg max-w-2xl">
              Advanced multi-layer threat detection engine. Correlating signals from network flows, 
              endpoint processes, and application logs in real-time.
            </p>
          </motion.div>
        </header>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <MonitoringDashboard />
        </motion.div>
      </div>
    </DashboardLayout>
  );
}
