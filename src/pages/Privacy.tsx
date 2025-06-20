import React from "react";
import LegalPageLayout from "@/components/layout/LegalPageLayout";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Info, CheckSquare } from "lucide-react";
import { Helmet } from "react-helmet-async";

const Privacy = () => {
  return (
    <>
      <Helmet>
        <title>プライバシーポリシー | Queue株式会社</title>
        <meta name="description" content="Queue株式会社のプライバシーポリシーです。当社がどのようにお客様の情報を収集、使用、保護するかについてご説明します。" />
        <meta name="keywords" content="プライバシーポリシー, 個人情報保護, Queue株式会社, データセキュリティ" />
        <meta property="og:title" content="プライバシーポリシー | Queue株式会社" />
        <meta property="og:description" content="Queue株式会社のプライバシーポリシーです。当社がどのようにお客様の情報を収集、使用、保護するかについて説明します。" />
        <meta property="og:type" content="website" />
        <link rel="canonical" href="https://www.queue-ai.co.jp/privacy" />
      </Helmet>

      <LegalPageLayout title="プライバシーポリシー" updatedDate="2025年3月26日">
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-8 flex items-start">
          <Info className="text-blue-500 mr-3 mt-1 flex-shrink-0" />
          <p className="text-sm text-blue-700">
            株式会社ワークメイト（以下「当社」）は、お客様のプライバシーを尊重し、個人情報の保護に努めています。
            このプライバシーポリシーでは、当社がどのようにお客様の情報を収集、使用、保護するかについて説明します。
          </p>
        </div>

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-4">1. 収集する情報</h2>
          <p className="mb-4">当社は、以下の個人情報を収集することがあります：</p>
          <ul className="list-disc pl-6 space-y-2 mb-4">
            <li>お名前、メールアドレス、電話番号などの連絡先情報</li>
            <li>会社名、部署、役職などの勤務先情報</li>
            <li>IPアドレス、ブラウザの種類、アクセス日時などの利用ログ情報</li>
            <li>サービス利用履歴、検索履歴などの利用状況に関する情報</li>
            <li>お問い合わせやサポートリクエストの内容</li>
          </ul>
          <p>
            当社は、クッキー（Cookies）などの技術を使用して、お客様がサービスをどのように利用しているかに関する情報を自動的に収集する場合があります。
          </p>
        </section>

        <Separator className="my-8" />

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-4">2. 情報の利用目的</h2>
          <p className="mb-4">収集した個人情報は、以下の目的で利用します：</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <PolicyCard title="サービス提供" description="ワークメイトAIサービスの提供、維持、改善のため" />
            <PolicyCard title="カスタマーサポート" description="お問い合わせやサポートリクエストへの対応" />
            <PolicyCard title="サービス改善" description="ユーザー体験の向上とサービス品質の改善" />
            <PolicyCard title="コミュニケーション" description="重要な更新情報や新機能のお知らせ" />
          </div>
          <p>
            当社は、お客様の同意なく、上記の目的以外で個人情報を利用することはありません。
          </p>
        </section>

        <Separator className="my-8" />

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-4">3. 情報の共有と開示</h2>
          <p className="mb-4">当社は、以下の場合を除き、お客様の個人情報を第三者と共有することはありません：</p>
          <ul className="list-disc pl-6 space-y-2 mb-4">
            <li>お客様の同意がある場合</li>
            <li>サービス提供に必要な範囲で、信頼できる業務委託先と共有する場合</li>
            <li>法的な要請に応じる必要がある場合</li>
            <li>当社の権利を保護する必要がある場合</li>
          </ul>
          <p>
            当社がお客様の情報を共有する場合、その取り扱いについて適切な契約上の保護措置を講じます。
          </p>
        </section>

        <Separator className="my-8" />

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-4">4. データセキュリティ</h2>
          <p className="mb-4">
            当社は、お客様の個人情報を不正アクセス、紛失、改ざん、漏洩から保護するため、適切な技術的・組織的措置を講じています。
            ただし、インターネット上のデータ転送や電子ストレージの方法は、100%安全ではないことをご了承ください。
          </p>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
            <h3 className="text-lg font-medium mb-3">セキュリティ対策</h3>
            <ul className="space-y-2">
              <li className="flex items-start">
                <CheckSquare className="text-green-500 mr-2 mt-1 flex-shrink-0" />
                <span>SSL暗号化による通信の保護</span>
              </li>
              <li className="flex items-start">
                <CheckSquare className="text-green-500 mr-2 mt-1 flex-shrink-0" />
                <span>アクセス制御と認証システムの実装</span>
              </li>
              <li className="flex items-start">
                <CheckSquare className="text-green-500 mr-2 mt-1 flex-shrink-0" />
                <span>定期的なセキュリティ監査とシステム更新</span>
              </li>
              <li className="flex items-start">
                <CheckSquare className="text-green-500 mr-2 mt-1 flex-shrink-0" />
                <span>従業員に対するプライバシー研修の実施</span>
              </li>
            </ul>
          </div>
        </section>

        <Separator className="my-8" />

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-4">5. データ保持</h2>
          <p>
            当社は、サービス提供に必要な期間、または法的義務を遵守するために必要な期間、お客様の個人情報を保持します。
            不要になった個人情報は、安全な方法で削除または匿名化されます。
          </p>
        </section>

        <Separator className="my-8" />

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-4">6. お客様の権利</h2>
          <p className="mb-4">お客様は、ご自身の個人情報に関して以下の権利を有しています：</p>
          <ul className="list-disc pl-6 space-y-2 mb-4">
            <li>個人情報へのアクセス権</li>
            <li>個人情報の訂正権</li>
            <li>個人情報の削除権（適用される法律による制限がある場合があります）</li>
            <li>個人情報の処理に対する制限権</li>
            <li>データポータビリティの権利</li>
          </ul>
          <p className="mb-6">
            これらの権利を行使するには、下記の連絡先までお問い合わせください。
          </p>
          <Button className="bg-primary hover:bg-primary/90">お問い合わせフォームへ</Button>
        </section>

        <Separator className="my-8" />

        <section className="mb-10">
          <h2 className="text-xl font-bold mb-4">7. プライバシーポリシーの変更</h2>
          <p>
            当社は、必要に応じてこのプライバシーポリシーを更新することがあります。
            重要な変更がある場合は、サービス内での通知やメールによる連絡など、適切な方法でお知らせします。
            定期的にプライバシーポリシーを確認することをお勧めします。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-4">8. お問い合わせ</h2>
          <p className="mb-4">
            このプライバシーポリシーに関するご質問やご不明点がございましたら、以下の連絡先までお問い合わせください：
          </p>
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-100">
            <h3 className="font-medium text-gray-900 mb-2">株式会社Queue 個人情報保護窓口</h3>
            <p className="text-gray-600">
              住所：〒104-0061 東京都中央区銀座一丁目22番11号 銀座大竹ビジデンス 2F<br />
              メール：queue@queuefood.co.jp<br />
              電話：03-6687-0550（平日9:00-18:00）
            </p>
          </div>
        </section>
      </LegalPageLayout>
    </>
  );
};

const PolicyCard = ({ title, description }: { title: string; description: string }) => {
  return (
    <div className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
      <h3 className="font-medium text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
};

export default Privacy;
