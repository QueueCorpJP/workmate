import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Paper,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import api from '../api';
import { useAuth } from '../contexts/AuthContext';

export interface FileUploadStatus {
  file: File;
  status: 'waiting' | 'uploading' | 'completed' | 'error';
  progress: number;
  message: string;
  error?: string;
}

interface MultiFileUploadProps {
  open: boolean;
  onClose: () => void;
  onUploadComplete: () => void;
}

const MultiFileUpload: React.FC<MultiFileUploadProps> = ({
  open,
  onClose,
  onUploadComplete,
}) => {
  const { refreshUserData } = useAuth();
  const [files, setFiles] = useState<FileUploadStatus[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [currentUploadIndex, setCurrentUploadIndex] = useState(-1);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: FileUploadStatus[] = acceptedFiles.map(file => ({
      file,
      status: 'waiting',
      progress: 0,
      message: '待機中',
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.ms-excel.sheet.macroEnabled.12': ['.xlsm'],
      'application/vnd.ms-excel.sheet.binary.macroEnabled.12': ['.xlsb'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'application/rtf': ['.rtf'],
      'text/html': ['.html', '.htm'],
      'application/json': ['.json'],
      'application/xml': ['.xml'],
      'text/xml': ['.xml'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/gif': ['.gif'],
      'image/bmp': ['.bmp'],
    },
    multiple: true,
  });

  const removeFile = (index: number) => {
    if (isUploading && index <= currentUploadIndex) {
      return; // アップロード中または完了したファイルは削除不可
    }
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setIsUploading(true);
    
    for (let i = 0; i < files.length; i++) {
      if (files[i].status === 'completed') continue;
      
      setCurrentUploadIndex(i);
      
      // 現在のファイルを「アップロード中」に設定
      setFiles(prev => prev.map((file, index) => 
        index === i 
          ? { ...file, status: 'uploading', message: 'アップロード準備中...', progress: 0 }
          : file
      ));

      try {
        const formData = new FormData();
        formData.append('file', files[i].file);

        const response = await api.post('/v1/upload-document', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              
              setFiles(prev => prev.map((file, index) => 
                index === i 
                  ? { 
                      ...file, 
                      progress: percentCompleted,
                      message: percentCompleted < 100 
                        ? `アップロード中... ${percentCompleted}%`
                        : 'サーバーで処理中...'
                    }
                  : file
              ));
            } else {
              const loadedMB = (progressEvent.loaded / (1024 * 1024)).toFixed(1);
              setFiles(prev => prev.map((file, index) => 
                index === i 
                  ? { ...file, message: `アップロード中... ${loadedMB}MB` }
                  : file
              ));
            }
          },
        });

        // アップロード成功
        setFiles(prev => prev.map((file, index) => 
          index === i 
            ? { 
                ...file, 
                status: 'completed', 
                progress: 100, 
                message: 'アップロード完了'
              }
            : file
        ));

        console.log(`ファイル ${files[i].file.name} のアップロード成功:`, response.data);

      } catch (error: any) {
        console.error(`ファイル ${files[i].file.name} のアップロードエラー:`, error);
        const errorMessage = error.response?.data?.detail || error.message || 'アップロードに失敗しました';
        
        setFiles(prev => prev.map((file, index) => 
          index === i 
            ? { 
                ...file, 
                status: 'error', 
                message: 'アップロード失敗',
                error: errorMessage
              }
            : file
        ));
      }

      // 次のファイルに進む前に少し待機
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    setIsUploading(false);
    setCurrentUploadIndex(-1);
    
    // ユーザーデータを更新
    await refreshUserData();
    
    // 親コンポーネントに完了を通知
    onUploadComplete();
  };

  const getStatusIcon = (status: FileUploadStatus['status']) => {
    switch (status) {
      case 'waiting':
        return <HourglassEmptyIcon color="action" />;
      case 'uploading':
        return <PlayArrowIcon color="primary" />;
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <InsertDriveFileIcon />;
    }
  };

  const getStatusColor = (status: FileUploadStatus['status']) => {
    switch (status) {
      case 'waiting':
        return 'default';
      case 'uploading':
        return 'primary';
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const handleClose = () => {
    if (isUploading) {
      // アップロード中は閉じられない
      return;
    }
    setFiles([]);
    setCurrentUploadIndex(-1);
    onClose();
  };

  const completedCount = files.filter(f => f.status === 'completed').length;
  const errorCount = files.filter(f => f.status === 'error').length;
  const totalCount = files.length;

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      disableEscapeKeyDown={isUploading}
    >
      <DialogTitle>
        複数ファイルアップロード
        {totalCount > 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            進行状況: {completedCount + errorCount}/{totalCount} ファイル処理済み
            {errorCount > 0 && ` (${errorCount}件エラー)`}
          </Typography>
        )}
      </DialogTitle>
      
      <DialogContent>
        {/* ドロップゾーン */}
        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            borderRadius: 2,
            p: 3,
            textAlign: 'center',
            cursor: isUploading ? 'not-allowed' : 'pointer',
            bgcolor: isDragActive ? 'action.hover' : 'background.paper',
            mb: 3,
            opacity: isUploading ? 0.6 : 1,
          }}
        >
          <input {...getInputProps()} disabled={isUploading} />
          <CloudUploadIcon color="primary" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive
              ? 'ファイルをドロップしてください'
              : 'ファイルをドラッグ&ドロップまたはクリックして選択'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            PDF、Excel、Word、テキスト、CSV、画像ファイルに対応
          </Typography>
          {isUploading && (
            <Typography variant="body2" color="warning.main" sx={{ mt: 1 }}>
              アップロード中は新しいファイルを追加できません
            </Typography>
          )}
        </Box>

        {/* ファイル一覧 */}
        {files.length > 0 && (
          <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
            <List>
              {files.map((fileStatus, index) => (
                <ListItem
                  key={index}
                  sx={{
                    borderBottom: index < files.length - 1 ? '1px solid' : 'none',
                    borderColor: 'divider',
                  }}
                >
                  <ListItemIcon>
                    {getStatusIcon(fileStatus.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ flexGrow: 1 }}>
                          {fileStatus.file.name}
                        </Typography>
                        <Chip
                          label={fileStatus.status === 'waiting' ? '待機中' : 
                                fileStatus.status === 'uploading' ? '処理中' :
                                fileStatus.status === 'completed' ? '完了' : 'エラー'}
                          color={getStatusColor(fileStatus.status) as any}
                          size="small"
                        />
                        {!isUploading && fileStatus.status === 'waiting' && (
                          <Button
                            size="small"
                            color="error"
                            onClick={() => removeFile(index)}
                          >
                            削除
                          </Button>
                        )}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          {fileStatus.message}
                        </Typography>
                        {fileStatus.status === 'uploading' && (
                          <LinearProgress
                            variant="determinate"
                            value={fileStatus.progress}
                            sx={{ mt: 1 }}
                          />
                        )}
                        {fileStatus.error && (
                          <Alert severity="error" sx={{ mt: 1 }}>
                            {fileStatus.error}
                          </Alert>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        )}

        {/* 全体の進行状況 */}
        {isUploading && totalCount > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" gutterBottom>
              全体の進行状況: {completedCount + errorCount}/{totalCount}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={((completedCount + errorCount) / totalCount) * 100}
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button
          onClick={handleClose}
          disabled={isUploading}
          color="inherit"
        >
          {isUploading ? 'アップロード中...' : 'キャンセル'}
        </Button>
        <Button
          onClick={uploadFiles}
          disabled={files.length === 0 || isUploading}
          variant="contained"
          startIcon={<CloudUploadIcon />}
        >
          {isUploading ? 'アップロード中...' : `${files.length}件のファイルをアップロード`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MultiFileUpload;