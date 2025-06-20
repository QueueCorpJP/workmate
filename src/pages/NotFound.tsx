
import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname
    );
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4 sm:p-6">
      <Helmet>
        <title>ページが見つかりません | ワークメイトAI</title>
        <meta name="description" content="お探しのページは移動または削除された可能性があります。ワークメイトAIのホームページにお戻りください。" />
        <meta name="robots" content="noindex, follow" />
      </Helmet>
      
      <div className="max-w-md w-full text-center px-4 py-8 sm:py-12 rounded-lg bg-white/80 backdrop-blur-sm shadow-sm">
        <div className="mb-8 text-primary">
          <div className="text-7xl sm:text-9xl font-bold">404</div>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold mb-4 text-gray-900">ページが見つかりません</h1>
        <p className="text-lg sm:text-xl text-gray-600 mb-8">
          お探しのページは移動または削除された可能性があります。
        </p>
        <Button asChild size="lg" className="bg-primary hover:bg-primary/90 text-white">
          <Link to="/">
            ホームに戻る
          </Link>
        </Button>
      </div>
    </div>
  );
};

export default NotFound;
