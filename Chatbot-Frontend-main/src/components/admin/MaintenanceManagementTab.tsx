import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Stack,
  Alert,
  AlertTitle,
  Divider,
  Chip,
  Grid,
  Paper,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Construction as ConstructionIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Refresh as RefreshIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ja } from 'date-fns/locale';
import api from '../../api';

interface MaintenanceStatus {
  is_active: boolean;
  message: string;
  start_time?: string;
  end_time?: string;
  created_by?: string;
  updated_at: string;
}

interface MaintenanceManagementTabProps {
  user?: any;
}

const MaintenanceManagementTab: React.FC<MaintenanceManagementTabProps> = ({ user }) => {
  const [maintenanceStatus, setMaintenanceStatus] = useState<MaintenanceStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('システムメンテナンス中です。しばらくお待ちください。');
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [endTime, setEndTime] = useState<Date | null>(null);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  // メンテナンス状態を取得
  const fetchMaintenanceStatus = async () => {
    try {
      const response = await api.get('/maintenance/status');
      const status = response.data.status;
      setMaintenanceStatus(status);
      
      if (status.is_active) {
        setMessage(status.message || 'システムメンテナンス中です。');
        if (status.start_time) setStartTime(new Date(status.start_time));
        if (status.end_time) setEndTime(new Date(status.end_time));
      }
    } catch (error: any) {
      console.error('メンテナンス状態取得エラー:', error);
      setError(`状態取得エラー: ${error.response?.data?.detail || error.message}`);
    }
  };

  // メンテナンスモード切り替え
  const toggleMaintenanceMode = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const isActivating = !maintenanceStatus?.is_active;
      
      const response = await api.post('/maintenance/toggle', {
        is_active: isActivating,
        message: isActivating ? message : 'メンテナンスが完了しました。',
        start_time: isActivating && startTime ? startTime.toISOString() : null,
        end_time: isActivating && endTime ? endTime.toISOString() : null
      });
      
      setSuccess(response.data.message);
      await fetchMaintenanceStatus();
      
      // フォームをリセット
      if (!isActivating) {
        setMessage('システムメンテナンス中です。しばらくお待ちください。');
        setStartTime(null);
        setEndTime(null);
      }
      
    } catch (error: any) {
      setError(`エラー: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMaintenanceStatus();
  }, []);

  // 管理者権限チェック
  const isMaintenanceAdmin = user?.email === 'taichi.taniguchi@queue-tech.jp' || 
                           user?.email === 'queue@queue-tech.jp';

  if (!isMaintenanceAdmin) {
    return (
      <Box p={3}>
        <Alert severity="error">
          <AlertTitle>アクセス権限エラー</AlertTitle>
          このタブはメンテナンス管理者のみアクセス可能です。
        </Alert>
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ja}>
      <Box p={3}>
        <Stack spacing={3}>
          {/* ヘッダー */}
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={1}>
              <ConstructionIcon color="primary" />
              <Typography variant="h5" fontWeight="bold">
                メンテナンス管理
              </Typography>
            </Box>
            <Tooltip title="状態を更新">
              <IconButton onClick={fetchMaintenanceStatus} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* エラー・成功メッセージ */}
          {error && (
            <Alert severity="error" onClose={() => setError('')}>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" onClose={() => setSuccess('')}>
              {success}
            </Alert>
          )}

          {/* 現在のメンテナンス状態 */}
          <Card>
            <CardContent>
              <Stack spacing={2}>
                <Box display="flex" alignItems="center" justifyContent="between">
                  <Typography variant="h6" gutterBottom>
                    現在のメンテナンス状態
                  </Typography>
                  {maintenanceStatus && (
                    <Chip
                      icon={maintenanceStatus.is_active ? <WarningIcon /> : <CheckIcon />}
                      label={maintenanceStatus.is_active ? 'メンテナンス中' : '通常運用中'}
                      color={maintenanceStatus.is_active ? 'warning' : 'success'}
                      variant="outlined"
                    />
                  )}
                </Box>
                
                {maintenanceStatus && (
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary">
                          メッセージ
                        </Typography>
                        <Typography variant="body1">
                          {maintenanceStatus.message}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary">
                          最終更新
                        </Typography>
                        <Typography variant="body2">
                          {new Date(maintenanceStatus.updated_at).toLocaleString('ja-JP', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit', 
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            timeZone: 'Asia/Tokyo'
                          })}
                        </Typography>
                        {maintenanceStatus.created_by && (
                          <Typography variant="caption" color="text.secondary">
                            by {maintenanceStatus.created_by}
                          </Typography>
                        )}
                      </Paper>
                    </Grid>
                  </Grid>
                )}
              </Stack>
            </CardContent>
          </Card>

          <Divider />

          {/* メンテナンス設定 */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                メンテナンス設定
              </Typography>
              
              <Stack spacing={3}>
                {/* メンテナンス切り替え */}
                <FormControlLabel
                  control={
                    <Switch
                      checked={maintenanceStatus?.is_active || false}
                      onChange={toggleMaintenanceMode}
                      disabled={loading}
                      color="warning"
                    />
                  }
                  label={
                    <Typography variant="body1" fontWeight="medium">
                      {maintenanceStatus?.is_active ? 'メンテナンスモードを無効化' : 'メンテナンスモードを有効化'}
                    </Typography>
                  }
                />

                {/* メッセージ設定 */}
                <TextField
                  label="メンテナンスメッセージ"
                  multiline
                  rows={3}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="ユーザーに表示するメンテナンスメッセージを入力..."
                  fullWidth
                  disabled={loading}
                />

                {/* 時刻設定 */}
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <DateTimePicker
                      label="開始時刻（オプション）"
                      value={startTime}
                      onChange={(newValue) => setStartTime(newValue)}
                      disabled={loading}
                      slotProps={{
                        textField: {
                          fullWidth: true,
                          helperText: "メンテナンス開始予定時刻"
                        }
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <DateTimePicker
                      label="終了予定時刻（オプション）"
                      value={endTime}
                      onChange={(newValue) => setEndTime(newValue)}
                      disabled={loading}
                      slotProps={{
                        textField: {
                          fullWidth: true,
                          helperText: "メンテナンス終了予定時刻"
                        }
                      }}
                    />
                  </Grid>
                </Grid>

                {/* 実行ボタン */}
                <Box display="flex" gap={2}>
                  <Button
                    variant="contained"
                    color={maintenanceStatus?.is_active ? "error" : "warning"}
                    startIcon={maintenanceStatus?.is_active ? <CheckIcon /> : <ConstructionIcon />}
                    onClick={toggleMaintenanceMode}
                    disabled={loading}
                    size="large"
                  >
                    {loading ? '処理中...' : 
                     maintenanceStatus?.is_active ? 'メンテナンス終了' : 'メンテナンス開始'}
                  </Button>
                  
                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={fetchMaintenanceStatus}
                    disabled={loading}
                  >
                    状態更新
                  </Button>
                </Box>
              </Stack>
            </CardContent>
          </Card>

          {/* 注意事項 */}
          <Alert severity="info">
            <AlertTitle>メンテナンス管理について</AlertTitle>
            <Typography variant="body2">
              • メンテナンスモードが有効になると、taichi.taniguchi@queue-tech.jp と queue@queue-tech.jp 以外のすべてのユーザーがシステムにアクセスできなくなります。
              <br />
              • ユーザーには設定したメッセージが表示されます。
              <br />
              • 終了予定時刻を設定すると、ユーザーに終了予定が表示されます。
            </Typography>
          </Alert>
        </Stack>
      </Box>
    </LocalizationProvider>
  );
};

export default MaintenanceManagementTab;
