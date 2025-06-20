import React, { useState } from "react";
import {
  Box,
  Typography,
  Button,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Snackbar,
  LinearProgress,
} from "@mui/material";
import { useDropzone } from "react-dropzone";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import LinkIcon from "@mui/icons-material/Link";
import AddIcon from "@mui/icons-material/Add";
import { Resource } from "./types";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";
import api from "../../api";
import { isValidURL } from './utils';
import { GoogleDriveAuth } from '../GoogleDriveAuth';
import { GoogleDriveFilePicker } from '../GoogleDriveFilePicker';
import { GoogleAuthStorage } from '../../utils/googleAuthStorage';
import { useAuth } from '../../contexts/AuthContext';

interface ResourcesTabProps {
  resources: Resource[];
  isLoading: boolean;
  onRefresh: () => void;
}

const ResourcesTab: React.FC<ResourcesTabProps> = ({
  resources,
  isLoading,
  onRefresh,
}) => {
  const { refreshUserData } = useAuth();
  
  // アップロードダイアログの状態
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadTab, setUploadTab] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>("");
  const [uploadPercentage, setUploadPercentage] = useState<number>(0);
  const [isSubmittingUrl, setIsSubmittingUrl] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  
  // Google Drive関連
  const [driveAccessToken, setDriveAccessToken] = useState<string>(() => {
    return GoogleAuthStorage.getAccessToken() || '';
  });
  const [drivePickerOpen, setDrivePickerOpen] = useState(false);
  const [driveAuthError, setDriveAuthError] = useState<string>('');
  
  // 通知関連
  const [showAlert, setShowAlert] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertSeverity, setAlertSeverity] = useState<'success' | 'error'>('success');

  // ファイルアップロード設定
  const { getRootProps, getInputProps } = useDropzone({
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      if (!file) return;

      // ファイルサイズとタイプをチェック
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (file.size > maxSize) {
        setAlertMessage("ファイルサイズが100MBを超えています。");
        setAlertSeverity('error');
        setShowAlert(true);
        return;
      }

      const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword'
      ];

      if (!allowedTypes.includes(file.type)) {
        setAlertMessage("サポートされていないファイル形式です。PDF、Excel、Word、テキストファイルのみアップロード可能です。");
        setAlertSeverity('error');
        setShowAlert(true);
        return;
      }

      await handleFileUpload(file);
    },
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc']
    },
    multiple: false,
  });

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setUploadProgress("アップロード準備中...");
    setUploadPercentage(0);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post("/upload-knowledge", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadPercentage(percentCompleted);
            
            if (percentCompleted < 100) {
              setUploadProgress(`アップロード中... ${percentCompleted}%`);
            } else {
              setUploadProgress("処理中... サーバーでファイルを解析しています");
            }
          } else {
            // totalが不明な場合は、loadedの値で大まかな進捗を表示
            const loadedMB = (progressEvent.loaded / (1024 * 1024)).toFixed(1);
            setUploadProgress(`アップロード中... ${loadedMB}MB`);
          }
        },
      });

      console.log("アップロード成功:", response.data);
      setUploadProgress("完了");
      setUploadPercentage(100);
      
      // 少し待ってから成功メッセージを表示
      setTimeout(() => {
        setAlertMessage(`ファイル "${file.name}" のアップロードが完了しました。`);
        setAlertSeverity('success');
        setShowAlert(true);
        
        // ユーザーデータを更新
        refreshUserData();
        
        // リソース一覧を更新
        onRefresh();
        
        // ダイアログを閉じる
        setUploadDialogOpen(false);
      }, 500);
      
    } catch (error: any) {
      console.error("アップロードエラー:", error);
      const errorMessage = error.response?.data?.detail || error.message || "アップロードに失敗しました";
      setAlertMessage(`アップロードエラー: ${errorMessage}`);
      setAlertSeverity('error');
      setShowAlert(true);
    } finally {
      // 少し待ってからリセット
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress("");
        setUploadPercentage(0);
      }, 1000);
    }
  };

  const handleSubmitUrl = async () => {
    if (!isValidURL(urlInput.trim())) {
      setAlertMessage("有効なURLを入力してください。");
      setAlertSeverity('error');
      setShowAlert(true);
      return;
    }

    setIsSubmittingUrl(true);
    try {
      const response = await api.post("/submit-url", {
        url: urlInput.trim(),
      });

      console.log("URL送信成功:", response.data);
      setAlertMessage(`URL "${urlInput}" の処理が完了しました。`);
      setAlertSeverity('success');
      setShowAlert(true);
      
      // ユーザーデータを更新
      refreshUserData();
      
      // リソース一覧を更新
      onRefresh();
      
      // フォームをリセット
      setUrlInput("");
      
      // ダイアログを閉じる
      setUploadDialogOpen(false);
      
    } catch (error: any) {
      console.error("URL送信エラー:", error);
      const errorMessage = error.response?.data?.detail || error.message || "URL処理に失敗しました";
      setAlertMessage(`URL処理エラー: ${errorMessage}`);
      setAlertSeverity('error');
      setShowAlert(true);
    } finally {
      setIsSubmittingUrl(false);
    }
  };

  const handleDriveAuthSuccess = (accessToken: string) => {
    setDriveAccessToken(accessToken);
    setDriveAuthError('');
  };

  const handleDriveAuthError = (error: string) => {
    setDriveAuthError(error);
    setDriveAccessToken('');
  };

  const handleDriveFileSelect = async (file: any) => {
    setIsUploading(true);
    setUploadProgress("Google Driveからダウンロード中...");
    setUploadPercentage(0);

    try {
      const formData = new FormData();
      formData.append('file_id', file.id);
      formData.append('access_token', driveAccessToken);
      formData.append('file_name', file.name);
      formData.append('mime_type', file.mimeType);

      const response = await api.post('/upload-from-drive', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadPercentage(percentCompleted);
            
            if (percentCompleted < 100) {
              setUploadProgress(`処理中... ${percentCompleted}%`);
            } else {
              setUploadProgress("Google Driveファイルを解析中...");
            }
          } else {
            setUploadProgress("Google Driveファイルを処理中...");
          }
        },
      });

      console.log("Google Driveアップロード成功:", response.data);
      setUploadProgress("完了");
      setUploadPercentage(100);
      
      setTimeout(() => {
        setAlertMessage(`Google Driveファイル "${file.name}" の処理が完了しました。`);
        setAlertSeverity('success');
        setShowAlert(true);
        
        // ユーザーデータを更新
        refreshUserData();
        
        // リソース一覧を更新
        onRefresh();
        
        // ダイアログを閉じる
        setUploadDialogOpen(false);
        setDrivePickerOpen(false);
      }, 500);
      
    } catch (error: any) {
      console.error("Google Driveアップロードエラー:", error);
      const errorMessage = error.response?.data?.detail || error.message || "Google Driveからの処理に失敗しました";
      setAlertMessage(`Google Drive処理エラー: ${errorMessage}`);
      setAlertSeverity('error');
      setShowAlert(true);
    } finally {
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress("");
        setUploadPercentage(0);
      }, 1000);
    }
  };

  const handleToggleResourceStatus = async (sourceId: string) => {
    try {
      const response = await api.post(
        `${import.meta.env.VITE_API_URL}/admin/resources/${encodeURIComponent(sourceId)}/toggle`
      );
      console.log("リソース状態切り替え結果:", response.data);
      // リソース情報を再取得
      onRefresh();
    } catch (error) {
      console.error("リソース状態の切り替えに失敗しました:", error);
      setAlertMessage("リソース状態の切り替えに失敗しました。");
      setAlertSeverity('error');
      setShowAlert(true);
    }
  };

  const handleDeleteResource = async (sourceId: string, name: string) => {
    // 確認ダイアログを表示
    if (
      !confirm(
        `リソース「${name}」を削除してもよろしいですか？この操作は元に戻せません。`
      )
    ) {
      return;
    }

    try {
      console.log(`リソース ${sourceId} を削除中...`);
      const response = await api.delete(
        `${import.meta.env.VITE_API_URL}/admin/resources/${encodeURIComponent(sourceId)}`
      );
      console.log("リソース削除結果:", response.data);
      // リソース情報を再取得
      onRefresh();
      setAlertMessage(`リソース「${name}」を削除しました。`);
      setAlertSeverity('success');
      setShowAlert(true);
    } catch (error) {
      console.error("リソースの削除に失敗しました:", error);
      setAlertMessage("リソースの削除に失敗しました。");
      setAlertSeverity('error');
      setShowAlert(true);
    }
  };

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setUploadTab(newValue);
  };

  return (
    <>
      <Box
        sx={{
          mb: 3,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          アップロードリソース
        </Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => setUploadDialogOpen(true)}
            sx={{
              borderRadius: "12px",
              fontWeight: 600,
              textTransform: "none",
              boxShadow: "0 2px 10px rgba(37, 99, 235, 0.2)",
              background: "linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)",
              "&:hover": {
                boxShadow: "0 4px 14px rgba(37, 99, 235, 0.3)",
                background: "linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)",
              },
            }}
          >
            新規アップロード
          </Button>
          <Button variant="outlined" onClick={onRefresh} disabled={isLoading}>
            更新
          </Button>
        </Box>
      </Box>

      {isLoading ? (
        <LoadingIndicator />
      ) : resources.length === 0 ? (
        <EmptyState message="アップロードされたリソースがありません" />
      ) : (
        <TableContainer
          component={Paper}
          sx={{
            boxShadow: "none",
            border: "1px solid",
            borderColor: "divider",
          }}
        >
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: "background.default" }}>
                <TableCell>名前</TableCell>
                <TableCell>タイプ</TableCell>
                <TableCell>ページ数</TableCell>
                <TableCell>アップロード日時</TableCell>
                <TableCell>状態</TableCell>
                <TableCell>操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {resources.map((resource, index) => (
                <TableRow
                  key={index}
                  hover
                  sx={{
                    opacity: resource.active ? 1 : 0.5,
                  }}
                >
                  <TableCell>{resource.name}</TableCell>
                  <TableCell>
                    <Chip
                      label={resource.type}
                      size="small"
                      sx={{
                        bgcolor:
                          resource.type === "URL"
                            ? "rgba(54, 162, 235, 0.6)"
                            : resource.type === "PDF"
                              ? "rgba(255, 99, 132, 0.6)"
                              : resource.type === "TXT"
                                ? "rgba(75, 192, 192, 0.6)"
                                : "rgba(255, 206, 86, 0.6)",
                        color: "white",
                        fontWeight: 500,
                      }}
                    />
                  </TableCell>
                  <TableCell>{resource.page_count || "-"}</TableCell>
                  <TableCell>
                    {resource.timestamp
                      ? new Date(resource.timestamp).toLocaleString("ja-JP", {
                        year: "numeric",
                        month: "2-digit",
                        day: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })
                      : "情報なし"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={resource.active ? "有効" : "無効"}
                      size="small"
                      color={resource.active ? "success" : "default"}
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="outlined"
                      size="small"
                      sx={{ marginRight: "5px" }}
                      color={resource.active ? "error" : "success"}
                      onClick={() => handleToggleResourceStatus(resource.id)}
                    >
                      {resource.active ? "無効にする" : "有効にする"}
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      color="error"
                      onClick={() =>
                        handleDeleteResource(resource.id, resource.name)
                      }
                    >
                      削除
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* アップロードダイアログ */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: "16px",
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.12)",
          },
        }}
      >
        <DialogTitle
          sx={{
            textAlign: "center",
            fontWeight: 600,
            fontSize: "1.25rem",
            pb: 1,
          }}
        >
          新しいリソースをアップロード
        </DialogTitle>
        <DialogContent sx={{ px: 3, pb: 2 }}>
          <Tabs
            value={uploadTab}
            onChange={handleTabChange}
            variant="fullWidth"
            sx={{
              mb: 3,
              "& .MuiTab-root": {
                textTransform: "none",
                fontWeight: 600,
                minHeight: 48,
              },
            }}
          >
            <Tab label="ファイル" />
            <Tab label="URL" />
            <Tab label="Google Drive" />
          </Tabs>

          {uploadTab === 0 && (
            <Box>
              <Box
                {...getRootProps()}
                sx={{
                  border: "2px dashed",
                  borderColor: "rgba(37, 99, 235, 0.3)",
                  borderRadius: "16px",
                  p: 4,
                  textAlign: "center",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  backgroundColor: "rgba(237, 242, 255, 0.5)",
                  "&:hover": {
                    borderColor: "primary.main",
                    backgroundColor: "rgba(237, 242, 255, 0.8)",
                    transform: "translateY(-2px)",
                    boxShadow: "0 4px 12px rgba(37, 99, 235, 0.15)",
                  },
                }}
              >
                <input {...getInputProps()} />
                <CloudUploadIcon
                  color="primary"
                  sx={{ fontSize: "3.5rem", mb: 2, opacity: 0.9 }}
                />
                <Typography
                  variant="body1"
                  sx={{ fontWeight: 600, mb: 1, color: "primary.main" }}
                >
                  ファイルをドロップまたはクリックして選択
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  PDF、Excel、Word、テキストファイル（最大100MB）
                </Typography>
              </Box>
              {(isUploading || uploadProgress) && (
                <Box sx={{ my: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ fontWeight: 500, flexGrow: 1 }}
                    >
                      {uploadProgress}
                    </Typography>
                    {uploadPercentage > 0 && uploadPercentage < 100 && (
                      <Typography
                        variant="body2"
                        color="primary.main"
                        sx={{ fontWeight: 600, ml: 1 }}
                      >
                        {uploadPercentage}%
                      </Typography>
                    )}
                  </Box>
                  {uploadPercentage > 0 && uploadPercentage < 100 ? (
                    <LinearProgress
                      variant="determinate"
                      value={uploadPercentage}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 3,
                          background: 'linear-gradient(90deg, #2563eb, #3b82f6)',
                        },
                      }}
                    />
                  ) : isUploading ? (
                    <LinearProgress
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 3,
                          background: 'linear-gradient(90deg, #2563eb, #3b82f6)',
                        },
                      }}
                    />
                  ) : null}
                </Box>
              )}
            </Box>
          )}

          {uploadTab === 1 && (
            <Box>
              <TextField
                fullWidth
                placeholder="https://example.com/document.pdf"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                variant="outlined"
                sx={{
                  mb: 3,
                  mt: 1,
                  "& .MuiOutlinedInput-root": {
                    borderRadius: "12px",
                    "& fieldset": {
                      borderColor: "rgba(37, 99, 235, 0.2)",
                      borderWidth: "1.5px",
                    },
                    "&:hover fieldset": {
                      borderColor: "rgba(37, 99, 235, 0.4)",
                    },
                    "&.Mui-focused fieldset": {
                      borderColor: "primary.main",
                      borderWidth: "2px",
                    },
                  },
                }}
                InputProps={{
                  startAdornment: (
                    <LinkIcon color="primary" sx={{ mr: 1, opacity: 0.7 }} />
                  ),
                }}
              />
              <Button
                variant="contained"
                color="primary"
                disabled={!isValidURL(urlInput.trim()) || isSubmittingUrl}
                onClick={handleSubmitUrl}
                fullWidth
                sx={{
                  py: 1.2,
                  borderRadius: "12px",
                  fontWeight: 600,
                  textTransform: "none",
                  boxShadow: "0 2px 10px rgba(37, 99, 235, 0.2)",
                  background: "linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)",
                  "&:hover": {
                    boxShadow: "0 4px 14px rgba(37, 99, 235, 0.3)",
                    background: "linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)",
                  },
                  transition: "all 0.2s ease",
                }}
              >
                {isSubmittingUrl ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  "URLを送信"
                )}
              </Button>
            </Box>
          )}

          {uploadTab === 2 && (
            <Box>
              <GoogleDriveAuth
                onAuthSuccess={handleDriveAuthSuccess}
                onAuthError={handleDriveAuthError}
              />
              
              {driveAuthError && (
                <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                  {driveAuthError}
                </Alert>
              )}

              {driveAccessToken && (
                <Box>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => setDrivePickerOpen(true)}
                    fullWidth
                    sx={{
                      py: 1.5,
                      borderRadius: "12px",
                      fontWeight: 600,
                      textTransform: "none",
                      boxShadow: "0 2px 10px rgba(37, 99, 235, 0.2)",
                      background: "linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)",
                      "&:hover": {
                        boxShadow: "0 4px 14px rgba(37, 99, 235, 0.3)",
                        background: "linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)",
                      },
                      transition: "all 0.2s ease",
                    }}
                  >
                    Google Driveからファイルを選択
                  </Button>
                </Box>
              )}

              {(isUploading || uploadProgress) && (
                <Box sx={{ my: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ fontWeight: 500, flexGrow: 1 }}
                    >
                      {uploadProgress}
                    </Typography>
                    {uploadPercentage > 0 && uploadPercentage < 100 && (
                      <Typography
                        variant="body2"
                        color="primary.main"
                        sx={{ fontWeight: 600, ml: 1 }}
                      >
                        {uploadPercentage}%
                      </Typography>
                    )}
                  </Box>
                  {uploadPercentage > 0 && uploadPercentage < 100 ? (
                    <LinearProgress
                      variant="determinate"
                      value={uploadPercentage}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 3,
                          background: 'linear-gradient(90deg, #2563eb, #3b82f6)',
                        },
                      }}
                    />
                  ) : isUploading ? (
                    <LinearProgress
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 3,
                          background: 'linear-gradient(90deg, #2563eb, #3b82f6)',
                        },
                      }}
                    />
                  ) : null}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button
            onClick={() => setUploadDialogOpen(false)}
            sx={{
              borderRadius: "8px",
              textTransform: "none",
              fontWeight: 600,
            }}
          >
            キャンセル
          </Button>
        </DialogActions>
      </Dialog>

      {/* Google Drive ファイルピッカー */}
      <GoogleDriveFilePicker
        open={drivePickerOpen}
        onClose={() => setDrivePickerOpen(false)}
        onFileSelect={handleDriveFileSelect}
        accessToken={driveAccessToken}
      />

      {/* 通知スナックバー */}
      <Snackbar
        open={showAlert}
        autoHideDuration={6000}
        onClose={() => setShowAlert(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setShowAlert(false)}
          severity={alertSeverity}
          sx={{ width: '100%', borderRadius: 2 }}
        >
          {alertMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default ResourcesTab;
