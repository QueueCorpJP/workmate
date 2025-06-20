
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { supabase } from "@/integrations/supabase/client";
import { Article } from "@/types/article";
import { ArrowLeft, Clock, Eye } from "lucide-react";

const ArticleDetail = () => {
  const { slug } = useParams<{ slug: string }>();
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchArticle = async () => {
      if (!slug) return;
      
      setLoading(true);
      try {
        // Direct Supabase query to fetch article by slug
        const { data, error } = await supabase
          .from('articles')
          .select('*')
          .eq('slug', slug)
          .single();

        if (error) {
          console.error("Error fetching article:", error);
          return;
        }

        setArticle(data as Article);
        
        // Record view
        if (data?.id) {
          // Increment view count
          const { error: updateError } = await supabase
            .from('articles')
            .update({ views: (data.views || 0) + 1 })
            .eq('id', data.id);
            
          if (updateError) {
            console.error("Error updating view count:", updateError);
          }
        }
      } catch (error) {
        console.error("Failed to fetch article:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchArticle();
  }, [slug]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto py-12 px-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-6"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-12"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="max-w-3xl mx-auto py-12 px-4 text-center">
        <h1 className="text-2xl font-bold mb-4">記事が見つかりませんでした</h1>
        <p className="mb-6">お探しの記事は存在しないか、削除された可能性があります。</p>
        <Link to="/help" className="text-blue-600 hover:underline flex items-center justify-center gap-2">
          <ArrowLeft size={16} />
          ヘルプセンターに戻る
        </Link>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return "日付なし";
    const date = new Date(dateString);
    return date.toLocaleDateString("ja-JP", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="max-w-3xl mx-auto py-12 px-4">
      <Helmet>
        <title>{article.title} | ワークメイトAI ヘルプセンター</title>
        <meta name="description" content={article.excerpt} />
      </Helmet>

      <Link to="/help" className="text-blue-600 hover:underline flex items-center gap-2 mb-6">
        <ArrowLeft size={16} />
        ヘルプセンターに戻る
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">{article.title}</h1>
        
        <div className="flex flex-wrap items-center text-sm text-gray-600 gap-4 mb-6">
          <span className="inline-flex items-center gap-1">
            <Clock size={14} />
            {formatDate(article.published_at)}
          </span>
          <span className="inline-flex items-center gap-1">
            <Eye size={14} />
            {article.views?.toLocaleString() || "0"}閲覧
          </span>
          <span className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full">
            {article.category}
          </span>
        </div>
      </div>

      <div className="prose prose-blue max-w-none" dangerouslySetInnerHTML={{ __html: article.content }} />
    </div>
  );
};

export default ArticleDetail;
