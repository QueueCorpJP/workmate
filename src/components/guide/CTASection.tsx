const CTASection = () => {
  return (
    <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
      <div className="container mx-auto px-4 max-w-4xl text-center">
        <h2 className="text-4xl md:text-5xl font-bold mb-6">
          今すぐワークメイトAIを
          <br />
          活用してみませんか？
        </h2>
        <p className="text-xl md:text-2xl text-blue-100 mb-10 leading-relaxed">
          AIアシスタントがあなたの業務効率を大幅に改善します。
          まずは簡単な質問から始めてみてください。
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button className="bg-white text-blue-600 px-8 py-4 rounded-full font-semibold text-lg hover:bg-gray-100 transition-colors duration-200 shadow-lg">
            チャットを開始する
          </button>
          <button className="bg-transparent border-2 border-white text-white px-8 py-4 rounded-full font-semibold text-lg hover:bg-white hover:text-blue-600 transition-colors duration-200">
            デモを試す
          </button>
        </div>
        <div className="mt-12 grid md:grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-3xl font-bold mb-2">24/7</div>
            <div className="text-blue-100">いつでも利用可能</div>
          </div>
          <div>
            <div className="text-3xl font-bold mb-2">99.9%</div>
            <div className="text-blue-100">高い可用性</div>
          </div>
          <div>
            <div className="text-3xl font-bold mb-2">∞</div>
            <div className="text-blue-100">無制限の質問</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection; 