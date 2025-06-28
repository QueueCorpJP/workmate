import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  Button,
  CircularProgress,
  Typography,
  Box,
  Chip,
  TextField,
  InputAdornment,
  Breadcrumbs,
  Link
} from '@mui/material';
import {
  InsertDriveFile,
  Folder,
  Search as SearchIcon,
  ArrowBack as ArrowBackIcon,
  CloudDownload as CloudDownloadIcon
} from '@mui/icons-material';
import { SUPPORTED_MIME_TYPES } from '../utils/googleConfig';
import { GoogleAuthStorage } from '../utils/googleAuthStorage';

interface GoogleDriveFile {
  id: string;
  name: string;
  mimeType: string;
  size?: number;
  modifiedTime?: string;
  webViewLink?: string;
}

interface GoogleDriveFilePickerProps {
  open: boolean;
  onClose: () => void;
  onFileSelect: (file: GoogleDriveFile) => void;
  accessToken: string;
}

interface Folder {
  id: string;
  name: string;
}

export const GoogleDriveFilePicker: React.FC<GoogleDriveFilePickerProps> = ({
  open,
  onClose,
  onFileSelect,
  accessToken
}) => {
  const [files, setFiles] = useState<GoogleDriveFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentFolder, setCurrentFolder] = useState<string>('root');
  const [folderPath, setFolderPath] = useState<Folder[]>([
    { id: 'root', name: 'マイドライブ' }
  ]);

  useEffect(() => {
    if (open) {
      // アクセストークンが渡されていない場合は保存された認証状態から取得
      const token = accessToken || GoogleAuthStorage.getAccessToken();
      if (token) {
        loadFiles();
      }
    }
  }, [open, accessToken, currentFolder]);

  const loadFiles = async () => {
    setLoading(true);
    try {
      // gapiが利用可能かチェック
      if (!window.gapi) {
        throw new Error('Google API が読み込まれていません。ページを再読み込みしてください。');
      }

      console.log('Google Drive API読み込み開始...');

      // clientライブラリを読み込み
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Google API の読み込みがタイムアウトしました'));
        }, 10000); // 10秒タイムアウト

        window.gapi.load('client', {
          callback: () => {
            clearTimeout(timeout);
            console.log('Google API client 読み込み完了');
            resolve();
          },
          onerror: (error: Error) => {
            clearTimeout(timeout);
            reject(error);
          }
        });
      });

      // clientが初期化されているかチェック
      if (!window.gapi.client) {
        throw new Error('Google API Client が初期化されていません');
      }

      const initConfig: any = {
        discoveryDocs: ['https://www.googleapis.com/discovery/v1/apis/drive/v3/rest']
      };
      
      // APIキーがある場合は設定（OAuth使用時は不要だが念のため）
      const apiKey = import.meta.env.VITE_GOOGLE_DRIVE_API_KEY;
      if (apiKey) {
        initConfig.apiKey = apiKey;
      }
      
      console.log('Google Drive API初期化中...');
      await window.gapi.client.init(initConfig);
      console.log('Google Drive API初期化完了');
      
      // アクセストークンを設定（渡されたトークンか保存されたトークンを使用）
      const token = accessToken || GoogleAuthStorage.getAccessToken();
      if (!token) {
        throw new Error('アクセストークンが見つかりません。再度認証してください。');
      }
      window.gapi.client.setToken({ access_token: token });

      // Driveクライアントが利用可能かチェック
      if (!window.gapi.client.drive) {
        throw new Error('Google Drive API が読み込まれていません');
      }

      let query = `'${currentFolder}' in parents and trashed = false`;
      
      if (searchQuery) {
        query += ` and name contains '${searchQuery}'`;
      }

      const response = await window.gapi.client.drive.files.list({
        q: query,
        pageSize: 100,
        fields: 'files(id, name, mimeType, size, modifiedTime, webViewLink)',
        orderBy: 'folder,name'
      });

      const allFiles = response.result.files || [];
      
      // サポートされているファイル形式のみフィルター（より包括的に）
      const supportedFiles = allFiles.filter((file: GoogleDriveFile) => {
        // フォルダは常に表示
        if (file.mimeType === 'application/vnd.google-apps.folder') {
          return true;
        }
        
        // サポートされているMIMEタイプをチェック
        if (SUPPORTED_MIME_TYPES.includes(file.mimeType)) {
          return true;
        }
        
        // ファイル拡張子による追加チェック（MIMEタイプが不正確な場合のフォールバック）
        const fileName = file.name.toLowerCase();
        const supportedExtensions = [
          '.pdf', '.xlsx', '.xls', '.xlsm', '.xlsb', '.csv',
          '.docx', '.doc', '.txt', '.rtf', '.html', '.htm',
          '.json', '.xml'
        ];
        
        return supportedExtensions.some(ext => fileName.endsWith(ext));
      });

      setFiles(supportedFiles);
    } catch (error) {
      console.error('ファイル読み込みエラー:', error);
      const errorMessage = error instanceof Error ? error.message : '不明なエラー';
      console.error('詳細:', errorMessage);
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFolderClick = (folder: GoogleDriveFile) => {
    if (folder.mimeType === 'application/vnd.google-apps.folder') {
      setCurrentFolder(folder.id);
      setFolderPath([...folderPath, { id: folder.id, name: folder.name }]);
    }
  };

  const handleFileClick = (file: GoogleDriveFile) => {
    if (file.mimeType === 'application/vnd.google-apps.folder') {
      handleFolderClick(file);
    } else {
      onFileSelect(file);
      onClose();
    }
  };

  const handleBreadcrumbClick = (folder: Folder, index: number) => {
    setCurrentFolder(folder.id);
    setFolderPath(folderPath.slice(0, index + 1));
  };

  const handleSearch = () => {
    loadFiles();
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  const formatFileSize = (size?: number) => {
    if (!size) return '-';
    
    const units = ['B', 'KB', 'MB', 'GB'];
    let unitIndex = 0;
    let fileSize = size;
    
    while (fileSize >= 1024 && unitIndex < units.length - 1) {
      fileSize /= 1024;
      unitIndex++;
    }
    
    return `${fileSize.toFixed(1)} ${units[unitIndex]}`;
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType === 'application/vnd.google-apps.folder') {
      return <Folder color="primary" />;
    }
    return <InsertDriveFile color="action" />;
  };

  const getMimeTypeLabel = (mimeType: string) => {
    const typeMap: { [key: string]: string } = {
      'application/pdf': 'PDF',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel',
      'application/vnd.ms-excel': 'Excel',
      'text/plain': 'テキスト',
      'application/vnd.google-apps.document': 'Google Doc',
      'application/vnd.google-apps.spreadsheet': 'Google Sheet',
      'application/vnd.google-apps.folder': 'フォルダ'
    };
    return typeMap[mimeType] || 'ファイル';
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { height: '80vh', maxHeight: '600px' }
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <CloudDownloadIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6">Google Driveからファイルを選択</Typography>
        </Box>
        
        {/* パンくずナビ */}
        <Breadcrumbs sx={{ fontSize: '0.875rem' }}>
          {folderPath.map((folder, index) => (
            <Link
              key={folder.id}
              component="button"
              variant="body2"
              onClick={() => handleBreadcrumbClick(folder, index)}
              sx={{
                cursor: 'pointer',
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' }
              }}
            >
              {folder.name}
            </Link>
          ))}
        </Breadcrumbs>
      </DialogTitle>

      <DialogContent sx={{ px: 0, pb: 0 }}>
        {/* 検索バー */}
        <Box sx={{ px: 3, mb: 2 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="ファイル名で検索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: searchQuery && (
                <InputAdornment position="end">
                  <Button size="small" onClick={handleSearch}>
                    検索
                  </Button>
                </InputAdornment>
              )
            }}
          />
        </Box>

        {/* ファイル一覧 */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : files.length === 0 ? (
          <Box sx={{ textAlign: 'center', p: 4 }}>
            <Typography color="text.secondary">
              {searchQuery ? '検索結果が見つかりません' : 'ファイルがありません'}
            </Typography>
          </Box>
        ) : (
          <List sx={{ px: 1 }}>
            {files.map((file) => (
              <ListItem key={file.id} disablePadding>
                <ListItemButton
                  onClick={() => handleFileClick(file)}
                  sx={{
                    borderRadius: 1,
                    mx: 1,
                    mb: 0.5,
                    '&:hover': {
                      backgroundColor: 'action.hover'
                    }
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    {getFileIcon(file.mimeType)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {file.name}
                        </Typography>
                        <Chip
                          label={getMimeTypeLabel(file.mimeType)}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.75rem', height: 20 }}
                        />
                      </Box>
                    }
                    secondary={
                      <Typography variant="caption" color="pink.main">
                        {file.modifiedTime ? new Date(file.modifiedTime).toLocaleDateString('ja-JP') : '日付不明'}
                      </Typography>
                    }
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} variant="outlined">
          キャンセル
        </Button>
      </DialogActions>
    </Dialog>
  );
}; 