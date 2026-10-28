"use client";

import { useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";

export default function BackgroundScanner() {
  const { user } = useAuth();
  const lastScanRef = useRef<number>(0);

  useEffect(() => {
    if (!user) return;

    const performScan = async () => {
      // Use localStorage to coordinate between tabs
      const lastGlobalSync = localStorage.getItem("last_gmail_sync_time");
      const now = Date.now();
      const COOLDOWN = 30 * 1000; // 30 second cooldown for background sync

      if (lastGlobalSync && (now - parseInt(lastGlobalSync)) < COOLDOWN) {
        // Silenced log so it doesn't spam every 2 seconds
        return;
      }
      
      try {
        const response = await fetch(`/api/gmail?uid=${user.uid}&t=${Date.now()}`);
        if (response.ok) {
          localStorage.setItem("last_gmail_sync_time", Date.now().toString());
        }
      } catch (error) {
        console.error("[BACKGROUND SCAN] Sync error:", error);
      }
    };

    // Initial check on mount
    performScan();

    const interval = setInterval(performScan, 30000); // Check every 30 seconds if a sync is needed

    return () => clearInterval(interval);
  }, [user]);

  return null; // This is a background logic component
}
