
const AdminFeatureSection = () => {
  return (
    
    <section className="py-16 bg-gradient-to-b from-blue-50/50 to-white">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            管理者向け高度な機能
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            リソース管理画面での詳細な機能により、より効果的なAIアシスタントを構築できます
          </p>
        </div>

        <div className="grid md:grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* 管理者指令機能 */}
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100 hover:shadow-xl transition-shadow duration-300">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center text-white text-xl font-bold mr-4">
                ★
              </div>
              <h3 className="text-2xl font-bold text-gray-900">管理者指令機能</h3>
            </div>
            <p className="text-gray-600 mb-6 leading-relaxed">
              リソース画面で各アップロードファイルに対して個別の「管理者指令」を設定できます。
              これにより、AIがそのリソースを参照する際に特別な指示を与えることができます。
            </p>
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">リソース一覧で「管理者指令」列の編集ボタンをクリック</span>
              </div>
              <div className="flex items-start">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">機密情報の取り扱い注意、要約方法の指定、特定の観点での分析指示など</span>
              </div>
              <div className="flex items-start">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">例：「この資料は機密情報なので、要約時に注意喚起を含めてください」</span>
              </div>
            </div>
          </div>

          {/* リソース管理機能 */}
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100 hover:shadow-xl transition-shadow duration-300">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white text-xl font-bold mr-4">
                ⚙
              </div>
              <h3 className="text-2xl font-bold text-gray-900">リソース管理機能</h3>
            </div>
            <p className="text-gray-600 mb-6 leading-relaxed">
              リソース画面では、アップロードした資料の詳細管理が可能です。
              効率的な知識ベース管理のために以下の機能をご活用ください。
            </p>
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">リソースの有効/無効切り替え - 一時的に特定の資料を無効化</span>
              </div>
              <div className="flex items-start">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">Google Drive連携 - Googleドライブから直接ファイルを取り込み</span>
              </div>
              <div className="flex items-start">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">URL取り込み - ウェブページの内容を自動分析・取り込み</span>
              </div>
              <div className="flex items-start">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-3 mt-0.5">
                  ✓
                </div>
                <span className="text-gray-700">アップロード進捗表示 - リアルタイムでのファイル処理状況確認</span>
              </div>
            </div>
          </div>
        </div>

        {/* 最新の追加機能 */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl shadow-lg p-8 text-white">
          <div className="flex items-center mb-6">
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-purple-600 text-xl font-bold mr-4">
              🆕
            </div>
            <h3 className="text-2xl font-bold">最新の追加機能</h3>
          </div>
          <p className="text-blue-100 mb-6 leading-relaxed text-lg">
            分析画面の品質が大幅に向上しました。より詳細で正確な分析結果を提供し、
            視覚的にも分かりやすい表示を実現しています。
          </p>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-white/10 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <div className="w-4 h-4 bg-white rounded-full flex items-center justify-center text-purple-600 text-xs font-bold mr-2">
                  ✓
                </div>
                <span className="font-semibold">詳細分析</span>
              </div>
              <p className="text-blue-100 text-sm">より詳細な分析結果の表示</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <div className="w-4 h-4 bg-white rounded-full flex items-center justify-center text-purple-600 text-xs font-bold mr-2">
                  ✓
                </div>
                <span className="font-semibold">視覚的改善</span>
              </div>
              <p className="text-blue-100 text-sm">視覚的に分かりやすいレポート形式</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <div className="w-4 h-4 bg-white rounded-full flex items-center justify-center text-purple-600 text-xs font-bold mr-2">
                  ✓
                </div>
                <span className="font-semibold">精度向上</span>
              </div>
              <p className="text-blue-100 text-sm">分析精度の向上とエラー処理の強化</p>
            </div>
          </div>
        </div>
      </div>
    </section>
    
  );
};

export default AdminFeatureSection; 