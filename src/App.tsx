import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/toaster";
import { HelmetProvider, Helmet } from "react-helmet-async";
import Index from "./pages/Index";
import About from "./pages/About";
import Privacy from "./pages/Privacy";
import Terms from "./pages/Terms";
import Contact from "./pages/Contact";
import HelpCenter from "./pages/HelpCenter";
import NotFound from "./pages/NotFound";
import Recruitment from "./pages/Recruitment";
import JobDetail from "./pages/JobDetail";
import JobApplication from "./pages/JobApplication";
import Login from "./pages/Login";
import Download from "./pages/Download";
import Guide from "./pages/Guide";
import Admin from "./pages/Admin";
import AdminUsers from "./pages/AdminUsers";
import AdminSettings from "./pages/AdminSettings";
import AdminAnalytics from "./pages/AdminAnalytics";
import AdminKnowledgeBase from "./pages/AdminKnowledgeBase";
import { Toaster as SonnerToaster } from "sonner";
import AdminArticles from "./pages/AdminArticles";
import ArticleForm from "./pages/ArticleForm";
import ArticleDetail from "./pages/ArticleDetail";
import ArticleList from "./pages/ArticleList";
import ServiceStatus from "./pages/ServiceStatus";
import DemoComingSoon from "./pages/DemoComingSoon";
import AdminContacts from "./pages/AdminContacts";
import { AuthProvider } from "./context/AuthContext";
import Dashboard from "./pages/Dashboard";
import ScrollToTop from "@/components/utils/ScrollToTop";
import Pricing from "./pages/Pricing";
import { Blog } from "./pages/Blog";
import { BlogPost } from "./pages/BlogPost";
import Register from "./pages/Register";
import PrivateRoute from "./components/PrivateRoute";

export default function App() {
  return (
    <HelmetProvider>
      <Router>
        <AuthProvider>
          <ScrollToTop />
          <Helmet>
            <meta name="description" content="ワークメイトAI - 業務効率を飛躍的に高めるAIチャットボット。社内情報へのアクセスを迅速化し、日々の業務フローをスマートにする次世代の社内コミュニケーションツール。" />
            <meta name="keywords" content="ワークメイトAI, AI, チャットボット, 業務効率化, 生産性向上, 社内チャットボット, AI業務支援, 自然言語処理, 社内知識検索" />
            <meta property="og:title" content="ワークメイトAI | 次世代の業務効率化チャットボット" />
            <meta property="og:description" content="ワークメイトAIが提供する効率的な業務サポートのためのAIチャットボット - 業務効率化の新しいカタチ" />
            <meta property="og:type" content="website" />
            <meta property="og:site_name" content="ワークメイトAI" />
            <meta name="twitter:card" content="summary_large_image" />
            <meta name="twitter:title" content="ワークメイトAI | 次世代の業務効率化チャットボット" />
            <meta name="twitter:description" content="ワークメイトAIが提供する効率的な業務サポートのためのAIチャットボット" />
          </Helmet>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/about" element={<About />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/help" element={<HelpCenter />} />
            <Route path="/recruitment" element={<Recruitment />} />
            <Route path="/recruitment/:id" element={<JobDetail />} />
            <Route path="/apply/:id" element={<JobApplication />} />
            <Route path="/apply" element={<JobApplication />} />
            <Route path="/login" element={<Login />} />
            <Route path="/download" element={<Download />} />
            <Route path="/guide" element={<Guide />} />
            <Route path="/articles" element={<ArticleList />} />
            <Route path="/articles/:slug" element={<ArticleDetail />} />
            <Route path="/status" element={<ServiceStatus />} />
            <Route path="/demo" element={<DemoComingSoon />} />
            <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/admin/contacts" element={<AdminContacts />} />
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/admin/settings" element={<AdminSettings />} />
            <Route path="/admin/analytics" element={<AdminAnalytics />} />
            <Route path="/admin/knowledge" element={<AdminKnowledgeBase />} />
            <Route path="/admin/articles" element={<AdminArticles />} />
            <Route path="/admin/articles/new" element={<ArticleForm />} />
            <Route path="/admin/articles/edit/:id" element={<ArticleForm />} />
            <Route path="/blog" element={<Blog />} />
            <Route path="/blog/:id" element={<BlogPost />} />
            <Route path="/register" element={<Register />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
          <Toaster />
          <SonnerToaster position="top-center" closeButton />
        </AuthProvider>
      </Router>
    </HelmetProvider>
  );
}
