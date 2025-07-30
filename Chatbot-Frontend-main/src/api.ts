import axios from "axios";

// 環境を判定する関数
const getEnvironment = () => {
  // ホスト名で本番環境を判定（wwwサブドメインも含む）
  if (window.location.hostname === "workmatechat.com" ||
      window.location.hostname === "www.workmatechat.com") {
    return "production";
  }

  // NODE_ENVまたはVITE_ENVIRONMENTをチェック
  const nodeEnv = import.meta.env.NODE_ENV?.toLowerCase();
  const viteEnv = import.meta.env.VITE_ENVIRONMENT?.toLowerCase();
  
  if (nodeEnv === "production" || viteEnv === "production") {
    return "production";
  }
  
  // import.meta.env.PRODがtrueの場合も本番環境
  if (import.meta.env.PROD) {
    return "production";
  }
  
  return "development";
};

// 環境に応じたAPI URLを取得する関数
const getApiUrl = () => {
  const environment = getEnvironment();
  
  // 本番環境では、ハードコードされた本番用URLを常に使用する
  if (environment === "production") {
    const productionUrl = "https://workmatechat.com/chatbot/api";
    console.log(`🌐 API URL: ${productionUrl} (本番環境固定)`);
    return productionUrl;
  }
  
  // 環境変数VITE_API_URLが明示的に設定されている場合は優先
  if (import.meta.env.VITE_API_URL) {
    console.log(`🌐 API URL: ${import.meta.env.VITE_API_URL} (環境変数VITE_API_URL指定)`);
    return import.meta.env.VITE_API_URL;
  }
  
  // ローカル開発環境のデフォルト
  const backendPort = import.meta.env.VITE_BACKEND_PORT || 8085;
  const developmentUrl = `http://localhost:${backendPort}/chatbot/api`;
  console.log(`🌐 API URL: ${developmentUrl} (ローカル開発環境デフォルト)`);
  return developmentUrl;
};

// 環境情報を表示
const environment = getEnvironment();
const API_URL = getApiUrl();

console.log("🌍 フロントエンド実行環境:", environment);
console.log("🔧 NODE_ENV:", import.meta.env.NODE_ENV);
console.log("🔧 VITE_ENVIRONMENT:", import.meta.env.VITE_ENVIRONMENT);
console.log("🔧 import.meta.env.PROD:", import.meta.env.PROD);
console.log("🔧 VITE_API_URL:", import.meta.env.VITE_API_URL);
console.log("🔧 VITE_BACKEND_PORT:", import.meta.env.VITE_BACKEND_PORT);
console.log("📡 最終API URL:", API_URL);

// axiosのインスタンス
const api = axios.create({
  baseURL: API_URL,
  // リクエストとレスポンスのログを出力
  transformRequest: [
    (data, headers) => {
      console.log("Request:", { url: API_URL, data, headers });
      // CORSヘッダーを追加
      const requestHeaders = headers || ({} as any);
      requestHeaders['Access-Control-Allow-Origin'] = '*';
      
      // FormDataの場合はContent-Typeを設定しない（axiosが自動的に設定する）
      if (!(data instanceof FormData)) {
        requestHeaders['Content-Type'] = 'application/json';
      }
      
      return data;
    },
    ...(axios.defaults.transformRequest as any),
  ],
  transformResponse: [
    (data) => {
      console.log("🔄 Response transform開始:", { 
        dataType: typeof data, 
        dataLength: data?.length || 0,
        dataPreview: typeof data === 'string' ? data.substring(0, 200) : data
      });
      
      try {
        // 既にオブジェクトの場合はそのまま返す
        if (typeof data === "object" && data !== null) {
          console.log("✅ データは既にオブジェクト形式");
          return data;
        }
        
        // 文字列の場合はJSONパースを試行
        if (typeof data === "string" && data) {
          console.log("🔄 文字列データのJSONパース試行...");
          
          // 空白文字や制御文字をチェック
          const cleanData = data.trim();
          if (!cleanData) {
            console.log("⚠️ データが空文字列です");
            return null;
          }
          
          // JSONとして有効かチェック
          if (!cleanData.startsWith('{') && !cleanData.startsWith('[')) {
            console.log("⚠️ データがJSON形式ではありません:", cleanData.substring(0, 100));
            return cleanData; // そのまま返す
          }
          
          const parsed = JSON.parse(cleanData);
          console.log("✅ JSONパース成功:", { 
            parsedType: typeof parsed,
            parsedKeys: parsed && typeof parsed === 'object' ? Object.keys(parsed) : 'not object'
          });
          return parsed;
        }
        
        console.log("✅ データをそのまま返します");
        return data;
        
      } catch (error) {
        console.error("❌ レスポンス変換エラー:", {
          error: error.message,
          errorType: error.constructor.name,
          dataType: typeof data,
          dataLength: data?.length || 0,
          dataString: typeof data === 'string' ? data.substring(0, 500) : String(data).substring(0, 500)
        });
        
        // パースエラーの詳細分析
        if (error instanceof SyntaxError) {
          console.error("JSONパースエラー詳細:", {
            message: error.message,
            position: error.message.match(/position (\d+)/) ? error.message.match(/position (\d+)/)[1] : 'unknown',
            rawData: data
          });
        }
        
        console.log("⚠️ パースに失敗したため、元データを返します");
        return data;
      }
    },
  ],
  // タイムアウトを設定（大きなファイル処理のために10分に延長）
  timeout: 600000,
  // エラーハンドリング
  validateStatus: (status) => {
    console.log("Response status:", status);
    return status >= 200 && status < 300;
  },
  // CORSを許可
  headers: {
    'Access-Control-Allow-Origin': '*',
  },
  withCredentials: false
});

// 認証ヘッダーを追加するインターセプター
api.interceptors.request.use((config) => {
  const storedUser = localStorage.getItem("user");
  if (storedUser) {
    const user = JSON.parse(storedUser);
    if (user && user.email) {
      // Basic認証のヘッダーを設定
      const credentials = `${user.email}:${localStorage.getItem("password") || ""
        }`;
      const encodedCredentials = btoa(credentials);
      config.headers.Authorization = `Basic ${encodedCredentials}`;
    }
  }
  return config;
});

// リクエストインターセプター
api.interceptors.request.use(
  (config) => {
    console.log("Sending request:", config);
    return config;
  },
  (error) => {
    console.error("Request error:", error);
    return Promise.reject(error);
  }
);

// レスポンスインターセプター
api.interceptors.response.use(
  (response) => {
    console.log("Response received:", response);
    return response;
  },
  (error) => {
    console.error("Response error:", error);
    if (error.response) {
      // サーバーからのレスポンスがある場合
      console.error("Error data:", error.response.data);
      console.error("Error status:", error.response.status);
      console.error("Error headers:", error.response.headers);
    } else if (error.request) {
      // リクエストは送信されたが、レスポンスがない場合
      console.error("No response received:", error.request);
    } else {
      // リクエストの設定中にエラーが発生した場合
      console.error("Request setup error:", error.message);
    }
    return Promise.reject(error);
  }
);

export default api;

// 通知関連のAPI関数
export interface Notification {
  id: string;
  title: string;
  content: string;
  notification_type: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

// 全ての通知を取得（全ユーザー共通）
export const getNotifications = async (): Promise<Notification[]> => {
  try {
    console.log("🔍 Getting notifications from: /notifications");
    const response = await api.get('/notifications');
    console.log("✅ Notifications response:", response.data);
    return response.data;
  } catch (error) {
    console.error("通知の取得に失敗しました:", error);
    console.error("Error details:", error);
    throw error;
  }
};

// 通知を作成（管理者用）
export const createNotification = async (notification: Omit<Notification, 'id' | 'created_at' | 'updated_at' | 'created_by'>): Promise<Notification> => {
  try {
    console.log("🔍 Creating notification:", notification);
    const response = await api.post('/notifications', notification);
    console.log("✅ Create notification response:", response.data);
    return response.data;
  } catch (error) {
    console.error("通知の作成に失敗しました:", error);
    console.error("Error details:", error);
    throw error;
  }
};

// 通知を削除（管理者用）
export const deleteNotification = async (notificationId: string): Promise<void> => {
  try {
    console.log("🔍 Deleting notification:", notificationId);
    await api.delete(`/notifications/${notificationId}`);
    console.log("✅ Notification deleted successfully");
  } catch (error) {
    console.error("通知の削除に失敗しました:", error);
    console.error("Error details:", error);
    throw error;
  }
};
