
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminHeader from "@/components/admin/AdminHeader";
import AdminSidebar from "@/components/admin/AdminSidebar";
import ContactList from "@/components/admin/ContactList";
import DashboardCards from "@/components/admin/DashboardCards";
import StatisticsChart from "@/components/admin/StatisticsChart";
import { Helmet } from "react-helmet-async";
import { toast } from "sonner";

const Admin = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);

  // 管理者チェック
  useEffect(() => {
    const checkAdmin = async () => {
      try {
        // ローカルストレージから管理者権限を確認
        const userRole = localStorage.getItem("userRole");
        
        if (userRole !== "admin") {
          toast.error("管理者ページにアクセスするには管理者権限が必要です");
          navigate("/login");
          return;
        }
        
        setIsLoading(false);
      } catch (error) {
        console.error('認証チェック中にエラーが発生しました:', error);
        toast.error("認証エラーが発生しました");
        navigate("/login");
      }
    };

    checkAdmin();
  }, [navigate]);

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">読み込み中...</div>;
  }

  return (
    <div className="flex min-h-screen bg-gray-100">
      <Helmet>
        <title>管理者ダッシュボード | ワークメイトAI - チャットボット管理</title>
        <meta name="description" content="ワークメイトAIチャットボットの管理ダッシュボード。システム設定、ユーザー管理、分析データの確認ができます。" />
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      
      <AdminSidebar />
      
      <div className="flex-1 flex flex-col">
        <AdminHeader />
        
        <main className="flex-1 p-6">
          <div className="container mx-auto">
            <h1 className="text-2xl font-bold mb-6">ダッシュボード</h1>
            
            <DashboardCards />
            
            <div className="mt-8">
              <StatisticsChart />
            </div>
            
            <div className="mt-8">
              <ContactList />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Admin;
