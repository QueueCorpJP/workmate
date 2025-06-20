import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import type { BlogPost } from '@/types/blog';
import { getBlogPost } from '@/services/blogService';
import Navbar from '@/components/layout/Navbar';
import { Helmet } from 'react-helmet-async';
import Footer from '@/components/layout/Footer';

export const BlogPost = () => {
  const { id } = useParams<{ id: string }>();
  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPost = async () => {
      if (!id) return;

      try {
        const data = await getBlogPost(id);
        setPost(data);
      } catch (err) {
        console.error('Error fetching post:', err);
        setError('ブログ記事の取得に失敗しました。');
      } finally {
        setLoading(false);
      }
    };

    fetchPost();
  }, [id]);

  // メタタグ用のデータを準備
  const metaTitle = post ? `${post.title} | Workmate AI Blog` : 'ブログ記事 | Workmate AI';
  const metaDescription = post?.body?.replace(/<[^>]*>/g, '').slice(0, 120) + '...' || 'Workmate AIのブログ記事です。';
  const metaImage = post?.picture?.url || '/default-ogp.jpg';

  return (
    <div className="min-h-screen bg-white">
      <Helmet>
        {/* 基本的なメタタグ */}
        <title>{metaTitle}</title>
        <meta name="description" content={metaDescription} />

        {/* OGP（Open Graph Protocol）タグ */}
        <meta property="og:title" content={metaTitle} />
        <meta property="og:description" content={metaDescription} />
        <meta property="og:image" content={metaImage} />
        <meta property="og:type" content="article" />
        {post && (
          <>
            <meta property="article:published_time" content={post.publishedAt} />
            {post.category && (
              <meta property="article:section" content={post.category.name} />
            )}
          </>
        )}

        {/* Twitter Card タグ */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={metaTitle} />
        <meta name="twitter:description" content={metaDescription} />
        <meta name="twitter:image" content={metaImage} />
      </Helmet>

      <Navbar />
      <main className="container mx-auto px-4 py-8 pt-28">
        {loading ? (
          <div className="max-w-2xl mx-auto">
            <div className="animate-pulse">
              <div className="h-[400px] bg-gray-100 mb-8"></div>
              <div className="space-y-4">
                <div className="h-8 bg-gray-100 w-3/4"></div>
                <div className="h-4 bg-gray-100 w-1/4"></div>
                <div className="h-4 bg-gray-100 w-full"></div>
                <div className="h-4 bg-gray-100 w-full"></div>
                <div className="h-4 bg-gray-100 w-2/3"></div>
              </div>
            </div>
          </div>
        ) : error ? (
          <div className="max-w-2xl mx-auto text-center py-12">
            <p className="text-red-600">{error}</p>
          </div>
        ) : post ? (
          <>
            <article className="max-w-2xl mx-auto">
              <div className="mb-12">
                <div className="aspect-w-16 aspect-h-9 mb-8">
                  <img
                    src={post.picture.url}
                    alt={post.title}
                    className="object-cover w-full h-full"
                    width={post.picture.width}
                    height={post.picture.height}
                  />
                </div>

                {post.category && (
                  <span className="inline-block px-4 py-1 text-sm font-medium bg-yellow-400 text-black mb-4">
                    {post.category.name}
                  </span>
                )}
                <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4 leading-tight">
                  {post.title}
                </h1>
                <time
                  dateTime={post.publishedAt}
                  className="text-gray-500 block text-base mb-8"
                >
                  {format(new Date(post.publishedAt), 'yyyy年MM月dd日', {
                    locale: ja,
                  })}
                </time>
              </div>

              <div 
                className="
                  mb-16 mx-auto
                  [&_h2]:text-3xl [&_h2]:font-bold [&_h2]:mt-12 [&_h2]:mb-6 [&_h2]:text-gray-900
                  [&_h3]:text-2xl [&_h3]:font-bold [&_h3]:mt-8 [&_h3]:mb-4 [&_h3]:text-gray-900
                  [&_p]:text-base [&_p]:leading-relaxed [&_p]:my-6 [&_p]:text-gray-700
                  [&_ul]:list-disc [&_ul]:pl-6 [&_ul]:my-6
                  [&_ol]:list-decimal [&_ol]:pl-6 [&_ol]:my-6
                  [&_li]:my-2 [&_li]:text-gray-700
                  [&_img]:rounded-lg [&_img]:my-8 [&_img]:mx-auto [&_img]:max-w-full
                  [&_hr]:my-8 [&_hr]:border-gray-200
                  [&_table]:w-full [&_table]:my-8 [&_table]:border-collapse
                  [&_th]:border [&_th]:border-gray-200 [&_th]:p-2 [&_th]:bg-gray-50
                  [&_td]:border [&_td]:border-gray-200 [&_td]:p-2
                  [&_strong]:text-gray-900 [&_strong]:font-bold
                  [&_em]:italic
                  [&_a]:text-primary [&_a]:underline hover:[&_a]:no-underline
                  [&_blockquote]:border-l-4 [&_blockquote]:border-primary [&_blockquote]:pl-4 [&_blockquote]:italic [&_blockquote]:my-6 [&_blockquote]:text-gray-700
                  [&_pre]:bg-gray-50 [&_pre]:p-4 [&_pre]:rounded-lg [&_pre]:overflow-x-auto [&_pre]:my-6 [&_pre]:text-sm
                  [&_code]:font-mono [&_code]:text-sm [&_code]:bg-gray-50 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded
                  [&_figure]:my-8 [&_figure]:mx-auto
                  [&_figcaption]:text-center [&_figcaption]:text-sm [&_figcaption]:text-gray-500 [&_figcaption]:mt-2
                  [&_iframe]:w-full [&_iframe]:my-8 [&_iframe]:aspect-video
                  [&>div]:whitespace-pre-wrap
                "
              >
                <div
                  dangerouslySetInnerHTML={{ 
                    __html: post.body
                  }}
                  className="rich-content"
                />
              </div>

              {/* 会社プロフィール */}
              <div className="border-t border-gray-100 pt-16 mb-16">
                <div className="flex flex-col items-center text-center">
                  <div className="flex items-center gap-6 mb-6">
                    <img
                      src="/Queuepic.png"
                      alt="Workmate AI"
                      className="w-24 h-24 object-cover rounded-full"
                    />
                    <h2 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
                      <span className="w-1 h-6 bg-primary"></span>
                      Workmate AI
                    </h2>
                  </div>
                  <p className="text-gray-600 mb-6 max-w-lg">
                  社内情報へのアクセスを迅速化し、日々の業務フローをスマートにする次世代の社内コミュニケーションツールWorkMate AIを提供しています。
                  </p>
                  <div className="flex gap-4">
                    <Link
                      to="/about"
                      className="inline-flex items-center justify-center px-6 py-2 border-2 border-gray-900 text-sm rounded-md font-medium text-gray-900 hover:bg-gray-900 hover:text-white transition-colors duration-200"
                    >
                      会社概要
                    </Link>
                    <Link
                      to="/contact"
                      className="inline-flex items-center justify-center px-6 py-2 rounded-md   text-sm font-medium text-white bg-primary hover:bg-primary/90 transition-colors duration-200"
                    >
                      お問い合わせ
                    </Link>
                  </div>
                </div>
              </div>
            </article>
          </>
        ) : (
          <div className="max-w-2xl mx-auto text-center py-12">
            <p className="text-gray-500">記事が見つかりませんでした。</p>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}; 