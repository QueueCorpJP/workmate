const HeroSection = () => {
  return (
    <section className="bg-gradient-to-br from-blue-50 via-white to-indigo-50 py-20">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              ワークメイトAI
            </span>
            <br />
            利用ガイド
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
            AIアシスタントを最大限に活用するためのガイドです。
            資料のアップロード、質問の仕方、得られる回答の理解など、
            基本的な使い方から高度なテクニックまで解説します。
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-full font-semibold text-lg transition-colors duration-200 shadow-lg">
              チャットボットを使ってみる
            </button>
            <button className="bg-white hover:bg-gray-50 text-blue-600 px-8 py-4 rounded-full font-semibold text-lg border-2 border-blue-600 transition-colors duration-200">
              デモを見る
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection; 