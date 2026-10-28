"use client";

import React, { useState } from "react";
import { useRouter } from "../../../navigation";
import { Link } from "../../../navigation";
import { motion } from "framer-motion";
import { Shield, Mail, Lock, ArrowRight, ArrowLeft } from "lucide-react";
import { loginUser } from "@/services/firebaseService";
import { useTranslations } from "next-intl";

export default function Login() {
  const t = useTranslations("Common");
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const profile = await loginUser(formData.email, formData.password);
      if (profile.role === "admin") {
        const locale = window.location.pathname.split("/")[1] || "en";
        window.location.href = `/${locale}/admin`;
      } else {
        router.push("/dashboard");
      }


    } catch (err: any) {
      setError(err.message || "Failed to login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden bg-background">
      <div className="absolute top-0 left-0 w-full h-full -z-10 bg-background">
         <div className="absolute top-[10%] left-[10%] w-[30%] h-[40%] bg-primary/10 blur-[120px] rounded-full" />
         <div className="absolute bottom-[10%] right-[10%] w-[30%] h-[40%] bg-accent/10 blur-[120px] rounded-full" />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md glass rounded-3xl p-6 md:p-8 border-white/10 relative"
      >
        <Link
          href="/"
          className="absolute top-6 left-6 text-white/50 hover:text-white transition-colors flex items-center gap-2 text-sm group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span>Back</span>
        </Link>
        <div className="text-center mb-8 space-y-2">
          <Link href="/" className="inline-flex items-center space-x-2 group mb-4">
            <Shield className="w-10 h-10 text-primary" />
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
              Human Firewall
            </span>
          </Link>
          <h2 className="text-2xl font-bold">{t("welcome")}</h2>
          <p className="text-white/50">Secure your communication dashboard</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div className="relative group">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-primary transition-colors" />
            <input
              type="email"
              required
              placeholder="Email Address"
              className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/50 transition-all text-white"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div className="relative group">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-primary transition-colors" />
            <input
              type="password"
              required
              placeholder="Password"
              className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/50 transition-all text-white"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          <div className="flex justify-end px-1">
            <Link 
              href="/forgot-password" 
              className="text-sm text-primary hover:underline transition-all"
            >
              {t("forgotPassword")}
            </Link>
          </div>


          {error && <p className="text-danger text-sm text-center">{error}</p>}


          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-primary text-background font-bold rounded-2xl hover:neon-glow-cyan transition-all disabled:opacity-50 flex items-center justify-center space-x-2"
          >
            {loading ? <span>Logging in...</span> : (
              <>
                <span>Login</span>
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </form>

        <p className="mt-8 text-center text-white/50">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="text-primary hover:underline font-bold">
            Sign Up
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
