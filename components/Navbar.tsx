"use client";

import React, { useState, useEffect } from "react";
import { Link, usePathname, useRouter } from "../navigation";
import { Shield, Menu, X, Globe } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslations, useLocale } from "next-intl";

const Navbar = () => {
  const t = useTranslations("Navbar");
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { name: t("home"), href: "/" },
    { name: t("features"), href: "#features" },
    { name: t("analyzer"), href: "#analyzer" },
    { name: t("about"), href: "#about" },
  ];

  const languages = [
    { code: "en", name: "English" },
    { code: "kn", name: "ಕನ್ನಡ" },
    { code: "hi", name: "हिन्दी" },
  ];

  const handleLanguageChange = (newLocale: string) => {
    router.replace(pathname, { locale: newLocale });
    setLangMenuOpen(false);
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? "bg-background/80 backdrop-blur-lg border-b border-white/10 py-3" : "bg-transparent py-6"
      }`}
    >
      <div className="container mx-auto px-4 md:px-6 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-2 group">
          <Shield className="w-6 h-6 md:w-8 md:h-8 text-primary group-hover:scale-110 transition-transform" />
          <span className="text-lg md:text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
            Human Firewall
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center space-x-8">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className="text-sm font-medium text-white/70 hover:text-primary transition-colors"
            >
              {link.name}
            </Link>
          ))}
          
          <div className="relative">
            <button 
              onClick={() => setLangMenuOpen(!langMenuOpen)}
              className="flex items-center space-x-1 text-white/70 hover:text-primary transition-colors text-sm font-medium"
            >
              <Globe className="w-4 h-4" />
              <span>{languages.find(l => l.code === locale)?.name}</span>
            </button>
            
            <AnimatePresence>
              {langMenuOpen && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute right-0 mt-2 py-2 w-32 bg-background/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl"
                >
                  {languages.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => handleLanguageChange(lang.code)}
                      className={`w-full text-left px-4 py-2 text-sm transition-colors hover:bg-white/5 ${
                        locale === lang.code ? "text-primary font-bold" : "text-white/70"
                      }`}
                    >
                      {lang.name}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="flex items-center space-x-4">
            <Link
              href="/login"
              className="text-sm font-medium text-white/70 hover:text-primary transition-colors"
            >
              {t("login")}
            </Link>
            <Link
              href="/signup"
              className="px-6 py-2 text-sm font-bold bg-primary text-background rounded-full hover:neon-glow-cyan transition-all"
            >
              {t("signup")}
            </Link>
          </div>
        </div>

        {/* Mobile Toggle */}
        <div className="flex items-center space-x-4 md:hidden">
           <button 
              onClick={() => setLangMenuOpen(!langMenuOpen)}
              className="text-white/70"
            >
              <Globe className="w-5 h-5" />
            </button>
            <button
              className="text-white"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X /> : <Menu />}
            </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-background border-b border-white/10 overflow-hidden"
          >
            <div className="flex flex-col space-y-4 p-6">
              {navLinks.map((link) => (
                <Link
                  key={link.name}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="text-lg font-medium text-white/70 hover:text-primary"
                >
                  {link.name}
                </Link>
              ))}
              <hr className="border-white/10" />
              <div className="grid grid-cols-3 gap-2 py-2">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => handleLanguageChange(lang.code)}
                    className={`text-xs py-2 rounded-lg border border-white/10 ${
                      locale === lang.code ? "bg-primary text-background font-bold" : "text-white/70"
                    }`}
                  >
                    {lang.name}
                  </button>
                ))}
              </div>
              <hr className="border-white/10" />
              <Link
                href="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="text-lg font-medium hover:text-primary"
              >
                {t("login")}
              </Link>
              <Link
                href="/signup"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full py-3 text-center font-bold bg-primary text-background rounded-xl"
              >
                {t("signup")}
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Mobile Language Overlay when clicking Globe */}
      <AnimatePresence>
        {langMenuOpen && !mobileMenuOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setLangMenuOpen(false)}
            className="fixed inset-0 z-40 bg-background/60 backdrop-blur-sm md:hidden"
          >
            <motion.div 
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              onClick={(e) => e.stopPropagation()}
              className="absolute bottom-0 left-0 right-0 bg-background border-t border-white/10 p-6 rounded-t-3xl"
            >
              <h3 className="text-white font-bold mb-4">Select Language</h3>
              <div className="flex flex-col space-y-2">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => handleLanguageChange(lang.code)}
                    className={`w-full text-left p-4 rounded-xl transition-colors ${
                      locale === lang.code ? "bg-primary text-background font-bold" : "bg-white/5 text-white/70"
                    }`}
                  >
                    {lang.name}
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;
