"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "@/navigation";
import { useAuth } from "@/context/AuthContext";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import BackgroundScanner from "./BackgroundScanner";
import { motion, AnimatePresence } from "framer-motion";

const DashboardLayout = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-white flex overflow-x-hidden">
      <BackgroundScanner />
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      <div className="flex-1 flex flex-col md:ml-64 min-h-screen transition-all duration-300">
        <Topbar toggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        <motion.main
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="p-4 md:p-8 pb-20 overflow-y-auto"
        >
          {children}
        </motion.main>
      </div>
    </div>
  );
};

export default DashboardLayout;
