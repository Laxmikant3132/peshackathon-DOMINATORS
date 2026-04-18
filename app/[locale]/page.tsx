import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Hero3D from "@/components/Hero3D";
import AnalyzerCards from "@/components/AnalyzerCards";
import Features from "@/components/Features";
import HowItWorks from "@/components/HowItWorks";
import CTA from "@/components/CTA";

export default function Home() {
  return (
    <main className="flex flex-col min-h-screen bg-background text-white">
      <Navbar />
      
      <Hero3D />
      
      <div className="container mx-auto px-4">
        <AnalyzerCards />
        
        <Features />
        
        <HowItWorks />
        
        <CTA />
      </div>
      
      <Footer />
    </main>
  );
}
