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
      // gapiとgoogleの両方が読み込まれるまで待機
      const waitForGapi = () => {
        return new Promise<void>((resolve) => {
          const checkGapi = () => {
            if (window.gapi && window.google) {
              resolve();
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
      onAuthError('Google APIの読み込みに失敗しました');
    }
  };

  const initializeAuth = async () => {
    try {
      // 新しいGoogle Identity Servicesで初期化
      window.google.accounts.oauth2.initTokenClient({
        client_id: import.meta.env.VITE_GOOGLE_DRIVE_CLIENT_ID,
        scope: 'https://www.googleapis.com/auth/drive.readonly',
        callback: (response: any) => {
          if (response.error) {
            console.error('認証エラー:', response.error);
            onAuthError('認証に失敗しました');
          } else {
            setIsAuthenticated(true);
            onAuthSuccess(response.access_token);
          }
        }
      });
      setGapiLoaded(true);
    } catch (error) {
      console.error('認証初期化エラー:', error);
      onAuthError('認証の初期化に失敗しました');
    }
  };

  const handleAuth = async () => {
    if (!gapiLoaded) {
      onAuthError('Google APIが読み込まれていません');
      return;
    }

    setIsLoading(true);
    try {
      // 新しいGoogle Identity Servicesでトークンを要求
      const tokenClient = window.google.accounts.oauth2.initTokenClient({
        client_id: import.meta.env.VITE_GOOGLE_DRIVE_CLIENT_ID,
        scope: 'https://www.googleapis.com/auth/drive.readonly',
        callback: (response: any) => {
          setIsLoading(false);
          if (response.error) {
            console.error('認証エラー:', response.error);
            if (response.error === 'popup_closed_by_user') {
              onAuthError('認証がキャンセルされました');
            } else {
              onAuthError('認証に失敗しました');
            }
          } else {
            setIsAuthenticated(true);
            onAuthSuccess(response.access_token);
          }
        }
      });
      
      tokenClient.requestAccessToken();
    } catch (error: any) {
      console.error('認証エラー:', error);
      onAuthError('認証に失敗しました');
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
        <Typography variant="body2" color="text.secondary">
          Google APIを読み込み中...
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