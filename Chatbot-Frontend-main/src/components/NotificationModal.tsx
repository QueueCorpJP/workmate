import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import NotificationsIcon from '@mui/icons-material/Notifications';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import AnnouncementIcon from '@mui/icons-material/Announcement';
import { 
  getNotifications, 
  Notification 
} from '../api';

interface NotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  onNotificationUpdate: () => void;
}

const NotificationModal: React.FC<NotificationModalProps> = ({
  isOpen,
  onClose,
  userId,
  onNotificationUpdate
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // 通知一覧を取得
  const fetchNotifications = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await getNotifications();
      setNotifications(data);
    } catch (error) {
      console.error('通知の取得に失敗しました:', error);
      setError('通知の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  // モーダルが開かれた時に通知を取得
  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen]);

  // 通知タイプのアイコン
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <WarningIcon sx={{ color: '#f59e0b' }} />;
      case 'info':
        return <InfoIcon sx={{ color: '#3b82f6' }} />;
      case 'announcement':
        return <AnnouncementIcon sx={{ color: '#10b981' }} />;
      default:
        return <NotificationsIcon sx={{ color: '#6b7280' }} />;
    }
  };

  // 相対時間の計算
  const getRelativeTime = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) return '数秒前';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}分前`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}時間前`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}日前`;
    
    return date.toLocaleDateString('ja-JP', { timeZone: 'Asia/Tokyo' });
  };

  if (!isOpen) return null;

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        bgcolor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        p: 2,
      }}
      onClick={onClose}
    >
      <Box
        sx={{
          bgcolor: 'white',
          borderRadius: 2,
          width: '100%',
          maxWidth: 600,
          maxHeight: '80vh',
          overflow: 'hidden',
          boxShadow: 24,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* ヘッダー */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 3,
            borderBottom: '1px solid #e5e5e5',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <NotificationsIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" component="h2" sx={{ fontWeight: 'bold' }}>
              通知
            </Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        {/* コンテンツ */}
        <Box sx={{ p: 3, maxHeight: 'calc(80vh - 120px)', overflow: 'auto' }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : notifications.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <NotificationsIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                通知はありません
              </Typography>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {notifications.map((notification) => (
                <Card key={notification.id} variant="outlined" sx={{ borderRadius: 2 }}>
                  <CardContent sx={{ py: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                      <Box sx={{ mr: 2, mt: 0.5 }}>
                        {getNotificationIcon(notification.notification_type)}
                      </Box>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                          {notification.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
                          {notification.content}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            {getRelativeTime(notification.created_at)}
                          </Typography>
                          <Chip
                            label={notification.notification_type}
                            size="small"
                            variant="outlined"
                            sx={{ height: 20, fontSize: '0.65rem' }}
                          />
                        </Box>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default NotificationModal; 