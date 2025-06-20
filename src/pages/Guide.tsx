
import { useState } from "react";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import HeroSection from "@/components/guide/HeroSection";
import TabsSection from "@/components/guide/TabsSection";
import WorkflowSection from "@/components/guide/WorkflowSection";
import CTASection from "@/components/guide/CTASection";
import AdminFeatureSection from "@/components/guide/AdminFeatureSection";
import UserFeatureSection from "@/components/guide/UserFeatureSection";
import { Helmet } from "react-helmet-async";

const Guide = () => {
  const [activeTab, setActiveTab] = useState("admin");

  return (
    <div className="min-h-screen flex flex-col">
      <Helmet>
        <title>ワークメイトAI 利用ガイド | AIチャットボット活用方法</title>
        <meta name="description" content="ワークメイトAIチャットボットの活用方法を詳しく解説。管理者向け設定方法から一般ユーザーの効果的な使い方まで、AIチャットボットを最大限に活用するためのガイドです。" />
        <meta name="keywords" content="ワークメイトAI, 利用ガイド, AIチャットボット, チャットボット設定, AIマニュアル, チャットボット活用法" />
        <meta property="og:title" content="ワークメイトAI 利用ガイド | AIチャットボット活用方法" />
        <meta property="og:description" content="ワークメイトAIチャットボットの活用方法を詳しく解説。管理者向け設定方法から一般ユーザーの効果的な使い方まで。" />
        <meta property="og:type" content="website" />
        <link rel="canonical" href="https://www.workmate-ai.jp/guide" />
      </Helmet>
      
      <Navbar />
      <main className="flex-grow pt-28">
        <HeroSection />
        <TabsSection activeTab={activeTab} setActiveTab={setActiveTab} />
        <WorkflowSection activeTab={activeTab} />
        
        {/* 管理画面機能詳細セクション */}
        <AdminFeatureSection />
        
        {/* ユーザー画面機能詳細セクション */}
        <UserFeatureSection />
        
        <CTASection />
      </main>
      <Footer />
    </div>
  );
};

export default Guide;
