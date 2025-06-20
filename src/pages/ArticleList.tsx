
import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getArticles } from "@/data/articles";
import { Article } from "@/types/article";
import { Helmet } from "react-helmet-async";

const ArticleList = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    const fetchArticles = async () => {
      setLoading(true);
      try {
        // Get only published articles
        const allArticles = await getArticles(true);
        setArticles(allArticles);

        // Extract unique categories
        const uniqueCategories = Array.from(new Set(allArticles.map(article => article.category)));
        setCategories(uniqueCategories);
      } catch (error) {
        console.error("Failed to fetch articles:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, []);

  const filteredArticles = activeCategory
    ? articles.filter(article => article.category === activeCategory)
    : articles;

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("ja-JP", {
      year: "numeric", 
      month: "long", 
      day: "numeric"
    });
  };

  return (
    <div className="bg-white">
      <Helmet>
        <title>ヘルプセンター | ワークメイトAI</title>
        <meta name="description" content="ワークメイトAIのヘルプセンターです。使い方やよくある質問をご確認いただけます。" />
      </Helmet>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">ヘルプセンター</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            ワークメイトAIの使い方やよくある質問をご確認いただけます
          </p>
        </div>

        <div className="mt-12">
          <div className="flex flex-wrap gap-2 justify-center mb-8">
            <button
              onClick={() => setActiveCategory(null)}
              className={`px-4 py-2 rounded-full text-sm font-medium ${
                activeCategory === null
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-800 hover:bg-gray-200"
              }`}
            >
              すべて
            </button>
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setActiveCategory(category)}
                className={`px-4 py-2 rounded-full text-sm font-medium ${
                  activeCategory === category
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-800 hover:bg-gray-200"
                }`}
              >
                {category}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredArticles.length > 0 ? (
                filteredArticles.map((article) => (
                  <Link
                    key={article.id}
                    to={`/help/${article.slug}`}
                    className="block bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200"
                  >
                    <div className="p-6">
                      <div className="inline-block mb-3 px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-700 rounded-full">
                        {article.category}
                      </div>
                      <h2 className="text-xl font-semibold text-gray-900 mb-2">
                        {article.title}
                      </h2>
                      <p className="text-gray-600 mb-4 line-clamp-2">
                        {article.excerpt}
                      </p>
                      <div className="flex justify-between items-center text-sm text-gray-500">
                        <span>{formatDate(article.published_at)}</span>
                        <span className="flex items-center gap-1">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-4 w-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                            />
                          </svg>
                          {article.views.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="col-span-full text-center py-12">
                  <p className="text-lg text-gray-600">
                    該当する記事はありません
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArticleList;
