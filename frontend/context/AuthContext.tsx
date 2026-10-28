"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { onAuthStateChanged, type User } from "firebase/auth";
import { doc, getDoc } from "firebase/firestore";
import { auth, db } from "@/services/firebaseConfig";
import { logoutUser, type UserProfile } from "@/services/firebaseService";

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  loading: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  loading: true,
  logout: async () => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for local admin bypass
    const localUser = localStorage.getItem("hf_admin_bypass");
    if (localUser) {
      try {
        const profileData = JSON.parse(localUser);
        setProfile(profileData);
        // Mock a user object that DashboardLayout can check
        setUser({ uid: profileData.uid, email: profileData.email } as User);
        setLoading(false);
      } catch (err) {
        console.error("Error parsing local bypass user:", err);
      }
    }

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      // If we already have a bypass profile, don't overwrite it unless a real user logs in
      if (user) {
        localStorage.removeItem("hf_admin_bypass"); // Clear bypass if real user logs in
        setUser(user);
        const userDoc = await getDoc(doc(db, "users", user.uid));
        if (userDoc.exists()) {
          setProfile(userDoc.data() as UserProfile);
        }
        setLoading(false);
      } else if (!localStorage.getItem("hf_admin_bypass")) {
        setUser(null);
        setProfile(null);
        setLoading(false);
      }
    });

    return () => unsubscribe();
  }, []);

  const logout = async () => {
    try {
      await logoutUser();
      setUser(null);
      setProfile(null);
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };


  return (
    <AuthContext.Provider value={{ user, profile, loading, logout }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
