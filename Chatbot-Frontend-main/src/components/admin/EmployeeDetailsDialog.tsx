import React, { useState, useMemo } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  List,
  Divider,
  Chip
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { ChatHistoryItem, EmployeeUsageItem, categoryColors, sentimentColors } from './types';
import LoadingIndicator from './LoadingIndicator';
import EmptyState from './EmptyState';
import { formatDate } from './utils';
import MarkdownRenderer from '../MarkdownRenderer';

interface EmployeeDetailsDialogProps {
  open: boolean;
  onClose: () => void;
  selectedEmployee: EmployeeUsageItem | null;
  employeeDetails: ChatHistoryItem[];
  isLoading: boolean;
}

const EmployeeDetailsDialog: React.FC<EmployeeDetailsDialogProps> = ({
  open,
  onClose,
  selectedEmployee,
  employeeDetails,
  isLoading
}) => {
  const [displayCount, setDisplayCount] = useState(5);
  
  // 表示する履歴データ（最新から表示数分）
  const displayedChats = useMemo(() => {
    const sortedChats = [...employeeDetails].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    return sortedChats.slice(0, displayCount);
  }, [employeeDetails, displayCount]);

  // 「もっと見る」ボタンの表示判定
  const hasMoreChats = displayCount < employeeDetails.length;

  // 「もっと見る」ボタンのハンドラー
  const handleLoadMore = () => {
    setDisplayCount(prevCount => Math.min(prevCount + 5, employeeDetails.length));
  };

  // ダイアログが開かれるたびに表示数をリセット
  React.useEffect(() => {
    if (open) {
      setDisplayCount(5);
    }
  }, [open]);

  // チャットメッセージのスタイル定義（実際のチャット画面と同じ）
  const userMessageStyles = {
    bgcolor: "primary.main",
    color: "white",
    p: { xs: 1.2, sm: 1.5, md: 2 },
    px: { xs: 1.5, sm: 2 },
    borderRadius: { xs: "12px 12px 4px 12px", sm: "16px 16px 6px 16px" },
    maxWidth: { xs: "85%", sm: "75%", md: "65%" },
    wordBreak: "break-word",
    boxShadow: "0 2px 8px rgba(37, 99, 235, 0.2)",
    alignSelf: "flex-end",
    mb: { xs: 1, sm: 2 },
    animation: "fadeIn 0.3s ease-out",
    fontSize: { xs: "0.85rem", sm: "0.95rem" },
    lineHeight: 1.5,
    transition: "all 0.2s ease",
    "&:hover": {
      boxShadow: "0 4px 16px rgba(37, 99, 235, 0.3)",
      transform: "translateY(-1px)",
    },
    position: "relative",
    "&::after": {
      content: '""',
      position: "absolute",
      right: "-6px",
      bottom: "0",
      width: "12px",
      height: "12px",
      background: "primary.main",
      clipPath: "polygon(0 0, 100% 100%, 0 100%)",
    },
    backgroundImage: "linear-gradient(135deg, #2563eb, #3b82f6)",
    backdropFilter: "blur(4px)",
    border: "1px solid rgba(255, 255, 255, 0.2)",
  };

  const botMessageStyles = {
    bgcolor: "#FFFFFF",
    p: { xs: 1.2, sm: 1.5, md: 2 },
    px: { xs: 1.5, sm: 2 },
    borderRadius: { xs: "12px 12px 12px 4px", sm: "16px 16px 16px 6px" },
    maxWidth: { xs: "85%", sm: "75%", md: "65%" },
    wordBreak: "break-word",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.06)",
    alignSelf: "flex-start",
    mb: { xs: 1, sm: 2 },
    animation: "fadeIn 0.3s ease-out",
    fontSize: { xs: "0.85rem", sm: "0.95rem" },
    lineHeight: 1.5,
    transition: "all 0.2s ease",
    "&:hover": {
      boxShadow: "0 4px 14px rgba(0, 0, 0, 0.1)",
      transform: "translateY(-1px)",
    },
    position: "relative",
    "&::before": {
      content: '""',
      position: "absolute",
      left: "-6px",
      bottom: "0",
      width: "12px",
      height: "12px",
      background: "linear-gradient(135deg, #FFFFFF, #F8FAFC)",
      clipPath: "polygon(100% 0, 100% 100%, 0 100%)",
      borderRadius: "0 0 0 4px",
      boxShadow: "-1px 1px 2px rgba(0, 0, 0, 0.05)",
    },
    backgroundImage: "linear-gradient(135deg, #FFFFFF, #F8FAFC)",
    border: "1px solid rgba(37, 99, 235, 0.08)",
    backdropFilter: "blur(4px)",
  };

  if (!selectedEmployee) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          maxHeight: '90vh'
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        pb: 1,
        borderBottom: '1px solid',
        borderColor: 'divider'
      }}>
        <Box>
          <Typography variant="h6" component="span" sx={{ fontWeight: 600 }}>
            {selectedEmployee.employee_name || '名前なし'}
          </Typography>
          <Typography variant="body2" component="span" sx={{ ml: 1, color: 'text.secondary' }}>
            (ID: {selectedEmployee.employee_id})
          </Typography>
        </Box>
        <IconButton edge="end" color="inherit" onClick={onClose} aria-label="close">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ p: 0 }}>
        {isLoading ? (
          <Box sx={{ p: 3 }}>
            <LoadingIndicator />
          </Box>
        ) : employeeDetails.length === 0 ? (
          <Box sx={{ p: 3 }}>
            <EmptyState message="メッセージ履歴がありません" />
          </Box>
        ) : (
          <Box sx={{ height: 'auto', overflow: 'auto' }}>
            {/* 統計情報 */}
            <Box sx={{ p: 3, bgcolor: 'grey.50' }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Card variant="outlined" sx={{ textAlign: 'center' }}>
                    <CardContent sx={{ py: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        利用数
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
                        {selectedEmployee.message_count}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Card variant="outlined" sx={{ textAlign: 'center' }}>
                    <CardContent sx={{ py: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        表示中
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main' }}>
                        {displayedChats.length}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Card variant="outlined">
                    <CardContent sx={{ py: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        最終利用
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {formatDate(selectedEmployee.last_activity)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>

            {/* チャット履歴 */}
            <Box sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, display: 'flex', alignItems: 'center' }}>
                チャット履歴
                <Chip 
                  label={`${displayedChats.length} / ${employeeDetails.length}`} 
                  size="small" 
                  sx={{ ml: 1 }}
                  color="primary"
                  variant="outlined"
                />
              </Typography>
              
              {/* チャットメッセージエリア */}
              <Box sx={{ 
                background: "rgba(248, 250, 252, 0.9)",
                backgroundImage: "radial-gradient(rgba(37, 99, 235, 0.04) 1px, transparent 0)",
                backgroundSize: "20px 20px",
                borderRadius: 2,
                p: 2,
                maxHeight: '400px',
                overflow: 'auto',
                border: '1px solid',
                borderColor: 'divider'
              }}>
                {displayedChats.map((chat, index) => (
                  <Box key={chat.id} sx={{ mb: 3 }}>
                    {/* タイムスタンプとカテゴリ情報 */}
                    <Box sx={{ 
                      display: 'flex', 
                      justifyContent: 'center',
                      alignItems: 'center',
                      mb: 2,
                      gap: 1
                    }}>
                      <Chip
                        label={chat.category || '未分類'}
                        size="small"
                        sx={{
                          bgcolor: categoryColors[0],
                          color: 'white',
                          fontWeight: 500,
                          fontSize: '0.75rem'
                        }}
                      />
                      {(() => {
                        const sentiment = chat.sentiment?.toLowerCase() || 'neutral';
                        const labelMap: Record<string, string> = {
                          positive: 'ポジティブ',
                          negative: 'ネガティブ',
                          neutral: '通常'
                        };
                        const jpLabel = labelMap[sentiment] || sentiment;
                        return (
                          <Chip
                            label={jpLabel}
                            size="small"
                            sx={{
                              bgcolor: sentimentColors[jpLabel as keyof typeof sentimentColors] || sentimentColors.neutral,
                              color: 'white',
                              fontWeight: 500,
                              fontSize: '0.75rem'
                            }}
                          />
                        );
                      })()}
                      <Typography variant="caption" color="pink.main" sx={{ fontWeight: 500 }}>
                        {formatDate(chat.timestamp)}
                      </Typography>
                    </Box>
                    
                    {/* チャットメッセージ（実際のチャット画面と同じスタイル） */}
                    <Box sx={{ 
                      display: 'flex', 
                      flexDirection: 'column',
                      gap: 1
                    }}>
                      {/* ユーザーメッセージ（右側） */}
                      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <Box sx={userMessageStyles}>
                          <Typography sx={{ 
                            fontSize: 'inherit',
                            lineHeight: 'inherit',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word'
                          }}>
                            {chat.user_message}
                          </Typography>
                        </Box>
                      </Box>
                      
                      {/* ボットメッセージ（左側） */}
                      <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                        <Box sx={botMessageStyles}>
                          <Box sx={{ 
                            '& .markdown-content': {
                              fontSize: 'inherit',
                              lineHeight: 'inherit',
                              '& p': { margin: '0.5rem 0' },
                              '& ul, & ol': { paddingLeft: '1.5rem', margin: '0.5rem 0' },
                              '& li': { margin: '0.25rem 0' },
                              '& code': { 
                                backgroundColor: 'rgba(0, 0, 0, 0.08)',
                                padding: '0.2rem 0.4rem',
                                borderRadius: '4px',
                                fontSize: '0.8rem'
                              },
                              '& pre': {
                                backgroundColor: 'rgba(0, 0, 0, 0.08)',
                                padding: '1rem',
                                borderRadius: '8px',
                                overflow: 'auto',
                                margin: '0.5rem 0'
                              },
                              '& blockquote': {
                                borderLeft: '4px solid #ccc',
                                paddingLeft: '1rem',
                                margin: '0.5rem 0',
                                fontStyle: 'italic'
                              }
                            }
                          }}>
                            <MarkdownRenderer content={chat.bot_response || ''} />
                          </Box>
                        </Box>
                      </Box>
                    </Box>
                  </Box>
                ))}
              </Box>

              {/* もっと見るボタン */}
              {hasMoreChats && (
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'center', 
                  mt: 3 
                }}>
                  <Button
                    variant="outlined"
                    onClick={handleLoadMore}
                    startIcon={<ExpandMoreIcon />}
                    sx={{
                      borderRadius: 3,
                      px: 3,
                      py: 1,
                      fontWeight: 600,
                      textTransform: 'none'
                    }}
                  >
                    もっと見る ({employeeDetails.length - displayCount}件)
                  </Button>
                </Box>
              )}
            </Box>
          </Box>
        )}
      </DialogContent>
      <DialogActions sx={{ 
        px: 3, 
        py: 2, 
        borderTop: '1px solid',
        borderColor: 'divider'
      }}>
        <Button 
          onClick={onClose}
          variant="contained"
          sx={{ 
            borderRadius: 2,
            px: 3,
            textTransform: 'none',
            fontWeight: 600
          }}
        >
          閉じる
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default EmployeeDetailsDialog;