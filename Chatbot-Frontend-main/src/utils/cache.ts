// キャッシュユーティリティ
interface CacheItem<T> {
  data: T;
  timestamp: number;
  ttl: number; // キャッシュ有効期限（ミリ秒）
}

class Cache {
  private storage = new Map<string, CacheItem<any>>();
  private subscribers = new Map<string, Set<(data: any) => void>>();

  // データをキャッシュに保存
  set<T>(key: string, data: T, ttl: number = 5 * 60 * 1000): void { // デフォルト5分
    this.storage.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
    
    // サブスクライバーに通知
    this.notifySubscribers(key, data);
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

  // データ変更の購読機能
  subscribe(key: string, callback: (data: any) => void): () => void {
    if (!this.subscribers.has(key)) {
      this.subscribers.set(key, new Set());
    }
    this.subscribers.get(key)!.add(callback);

    // アンサブスクライブ関数を返す
    return () => {
      const subs = this.subscribers.get(key);
      if (subs) {
        subs.delete(callback);
        if (subs.size === 0) {
          this.subscribers.delete(key);
        }
      }
    };
  }

  // サブスクライバーに通知
  private notifySubscribers(key: string, data: any): void {
    const subs = this.subscribers.get(key);
    if (subs) {
      subs.forEach(callback => callback(data));
    }
  }

  // キャッシュサイズを取得
  getSize(): number {
    return this.storage.size;
  }

  // キャッシュ統計を取得
  getStats(): { total: number; expired: number; valid: number } {
    const now = Date.now();
    let expired = 0;
    let valid = 0;

    for (const [_, item] of this.storage.entries()) {
      if (now - item.timestamp > item.ttl) {
        expired++;
      } else {
        valid++;
      }
    }

    return {
      total: this.storage.size,
      expired,
      valid
    };
  }
}

// グローバルキャッシュインスタンス
export const cache = new Cache();

// 共有データ用のスマートキャッシュラッパー
export const withSharedCache = async <T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl: number = 5 * 60 * 1000
): Promise<T> => {
  // キャッシュからデータを取得を試行
  const cached = cache.get<T>(key);
  if (cached) {
    console.log(`📦 共有キャッシュからデータを取得: ${key}`);
    return cached;
  }

  // キャッシュにない場合はAPIを呼び出し
  console.log(`🌐 共有データをAPIから取得: ${key}`);
  const data = await fetcher();
  cache.set(key, data, ttl);
  return data;
};

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

// React Hook用のキャッシュサブスクリプション
export const useCacheSubscription = <T>(
  key: string,
  initialData: T | null = null
): [T | null, (data: T) => void] => {
  const [data, setData] = useState<T | null>(initialData);

  useEffect(() => {
    // 初期データを取得
    const cached = cache.get<T>(key);
    if (cached) {
      setData(cached);
    }

    // データ変更を購読
    const unsubscribe = cache.subscribe(key, (newData: T) => {
      setData(newData);
    });

    return unsubscribe;
  }, [key]);

  const updateData = (newData: T) => {
    cache.set(key, newData);
  };

  return [data, updateData];
};

// デバッグ用の関数
export const getCacheDebugInfo = () => {
  const stats = cache.getStats();
  console.log('📊 キャッシュ統計:', stats);
  return stats;
};

// 定期的なキャッシュクリーンアップ
setInterval(() => {
  cache.cleanup();
}, 60 * 1000); // 1分毎にクリーンアップ

// Reactを追加で必要
import { useState, useEffect } from 'react'; 