
import { useEffect } from "react";
import { Helmet } from "react-helmet-async";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import HeroSection from "@/components/sections/HeroSection";
import FeaturesSection from "@/components/sections/FeaturesSection";
import BenefitsSection from "@/components/sections/BenefitsSection";
import HowItWorksSection from "@/components/sections/HowItWorksSection";
import FaqSection from "@/components/sections/FaqSection";
import CtaSection from "@/components/sections/CtaSection";
import ChallengesSection from "@/components/sections/ChallengesSection";

const Index = () => {
  // Smooth scrolling for anchor links
  useEffect(() => {
    const handleAnchorClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest('a');
      
      if (link && link.hash && link.origin + link.pathname === window.location.origin + window.location.pathname) {
        e.preventDefault();
        const targetId = link.hash.substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
          window.scrollTo({
            top: targetElement.offsetTop - 100,
            behavior: 'smooth'
          });
          
          // Update URL without scrolling
          window.history.pushState(null, '', link.hash);
        }
      }
    };

    document.addEventListener('click', handleAnchorClick);
    
    return () => {
      document.removeEventListener('click', handleAnchorClick);
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <Helmet>
        <title>ワークメイトAI | 次世代の業務効率化チャットボット</title>
        <meta name="description" content="ワークメイトAIは業務効率を飛躍的に高めるAIチャットボット。社内情報へのアクセスを迅速化し、日々の業務フローをスマートにする次世代の社内コミュニケーションツールです。" />
        <meta name="keywords" content="ワークメイトAI, AI, チャットボット, 業務効率化, 生産性向上, 社内チャットボット, AI業務支援, 社内知識検索, 業務自動化" />
        <link rel="canonical" href="https://www.workmate-ai.jp/" />
        <meta property="og:title" content="ワークメイトAI | 次世代の業務効率化チャットボット" />
        <meta property="og:description" content="ワークメイトAIは業務効率を飛躍的に高めるAIチャットボットです。社内情報へのアクセスを迅速化し、業務フローをスマートにします。" />
        <meta property="og:url" content="https://www.workmate-ai.jp/" />
        <meta property="og:type" content="website" />
        <meta name="twitter:title" content="ワークメイトAI | 次世代の業務効率化チャットボット" />
        <meta name="twitter:description" content="ワークメイトAIは業務効率を飛躍的に高めるAIチャットボットです。" />
        <script type="application/ld+json">
          {`
            {
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              "name": "ワークメイトAI",
              "applicationCategory": "BusinessApplication",
              "operatingSystem": "Web",
              "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "JPY"
              },
              "description": "業務効率を飛躍的に高めるAIチャットボット。社内情報へのアクセスを迅速化し、日々の業務フローをスマートにする次世代の社内コミュニケーションツール。"
            }
          `}
        </script>
      </Helmet>
      <Navbar />
      <main className="flex-grow">
        <HeroSection />
        <ChallengesSection />
        <FeaturesSection />
        <BenefitsSection />
        <HowItWorksSection />
        <FaqSection />
        <CtaSection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
