import React from "react";
import LegalPageLayout from "@/components/layout/LegalPageLayout";
import { Separator } from "@/components/ui/separator";
import { AlertTriangle, ShieldAlert } from "lucide-react";

const Terms = () => {
  return (
    <LegalPageLayout title="利用規約" updatedDate="2025年3月26日">
      <div className="bg-amber-50 border border-amber-100 rounded-lg p-4 mb-8 flex items-start">
        <AlertTriangle className="text-amber-500 mr-3 mt-1 flex-shrink-0" />
        <div className="text-sm text-amber-700">
          <p className="font-medium mb-1">重要なお知らせ</p>
          <p>
            本サービスをご利用になる前に、以下の利用規約を注意深くお読みください。
            本サービスを利用することにより、お客様はこの利用規約に同意したものとみなされます。
          </p>
        </div>
      </div>

      <section className="mb-10">
        <h2 className="text-xl font-bold mb-4">1. はじめに</h2>
        <p className="mb-4">
          この利用規約（以下「本規約」）は、株式会社ワークメイト（以下「当社」）が提供するサービス「ワークメイトAI」（以下「本サービス」）の利用条件を定めるものです。
          本規約は、本サービスを利用するすべての個人または法人（以下「利用者」）に適用されます。
        </p>
        <div className="p-4 rounded-lg bg-gray-50 border border-gray-100">
          <h3 className="font-medium text-gray-900 mb-2">適用範囲</h3>
          <p className="text-gray-600 text-sm">
            本規約は、本サービスのすべての機能、コンテンツ、関連ウェブサイト、および当社が提供するAPIを含むすべてのサービスに適用されます。
            本サービスを利用することにより、利用者は本規約に同意したものとみなされます。
          </p>
        </div>
      </section>

      <Separator className="my-8" />

      <section className="mb-10">
        <h2 className="text-xl font-bold mb-4">2. サービスの内容</h2>
        <p className="mb-4">
          本サービスは、AI技術を用いた業務支援ツールであり、以下の機能を提供します：
        </p>
        <ul className="list-disc pl-6 space-y-2 mb-4">
          <li>ビジネス文書の作成・編集支援</li>
          <li>社内情報の検索・集約</li>
          <li>業務プロセスの自動化支援</li>
          <li>データ分析とインサイト提供</li>
          <li>チーム間のコミュニケーション支援</li>
        </ul>
        <p className="mb-4">
          当社は、本サービスの品質向上のため、予告なくサービス内容を変更、追加、または中止する場合があります。
          重要な変更がある場合は、事前に通知するよう努めます。
        </p>
      </section>

      <Separator className="my-8" />

      <section className="mb-10">
        <h2 className="text-xl font-bold mb-4">3. アカウント</h2>
        <p className="mb-4">
          本サービスの利用には、アカウントの作成が必要です。アカウント作成時には、正確かつ最新の情報を提供してください。
          アカウントに関して、以下の点に同意していただきます：
        </p>
        <ul className="list-disc pl-6 space-y-2 mb-4">
          <li>アカウント情報（パスワード等）の秘密保持責任は利用者にあります</li>
          <li>アカウントの不正使用や不審な活動を発見した場合は、直ちに当社に報告してください</li>
          <li>一つのアカウントを複数の個人または法人で共有することはできません</li>
          <li>当社は、利用者のアカウントを保護するために適切な措置を講じますが、情報セキュリティに関する絶対的な保証はできません</li>
        </ul>
      </section>

      <Separator className="my-8" />

      <section className="mb-10">
        <h2 className="text-xl font-bold mb-4">4. 利用料金と支払い</h2>
        <p className="mb-4">
          本サービスの利用料金は、選択したプランに基づきます。料金プランと支払い条件は、当社のウェブサイトに記載されています。
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white p-6 rounded-lg border border-gray-100 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-4">料金の支払い</h3>
            <ul className="space-y-2 text-gray-600">
              <li>• 料金は、契約期間に応じて前払いとなります</li>
              <li>• 支払い方法は、クレジットカード、銀行振込、またはその他当社が指定する方法に限ります</li>
              <li>• 支払期日までに料金が支払われない場合、サービスの利用を一時停止することがあります</li>
              <li>• すべての料金は、特に明記されない限り、消費税を含みません</li>
            </ul>
          </div>
          <div className="bg-white p-6 rounded-lg border border-gray-100 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-4">返金ポリシー</h3>
            <ul className="space-y-2 text-gray-600">
              <li>• 初回契約から14日以内にサービスをキャンセルした場合、全額返金します</li>
              <li>• 14日を経過した後、または2回目以降の支払いについては、原則として返金はいたしません</li>
              <li>• サービスの重大な障害により長時間使用できなかった場合、当社の判断により一部返金することがあります</li>
            </ul>
          </div>
        </div>
      </section>

      <Separator className="my-8" />
      
      <section className="mb-10">
        <h2 className="text-xl font-bold mb-4">5. 禁止事項</h2>
        <p className="mb-4">
          本サービスを利用するにあたり、以下の行為を禁止します：
        </p>
        <div className="bg-red-50 border border-red-100 rounded-lg p-5 mb-6">
          <div className="flex items-center mb-3">
            <ShieldAlert className="text-red-500 mr-2" />
            <h3 className="font-semibold text-red-800">禁止行為</h3>
          </div>
          <ul className="space-y-3 text-red-700">
            <li className="flex items-start">
              <span className="font-medium mr-2">•</span>
              <span>法令に違反する行為、または違反を助長する行為</span>
            </li>
            <li className="flex items-start">
              <span className="font-medium mr-2">•</span>
              <span>当社または第三者の知的財産権、プライバシー権、その他の権利を侵害する行為</span>
            </li>
            <li className="flex items-start">
              <span className="font-medium mr-2">•</span>
              <span>本サービスの運営を妨害する行為（ハッキング、リバースエンジニアリングなど）</span>
            </li>
            <li className="flex items-start">
              <span className="font-medium mr-2">•</span>
              <span>不正確または虚偽の情報を提供する行為</span>
            </li>
            <li className="flex items-start">
              <span className="font-medium mr-2">•</span>
              <span>本サービスを通じて取得した情報を、当社の許可なく商業目的で利用する行為</span>
            </li>
            <li className="flex items-start">
              <span className="font-medium mr-2">•</span>
              <span>本サービスのセキュリティを回避または破壊しようとする行為</span>
            </li>
            <li className="flex items-start">
              <span className="font-medium mr-2">•</span>
              <span>その他、当社が不適切と判断する行為</span>
            </li>
          </ul>
        </div>
        <p>
          上記の禁止行為が確認された場合、当社はサービスの提供を一時停止または終了する権利を有します。
          また、当該行為によって当社に損害が生じた場合、法的措置を含む対応を取ることがあります。
        </p>
      </section>

      <Separator className="my-8" />

      <section className="mb-10">
        <h2 className="text-xl font-bold mb-4">6. 知的財産権</h2>
        <p className="mb-4">
          本サービスに関連するすべての知的財産権（著作権、商標権、特許権等）は、当社または正当な権利者に帰属します。
          本規約は、これらの権利をお客様に譲渡するものではありません。
        </p>
        <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 mb-4">
          <h3 className="font-medium text-gray-900 mb-2">利用者によるコンテンツ</h3>
          <p className="text-gray-600 text-sm">
            利用者が本サービスを通じて作成したコンテンツの知的財産権は、原則として利用者に帰属します。
            ただし、当社は、サービス提供、改善、宣伝のために、利用者のコンテンツを使用、複製、修正、配布、表示する非独占的な権利を有します。
          </p>
        </div>
      </section>

      <Separator className="my-8" />

      <section className="mb-10">
        <h2 className="text-xl font-bold mb-4">7. 免責事項</h2>
        <p className="mb-4">
          当社は、本サービスを「現状有姿」で提供し、明示または黙示を問わず、いかなる種類の保証も行いません。特に以下の点について免責されます：
        </p>
        <ul className="list-disc pl-6 space-y-2 mb-4">
          <li>本サービスが中断なく、タイムリーに、安全に、またはエラーなく提供されること</li>
          <li>本サービスを通じて得られる結果の正確性、信頼性、または完全性</li>
          <li>本サービスの欠陥が修正されること</li>
          <li>本サービスが特定の目的に適合すること</li>
        </ul>
        <p>
          当社は、本サービスの使用または使用不能から生じるいかなる間接的、偶発的、特別、結果的または懲罰的損害についても責任を負いません。
        </p>
      </section>

      <Separator className="my-8" />

      <section className="mb-10">
        <h2 className="text-xl font-bold mb-4">8. 契約期間と解約</h2>
        <p className="mb-4">
          本サービスの契約期間は、アカウント作成時または契約更新時に指定された期間とします。
          解約については、以下の条件が適用されます：
        </p>
        <ul className="list-disc pl-6 space-y-2 mb-4">
          <li>利用者は、いつでも当社に通知することにより本サービスを解約できます</li>
          <li>解約後、次回の請求サイクルから料金は発生しません</li>
          <li>解約時に未払いの料金がある場合、利用者はその支払い義務を負います</li>
          <li>当社は、利用者が本規約に違反した場合、または長期間サービスを利用していない場合、サービスを終了する権利を有します</li>
        </ul>
      </section>

      <Separator className="my-8" />

      <section className="mb-10">
        <h2 className="text-xl font-bold mb-4">9. プライバシー</h2>
        <p>
          当社のプライバシーポリシーは、本規約の一部を構成します。
          プライバシーポリシーについては、<a href="/privacy" className="text-primary hover:underline">こちら</a>をご参照ください。
        </p>
      </section>

      <Separator className="my-8" />

      <section>
        <h2 className="text-xl font-bold mb-4">10. お問い合わせ</h2>
        <p className="mb-4">
          本規約に関するご質問やご不明点がございましたら、以下の連絡先までお問い合わせください：
        </p>
        <div className="bg-gray-50 p-6 rounded-lg border border-gray-100">
          <h3 className="font-medium text-gray-900 mb-2">株式会社Queue</h3>
          <p className="text-gray-600">
            住所：〒104-0061 東京都中央区銀座一丁目22番11号 銀座大竹ビジデンス 2F<br />
            メール：queue@queuefood.co.jp<br />
            電話：03-6687-0550（平日9:00-18:00）
          </p>
        </div>
      </section>

      <Separator className="my-8" />

      <section>
        <h2 className="text-xl font-bold mb-4">11. その他</h2>
        <p className="mb-4">
          本規約は日本法に準拠し、解釈されます。本規約に関連して生じる紛争については、東京地方裁判所を第一審の専属的合意管轄裁判所とします。
        </p>
        <p className="mb-4">
          本規約のいずれかの条項が無効または執行不能と判断された場合でも、残りの条項は完全に効力を有します。
        </p>
      </section>
    </LegalPageLayout>
  );
};

export default Terms;
