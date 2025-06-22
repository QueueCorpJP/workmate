const Footer = () => {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <img 
                src="/work_mate.png" 
                alt="ワークメイトAI" 
                className="h-8 w-auto"
              />
              <span className="text-xl font-bold">ワークメイトAI</span>
            </div>
            <p className="text-gray-400 text-sm">
              AIアシスタントで業務効率を向上させる
              次世代のビジネスツールです。
            </p>
          </div>
          
          <div>
            <h3 className="font-semibold mb-4">プロダクト</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><a href="/" className="hover:text-white transition-colors">機能</a></li>
              <li><a href="/pricing" className="hover:text-white transition-colors">料金</a></li>
              <li><a href="/guide" className="hover:text-white transition-colors">ガイド</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold mb-4">サポート</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><a href="/contact" className="hover:text-white transition-colors">お問い合わせ</a></li>
              <li><a href="/help" className="hover:text-white transition-colors">ヘルプセンター</a></li>
              <li><a href="/status" className="hover:text-white transition-colors">サービス状況</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold mb-4">企業情報</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><a href="/about" className="hover:text-white transition-colors">会社概要</a></li>
              <li><a href="/privacy" className="hover:text-white transition-colors">プライバシー</a></li>
              <li><a href="/terms" className="hover:text-white transition-colors">利用規約</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-800 mt-8 pt-6 text-center text-sm text-gray-400">
          <p>&copy; 2024 ワークメイトAI. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 