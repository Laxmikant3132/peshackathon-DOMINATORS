"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ShieldAlert, 
  Search, 
  MessageSquare, 
  Globe, 
  Wallet, 
  ArrowRight,
  Lock,
  X,
  ShieldCheck,
  AlertTriangle,
  Zap,
  Activity,
  ChevronDown,
  CheckCircle2,
  Play
} from "lucide-react";
import { Link } from "../navigation";
import { useTranslations } from "next-intl";

const VideoPanel = ({ title, badge, thumbnail, youtubeId }: any) => {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="relative group"
    >
      <div className="absolute -inset-2 bg-gradient-to-r from-primary/20 to-accent/20 rounded-[32px] blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      <div className="relative glass rounded-[24px] border border-white/10 overflow-hidden shadow-xl aspect-video bg-background/40">
        {!isPlaying ? (
          <div 
            className="absolute inset-0 cursor-pointer overflow-hidden"
            onClick={() => setIsPlaying(true)}
          >
            <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent z-10" />
            <div className={`absolute inset-0 bg-cover bg-center opacity-40 group-hover:scale-110 transition-transform duration-700`} style={{ backgroundImage: `url(${thumbnail})` }} />
            
            <motion.div 
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="absolute inset-0 flex items-center justify-center z-20"
            >
              <div className="w-16 h-16 rounded-full bg-primary/90 flex items-center justify-center text-background shadow-[0_0_30px_rgba(0,255,255,0.3)] group-hover:shadow-[0_0_50px_rgba(0,255,255,0.5)] transition-all">
                <Play className="w-6 h-6 fill-current ml-1" />
              </div>
            </motion.div>
            
            <div className="absolute bottom-4 left-4 right-4 z-20">
              <div className="inline-flex items-center space-x-2 px-2 py-0.5 rounded-full bg-primary/20 border border-primary/30 backdrop-blur-md mb-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                <span className="text-[8px] font-bold uppercase tracking-widest text-primary">{badge}</span>
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-primary transition-colors line-clamp-1">{title}</h3>
            </div>
          </div>
        ) : (
          <iframe 
            className="w-full h-full"
            src={`https://www.youtube.com/embed/${youtubeId}?autoplay=1`}
            title={title}
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
          ></iframe>
        )}
      </div>
    </motion.div>
  );
};

const VideoShowcase = () => {
  const videos = [
    {
      title: "Learn to be safe from scams",
      badge: "English",
      thumbnail: "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&q=80",
      youtubeId: "DHOh4h3uOzA"
    },
    {
      title: "ಹಗರಣಗಳಿಂದ ಸುರಕ್ಷಿತವಾಗಿರಲು ಕಲಿಯಿರಿ",
      badge: "ಕನ್ನಡ (Kannada)",
      thumbnail: "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80",
      youtubeId: "KgysRiVlAOE"
    },
    {
      title: "घोटालों से सुरक्षित रहना सीखें",
      badge: "हिंदी (Hindi)",
      thumbnail: "https://images.unsplash.com/photo-1558494949-ef010cbdcc51?auto=format&fit=crop&q=80",
      youtubeId: "QhpVz0-uOr8"
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 max-w-7xl mx-auto mb-32 px-4 relative">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-primary/5 blur-[120px] rounded-full pointer-events-none" />
      {videos.map((v, i) => (
        <VideoPanel key={i} {...v} />
      ))}
    </div>
  );
};

const AnalyzerSection = ({ title, description, icon: Icon, placeholder, buttonText, type }: any) => {
  const t = useTranslations("Analyzer");
  const [inputValue, setInputValue] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAction = async () => {
    if (!inputValue) return;
    setIsScanning(true);
    setResult(null);
    setError(null);
    
    try {
      if (type === "url") {
        let response = await fetch("/backend-api/classify-url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: inputValue }),
        }).catch(() => null);

        if (!response || !response.ok) {
          response = await fetch("https://humanfirewall-backend.onrender.com/api/classify-url", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: inputValue }),
          });
        }
        if (!response.ok) throw new Error("Backend connection failed");
        const data = await response.json();
        setResult({
          safety: data.safety,
          confidence: data.confidence,
          indicators: data.indicators,
          details: data.details
        });
      } else if (type === "message") {
        let response = await fetch("/backend-api/classify-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ emailBody: inputValue }),
        }).catch(() => null);

        if (!response || !response.ok) {
          response = await fetch("https://humanfirewall-backend.onrender.com/api/classify-email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ emailBody: inputValue }),
          });
        }
        if (!response.ok) throw new Error("Backend connection failed");
        const data = await response.json();
        setResult({
          safety: data.safety,
          confidence: Math.round(data.confidence * 100),
          indicators: data.indicators,
          reason: data.reason
        });
      } else if (type === "upi") {
        let response = await fetch("/backend-api/classify-upi", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ upi: inputValue }),
        }).catch(() => null);

        if (!response || !response.ok) {
          response = await fetch("https://humanfirewall-backend.onrender.com/api/classify-upi", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ upi: inputValue }),
          });
        }
        if (!response.ok) throw new Error("Backend connection failed");
        const data = await response.json();
        setResult({
          safety: data.safety,
          confidence: data.confidence,
          indicators: data.indicators,
          reason: data.reason
        });
      }
    } catch (err) {
      console.error("Analysis error:", err);
      setError("Unable to connect to analysis engine. Please try again later.");
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="py-24 border-b border-white/5 last:border-0 relative">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        {/* Left: Info */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="space-y-8"
        >
          <div className="w-20 h-20 rounded-3xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-[0_0_20px_rgba(0,255,255,0.1)]">
            <Icon className="w-10 h-10" />
          </div>
          
          <div className="space-y-4">
            <h3 className="text-4xl font-bold tracking-tight">{title}</h3>
            <p className="text-xl text-white/50 leading-relaxed max-w-lg">
              {description}
            </p>
          </div>

          <div className="flex flex-wrap gap-4 pt-4">
            {[t("tags.0"), t("tags.1"), t("tags.2")].map(tag => (
              <span key={tag} className="px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono uppercase tracking-widest text-white/40">
                {tag}
              </span>
            ))}
          </div>
        </motion.div>

        {/* Right: Analyzer UI */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="glass p-8 md:p-10 rounded-[40px] border border-white/10 relative shadow-2xl overflow-hidden"
        >
          <div className="absolute top-0 right-0 p-6 text-primary/20 pointer-events-none">
            <Activity className="w-24 h-24 animate-pulse" />
          </div>

          <div className="space-y-6 relative z-10">
            <div className="space-y-4">
              <label className="text-sm font-bold uppercase tracking-widest text-primary/60">{t("inputSource")}</label>
              <div className="relative">
                {type === "message" ? (
                  <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder={placeholder}
                    className="w-full h-48 p-6 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/50 transition-all text-white resize-none placeholder-white/20 text-lg"
                  />
                ) : (
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder={placeholder}
                    className="w-full p-6 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:border-primary/50 transition-all text-white placeholder-white/20 text-lg"
                  />
                )}
                {isScanning && (
                   <div className="absolute bottom-6 right-6 flex items-center space-x-2 text-primary">
                      <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                      <span className="text-xs font-mono tracking-widest uppercase">{t("analyzing")}</span>
                   </div>
                )}
              </div>
            </div>

            {error && <p className="text-danger text-sm font-bold text-center">{error}</p>}

            <button
              onClick={handleAction}
              disabled={!inputValue || isScanning}
              className="w-full py-5 bg-primary text-background font-black rounded-2xl hover:neon-glow-cyan disabled:opacity-50 transition-all flex items-center justify-center space-x-3 text-lg"
            >
              <Zap className="w-6 h-6" />
              <span>{isScanning ? t("processing") : buttonText}</span>
            </button>

            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="pt-6"
                >
                  <div className={`p-6 rounded-2xl border space-y-4 ${
                    result.safety === "safe" ? "bg-secondary/10 border-secondary/30" : "bg-danger/10 border-danger/30"
                  }`}>
                    <div className="flex items-center justify-between">
                       <div className={`flex items-center space-x-3 ${result.safety === "safe" ? "text-secondary" : "text-danger"}`}>
                          {result.safety === "safe" ? <ShieldCheck className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                          <span className="font-black uppercase tracking-widest text-sm">
                            {result.safety === "safe" ? t("verifiedSafe") : result.safety === "suspicious" ? t("suspiciousActivity") : t("threatDetected")}
                          </span>
                       </div>
                       <div className={`text-2xl font-black ${result.safety === "safe" ? "text-secondary" : "text-danger"}`}>
                         {result.confidence}%
                       </div>
                    </div>
                    
                    {result.reason && (
                      <p className="text-sm text-white/60 leading-relaxed italic border-l-2 border-white/10 pl-4 py-1">
                        &quot;{result.reason}&quot;
                      </p>
                    )}

                    <div className="flex flex-wrap gap-2">
                       {result.indicators && result.indicators.length > 0 ? result.indicators.map((indicator: string) => (
                          <div key={indicator} className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-[10px] font-bold uppercase tracking-wider text-white/40 flex items-center space-x-1">
                             <span className="w-1 h-1 rounded-full bg-danger animate-pulse" />
                             <span>{indicator}</span>
                          </div>
                       )) : (
                          <div className="flex items-center space-x-2 text-secondary text-xs font-bold">
                             <CheckCircle2 className="w-4 h-4" />
                             <span>{t("noIndicators")}</span>
                          </div>
                       )}
                    </div>

                    <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                       <p className="text-[10px] text-white/30 italic">{t("poweredBy")}</p>
                       <button 
                         onClick={() => setShowLoginModal(true)}
                         className="text-primary text-sm font-bold flex items-center hover:underline"
                       >
                         {t("fullForensics")} <ArrowRight className="w-4 h-4 ml-1" />
                       </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>

      {/* Login Modal */}
      <AnimatePresence>
        {showLoginModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowLoginModal(false)}
              className="absolute inset-0 bg-background/80 backdrop-blur-md"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative w-full max-w-md glass p-10 rounded-[48px] border border-white/10 shadow-2xl text-center space-y-8"
            >
              <button 
                onClick={() => setShowLoginModal(false)}
                className="absolute top-8 right-8 text-white/30 hover:text-white transition-colors"
              >
                <X className="w-8 h-8" />
              </button>

              <div className="w-24 h-24 bg-primary/20 rounded-full flex items-center justify-center mx-auto">
                <Lock className="w-12 h-12 text-primary" />
              </div>

              <div className="space-y-3">
                <h3 className="text-3xl font-bold tracking-tight">{t("lockedTitle")}</h3>
                <p className="text-white/50 text-lg leading-relaxed">
                  {t("lockedDesc")}
                </p>
              </div>

              <div className="flex flex-col space-y-4">
                <Link
                  href="/login"
                  className="w-full py-5 bg-primary text-background font-black rounded-2xl hover:neon-glow-cyan transition-all text-lg"
                >
                  {t("loginToAccess")}
                </Link>
                <Link
                  href="/signup"
                  className="w-full py-5 bg-white/5 text-white font-black rounded-2xl border border-white/10 hover:bg-white/10 transition-all text-lg"
                >
                  {t("createFreeAccount")}
                </Link>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

const AnalyzerCards = () => {
  const t = useTranslations("Analyzer");
  return (
    <section id="analyzer" className="pt-24 pb-12 relative overflow-hidden">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-4xl mx-auto mb-20 space-y-8">
          <div className="inline-flex items-center space-x-2 px-4 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-mono uppercase tracking-[0.3em]">
            <span>{t("platformCapabilities")}</span>
          </div>
          <div className="space-y-4">
            <h2 className="text-5xl md:text-7xl font-bold tracking-tight">
              Universal <span className="text-primary">Detection</span>
            </h2>
            <p className="text-xl text-white/60 leading-relaxed max-w-2xl mx-auto">
              Protecting your digital life across every touchpoint. Our AI engines analyze 
              threats in real-time, no matter where they come from, ensuring 
              uncompromising security for your messages, links, and payments.
            </p>
          </div>
          <div className="flex justify-center pt-4">
            <motion.div
              animate={{ y: [0, 10, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="text-white/20"
            >
              <ChevronDown className="w-10 h-10" />
            </motion.div>
          </div>
        </div>

        <VideoShowcase />

        <AnalyzerSection
          title={t("upi.title")}
          description={t("upi.desc")}
          icon={Wallet}
          placeholder={t("upi.placeholder")}
          buttonText={t("upi.button")}
          type="upi"
        />

        <AnalyzerSection
          title={t("url.title")}
          description={t("url.desc")}
          icon={Globe}
          placeholder={t("url.placeholder")}
          buttonText={t("url.button")}
          type="url"
        />

        <AnalyzerSection
          title={t("message.title")}
          description={t("message.desc")}
          icon={MessageSquare}
          placeholder={t("message.placeholder")}
          buttonText={t("message.button")}
          type="message"
        />
      </div>
    </section>
  );
};

export default AnalyzerCards;
