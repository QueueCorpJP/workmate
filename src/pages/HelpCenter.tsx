import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Article } from "@/types/article";
import { Helmet } from "react-helmet-async";
import HelpHeader from "@/components/help/HelpHeader";
import HelpFooter from "@/components/help/HelpFooter";

// サンプル記事データ
const sampleArticles: Article[] = [
  {
    id: 1,
    title: "ワークメイトAIの基本的な使い方",
    slug: "basic-usage",
    content: "ワークメイトAIの基本的な使い方について説明します...",
    excerpt: "初めての方向けに、ワークメイトAIの基本的な機能と使い方を解説します。",
    category: "使い方ガイド",
    author: "WorkMate AI Team",
    created_at: "2024-01-01",
    updated_at: "2024-01-01",
    is_published: true,
    views: 1200,
    tags: ["入門", "基本機能"]
  },
  {
    id: 2,
    title: "AIアシスタントとの効果的な対話方法",
    slug: "effective-communication",
    content: "AIアシスタントとより効果的に対話するためのコツを紹介します...",
    excerpt: "AIアシスタントからより良い回答を得るためのコツと、よくある質問への対処法を解説します。",
    category: "使い方ガイド",
    author: "WorkMate AI Team",
    created_at: "2024-01-02",
    updated_at: "2024-01-02",
    is_published: true,
    views: 980,
    tags: ["AI対話", "コミュニケーション"]
  },
  {
    id: 3,
    title: "セキュリティ設定のベストプラクティス",
    slug: "security-best-practices",
    content: "企業でワークメイトAIを安全に利用するためのセキュリティ設定について...",
    excerpt: "企業環境での安全な利用のために、推奨されるセキュリティ設定とポリシーについて解説します。",
    category: "セキュリティ",
    author: "WorkMate AI Team",
    created_at: "2024-01-03",
    updated_at: "2024-01-03",
    is_published: true,
    views: 756,
    tags: ["セキュリティ", "設定"]
  },
  {
    id: 4,
    title: "よくあるトラブルと解決方法",
    slug: "troubleshooting",
    content: "ワークメイトAI利用時によくあるトラブルとその解決方法を紹介します...",
    excerpt: "システム利用時によく発生する問題とその対処方法をまとめています。",
    category: "トラブルシューティング",
    author: "WorkMate AI Team",
    created_at: "2024-01-04",
    updated_at: "2024-01-04",
    is_published: true,
    views: 1500,
    tags: ["トラブル対応", "FAQ"]
  },
  {
    id: 5,
    title: "データのバックアップと復元方法",
    slug: "backup-restore",
    content: "重要なデータを安全にバックアップし、必要な時に復元する方法を解説します...",
    excerpt: "データの定期バックアップの設定方法と、バックアップからの復元手順について説明します。",
    category: "データ管理",
    author: "WorkMate AI Team",
    created_at: "2024-01-05",
    updated_at: "2024-01-05",
    is_published: true,
    views: 634,
    tags: ["バックアップ", "データ管理"]
  }
];

const HelpCenter = () => {
  const [articles, setArticles] = useState<Article[]>(sampleArticles);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchArticles = async () => {
      setLoading(true);
      try {
        // Direct Supabase query to fetch published articles
        const { data, error } = await supabase
          .from('articles')
          .select('*')
          .eq('is_published', true)
          .order('created_at', { ascending: false });

        if (error) {
          console.error("Error fetching articles:", error);
          return;
        }
        
        setArticles(data || []);
      } catch (error) {
        console.error("Failed to fetch articles:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, []);

  // Get unique categories
  const categories = Array.from(new Set(articles.map(article => article.category)));

  // Group articles by category
  const articlesByCategory = categories.map(category => ({
    category,
    articles: articles.filter(article => article.category === category)
  }));

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Helmet>
        <title>ヘルプセンター | ワークメイトAI</title>
        <meta name="description" content="ワークメイトAIのヘルプセンターです。使い方やよくある質問をご確認いただけます。" />
      </Helmet>

      <HelpHeader />

      <main className="flex-grow">
        <div className="bg-blue-600">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-white mb-4">
                お困りの点はありませんか？
              </h1>
              <p className="text-xl text-blue-100">
                ワークメイトAIの使い方やよくある質問をご確認いただけます
              </p>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            <div className="space-y-12">
              {articlesByCategory.map(({ category, articles }) => (
                <div key={category} className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 sm:p-8">
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">{category}</h2>
                    <Link
                      to={`/help/categories/${category}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      すべて見る
                    </Link>
                  </div>

                  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {articles.map((article) => (
                      <Link
                        key={article.id}
                        to={`/help/articles/${article.slug}`}
                        className="block bg-gray-50 rounded-xl overflow-hidden hover:bg-gray-100 transition-colors duration-200"
                      >
                        <div className="p-6">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            {article.title}
                          </h3>
                          <p className="text-gray-600 text-sm line-clamp-2">
                            {article.excerpt}
                          </p>
                          <div className="mt-4 flex items-center justify-between">
                            <div className="text-blue-600 font-medium text-sm hover:text-blue-800">
                              続きを読む
                            </div>
                            <div className="text-gray-500 text-sm">
                              閲覧数: {article.views}
                            </div>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              ))}

              {/* お問い合わせ先情報 */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">お問い合わせ先</h2>
                <div className="grid md:grid-cols-3 gap-8">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">電話でのお問い合わせ</h3>
                    <p className="text-gray-600 text-lg mb-1">03-6687-0550</p>
                    <p className="text-sm text-gray-500">受付時間: 平日 9:00〜18:00</p>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">メールでのお問い合わせ</h3>
                    <a href="mailto:queue@queuefood.co.jp" className="text-blue-600 hover:text-blue-800 text-lg">
                      queue@queuefood.co.jp
                    </a>
                    <p className="text-sm text-gray-500 mt-1">24時間受付</p>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">所在地</h3>
                    <p className="text-gray-600">〒104-0061</p>
                    <p className="text-gray-600">東京都中央区銀座一丁目22番11号</p>
                    <p className="text-gray-600">銀座大竹ビジデンス 2F</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <HelpFooter />
    </div>
  );
};

export default HelpCenter;
