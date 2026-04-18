"use client";

import React from "react";
import { Bell, Search, User, Settings, Menu } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const Topbar = ({ toggleSidebar }: { toggleSidebar: () => void }) => {
  const { profile } = useAuth();

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
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-primary transition-colors" />
          <input
            type="text"
            placeholder="Search for threats, logs, or users..."
            className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/30 transition-all text-sm"
          />
        </div>
      </div>

      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
           <button className="p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 hover:text-primary transition-all relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-danger border-2 border-[#0a0a0f]" />
           </button>
           <button className="p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 hover:text-accent transition-all">
              <Settings className="w-5 h-5" />
           </button>
        </div>

        <div className="h-8 w-[1px] bg-white/10" />

        <div className="flex items-center space-x-4">
           <div className="text-right hidden sm:block">
              <div className="text-sm font-bold text-white">{profile?.name || "User"}</div>
              <div className="text-[10px] font-bold text-primary uppercase tracking-widest">{profile?.role || "User"}</div>
           </div>
           <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/30 to-accent/30 border border-white/10 flex items-center justify-center p-0.5">
              <div className="w-full h-full bg-background rounded-[10px] flex items-center justify-center">
                 <User className="w-6 h-6 text-primary" />
              </div>
           </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
