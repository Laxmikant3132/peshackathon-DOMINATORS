"use client";

import React from "react";
import { Link, usePathname } from "../navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  LayoutDashboard, 
  MessageSquare, 
  Wallet,
  Globe, 
  Inbox, 
  ShieldAlert, 
  Users, 
  BarChart3, 
  LogOut,
  Shield,
  X
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const Sidebar = ({ isOpen, setIsOpen }: { isOpen: boolean; setIsOpen: (val: boolean) => void }) => {
  const pathname = usePathname();
  const { profile, logout } = useAuth();

  const menuItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Abuse Analyzer", href: "/abuse-analyzer", icon: ShieldAlert },
    { name: "Message Analyzer", href: "/email-analyzer", icon: MessageSquare },
    { name: "UPI Analyzer", href: "/upi-analyzer", icon: Wallet },
    { name: "URL Scanner", href: "/url-scanner", icon: Globe },
    { name: "Inbox Scanner", href: "/inbox", icon: Inbox },
    { name: "Training Simulator", href: "/training", icon: ShieldAlert },
  ];

  const adminItems = [
    { name: "Admin Panel", href: "/admin", icon: Shield },
    { name: "Employee Directory", href: "/admin/employees", icon: Users },
    { name: "Reports", href: "/reports", icon: BarChart3 },
  ];

  return (
    <>
      {/* Mobile Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] md:hidden"
          />
        )}
      </AnimatePresence>

      <aside className={`
        fixed left-0 top-0 h-screen w-64 glass border-r border-white/10 flex flex-col z-[70] transition-transform duration-300 ease-in-out
        ${isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
      `}>
        <div className="p-8 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2 group">
            <Shield className="w-8 h-8 text-primary" />
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
              Human Firewall
            </span>
          </Link>
          <button 
            onClick={() => setIsOpen(false)}
            className="md:hidden p-2 text-white/50 hover:text-white"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

      <nav className="flex-1 min-h-0 overflow-y-auto px-4 pr-2 space-y-2 custom-scrollbar">
        <div className="text-xs font-bold text-white/30 uppercase tracking-widest px-4 mb-4">
          General
        </div>
        {menuItems.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            onClick={() => setIsOpen(false)}
            className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all group ${
              pathname === item.href 
              ? "bg-primary/20 text-primary border border-primary/20 shadow-[0_0_15px_rgba(0,255,255,0.1)]" 
              : "text-white/50 hover:bg-white/5 hover:text-white"
            }`}
          >
            <item.icon className={`w-5 h-5 ${pathname === item.href ? "text-primary" : "group-hover:text-primary"}`} />
            <span className="font-medium">{item.name}</span>
            {pathname === item.href && (
              <motion.div layoutId="active" className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />
            )}
          </Link>
        ))}

        {profile?.role === "admin" && (
          <>
            <div className="text-xs font-bold text-white/30 uppercase tracking-widest px-4 mt-8 mb-4">
              Management
            </div>
            {adminItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all group ${
                  pathname === item.href 
                  ? "bg-accent/20 text-accent border border-accent/20" 
                  : "text-white/50 hover:bg-white/5 hover:text-white"
                }`}
              >
                <item.icon className={`w-5 h-5 ${pathname === item.href ? "text-accent" : "group-hover:text-accent"}`} />
                <span className="font-medium">{item.name}</span>
              </Link>
            ))}
          </>
        )}
      </nav>

      <div className="p-4 border-t border-white/10">
        <button
          onClick={async () => {
            setIsOpen(false);
            await logout();
          }}
          className="flex items-center space-x-3 px-4 py-3 rounded-xl text-danger hover:bg-danger/10 w-full transition-all group"
        >
          <LogOut className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </aside>
    </>
  );
};

export default Sidebar;
