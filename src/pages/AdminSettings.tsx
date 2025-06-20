import React from "react";
import { Helmet } from "react-helmet-async";
import AdminHeader from "@/components/admin/AdminHeader";
import AdminSidebar from "@/components/admin/AdminSidebar";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StatisticsManager from "@/components/admin/StatisticsManager";

const AdminSettings = () => {
  return (
    <div className="flex min-h-screen bg-gray-100">
      <Helmet>
        <title>システム設定 | 管理者ダッシュボード</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      
      <AdminSidebar />
      
      <div className="flex-1 flex flex-col">
        <AdminHeader />
        
        <main className="flex-1 p-6">
          <div className="container mx-auto">
            <h1 className="text-2xl font-bold mb-6">システム設定</h1>
            
            <Tabs defaultValue="general">
              <TabsList className="mb-6">
                <TabsTrigger value="general">一般設定</TabsTrigger>
                <TabsTrigger value="security">セキュリティ</TabsTrigger>
                <TabsTrigger value="statistics">統計データ</TabsTrigger>
                <TabsTrigger value="notifications">通知設定</TabsTrigger>
              </TabsList>
              
              <TabsContent value="general">
                <div className="grid gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>サイト設定</CardTitle>
                      <CardDescription>
                        サイト全体の基本設定を管理します
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <label className="text-sm font-medium">サイト名</label>
                            <input
                              type="text"
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                              defaultValue="ワークメイトAI"
                            />
                          </div>
                          <div>
                            <label className="text-sm font-medium">管理者メールアドレス</label>
                            <input
                              type="email"
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                              defaultValue="admin@workmate.ai"
                            />
                          </div>
                        </div>
                        
                        <div>
                          <label className="text-sm font-medium">サイト説明</label>
                          <textarea
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                            rows={3}
                            defaultValue="ワークメイトAI - 業務効率を飛躍的に高めるAIチャットボット"
                          />
                        </div>
                        
                        <div className="flex justify-end">
                          <Button>設定を保存</Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
              
              <TabsContent value="security">
                <div className="grid gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>セキュリティ設定</CardTitle>
                      <CardDescription>
                        ユーザー認証とアクセス制御の設定
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium">二段階認証</h3>
                            <p className="text-sm text-gray-500">管理者アカウントに二段階認証を要求する</p>
                          </div>
                          <div className="flex items-center">
                            <label className="inline-flex items-center cursor-pointer">
                              <input type="checkbox" className="sr-only peer" defaultChecked />
                              <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                            </label>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium">セッションタイムアウト</h3>
                            <p className="text-sm text-gray-500">非アクティブ状態が続いた場合に自動的にログアウトする</p>
                          </div>
                          <select className="rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50">
                            <option>30分</option>
                            <option>1時間</option>
                            <option>2時間</option>
                            <option>4時間</option>
                          </select>
                        </div>
                        
                        <div className="flex justify-end">
                          <Button>設定を保存</Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
              
              <TabsContent value="statistics">
                <div className="grid gap-6">
                  <StatisticsManager />
                </div>
              </TabsContent>
              
              <TabsContent value="notifications">
                <div className="grid gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>通知設定</CardTitle>
                      <CardDescription>
                        システム通知とアラートの設定
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium">メール通知</h3>
                            <p className="text-sm text-gray-500">新しいお問い合わせがあった場合にメールで通知する</p>
                          </div>
                          <div className="flex items-center">
                            <label className="inline-flex items-center cursor-pointer">
                              <input type="checkbox" className="sr-only peer" defaultChecked />
                              <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                            </label>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium">ブラウザ通知</h3>
                            <p className="text-sm text-gray-500">管理画面を開いている時にリアルタイム通知を表示する</p>
                          </div>
                          <div className="flex items-center">
                            <label className="inline-flex items-center cursor-pointer">
                              <input type="checkbox" className="sr-only peer" defaultChecked />
                              <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                            </label>
                          </div>
                        </div>
                        
                        <div className="flex justify-end">
                          <Button>設定を保存</Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
};

export default AdminSettings;
