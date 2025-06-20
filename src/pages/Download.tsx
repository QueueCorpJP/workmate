
import React from "react";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import DownloadHero from "@/components/download/DownloadHero";
import ChatbotDemoSection from "@/components/download/ChatbotDemoSection";
import DownloadCta from "@/components/download/DownloadCta";
import { Helmet } from "react-helmet-async";

const Download = () => {
  return (
    <div className="flex min-h-screen flex-col">
      <Helmet>
        <title>AIチャットボット体験 | ワークメイトAI 無料トライアル</title>
        <meta name="description" content="ワークメイトAIチャットボットの無料トライアル版をダウンロード。社内情報検索・業務自動化を実現する次世代AIチャットボットを今すぐ体験できます。" />
        <meta name="keywords" content="AIチャットボット, 無料トライアル, ワークメイトAI, 業務効率化, ダウンロード, AIデモ, チャットボット体験" />
        <meta property="og:title" content="AIチャットボット体験 | ワークメイトAI 無料トライアル" />
        <meta property="og:description" content="ワークメイトAIチャットボットの無料トライアル版をダウンロード。社内情報検索・業務自動化を実現する次世代AIを今すぐ体験できます。" />
        <meta property="og:type" content="website" />
        <link rel="canonical" href="https://www.workmate-ai.jp/download" />
      </Helmet>
      
      <Navbar />
      <main className="flex-1">
        <DownloadHero />
        <ChatbotDemoSection />
        <DownloadCta />
      </main>
      <Footer />
    </div>
  );
};

export default Download;
