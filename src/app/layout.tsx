import { Toaster } from "@/components/ui/toaster";
import { Toaster as SonnerToaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import ScrollToTop from "@/components/utils/ScrollToTop";
import "@/index.css";

export const metadata = {
  title: "ワークメイトAI | 次世代の業務効率化チャットボット",
  description: "ワークメイトAIが提供する効率的な業務サポートのためのAIチャットボット - 業務効率化の新しいカタチ",
  keywords: "ワークメイトAI, AI, チャットボット, 業務効率化, 生産性向上, 社内チャットボット, AI業務支援, 自然言語処理, 社内知識検索",
  openGraph: {
    title: "ワークメイトAI | 次世代の業務効率化チャットボット",
    description: "ワークメイトAIが提供する効率的な業務サポートのためのAIチャットボット",
    type: "website",
    siteName: "ワークメイトAI",
  },
  twitter: {
    card: "summary_large_image",
    title: "ワークメイトAI | 次世代の業務効率化チャットボット",
    description: "ワークメイトAIが提供する効率的な業務サポートのためのAIチャットボット",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>
        <AuthProvider>
          <ScrollToTop />
          {children}
          <Toaster />
          <SonnerToaster position="top-center" closeButton />
        </AuthProvider>
      </body>
    </html>
  );
} 