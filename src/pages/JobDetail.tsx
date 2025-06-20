
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import JobBasicInfo from "@/components/job/JobBasicInfo";
import JobDescription from "@/components/job/JobDescription";
import JobRequirements from "@/components/job/JobRequirements";
import { ApplicationSidebar } from "@/components/job/ApplicationSidebar";

interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  type: string;
  description: string;
  requirements: string[];
  salary: string;
  postedDate: string;
  applicationDeadline: string;
  contactEmail: string;
  companyLogo: string;
  // Added fields to match JobBasicInfo component requirements
  department?: string;
  schedule?: string;
  // Added fields to match JobRequirements component
  preferred?: string[];
  // Added fields to match JobDescription component
  responsibilities?: string[];
}

const JobDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchJob = async () => {
      try {
        setLoading(true);
        // Simulate fetching job data from an API
        await new Promise((resolve) => setTimeout(resolve, 500));

        const mockJobData: Job[] = [
          {
            id: 1,
            title: "フロントエンドエンジニア",
            company: "株式会社ABC",
            location: "東京都",
            type: "正社員",
            description: "React, TypeScriptを用いたWebアプリケーション開発",
            requirements: ["React", "TypeScript", "JavaScript", "HTML", "CSS"],
            salary: "年収600万円〜800万円",
            postedDate: "2024-04-01",
            applicationDeadline: "2024-04-30",
            contactEmail: "jobs@abc.com",
            companyLogo: "https://via.placeholder.com/100",
            // Added fields
            department: "エンジニアリング部",
            schedule: "週5日（リモート可）",
            responsibilities: [
              "新機能の実装とテスト",
              "既存コードの保守と改善",
              "技術文書の作成",
              "チームメンバーとの協業"
            ],
            preferred: [
              "Vue.js経験",
              "モバイルアプリ開発経験",
              "アジャイル開発経験"
            ]
          },
          {
            id: 2,
            title: "バックエンドエンジニア",
            company: "株式会社XYZ",
            location: "大阪府",
            type: "業務委託",
            description: "Node.js, AWSを用いたAPI開発",
            requirements: ["Node.js", "AWS", "JavaScript", "REST API"],
            salary: "月額50万円〜70万円",
            postedDate: "2024-04-05",
            applicationDeadline: "2024-05-05",
            contactEmail: "jobs@xyz.com",
            companyLogo: "https://via.placeholder.com/100",
            // Added fields
            department: "サーバーインフラ部門",
            schedule: "フレックスタイム制",
            responsibilities: [
              "バックエンドAPIの設計と実装",
              "データベース設計",
              "インフラ構築と運用",
              "パフォーマンス最適化"
            ],
            preferred: [
              "Python経験",
              "Docker/Kubernetes経験",
              "CI/CD経験"
            ]
          },
          {
            id: 3,
            title: "UI/UXデザイナー",
            company: "株式会社123",
            location: "福岡県",
            type: "アルバイト",
            description: "Figma, Adobe XDを用いたWebサイトデザイン",
            requirements: ["Figma", "Adobe XD", "UIデザイン", "UXデザイン"],
            salary: "時給1500円〜2000円",
            postedDate: "2024-04-10",
            applicationDeadline: "2024-05-10",
            contactEmail: "jobs@123.com",
            companyLogo: "https://via.placeholder.com/100",
            // Added fields
            department: "デザイン部",
            schedule: "週3日〜",
            responsibilities: [
              "UIデザインの作成",
              "ユーザビリティテスト実施",
              "デザインシステムの構築",
              "プロトタイプ作成"
            ],
            preferred: [
              "Illustrator/Photoshop経験",
              "モーショングラフィックス経験",
              "コーディング経験（HTML/CSS）"
            ]
          },
        ];

        const foundJob = mockJobData.find((j) => j.id === Number(id));

        if (foundJob) {
          setJob(foundJob);
        } else {
          setError("求人が見つかりませんでした。");
        }
      } catch (err) {
        setError("求人の取得に失敗しました。");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchJob();
  }, [id]);

  if (loading) {
    return (
      <div className="container mx-auto p-4">
        <p>ロード中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <p>エラー: {error}</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="container mx-auto p-4">
        <p>求人が見つかりませんでした。</p>
      </div>
    );
  }

  // Create a job object compatible with JobBasicInfo
  const jobBasicInfo = {
    department: job.department || job.company, // Fallback to company if department is not available
    type: job.type,
    location: job.location,
    schedule: job.schedule || "未設定" // Provide a default value
  };

  // Create job objects for other components
  const jobDescription = {
    description: job.description,
    responsibilities: job.responsibilities || []
  };

  const jobRequirements = {
    requirements: job.requirements,
    preferred: job.preferred || []
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-grow">
        <div className="container mx-auto p-4 md:p-6 lg:p-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <Button variant="ghost" className="mb-4 group" asChild>
                <Link to="/recruitment" className="flex items-center">
                  <ArrowLeft className="mr-2 h-4 w-4 transition group-hover:-translate-x-1" />
                  戻る
                </Link>
              </Button>
              <div className="space-y-8">
                <JobBasicInfo job={jobBasicInfo} />
                <div className="space-y-6">
                  <div>
                    <JobDescription job={jobDescription} />
                  </div>
                  <div>
                    <JobRequirements job={jobRequirements} />
                  </div>
                </div>
              </div>
            </div>
            <div>
              <ApplicationSidebar />
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default JobDetail;
