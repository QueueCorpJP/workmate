import React, { useState, useEffect } from 'react';
import { Button, Typography, Box, Alert } from '@mui/material';
import { Cloud } from '@mui/icons-material';

interface GoogleDriveAuthProps {
  onAuthSuccess: (accessToken: string) => void;
  onAuthError: (error: string) => void;
}

declare global {
  interface Window {
    gapi: any;
    google: {
      accounts: {
        oauth2: {
          initTokenClient: (config: any) => any;
        };
      };
    };
  }
}

export const GoogleDriveAuth: React.FC<GoogleDriveAuthProps> = ({
  onAuthSuccess,
  onAuthError
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [gapiLoaded, setGapiLoaded] = useState(false);

  useEffect(() => {
    loadGoogleAPI();
  }, []);

  const loadGoogleAPI = async () => {
    try {
      // gapiとgoogleの両方が読み込まれるまで待機（タイムアウト付き）
      const waitForGapi = () => {
        return new Promise<void>((resolve, reject) => {
          let attempts = 0;
          const maxAttempts = 300; // 30秒待機
          
          const checkGapi = () => {
            attempts++;
            if (window.gapi && window.google) {
              console.log('Google API 読み込み完了');
              resolve();
            } else if (attempts >= maxAttempts) {
              reject(new Error('Google API の読み込みがタイムアウトしました'));
            } else {
              setTimeout(checkGapi, 100);
            }
          };
          checkGapi();
        });
      };

      await waitForGapi();
      await initializeAuth();
    } catch (error) {
      console.error('Google API読み込みエラー:', error);
      onAuthError('Google APIの読み込みに失敗しました。ページを再読み込みしてください。');
    }
  };

  const initializeAuth = async () => {
    try {
      // 環境変数を確認
      const clientId = import.meta.env.VITE_GOOGLE_DRIVE_CLIENT_ID || '780511796066-1q5g2i7u8vla9jescuvatr41ob7698uq.apps.googleusercontent.com';
      const apiKey = import.meta.env.VITE_GOOGLE_DRIVE_API_KEY || 'AIzaSyC1B--LQvYZVDo95rLrDwfOidEAdkmGRSw';
      const redirectUri = import.meta.env.VITE_GOOGLE_REDIRECT_URI || 'https://workmatechat.com/auth/callback';
      
      console.log('=== 環境変数デバッグ ===');
      console.log('Client ID:', clientId);
      console.log('API Key:', apiKey);
      console.log('Redirect URI:', redirectUri);
      console.log('Client ID Type:', typeof clientId);
      console.log('Client ID Length:', clientId?.length);
      console.log('=== デバッグ終了 ===');
      
      if (!clientId) {
        throw new Error('Google Drive Client ID が設定されていません');
      }
      
      console.log('Google認証初期化中...');
      
      // Google Identity Services が利用可能かチェック
      if (!window.google?.accounts?.oauth2) {
        throw new Error('Google Identity Services が読み込まれていません');
      }
      
      setGapiLoaded(true);
      console.log('Google認証初期化完了');
    } catch (error) {
      console.error('認証初期化エラー:', error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      onAuthError(`認証の初期化に失敗しました: ${errorMessage}`);
    }
  };

  const handleAuth = async () => {
    if (!gapiLoaded) {
      onAuthError('Google APIが読み込まれていません');
      return;
    }

    const clientId = import.meta.env.VITE_GOOGLE_DRIVE_CLIENT_ID;
    console.log('=== handleAuth デバッグ ===');
    console.log('Client ID:', clientId);
    console.log('Client ID Type:', typeof clientId);
    console.log('Client ID Truthy:', !!clientId);
    console.log('=== デバッグ終了 ===');
    
    if (!clientId) {
      onAuthError('Google Drive Client ID が設定されていません');
      return;
    }

    setIsLoading(true);
    try {
      console.log('Google認証開始...');
      
      // 新しいGoogle Identity Servicesでトークンを要求
      const tokenClient = window.google.accounts.oauth2.initTokenClient({
        client_id: clientId,
        scope: 'https://www.googleapis.com/auth/drive.readonly',
        callback: (response: any) => {
          setIsLoading(false);
          console.log('認証レスポンス:', response);
          
          if (response.error) {
            console.error('認証エラー:', response.error);
            if (response.error === 'popup_closed_by_user') {
              onAuthError('認証がキャンセルされました');
            } else {
              onAuthError(`認証に失敗しました: ${response.error}`);
            }
          } else {
            console.log('Google認証成功');
            setIsAuthenticated(true);
            onAuthSuccess(response.access_token);
          }
        }
      });
      
      tokenClient.requestAccessToken();
    } catch (error: unknown) {
      console.error('認証エラー:', error);
      const errorMessage = error instanceof Error ? error.message : '不明なエラー';
      onAuthError(`認証に失敗しました: ${errorMessage}`);
      setIsLoading(false);
    }
  };

  const handleSignOut = async () => {
    try {
      // 新しいAPIではローカル状態のみリセット
      setIsAuthenticated(false);
      console.log('サインアウト完了');
    } catch (error) {
      console.error('サインアウトエラー:', error);
    }
  };

  if (!gapiLoaded) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Google APIを読み込み中...
        </Typography>
        <Typography variant="caption" color="text.secondary">
          しばらく待ってもこの画面が表示される場合は、ページを再読み込みしてください。
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ mb: 2 }}>
      {!isAuthenticated ? (
        <Button
          onClick={handleAuth}
          variant="outlined"
          color="primary"
          disabled={isLoading}
          startIcon={<Cloud />}
          fullWidth
          sx={{
            py: 1.5,
            borderRadius: 2,
            textTransform: 'none',
            fontSize: '0.9rem'
          }}
        >
          {isLoading ? 'Google Driveに接続中...' : 'Google Driveに接続'}
        </Button>
      ) : (
        <Alert 
          severity="success" 
          action={
            <Button color="inherit" size="small" onClick={handleSignOut}>
              切断
            </Button>
          }
          sx={{ borderRadius: 2 }}
        >
          Google Driveに接続済み
        </Alert>
      )}
    </Box>
  );
}; 