// 環境変数の一元管理
export const CONFIG = {
  GOOGLE_DRIVE: {
    CLIENT_ID: import.meta.env.VITE_GOOGLE_DRIVE_CLIENT_ID || '780511796066-1q5g2i7u8vla9jescuvatr41ob7698uq.apps.googleusercontent.com',
    API_KEY: import.meta.env.VITE_GOOGLE_DRIVE_API_KEY || 'AIzaSyC1B--LQvYZVDo95rLrDwfOidEAdkmGRSw',
    REDIRECT_URI: import.meta.env.VITE_GOOGLE_REDIRECT_URI || 'https://workmatechat.com/auth/callback'
  },
  API: {
    URL: import.meta.env.VITE_API_URL || 'https://workmatechat.com/chatbot/api/'
  },
  ENVIRONMENT: {
    NODE_ENV: import.meta.env.MODE || 'development',
    IS_PRODUCTION: import.meta.env.PROD || false,
    SHOW_DEMO_BADGE: import.meta.env.VITE_SHOW_DEMO_BADGE !== 'false' // デフォルトは表示
  }
} as const;

// 環境判定関数
export const isProduction = (): boolean => {
  // 本番環境判定ロジック
  const hostname = window.location.hostname;
  const apiUrl = CONFIG.API.URL;
  
  // 本番ドメインでの判定
  const isProductionDomain = hostname === 'workmatechat.com' || hostname.includes('workmatechat.com');
  
  // API URLでの判定
  const isProductionAPI = apiUrl.includes('workmatechat.com');
  
  // 環境変数での判定
  const isProductionEnv = CONFIG.ENVIRONMENT.IS_PRODUCTION;
  
  return isProductionDomain || isProductionAPI || isProductionEnv;
};

// デモバッジ表示判定関数
export const shouldShowDemoBadge = (): boolean => {
  // 環境変数で明示的に非表示指定されている場合は非表示
  if (!CONFIG.ENVIRONMENT.SHOW_DEMO_BADGE) {
    return false;
  }
  
  // 本番環境では非表示にする場合のロジック（必要に応じて調整）
  // return !isProduction();
  
  // 現在はデフォルトで表示
  return true;
};

// 環境変数チェック関数
export const validateConfig = () => {
  console.log('=== CONFIG 検証 ===');
  console.log('Google Drive Client ID:', CONFIG.GOOGLE_DRIVE.CLIENT_ID);
  console.log('Google Drive API Key:', CONFIG.GOOGLE_DRIVE.API_KEY);
  console.log('API URL:', CONFIG.API.URL);
  console.log('Environment:', CONFIG.ENVIRONMENT.NODE_ENV);
  console.log('Is Production:', isProduction());
  console.log('Show Demo Badge:', shouldShowDemoBadge());
  console.log('=== 検証終了 ===');
};