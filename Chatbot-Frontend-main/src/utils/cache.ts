// キャッシュユーティリティ
interface CacheItem<T> {
  data: T;
  timestamp: number;
  ttl: number; // キャッシュ有効期限（ミリ秒）
}

class Cache {
  private storage = new Map<string, CacheItem<any>>();

  // データをキャッシュに保存
  set<T>(key: string, data: T, ttl: number = 5 * 60 * 1000): void { // デフォルト5分
    this.storage.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  // キャッシュからデータを取得
  get<T>(key: string): T | null {
    const item = this.storage.get(key);
    
    if (!item) {
      return null;
    }

    // キャッシュが期限切れかチェック
    if (Date.now() - item.timestamp > item.ttl) {
      this.storage.delete(key);
      return null;
    }

    return item.data as T;
  }

  // キャッシュをクリア
  clear(key?: string): void {
    if (key) {
      this.storage.delete(key);
    } else {
      this.storage.clear();
    }
  }

  // 期限切れのキャッシュを削除
  cleanup(): void {
    const now = Date.now();
    for (const [key, item] of this.storage.entries()) {
      if (now - item.timestamp > item.ttl) {
        this.storage.delete(key);
      }
    }
  }
}

// グローバルキャッシュインスタンス
export const cache = new Cache();

// API呼び出し用のキャッシュラッパー
export const withCache = async <T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl: number = 5 * 60 * 1000
): Promise<T> => {
  // キャッシュからデータを取得を試行
  const cached = cache.get<T>(key);
  if (cached) {
    console.log(`📦 キャッシュからデータを取得: ${key}`);
    return cached;
  }

  // キャッシュにない場合はAPIを呼び出し
  console.log(`🌐 APIからデータを取得: ${key}`);
  const data = await fetcher();
  cache.set(key, data, ttl);
  return data;
};

// 定期的なキャッシュクリーンアップ
setInterval(() => {
  cache.cleanup();
}, 60 * 1000); // 1分毎にクリーンアップ 