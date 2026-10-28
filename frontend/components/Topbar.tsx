"use client";

import React, { useState, useRef, useEffect } from "react";
import { 
  Bell, 
  Search, 
  User, 
  Settings, 
  Menu, 
  LogOut, 
  Shield, 
  Clock, 
  AlertCircle,
  CheckCircle2,
  X
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "../navigation";

const Topbar = ({ toggleSidebar }: { toggleSidebar: () => void }) => {
  const { profile, logout } = useAuth();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  
  const notificationRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const notifications = [
    {
      id: 1,
      title: "New Threat Detected",
      desc: "Phishing attempt blocked from 185.x.x.x",
      time: "2 mins ago",
      type: "danger",
      icon: AlertCircle
    },
    {
      id: 2,
      title: "System Health Optimal",
      desc: "Daily security scan completed successfully.",
      time: "1 hour ago",
      type: "success",
      icon: CheckCircle2
    },
    {
      id: 3,
      title: "Login from New Device",
      desc: "Account accessed from Chrome on Windows.",
      time: "3 hours ago",
      type: "warning",
      icon: Shield
    }
  ];

  return (
    <header className="h-20 glass border-b border-white/10 px-4 md:px-8 flex items-center justify-between sticky top-0 z-40 backdrop-blur-xl">
      <div className="flex items-center space-x-4 flex-1">
        <button 
          onClick={toggleSidebar}
          className="md:hidden p-2 text-white/70 hover:text-white"
        >
          <Menu className="w-6 h-6" />
        </button>
        
        <div className="relative group max-w-md w-full hidden md:block">
          <Search className={`absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 transition-colors ${searchQuery ? 'text-primary' : 'text-white/30 group-focus-within:text-primary'}`} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for threats, logs, or users..."
            className="w-full pl-12 pr-10 py-3 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/30 transition-all text-sm font-medium"
          />
          {searchQuery && (
            <button 
              onClick={() => setSearchQuery("")}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="flex items-center space-x-4 md:space-x-6">
        <div className="flex items-center space-x-2">
           {/* Notifications */}
           <div className="relative" ref={notificationRef}>
             <button 
               onClick={() => setShowNotifications(!showNotifications)}
               className={`p-3 rounded-xl transition-all relative ${showNotifications ? 'bg-primary/20 text-primary' : 'bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 hover:text-primary'}`}
             >
                <Bell className="w-5 h-5" />
                <span className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-danger border-2 border-[#0a0a0f]" />
             </button>

             <AnimatePresence>
               {showNotifications && (
                 <motion.div 
                   initial={{ opacity: 0, y: 10, scale: 0.95 }}
                   animate={{ opacity: 1, y: 0, scale: 1 }}
                   exit={{ opacity: 0, y: 10, scale: 0.95 }}
                   className="absolute right-0 mt-3 w-80 md:w-96 glass-dark border border-white/10 rounded-3xl shadow-2xl overflow-hidden z-50"
                 >
                   <div className="p-5 border-b border-white/5 flex items-center justify-between">
                     <h3 className="text-sm font-bold uppercase tracking-widest text-white/50">Notifications</h3>
                     <span className="text-[10px] font-bold bg-primary/20 text-primary px-2 py-0.5 rounded-full">3 NEW</span>
                   </div>
                   <div className="max-h-[400px] overflow-y-auto">
                     {notifications.map((n) => (
                       <button key={n.id} className="w-full p-4 flex items-start space-x-4 hover:bg-white/5 transition-all text-left border-b border-white/5 last:border-0 group">
                         <div className={`p-2 rounded-xl flex-shrink-0 ${
                           n.type === 'danger' ? 'bg-danger/10 text-danger' : 
                           n.type === 'success' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-warning/10 text-warning'
                         }`}>
                           <n.icon className="w-5 h-5" />
                         </div>
                         <div className="flex-1 min-w-0">
                           <div className="text-sm font-bold text-white group-hover:text-primary transition-colors">{n.title}</div>
                           <p className="text-xs text-white/40 line-clamp-2 mt-0.5">{n.desc}</p>
                           <div className="flex items-center space-x-2 mt-2 text-[10px] font-bold text-white/20 uppercase">
                             <Clock className="w-3 h-3" />
                             <span>{n.time}</span>
                           </div>
                         </div>
                       </button>
                     ))}
                   </div>
                   <button className="w-full py-4 text-[10px] font-black uppercase tracking-[0.2em] text-primary hover:bg-primary/10 transition-all">
                     View All Alerts
                   </button>
                 </motion.div>
               )}
             </AnimatePresence>
           </div>

           <button 
             onClick={() => router.push("/dashboard")}
             className="p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 hover:text-accent transition-all text-white/70"
           >
              <Settings className="w-5 h-5" />
           </button>
        </div>

        <div className="h-8 w-[1px] bg-white/10 hidden sm:block" />

        {/* User Profile Menu */}
        <div className="relative" ref={userMenuRef}>
          <button 
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center space-x-3 p-1 rounded-2xl hover:bg-white/5 transition-all group"
          >
            <div className="text-right hidden sm:block">
              <div className="text-sm font-bold text-white group-hover:text-primary transition-colors">{profile?.name || "User"}</div>
              <div className="text-[10px] font-bold text-primary uppercase tracking-widest">{profile?.role || "User"}</div>
            </div>
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br from-primary/30 to-accent/30 border border-white/10 flex items-center justify-center p-0.5 transition-transform ${showUserMenu ? 'scale-110' : ''}`}>
              <div className="w-full h-full bg-background rounded-[10px] flex items-center justify-center">
                <User className="w-6 h-6 text-primary" />
              </div>
            </div>
          </button>

          <AnimatePresence>
            {showUserMenu && (
              <motion.div 
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute right-0 mt-3 w-64 glass-dark border border-white/10 rounded-3xl shadow-2xl overflow-hidden z-50 p-2"
              >
                <div className="px-4 py-3 border-b border-white/5 mb-1">
                  <div className="text-xs font-bold text-white/40 uppercase tracking-widest mb-1">Account</div>
                  <div className="text-sm font-bold text-white truncate">{profile?.email || "user@example.com"}</div>
                </div>
                
                <button className="w-full px-4 py-3 flex items-center space-x-3 rounded-2xl hover:bg-white/5 transition-all text-white/70 hover:text-primary group text-sm font-medium">
                  <User className="w-4 h-4 group-hover:scale-110 transition-transform" />
                  <span>Profile Settings</span>
                </button>
                
                <button className="w-full px-4 py-3 flex items-center space-x-3 rounded-2xl hover:bg-white/5 transition-all text-white/70 hover:text-accent group text-sm font-medium">
                  <Shield className="w-4 h-4 group-hover:scale-110 transition-transform" />
                  <span>Security Dashboard</span>
                </button>
                
                <div className="h-[1px] bg-white/5 my-1 mx-2" />
                
                <button 
                  onClick={handleLogout}
                  className="w-full px-4 py-3 flex items-center space-x-3 rounded-2xl hover:bg-danger/10 text-danger/70 hover:text-danger group text-sm font-bold transition-all"
                >
                  <LogOut className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  <span>Sign Out</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
