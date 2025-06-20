
import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { Clock, Calendar, BellRing, MailCheck, Github } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { motion } from "framer-motion";
import { useToast } from "@/hooks/use-toast";

const DemoComingSoon = () => {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const [timeLeft, setTimeLeft] = useState({
    days: 15,
    hours: 8,
    minutes: 30,
    seconds: 0
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev.seconds > 0) {
          return { ...prev, seconds: prev.seconds - 1 };
        } else if (prev.minutes > 0) {
          return { ...prev, minutes: prev.minutes - 1, seconds: 59 };
        } else if (prev.hours > 0) {
          return { ...prev, hours: prev.hours - 1, minutes: 59, seconds: 59 };
        } else if (prev.days > 0) {
          return { ...prev, days: prev.days - 1, hours: 23, minutes: 59, seconds: 59 };
        }
        return prev;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);

  const handleNotify = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      toast({
        title: "メールアドレスを入力してください",
        variant: "destructive"
      });
      return;
    }
    
    setIsLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      toast({
        title: "登録が完了しました",
        description: "デモ公開時にご連絡いたします",
        variant: "default"
      });
      setEmail("");
    }, 1000);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Helmet>
        <title>準備中 | ワークメイトAI 無料デモ体験</title>
        <meta name="description" content="ワークメイトAI無料デモ版は現在準備中です。公開まで今しばらくお待ちください。メールアドレスをご登録いただくと、公開時にご連絡いたします。" />
        <meta name="robots" content="noindex, follow" />
      </Helmet>
      
      <Navbar />
      
      <main className="flex-1 bg-gradient-to-b from-blue-50 to-white py-16 md:py-24">
        <div className="container mx-auto px-4">
          <motion.div 
            className="max-w-4xl mx-auto text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-block mb-6 bg-blue-100 p-3 rounded-xl">
              <Clock className="h-8 w-8 text-blue-600" />
            </div>
            
            <h1 className="text-4xl md:text-5xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-700">
              無料デモ準備中
            </h1>
            
            <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
              ワークメイトAIの無料デモ版は現在開発中です。
              より良い体験をお届けするため、今しばらくお待ちください。
            </p>
            
            {/* Countdown Timer */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
              <CountdownItem value={timeLeft.days} label="日" />
              <CountdownItem value={timeLeft.hours} label="時間" />
              <CountdownItem value={timeLeft.minutes} label="分" />
              <CountdownItem value={timeLeft.seconds} label="秒" />
            </div>
            
            {/* Features coming soon */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
              <FeatureCard 
                icon={<BellRing className="h-6 w-6 text-blue-600" />}
                title="リリース通知"
                description="メールアドレスを登録すると、デモ版公開時にすぐお知らせします"
              />
              <FeatureCard 
                icon={<Github className="h-6 w-6 text-blue-600" />}
                title="オープンソース"
                description="ワークメイトAIは最新のAI技術を活用したオープンプラットフォームです"
              />
              <FeatureCard 
                icon={<Calendar className="h-6 w-6 text-blue-600" />}
                title="早期アクセス"
                description="登録者には早期アクセス特典をご用意しています"
              />
            </div>
            
            {/* Notification Form */}
            <div className="bg-white p-8 rounded-2xl shadow-lg max-w-xl mx-auto border border-gray-100">
              <h3 className="text-xl font-semibold mb-4">
                デモ版公開時にお知らせします
              </h3>
              <form onSubmit={handleNotify} className="flex flex-col sm:flex-row gap-3">
                <Input
                  type="email"
                  placeholder="メールアドレスを入力"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="flex-1"
                />
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? (
                    <span className="flex items-center">
                      <span className="animate-spin mr-2 h-4 w-4 border-2 border-white border-r-transparent rounded-full"></span>
                      送信中...
                    </span>
                  ) : (
                    <span className="flex items-center">
                      <MailCheck className="mr-2 h-4 w-4" />
                      登録する
                    </span>
                  )}
                </Button>
              </form>
              <p className="text-xs text-gray-500 mt-3">
                ※ お客様の個人情報は当社プライバシーポリシーに基づき適切に管理いたします
              </p>
            </div>
          </motion.div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

const CountdownItem = ({ value, label }: { value: number; label: string }) => {
  return (
    <div className="bg-white rounded-xl p-4 shadow-md border border-gray-100">
      <div className="text-3xl md:text-4xl font-bold text-blue-600">{value}</div>
      <div className="text-gray-500">{label}</div>
    </div>
  );
};

const FeatureCard = ({ 
  icon, 
  title, 
  description 
}: { 
  icon: React.ReactNode; 
  title: string; 
  description: string 
}) => {
  return (
    <motion.div 
      className="bg-white p-6 rounded-xl shadow-sm border border-gray-100"
      whileHover={{ y: -5, boxShadow: "0 10px 30px -15px rgba(0,0,0,0.1)" }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-center justify-center mb-4 bg-blue-50 w-12 h-12 rounded-full mx-auto">
        {icon}
      </div>
      <h3 className="text-lg font-medium mb-2 text-center">{title}</h3>
      <p className="text-gray-600 text-center text-sm">{description}</p>
    </motion.div>
  );
};

export default DemoComingSoon;
