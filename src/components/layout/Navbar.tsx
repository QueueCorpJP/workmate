const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-b border-gray-200 z-50">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="flex items-center justify-between h-20">
          <div className="flex items-center space-x-4">
            <img 
              src="/work_mate.png" 
              alt="ワークメイトAI" 
              className="h-8 w-auto"
            />
            <span className="text-xl font-bold text-gray-900">
              ワークメイトAI
            </span>
          </div>
          
          <div className="hidden md:flex items-center space-x-8">
            <a href="/" className="text-gray-600 hover:text-gray-900 transition-colors">
              ホーム
            </a>
            <a href="/guide" className="text-gray-600 hover:text-gray-900 transition-colors">
              ガイド
            </a>
            <a href="/pricing" className="text-gray-600 hover:text-gray-900 transition-colors">
              料金
            </a>
            <a href="/contact" className="text-gray-600 hover:text-gray-900 transition-colors">
              お問い合わせ
            </a>
          </div>

          <div className="flex items-center space-x-4">
            <button className="text-gray-600 hover:text-gray-900 transition-colors">
              ログイン
            </button>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
              無料で始める
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 