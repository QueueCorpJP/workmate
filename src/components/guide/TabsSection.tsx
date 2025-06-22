interface TabsSectionProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsSection = ({ activeTab, setActiveTab }: TabsSectionProps) => {
  return (
    <section className="py-12 bg-white border-b border-gray-200">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="flex justify-center">
          <div className="bg-gray-100 rounded-full p-2 flex space-x-2">
            <button
              onClick={() => setActiveTab('admin')}
              className={`px-8 py-3 rounded-full font-semibold transition-all duration-200 ${
                activeTab === 'admin'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              管理者向け
            </button>
            <button
              onClick={() => setActiveTab('user')}
              className={`px-8 py-3 rounded-full font-semibold transition-all duration-200 ${
                activeTab === 'user'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              ユーザー向け
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default TabsSection; 