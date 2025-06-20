
import React from "react";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, AlertCircle, CheckCircle, Server, Database, Wifi, Clock, RefreshCw } from "lucide-react";

const ServiceStatus = () => {
  const currentTime = new Date().toLocaleString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1 pt-24 pb-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-5xl">
          <div className="mb-8 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-4 rounded-full bg-primary/10 text-primary">
              <Activity size={18} />
              <span className="text-sm font-medium">サービスステータス</span>
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 mb-3">
              システム稼働状況
            </h1>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              ワークメイトAIの各サービスの稼働状況をリアルタイムで確認できます。
            </p>
          </div>

          <div className="mb-8">
            <Card>
              <CardHeader className="pb-4">
                <div className="flex justify-between items-center">
                  <CardTitle className="text-xl">現在の稼働状況</CardTitle>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">{currentTime} 現在</span>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <RefreshCw size={16} />
                    </Button>
                  </div>
                </div>
                <CardDescription>
                  全てのシステムは正常に稼働しています
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4">
                  <StatusItem
                    icon={<Server className="h-5 w-5 text-green-500" />}
                    name="APIサービス"
                    status="正常"
                    statusType="operational"
                    response="98ms"
                    uptime="99.98%"
                  />
                  <StatusItem
                    icon={<Database className="h-5 w-5 text-green-500" />}
                    name="データベース"
                    status="正常"
                    statusType="operational"
                    response="45ms"
                    uptime="99.99%"
                  />
                  <StatusItem
                    icon={<Wifi className="h-5 w-5 text-green-500" />}
                    name="認証サービス"
                    status="正常"
                    statusType="operational"
                    response="120ms"
                    uptime="99.95%"
                  />
                  <StatusItem
                    icon={<Clock className="h-5 w-5 text-yellow-500" />}
                    name="ストレージサービス"
                    status="パフォーマンス低下"
                    statusType="degraded"
                    response="350ms"
                    uptime="99.80%"
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">過去のインシデント</h2>
            <div className="space-y-4">
              <IncidentCard
                date="2023年12月15日"
                title="認証サービスの一時的な障害"
                status="解決済み"
                description="14:30-15:45の間、認証サービスにて一部ユーザーがログインできない問題が発生しました。システムの再起動により解決しました。"
              />
              <IncidentCard
                date="2023年11月05日"
                title="定期メンテナンス"
                status="計画済み"
                description="02:00-04:00の間、システムアップグレードのための定期メンテナンスを実施しました。この間、サービスは一時的に利用できませんでした。"
              />
              <IncidentCard
                date="2023年10月22日"
                title="データベース接続エラー"
                status="解決済み"
                description="10:15-11:30の間、データベース接続エラーにより一部機能が利用できない状態が発生しました。構成の修正により解決しました。"
              />
            </div>
          </div>

          <div className="text-center mt-12">
            <h2 className="text-2xl font-bold mb-3">問題が発生していますか？</h2>
            <p className="text-gray-500 mb-6">
              サービスに関する問題やご質問がございましたら、お気軽にお問い合わせください。
            </p>
            <div className="flex justify-center gap-4">
              <Button className="gap-2">
                <AlertCircle size={18} />
                問題を報告する
              </Button>
              <Button variant="outline" className="gap-2">
                ヘルプセンターを訪問する
              </Button>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

interface StatusItemProps {
  icon: React.ReactNode;
  name: string;
  status: string;
  statusType: "operational" | "degraded" | "outage";
  response: string;
  uptime: string;
}

const StatusItem = ({ icon, name, status, statusType, response, uptime }: StatusItemProps) => {
  return (
    <div className="flex items-center justify-between p-4 rounded-lg border border-gray-100 bg-white hover:shadow-sm transition-all">
      <div className="flex items-center gap-3">
        {icon}
        <span className="font-medium">{name}</span>
      </div>
      <div className="flex items-center">
        <StatusBadge type={statusType} label={status} />
        <div className="ml-6 text-sm text-gray-500 hidden md:block">
          <span className="inline-flex items-center mr-4">
            <Clock size={14} className="mr-1 opacity-70" />
            応答時間: {response}
          </span>
          <span className="inline-flex items-center">
            <CheckCircle size={14} className="mr-1 opacity-70" />
            稼働率: {uptime}
          </span>
        </div>
      </div>
    </div>
  );
};

interface StatusBadgeProps {
  type: "operational" | "degraded" | "outage";
  label: string;
}

const StatusBadge = ({ type, label }: StatusBadgeProps) => {
  const getVariant = () => {
    switch (type) {
      case "operational":
        return "bg-green-100 text-green-800 border-green-200";
      case "degraded":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "outage":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <div
      className={`px-3 py-1 rounded-full text-xs font-medium border ${getVariant()}`}
    >
      {label}
    </div>
  );
};

interface IncidentCardProps {
  date: string;
  title: string;
  status: string;
  description: string;
}

const IncidentCard = ({ date, title, status, description }: IncidentCardProps) => {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <div className="text-sm text-gray-500 mb-1">{date}</div>
            <CardTitle className="text-lg">{title}</CardTitle>
          </div>
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            {status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-gray-600">{description}</p>
      </CardContent>
    </Card>
  );
};

export default ServiceStatus;
