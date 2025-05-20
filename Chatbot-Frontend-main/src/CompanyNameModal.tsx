import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Box,
  CircularProgress,
  Alert
} from '@mui/material';
import { styled } from '@mui/material/styles';
import BusinessIcon from '@mui/icons-material/Business';
import { useCompany } from './contexts/CompanyContext';
import api from './api';

// スタイル付きコンポーネント
const LogoContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  marginBottom: theme.spacing(3),
}));

const LogoIcon = styled(BusinessIcon)(({ theme }) => ({
  fontSize: 64,
  color: theme.palette.primary.main,
  marginBottom: theme.spacing(2),
}));

interface CompanyNameModalProps {
  open: boolean;
  onClose?: () => void;
}

const CompanyNameModal: React.FC<CompanyNameModalProps> = ({ open, onClose }) => {
  const { setCompanyName } = useCompany();
  const [newCompanyName, setNewCompanyName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // モーダルが開いたときに入力フィールドをクリア
  useEffect(() => {
    if (open) {
      setNewCompanyName('');
      setError(null);
    }
  }, [open]);

  const handleSave = async () => {
    if (!newCompanyName.trim()) {
      setError('会社名を入力してください');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.post(`${import.meta.env.VITE_API_URL}/company-name`, {
        company_name: newCompanyName.trim()
      });
      
      if (response.data && response.data.company_name) {
        setCompanyName(response.data.company_name);
        // 成功したらモーダルを閉じる
        if (onClose) onClose();
      }
    } catch (error: any) {
      console.error('会社名の設定に失敗しました:', error);
      
      // エラーメッセージの詳細を取得
      let errorMessage = '会社名の設定に失敗しました。';
      if (error.response?.data?.detail) {
        errorMessage += ` ${error.response.data.detail}`;
      } else if (error.message) {
        errorMessage += ` ${error.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      maxWidth="sm"
      fullWidth
      disableEscapeKeyDown
      onClose={onClose} // onCloseを使用
    >
      <DialogTitle sx={{ textAlign: 'center', pt: 4 }}>
        ようこそ！
      </DialogTitle>
      <DialogContent>
        <LogoContainer>
          <LogoIcon />
          <Typography variant="h5" component="div" sx={{ fontWeight: 600, mb: 1 }}>
            会社名を設定してください
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mb: 2 }}>
            チャットボットに表示される会社名を設定します。
            この設定はいつでも変更できます。
          </Typography>
        </LogoContainer>

        <TextField
          fullWidth
          label="会社名"
          variant="outlined"
          placeholder="例: 株式会社サンプル"
          value={newCompanyName}
          onChange={(e) => setNewCompanyName(e.target.value)}
          error={!!error}
          helperText={error}
          sx={{ mb: 3 }}
        />

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button
          fullWidth
          variant="contained"
          color="primary"
          size="large"
          onClick={handleSave}
          disabled={isLoading || !newCompanyName.trim()}
          sx={{ py: 1.5 }}
        >
          {isLoading ? <CircularProgress size={24} /> : '設定して始める'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CompanyNameModal;