
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Edit, Trash2, Plus, Eye, EyeOff } from "lucide-react";
import { Article } from "@/types/article";
import { getArticles, deleteArticle, updateArticle } from "@/data/articles";
import AdminSidebar from "@/components/admin/AdminSidebar";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { 
  Card, 
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Helmet } from "react-helmet-async";

const AdminArticles = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    refreshArticles();
  }, []);

  const refreshArticles = async () => {
    setLoading(true);
    try {
      const articlesData = await getArticles(false); // false = get all articles including unpublished
      setArticles(articlesData);
    } catch (error) {
      toast.error("記事の読み込みに失敗しました");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm("この記事を削除してもよろしいですか？")) {
      const success = await deleteArticle(id);
      if (success) {
        refreshArticles();
      }
    }
  };

  const togglePublishStatus = async (article: Article) => {
    const updated = await updateArticle(article.id, {
      is_published: !article.is_published
    });
    
    if (updated) {
      refreshArticles();
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("ja-JP", {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      <Helmet>
        <title>記事管理 | ワークメイトAI 管理画面</title>
        <meta name="description" content="ワークメイトAIの記事を管理するための管理画面です。記事の作成、編集、削除、公開設定ができます。" />
      </Helmet>
      
      <AdminSidebar />
      
      <div className="flex-1">
        <div className="p-8">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-2xl font-bold mb-2">記事管理</h1>
              <p className="text-gray-600">ヘルプセンター記事の作成、編集、削除を行います</p>
            </div>
            <Button 
              onClick={() => navigate("/admin/articles/new")}
              className="flex items-center gap-2"
            >
              <Plus size={16} />
              記事を作成
            </Button>
          </div>
          
          <Card>
            <CardHeader>
              <CardTitle>記事一覧</CardTitle>
              <CardDescription>
                全{articles.length}件の記事
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="py-8 text-center">
                  <p className="text-gray-500">読み込み中...</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>タイトル</TableHead>
                      <TableHead>カテゴリ</TableHead>
                      <TableHead>公開状態</TableHead>
                      <TableHead>閲覧数</TableHead>
                      <TableHead>公開日</TableHead>
                      <TableHead className="text-right">アクション</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {articles.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                          記事がありません
                        </TableCell>
                      </TableRow>
                    ) : (
                      articles.map((article) => (
                        <TableRow key={article.id}>
                          <TableCell className="font-medium max-w-xs truncate">
                            {article.title}
                          </TableCell>
                          <TableCell>
                            <span className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full">
                              {article.category}
                            </span>
                          </TableCell>
                          <TableCell>
                            {article.is_published ? (
                              <span className="text-green-600 flex items-center gap-1">
                                <Eye size={14} />
                                公開中
                              </span>
                            ) : (
                              <span className="text-gray-500 flex items-center gap-1">
                                <EyeOff size={14} />
                                非公開
                              </span>
                            )}
                          </TableCell>
                          <TableCell>{article.views.toLocaleString()}</TableCell>
                          <TableCell>{formatDate(article.published_at)}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => togglePublishStatus(article)}
                                title={article.is_published ? "非公開にする" : "公開する"}
                              >
                                {article.is_published ? <EyeOff size={16} /> : <Eye size={16} />}
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => navigate(`/admin/articles/edit/${article.id}`)}
                              >
                                <Edit size={16} />
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDelete(article.id)}
                                className="text-red-500 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 size={16} />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminArticles;
