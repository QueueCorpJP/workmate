const UserFeatureSection = () => {
  return (
    <section className="py-16 bg-white">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            ユーザー向け活用機能
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            AIアシスタントとの効果的な対話方法と便利な機能をご紹介します
          </p>
        </div>

        <div className="grid md:grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* 効果的な質問方法 */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl shadow-lg p-8 border border-blue-100">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white text-xl font-bold mr-4">
                💡
              </div>
              <h3 className="text-2xl font-bold text-gray-900">効果的な質問方法</h3>
            </div>
            <p className="text-gray-600 mb-6 leading-relaxed">
              AIから的確な回答を得るために、質問の仕方にちょっとしたコツがあります。
            </p>
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">具体的で明確な質問をする</span>
              </div>
              <div className="flex items-start">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">必要な情報の範囲を指定する</span>
              </div>
              <div className="flex items-start">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">追加質問で詳細を深掘りする</span>
              </div>
            </div>
          </div>

          {/* 便利な機能 */}
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl shadow-lg p-8 border border-green-100">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white text-xl font-bold mr-4">
                🔧
              </div>
              <h3 className="text-2xl font-bold text-gray-900">便利な機能</h3>
            </div>
            <p className="text-gray-600 mb-6 leading-relaxed">
              チャットインターフェースには、作業効率を上げる様々な機能が備わっています。
            </p>
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">回答内容のワンクリックコピー</span>
              </div>
              <div className="flex items-start">
                <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">引用元資料の確認機能</span>
              </div>
              <div className="flex items-start">
                <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">会話履歴の自動保存</span>
              </div>
            </div>
          </div>
        </div>

        {/* 質問例 */}
        <div className="bg-gray-50 rounded-2xl shadow-lg p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">質問例</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg p-6 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-3">📊 分析・要約</h4>
              <ul className="space-y-2 text-gray-600 text-sm">
                <li>「この資料の要点を3つに要約してください」</li>
                <li>「売上データの傾向を分析して教えてください」</li>
                <li>「プロジェクトのリスクを洗い出してください」</li>
              </ul>
            </div>
            <div className="bg-white rounded-lg p-6 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-3">🔍 詳細調査</h4>
              <ul className="space-y-2 text-gray-600 text-sm">
                <li>「〇〇について詳しく説明してください」</li>
                <li>「この問題の解決策を提案してください」</li>
                <li>「関連する参考資料はありますか？」</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default UserFeatureSection; 