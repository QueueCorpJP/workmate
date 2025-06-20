
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Helmet } from 'react-helmet-async';

const Dashboard = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login');
    }
  }, [user, loading, navigate]);

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">読み込み中...</div>;
  }

  if (!user) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Helmet>
        <title>ダッシュボード | ワークメイトAI</title>
        <meta name="description" content="ワークメイトAIのユーザーダッシュボード" />
      </Helmet>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">ダッシュボード</h1>
        
        <div className="bg-white shadow-sm rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">ようこそ、{user.email}さん</h2>
          <p className="text-gray-600">
            ワークメイトAIへようこそ。こちらはあなたの個人ダッシュボードです。
            サービスの機能はこれから順次実装されていきます。
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-3">最近のアクティビティ</h3>
            <p className="text-gray-600">アクティビティはまだありません</p>
          </div>
          
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-3">未読の通知</h3>
            <p className="text-gray-600">新しい通知はありません</p>
          </div>
          
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-3">クイックリンク</h3>
            <ul className="space-y-2 text-gray-600">
              <li><a href="/help" className="text-blue-600 hover:underline">ヘルプセンター</a></li>
              <li><a href="/contact" className="text-blue-600 hover:underline">お問い合わせ</a></li>
              <li><a href="/articles" className="text-blue-600 hover:underline">サポート記事</a></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
