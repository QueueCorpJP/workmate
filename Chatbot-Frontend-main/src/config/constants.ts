// 環境変数の一元管理
export const CONFIG = {
  GOOGLE_DRIVE: {
    CLIENT_ID: import.meta.env.VITE_GOOGLE_DRIVE_CLIENT_ID || '780511796066-1q5g2i7u8vla9jescuvatr41ob7698uq.apps.googleusercontent.com',
    API_KEY: import.meta.env.VITE_GOOGLE_DRIVE_API_KEY || 'AIzaSyC1B--LQvYZVDo95rLrDwfOidEAdkmGRSw',
    REDIRECT_URI: import.meta.env.VITE_GOOGLE_REDIRECT_URI || 'https://workmatechat.com/auth/callback'
  },
  API: {
    URL: import.meta.env.VITE_API_URL || 'https://workmatechat.com/chatbot/api/'
  }
} as const;

// 環境変数チェック関数
export const validateConfig = () => {
  console.log('=== CONFIG 検証 ===');
  console.log('Google Drive Client ID:', CONFIG.GOOGLE_DRIVE.CLIENT_ID);
  console.log('Google Drive API Key:', CONFIG.GOOGLE_DRIVE.API_KEY);
  console.log('API URL:', CONFIG.API.URL);
  console.log('=== 検証終了 ===');
};