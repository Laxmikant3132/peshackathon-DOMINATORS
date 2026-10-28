"use client";

import React from "react";
import { Link } from "../navigation";
import { Shield, Twitter, Github, Linkedin, Mail, Facebook, Instagram } from "lucide-react";
import { useTranslations } from "next-intl";

const Footer = () => {
  const t = useTranslations("Footer");

  const footerLinks = [
    {
      title: t("product"),
      links: [
        { name: t("features"), href: "#features" },
        { name: t("securityTools"), href: "#analyzer" },
        { name: t("training"), href: "/training" },
      ],
    },
    {
      title: t("company"),
      links: [
        { name: t("about"), href: "#about" },
        { name: t("contact"), href: "/contact" },
      ],
    },
    {
      title: t("legal"),
      links: [
        { name: t("privacy"), href: "/privacy" },
        { name: t("terms"), href: "/terms" },
      ],
    },
  ];

  return (
    <footer className="py-20 relative border-t border-white/5 bg-background overflow-hidden">
      {/* Background Decor */}
      <div className="absolute bottom-0 right-0 w-[30%] h-[30%] bg-primary/5 blur-[100px] -z-10" />
      
      <div className="container mx-auto px-4 md:px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-20">
          <div className="lg:col-span-2 space-y-8">
            <Link href="/" className="flex items-center space-x-2 group">
              <Shield className="w-10 h-10 text-primary group-hover:scale-110 transition-transform" />
              <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
                Human Firewall
              </span>
            </Link>
            <p className="text-white/50 max-w-sm leading-relaxed text-lg">
              {t("description")}
            </p>
            <div className="flex items-center space-x-5">
              {[Twitter, Github, Linkedin, Facebook, Instagram].map((Icon, i) => (
                <Link
                  key={i}
                  href="#"
                  className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center hover:bg-primary/20 hover:text-primary transition-all duration-300 border border-white/10 hover:border-primary/30"
                >
                  <Icon className="w-5 h-5" />
                </Link>
              ))}
            </div>
          </div>

          {footerLinks.map((column) => (
            <div key={column.title} className="space-y-6">
              <h5 className="font-bold text-white text-lg">
                {column.title}
              </h5>
              <ul className="space-y-4">
                {column.links.map((link) => (
                  <li key={link.name}>
                    <Link
                      href={link.href}
                      className="text-white/50 hover:text-primary transition-colors flex items-center group text-sm"
                    >
                      <span className="group-hover:translate-x-1 transition-transform">{link.name}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0 text-sm text-white/30">
          <p>{t("rights")}</p>
          <p className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-primary/30" />
            <span>{t("secured")}</span>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
