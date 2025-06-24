import React, { memo, useCallback, useMemo } from 'react';

// 最適化されたコンポーネントのテンプレート

interface OptimizedComponentProps {
  data: any[];
  onUpdate: (id: string) => void;
  isLoading: boolean;
  user: any;
}

// 子コンポーネントをメモ化
const OptimizedListItem = memo(({ item, onUpdate }: { item: any; onUpdate: (id: string) => void }) => {
  const handleUpdate = useCallback(() => {
    onUpdate(item.id);
  }, [item.id, onUpdate]);

  return (
    <div onClick={handleUpdate}>
      {item.name}
    </div>
  );
});

// メインコンポーネント
const OptimizedComponent: React.FC<OptimizedComponentProps> = memo(({
  data,
  onUpdate,
  isLoading,
  user
}) => {
  // メモ化されたコールバック
  const handleUpdateCallback = useCallback((id: string) => {
    onUpdate(id);
  }, [onUpdate]);

  // メモ化された計算値
  const filteredData = useMemo(() => {
    if (!data || !user) return [];
    return data.filter(item => item.userId === user.id);
  }, [data, user?.id]);

  const sortedData = useMemo(() => {
    return [...filteredData].sort((a, b) => 
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }, [filteredData]);

  // レンダリング最適化のためのメモ化されたコンポーネント
  const renderedItems = useMemo(() => {
    return sortedData.map(item => (
      <OptimizedListItem
        key={item.id}
        item={item}
        onUpdate={handleUpdateCallback}
      />
    ));
  }, [sortedData, handleUpdateCallback]);

  if (isLoading) {
    return <div>読み込み中...</div>;
  }

  return (
    <div>
      <h2>最適化されたコンポーネント</h2>
      <div>
        {renderedItems}
      </div>
    </div>
  );
});

export default OptimizedComponent; 