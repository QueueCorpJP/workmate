
import React, { useState } from "react";
import { Helmet } from "react-helmet-async";
import AdminHeader from "@/components/admin/AdminHeader";
import AdminSidebar from "@/components/admin/AdminSidebar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import QuestionLogTable from "@/components/admin/QuestionLogTable";
import UserActivityChart from "@/components/admin/UserActivityChart";
import QuestionAnalytics from "@/components/admin/QuestionAnalytics";

const AdminAnalytics = () => {
  const [activeTab, setActiveTab] = useState("logs");

  return (
    <div className="flex min-h-screen bg-gray-100">
      <Helmet>
        <title>アナリティクス | 管理者ダッシュボード</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      
      <AdminSidebar />
      
      <div className="flex-1 flex flex-col">
        <AdminHeader />
        
        <main className="flex-1 p-6">
          <div className="container mx-auto">
            <h1 className="text-2xl font-bold mb-6">質問分析・ログ管理</h1>
            
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="mb-6">
                <TabsTrigger value="logs">質問ログ</TabsTrigger>
                <TabsTrigger value="analytics">分析データ</TabsTrigger>
                <TabsTrigger value="users">ユーザー活動</TabsTrigger>
              </TabsList>
              
              <TabsContent value="logs" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>質問ログ履歴</CardTitle>
                    <CardDescription>
                      社員・ユーザーからの質問履歴一覧
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <QuestionLogTable />
                  </CardContent>
                </Card>
              </TabsContent>
              
              <TabsContent value="analytics" className="space-y-6">
                <QuestionAnalytics />
              </TabsContent>
              
              <TabsContent value="users" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>ユーザー活動分析</CardTitle>
                    <CardDescription>
                      ユーザー別の利用状況と活動分析
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <UserActivityChart />
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
};

export default AdminAnalytics;
