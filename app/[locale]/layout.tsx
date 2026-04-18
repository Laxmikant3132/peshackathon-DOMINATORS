import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "../globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { MonitoringProvider } from "@/context/MonitoringContext";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Human Firewall | AI-Powered Phishing Detection",
  description: "Protect organizations from phishing attacks using AI-powered email analysis, URL scanning, and employee awareness training.",
};

export default async function RootLayout({
  children,
  params: { locale }
}: Readonly<{
  children: React.ReactNode;
  params: { locale: string };
}>) {
  const messages = await getMessages();

  return (
    <html lang={locale} className="scroll-smooth">
      <body className={inter.className}>
        <NextIntlClientProvider messages={messages}>
          <AuthProvider>
            <MonitoringProvider>
              <main>{children}</main>
            </MonitoringProvider>
          </AuthProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
