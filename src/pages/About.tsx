import React from "react";
import LegalPageLayout from "@/components/layout/LegalPageLayout";
import { Card, CardContent } from "@/components/ui/card";
import { Building, Users, Award, Landmark, MapPin, CalendarDays } from "lucide-react";
import { Helmet } from "react-helmet-async";

const About = () => {
  return (
    <>
      <Helmet>
        <title>会社概要 | ワークメイトAI - 次世代AI業務支援ソリューション</title>
        <meta name="description" content="Queue株式会社が提供するワークメイトAIは、最先端のAI技術を活用して企業の業務効率化と生産性向上を支援します。私たちの企業理念やミッション、経営陣、そして会社沿革についてご紹介します。" />
        <meta name="keywords" content="ワークメイトAI, Queue株式会社, AI業務支援, AIチャットボット, 企業概要, 会社沿革, AI技術" />
        <meta property="og:title" content="会社概要 | ワークメイトAI" />
        <meta property="og:description" content="Queue株式会社が提供するワークメイトAIは、最先端のAI技術を活用して企業の業務効率化と生産性向上を支援します。" />
        <meta property="og:type" content="website" />
        <link rel="canonical" href="https://www.workmate-ai.jp/about" />
      </Helmet>
      
      <LegalPageLayout title="会社概要" updatedDate="2024年4月1日">
        <section className="mb-12">
          <p className="text-lg text-gray-600 leading-relaxed mb-8">
            Queue株式会社は、次世代型AI業務支援ツール「ワークメイトAI」を提供する会社です。私たちは最先端のAI技術を活用し、企業の業務効率化と生産性向上を支援しています。
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-10">
            <CompanyInfoCard 
              icon={<Building />}
              title="会社名"
              value="Queue株式会社"
            />
            <CompanyInfoCard 
              icon={<CalendarDays />}
              title="設立"
              value="2024年4月1日"
            />
            <CompanyInfoCard 
              icon={<Landmark />}
              title="資本金"
              value="115万円"
            />
            <CompanyInfoCard 
              icon={<Users />}
              title="従業員数"
              value="7名（2025年現在）"
            />
            <CompanyInfoCard 
              icon={<MapPin />}
              title="本社所在地"
              value="〒104-0061 東京都中央区銀座一丁目22番11号 銀座大竹ビジデンス 2F"
            />
            <CompanyInfoCard 
              icon={<Award />}
              title="事業内容"
              value="AIシステム・AIエージェントの開発、AIアバターの開発・カスタマイズ、業務システムの受託開発、AI技術に関するコンサルティング、AI業務支援ツールの開発・販売"
            />
          </div>
        </section>

        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-6">企業理念</h2>
          <div className="p-6 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100">
            <p className="text-xl font-medium text-center text-gray-800 mb-4">
              「テクノロジーの力で、人々の働き方を豊かに」
            </p>
            <p className="text-gray-600">
              私たちは、最新のAI技術を活用して、ビジネスパーソンの日常業務をサポートし、創造的で価値のある仕事に集中できる環境を提供します。
              単なる効率化だけでなく、人間らしい働き方と技術革新が共存する未来を目指しています。
            </p>
          </div>
        </section>

        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-6">経営陣</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <ExecutiveCard 
              name="谷口 太一（ジョン）"
              position="代表取締役社長 / CEO"
              bio="6歳のころからプログラミングを始め、圧倒的な技術力を持つ。ニュージーランド大学工学部を飛び級卒業。AI分野における豊富な経験を活かし、2024年に当社を創業。"
            />
            <ExecutiveCard 
              name="渡辺 一輝ジェームス"
              position="取締役 / COO"
              bio="ニュージーランドのハーフとして、多言語を操る圧倒的な行動力とグローバルな視点を持つ無敵営業マン。"
            />
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-bold mb-6">沿革</h2>
          <div className="space-y-6">
            <TimelineItem 
              year="2024年4月" 
              title="創業"
              description="Queue株式会社として創業。"
            />
            <TimelineItem 
              year="2024年9月" 
              title="資金調達"
              description="スカイランドベンチャーズから1,500万円の資金調達を実施。"
            />
            <TimelineItem 
              year="2025年4月" 
              title="ワークメイトAIリリース"
              description="ワークメイトAIをリリースし、複数社と提携開始。"
            />
          </div>
        </section>
      </LegalPageLayout>
    </>
  );
};

const CompanyInfoCard = ({ icon, title, value }: { icon: React.ReactNode; title: string; value: string }) => {
  return (
    <Card className="overflow-hidden border-gray-100 hover:shadow-md transition-shadow">
      <CardContent className="p-6 flex items-start">
        <div className="mr-4 p-3 rounded-full bg-primary/10 text-primary">
          {icon}
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500">{title}</h3>
          <p className="text-lg font-medium text-gray-900 mt-1">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
};

const ExecutiveCard = ({ name, position, bio }: { name: string; position: string; bio: string }) => {
  return (
    <Card className="overflow-hidden border-gray-100 hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <h3 className="text-xl font-bold text-gray-900">{name}</h3>
        <p className="text-primary font-medium mt-1 mb-3">{position}</p>
        <p className="text-gray-600">{bio}</p>
      </CardContent>
    </Card>
  );
};

const TimelineItem = ({ year, title, description }: { year: string; title: string; description: string }) => {
  return (
    <div className="flex">
      <div className="flex flex-col items-center mr-6">
        <div className="w-px h-full bg-gray-200 pointer-events-none"></div>
        <div className="w-4 h-4 rounded-full bg-primary border-4 border-white shadow"></div>
      </div>
      <div className="pb-8">
        <p className="text-sm font-medium text-primary">{year}</p>
        <h3 className="text-lg font-bold text-gray-900 mt-1">{title}</h3>
        <p className="mt-2 text-gray-600">{description}</p>
      </div>
    </div>
  );
};

export default About;
