interface WorkflowSectionProps {
  activeTab: string;
}

const WorkflowSection = ({ activeTab }: WorkflowSectionProps) => {
  const adminSteps = [
    {
      number: 1,
      title: 'リソースのアップロード',
      description: '管理画面のリソースタブで、分析したい資料をアップロードします。PDFやWord、Excel、URLなど様々な形式に対応しています。',
      features: [
        'ファイルドロップでの簡単アップロード',
        'Google Driveからの直接取り込み',
        'URLからのコンテンツ自動取得'
      ]
    },
    {
      number: 2,
      title: '管理者指令の設定',
      description: 'アップロードしたリソースに対して、AIに特別な指示を与える「管理者指令」を設定できます。',
      features: [
        '機密情報の取り扱い注意の指示',
        '要約方法や分析観点の指定',
        'リソース固有のコンテキスト設定'
      ]
    },
    {
      number: 3,
      title: 'リソース管理',
      description: 'アップロードしたリソースの有効/無効切り替えや削除など、詳細な管理が可能です。',
      features: [
        'リソースの有効/無効切り替え',
        'アップロード進捗の確認',
        'リソースの削除と整理'
      ]
    }
  ];

  const userSteps = [
    {
      number: 1,
      title: '質問の入力',
      description: 'チャット画面で質問を入力します。自然な言葉で問いかけてください。',
      features: [
        '自然言語での質問入力',
        '複雑な質問への対応',
        '追加質問や詳細説明の要求'
      ]
    },
    {
      number: 2,
      title: 'AIからの回答',
      description: 'アップロードされた資料を基に、AIが詳細な回答を提供します。',
      features: [
        '資料に基づいた正確な回答',
        '引用元の明確な表示',
        '複数資料からの情報統合'
      ]
    },
    {
      number: 3,
      title: '結果の活用',
      description: '回答内容をコピーしたり、さらに詳しい質問を続けることができます。',
      features: [
        '回答内容のコピー機能',
        '会話履歴の保存',
        '引用元資料の確認'
      ]
    }
  ];

  const steps = activeTab === 'admin' ? adminSteps : userSteps;

  return (
    <section className="py-16 bg-gray-50">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            {activeTab === 'admin' ? '管理者向け' : 'ユーザー向け'}使い方ガイド
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            {activeTab === 'admin' 
              ? 'AIアシスタントを効果的に設定・管理するためのステップ'
              : 'AIアシスタントを最大限に活用するためのステップ'
            }
          </p>
        </div>

        <div className="space-y-12">
          {steps.map((step) => (
            <div key={step.number} className="flex flex-col lg:flex-row items-center gap-8">
              <div className="flex-shrink-0">
                <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                  {step.number}
                </div>
              </div>
              <div className="flex-grow bg-white rounded-2xl shadow-lg p-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-4">{step.title}</h3>
                <p className="text-gray-600 mb-6 leading-relaxed">{step.description}</p>
                <div className="grid md:grid-cols-3 gap-4">
                  {step.features.map((feature, index) => (
                    <div key={index} className="flex items-center">
                      <div className="w-2 h-2 bg-blue-600 rounded-full mr-3"></div>
                      <span className="text-gray-700 text-sm">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default WorkflowSection; 