import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { BlogPost } from '@/types/blog';
import { getBlogPosts } from '@/services/blogService';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
export const Blog = () => {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    console.log('Blog component mounted');
    const fetchData = async () => {
      try {
        console.log('Starting to fetch data...');
        const response = await getBlogPosts();
        console.log('All data fetched:', response);
        setPosts(response.contents);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('ブログ記事の取得に失敗しました。');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // カテゴリーの一覧を取得
  const categories = Array.from(new Set(posts.map(post => post.category?.name).filter(Boolean)));

  // カテゴリーでフィルタリング
  const filteredPosts = selectedCategory
    ? posts.filter(post => post.category?.name === selectedCategory)
    : posts;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="container mx-auto px-4 py-8 pt-28">
        <div className="max-w-7xl mx-auto">
          {/* ヘッダーセクション */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4 relative inline-block">
              ブログ
            </h1>
            <p className="text-gray-600 max-w-2xl mx-auto">
              最新の記事やお知らせをお届けします
            </p>
          </div>

          {/* カテゴリーフィルター */}
          <div className="relative mb-12">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200"></div>
            </div>
            <div className="relative flex justify-center">
              <div className="bg-gray-50 px-4">
                <div className="flex flex-wrap justify-center gap-3">
                  <button
                    onClick={() => setSelectedCategory(null)}
                    className={`px-6 py-2.5 text-sm font-medium transition-all duration-200 relative overflow-hidden ${
                      selectedCategory === null
                        ? 'text-blue-600 bg-blue-50'
                        : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                    }`}
                  >
                    <span className="relative z-10">すべて</span>
                    {selectedCategory === null && (
                      <span className="absolute inset-0 bg-blue-100 transform scale-x-100 transition-transform duration-200"></span>
                    )}
                  </button>
                  {categories.map((category) => (
                    <button
                      key={category}
                      onClick={() => setSelectedCategory(category)}
                      className={`px-6 py-2.5 text-sm font-medium transition-all duration-200 relative overflow-hidden ${
                        selectedCategory === category
                          ? 'text-blue-600 bg-blue-50'
                          : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                      }`}
                    >
                      <span className="relative z-10">{category}</span>
                      {selectedCategory === category && (
                        <span className="absolute inset-0 bg-blue-100 transform scale-x-100 transition-transform duration-200"></span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-white shadow-sm overflow-hidden animate-pulse">
                  <div className="h-48 bg-gray-200"></div>
                  <div className="p-4">
                    <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3">
              {error}
            </div>
          ) : filteredPosts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">記事がありません。</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredPosts.map((post) => (
                <Link
                  key={post.id}
                  to={`/blog/${post.id}`}
                  className="block bg-white shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden group"
                >
                  <article>
                    <div className="aspect-w-16 aspect-h-9">
                      <img
                        src={post.picture.url}
                        alt={post.title}
                        className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-200"
                        width={post.picture.width}
                        height={post.picture.height}
                      />
                    </div>
                    <div className="p-6">
                      {post.category && (
                        <span className="inline-block px-3 py-1 text-xs font-medium text-blue-600 bg-blue-50 mb-3">
                          {post.category.name}
                        </span>
                      )}
                      <h2 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 group-hover:text-blue-600 transition-colors duration-200">
                        {post.title}
                      </h2>
                      <time
                        dateTime={post.publishedAt}
                        className="text-sm text-gray-500"
                      >
                        {format(new Date(post.publishedAt), 'yyyy年MM月dd日', {
                          locale: ja,
                        })}
                      </time>
                    </div>
                  </article>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}; 