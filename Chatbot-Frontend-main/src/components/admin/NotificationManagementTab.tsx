import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Grid,
  Snackbar,
} from '@mui/material';
import {
  Send as SendIcon,
  Notifications as NotificationsIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  People as PeopleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Announcement as AnnouncementIcon,
} from '@mui/icons-material';
import {
  getNotifications,
  createNotification,
  deleteNotification,
  Notification,
} from '../../api';
import api from '../../api';

interface NotificationManagementTabProps {
  onRefresh?: () => void;
}



const NotificationManagementTab: React.FC<NotificationManagementTabProps> = ({
  onRefresh
}) => {
  // 通知作成用のステート
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [notificationType, setNotificationType] = useState('general');
  
    // データステート
  const [recentNotifications, setRecentNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // エラー・成功メッセージ
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  
  // 削除確認ダイアログ
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [notificationToDelete, setNotificationToDelete] = useState<Notification | null>(null);

  // 初期データ読み込み
  useEffect(() => {
    fetchRecentNotifications();
  }, []);

  // 最近の通知取得（管理者用）
  const fetchRecentNotifications = async () => {
    setIsLoading(true);
    try {
      const notifications = await getNotifications();
      setRecentNotifications(notifications.slice(0, 10)); // 最新10件
    } catch (error) {
      console.error('通知の取得に失敗しました:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 全員への通知送信（1つの通知レコードのみ作成）
  const handleSendNotification = async () => {
    if (!title.trim() || !content.trim()) {
      setError('タイトルと内容を入力してください');
      return;
    }

    setIsCreating(true);
    setError('');
    
    try {
      // 1つの通知レコードのみ作成（全員が参照）
      await createNotification({
        title,
        content,
        notification_type: notificationType
      });

      setSuccess('全ユーザーに通知を送信しました');
      setTitle('');
      setContent('');
      setNotificationType('general');
      setSnackbarOpen(true);
      fetchRecentNotifications();
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('通知送信に失敗しました:', error);
      setError('通知の送信に失敗しました');
    } finally {
      setIsCreating(false);
    }
  };

  // 通知削除
  const handleDeleteNotification = async (notification: Notification) => {
    setNotificationToDelete(notification);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteNotification = async () => {
    if (!notificationToDelete) return;

    try {
      await deleteNotification(notificationToDelete.id);
      setSuccess('通知を削除しました');
      setSnackbarOpen(true);
      fetchRecentNotifications();
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('通知削除に失敗しました:', error);
      setError('通知の削除に失敗しました');
    } finally {
      setDeleteDialogOpen(false);
      setNotificationToDelete(null);
    }
  };

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

  return (
    <Box sx={{ p: 3, height: '100%', overflow: 'auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <NotificationsIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h5" component="h1" sx={{ fontWeight: 'bold' }}>
          通知管理
        </Typography>
        <Chip
          label="最上位管理者専用"
          size="small"
          sx={{ ml: 2, bgcolor: '#fef3c7', color: '#92400e' }}
        />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* 通知作成セクション */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
              <SendIcon sx={{ mr: 1 }} />
              新しい通知を作成
            </Typography>

            <Box sx={{ mb: 3 }}>
              <Box sx={{ mb: 2, p: 2, bgcolor: '#e3f2fd', borderRadius: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <PeopleIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                    送信対象: 全ユーザー
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  作成した通知は全てのユーザーに表示されます
                </Typography>
              </Box>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>通知タイプ</InputLabel>
                <Select
                  value={notificationType}
                  onChange={(e) => setNotificationType(e.target.value)}
                  label="通知タイプ"
                >
                  <MenuItem value="general">一般</MenuItem>
                  <MenuItem value="announcement">お知らせ</MenuItem>
                  <MenuItem value="warning">警告</MenuItem>
                  <MenuItem value="info">情報</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="通知タイトル"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                sx={{ mb: 2 }}
                placeholder="例: システムメンテナンスのお知らせ"
              />

              <TextField
                fullWidth
                label="通知内容"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                multiline
                rows={4}
                sx={{ mb: 2 }}
                placeholder="通知の詳細内容を入力してください..."
              />

              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleSendNotification}
                  disabled={isCreating || !title.trim() || !content.trim()}
                  startIcon={isCreating ? <CircularProgress size={20} /> : <PeopleIcon />}
                  sx={{ bgcolor: '#dc2626', '&:hover': { bgcolor: '#b91c1c' } }}
                >
                  {isCreating ? '送信中...' : '全員に送信'}
                </Button>

                <Button
                  variant="outlined"
                  onClick={() => {
                    setTitle('');
                    setContent('');
                    setNotificationType('general');
                    setError('');
                  }}
                >
                  クリア
                </Button>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* 統計情報 */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              統計情報
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">最近の通知数:</Typography>
                <Chip label={`${recentNotifications.length}件`} size="small" />
              </Box>
            </Box>
          </Paper>

          <Button
            variant="outlined"
            onClick={() => {
              fetchRecentNotifications();
            }}
            startIcon={<RefreshIcon />}
            fullWidth
          >
            データを更新
          </Button>
        </Grid>

        {/* 最近送信した通知 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              最近送信した通知
            </Typography>
            
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : recentNotifications.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 3 }}>
                まだ通知がありません
              </Typography>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {recentNotifications.map((notification) => (
                  <Card key={notification.id} variant="outlined">
                    <CardContent sx={{ py: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Box sx={{ flex: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            {getNotificationIcon(notification.notification_type)}
                            <Typography variant="subtitle2" sx={{ ml: 1, fontWeight: 'bold' }}>
                              {notification.title}
                            </Typography>
                            <Chip
                              label={notification.notification_type}
                              size="small"
                              variant="outlined"
                              sx={{ ml: 1 }}
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {notification.content}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(notification.created_at).toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}
                          </Typography>
                        </Box>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteNotification(notification)}
                          sx={{ color: 'error.main' }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* 削除確認ダイアログ */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>通知を削除しますか？</DialogTitle>
        <DialogContent>
          <Typography>
            「{notificationToDelete?.title}」を削除しますか？この操作は元に戻せません。
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>キャンセル</Button>
          <Button onClick={confirmDeleteNotification} color="error" variant="contained">
            削除
          </Button>
        </DialogActions>
      </Dialog>

      {/* 成功メッセージ */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
      >
        <Alert severity="success" onClose={() => setSnackbarOpen(false)}>
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default NotificationManagementTab; 