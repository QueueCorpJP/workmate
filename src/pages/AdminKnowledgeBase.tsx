
import React, { useState } from "react";
import { Helmet } from "react-helmet-async";
import AdminHeader from "@/components/admin/AdminHeader";
import AdminSidebar from "@/components/admin/AdminSidebar";
import KnowledgeUploader from "@/components/admin/KnowledgeUploader";
import KnowledgeResourceList from "@/components/admin/KnowledgeResourceList";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const AdminKnowledgeBase = () => {
  const [activeTab, setActiveTab] = useState("resources");

  return (
    <div className="flex min-h-screen bg-gray-100">
      <Helmet>
        <title>知識ベース管理 | ワークメイトAI チャットボット</title>
        <meta name="description" content="ワークメイトAIチャットボットの知識ベース管理ページ。チャットボットが参照する社内文書のアップロードや管理ができます。" />
        <meta name="keywords" content="知識ベース, チャットボット設定, 文書管理, AIトレーニング, ワークメイトAI" />
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      
      <AdminSidebar />
      
      <div className="flex-1 flex flex-col">
        <AdminHeader />
        
        <main className="flex-1 p-6">
          <div className="container mx-auto">
            <h1 className="text-2xl font-bold mb-6">知識ベース管理</h1>
            
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="mb-6">
                <TabsTrigger value="resources">リソース一覧</TabsTrigger>
                <TabsTrigger value="upload">アップロード</TabsTrigger>
              </TabsList>
              
              <TabsContent value="resources" className="space-y-6">
                <KnowledgeResourceList />
              </TabsContent>
              
              <TabsContent value="upload" className="space-y-6">
                <KnowledgeUploader />
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
};

export default AdminKnowledgeBase;
