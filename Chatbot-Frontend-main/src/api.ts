import axios from "axios";

// 環境変数からAPIのURL取得
// Use local backend server by default
const API_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? 
    `${window.location.origin}/chatbot/api` : 
    "http://localhost:8083/chatbot/api");

console.log("API URL:", API_URL);
console.log("Environment:", import.meta.env.MODE);
console.log("VITE_API_URL:", import.meta.env.VITE_API_URL);

// axiosのインスタンス
const api = axios.create({
  baseURL: API_URL,
  // リクエストとレスポンスのログを出力
  transformRequest: [
    (data, headers) => {
      console.log("Request:", { url: API_URL, data, headers });
      // CORSヘッダーを追
      headers = headers || {};
      headers['Access-Control-Allow-Origin'] = '*';
      
      // FormDataの場合はContent-Typeを設定しない（axiosが自動的に設定する）
      if (!(data instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
      }
      
      return data;
    },
    ...(axios.defaults.transformRequest as any),
  ],
  transformResponse: [
    (data) => {
      console.log("Response:", { data });
      try {
        return typeof data === "string" && data ? JSON.parse(data) : data;
      } catch (error) {
        console.error("Failed to parse response:", error);
        console.log("Raw response:", data);
        return data;
      }
    },
  ],
  // タイムアウトを設定（OCR処理のために3分に延長）
  timeout: 300000,
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
