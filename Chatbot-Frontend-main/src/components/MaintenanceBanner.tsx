import React, { useState, useEffect } from 'react';
import {
  Alert,
  AlertTitle,
  Box,
  Typography,
  Chip,
  Stack
} from '@mui/material';
import {
  Warning as WarningIcon,
  Construction as ConstructionIcon
} from '@mui/icons-material';
// メンテナンスバナーはユーザーが閉じられないようにIconButton、Collapse、CloseIconを削除
import api from '../api';
import { useAuth } from '../contexts/AuthContext';

interface MaintenanceStatus {
  is_active: boolean;
  message: string;
  start_time?: string;
  end_time?: string;
  created_by?: string;
  updated_at: string;
}

const MaintenanceBanner: React.FC = () => {
  const [maintenanceStatus, setMaintenanceStatus] = useState<MaintenanceStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  
  // メンテナンス管理者のメールアドレス
  const MAINTENANCE_ADMINS = ['taichi.taniguchi@queue-tech.jp', 'queue@queue-tech.jp'];
  
  // 管理者の場合はバナーを表示しない
  const isMaintenanceAdmin = user && MAINTENANCE_ADMINS.includes(user.email);
  
  // バナーを閉じる機能を完全に削除

  // メンテナンス状態を取得
  const fetchMaintenanceStatus = async () => {
    try {
      const response = await api.get('/maintenance/status');
      const status = response.data.status;
      setMaintenanceStatus(status);
      // バナー状態の制御を削除（常に表示）
    } catch (error) {
      console.error('メンテナンス状態取得エラー:', error);
      // エラー時は安全のためメンテナンス無効として処理
      setMaintenanceStatus({
        is_active: false,
        message: '',
        updated_at: new Date().toISOString()
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMaintenanceStatus();
    
    // 30秒ごとにメンテナンス状態を確認
    const interval = setInterval(fetchMaintenanceStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // メンテナンス中でない場合、管理者の場合、またはロード中は何も表示しない
  if (!maintenanceStatus?.is_active || loading || isMaintenanceAdmin) {
    return null;
  }

  return (
    <>
      <Alert 
        severity="warning" 
        icon={<ConstructionIcon />}
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 9999,
          borderRadius: 0,
          boxShadow: 3,
          backgroundColor: '#fff3cd',
          borderColor: '#ffeaa7',
        }}
        // actionを削除してユーザーがバナーを閉じられないようにする
        // action={...}
      >
        <AlertTitle>
          <Stack direction="row" alignItems="center" spacing={1}>
            <WarningIcon color="warning" />
            <Typography variant="h6" component="span" fontWeight="bold">
              システムメンテナンス中
            </Typography>
            <Chip 
              label="メンテナンス実行中" 
              color="warning" 
              size="small" 
              variant="outlined" 
            />
          </Stack>
        </AlertTitle>
        
        <Box sx={{ mt: 1 }}>
          <Typography variant="body1" color="text.secondary">
            {maintenanceStatus.message}
          </Typography>
          
          {maintenanceStatus.end_time && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              予定終了時刻: {new Date(maintenanceStatus.end_time).toLocaleString('ja-JP', {
                year: 'numeric',
                month: '2-digit', 
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'Asia/Tokyo'
              })}
            </Typography>
          )}
        </Box>
      </Alert>
      
      {/* バナー分のスペースを確保 */}
      <Box sx={{ height: 120 }} />
    </>
  );
};

export default MaintenanceBanner;
