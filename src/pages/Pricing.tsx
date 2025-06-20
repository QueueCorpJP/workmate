import { Helmet } from "react-helmet-async";
import Layout from "@/components/layout/Layout";
import { Link } from "react-router-dom";

const PricingCard = ({ plan, users, price }: { plan: string; users: string; price: string }) => {
  return (
    <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-100 hover:border-primary/20 hover:shadow-xl transition-all duration-200">
      <div className="bg-gray-100 text-gray-700 py-2 px-4 rounded-full text-sm font-medium inline-block mb-6">
        {users}
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-4">{plan}</h3>
      <div className="mb-6">
        <span className="text-4xl font-bold text-gray-900">{price}</span>
        <span className="text-gray-600 ml-2">円/月</span>
      </div>
      <ul className="space-y-3 text-gray-600">
        <li className="flex items-center">
          <svg className="w-5 h-5 text-primary mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          AIチャットボット機能
        </li>
        <li className="flex items-center">
          <svg className="w-5 h-5 text-primary mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          社内文書の検索・参照
        </li>
        <li className="flex items-center">
          <svg className="w-5 h-5 text-primary mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          24時間365日利用可能
        </li>
      </ul>
    </div>
  );
};

const Pricing = () => {
  return (
    <Layout>
      <Helmet>
        <title>料金プラン | Queue</title>
        <meta name="description" content="Queueの料金プラン一覧。利用人数に応じた最適なプランをご用意しています。初期費用不要で、固定料金のみのシンプルな料金体系です。" />
      </Helmet>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">料金プラン</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            基本的に初期費用は不要で、利用人数に応じた固定料金のみで、利用頻度が増えても追加料金はかかりません。
            ただし、カスタマイズをご希望の場合は別途初期費用が発生します。
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <svg className="w-8 h-8 text-primary mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              圧倒的な柔軟性
            </h2>
            <ul className="space-y-4">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-primary mr-2 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                <span>YouTube、ウェブサイト、スプレッドシート、OCR対応PDFなど、<span className="text-primary font-medium">あらゆる情報ソースに対応</span></span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-primary mr-2 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                <span>情報ソースの<span className="text-primary font-medium">適用方法を細かくカスタマイズ可能</span></span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-primary mr-2 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                <span>ご要望に応じて<span className="text-primary font-medium">多言語対応も可能</span>（詳細はお問い合わせください）</span>
              </li>
            </ul>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <svg className="w-8 h-8 text-primary mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              優れた使いやすさ
            </h2>
            <ul className="space-y-4">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-primary mr-2 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                <span>情報ソースをアップロードした瞬間から<span className="text-primary font-medium">すぐに利用開始可能</span>。FAQの個別設定は不要</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-primary mr-2 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                <span>ユーザーの意図を<span className="text-primary font-medium">正確に理解し、的確な回答を提供</span></span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-primary mr-2 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                <span>各回答に<span className="text-primary font-medium">参照元の情報ソースを明示</span>し、信頼性を担保</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <PricingCard plan="プランA" users="使用数1～10名" price="50,000" />
          <PricingCard plan="プランB" users="使用数11名～30名" price="100,000" />
          <PricingCard plan="プランC" users="使用数31名～50名" price="150,000" />
          <PricingCard plan="プランD" users="使用数51名～100名" price="250,000" />
          <PricingCard plan="プランE" users="使用数101名～200名" price="325,000" />
          <PricingCard plan="プランF" users="使用数201名～300名" price="400,000" />
        </div>

        <div className="text-center mt-12 text-gray-600">
          ※ 300名以上の場合は別途相談させていただきます
        </div>

        <div className="mt-16 bg-gradient-to-br from-primary/5 to-primary/10 rounded-2xl p-8 sm:p-10 md:p-12">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
              いつでもすぐに始められます！
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              わかりやすい機能ガイドと使い方マニュアルをご用意しています。<br />
              導入後すぐにチームで活用できます。
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/guide"
                className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary hover:bg-primary/90 transition-colors duration-200 w-full sm:w-auto"
              >
                機能ガイドを見る
              </Link>
              <Link
                to="/contact"
                className="inline-flex items-center justify-center px-6 py-3 border border-primary text-base font-medium rounded-md text-primary bg-white hover:bg-primary/5 transition-colors duration-200 w-full sm:w-auto"
              >
                お問い合わせ
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-16 text-center">
          <a
            href="/contact"
            className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary hover:bg-primary/90 transition-colors duration-200"
          >
            お問い合わせ
          </a>
        </div>
      </div>
    </Layout>
  );
};

export default Pricing; 