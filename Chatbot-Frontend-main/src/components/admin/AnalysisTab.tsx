import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  Tooltip,
  Divider,
  Fade,
  Chip,
  useTheme,
  useMediaQuery,
  alpha,
  // Tabs,
  // Tab,
  // Accordion,
  // AccordionSummary,
  // AccordionDetails,
  // CircularProgress
} from '@mui/material';
import { Bar, Pie } from 'react-chartjs-2';
import { AnalysisResult, categoryColors, sentimentColors } from './types';
import LoadingIndicator from './LoadingIndicator';
import EmptyState from './EmptyState';
import { getCategoryChartData, getSentimentChartData, exportAnalysisToCSV } from './utils';
import InsightsIcon from '@mui/icons-material/Insights';
import CategoryIcon from '@mui/icons-material/Category';
import MoodIcon from '@mui/icons-material/Mood';
import LiveHelpIcon from '@mui/icons-material/LiveHelp';
import RefreshIcon from '@mui/icons-material/Refresh';
import ChatIcon from '@mui/icons-material/Chat';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
// import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
// import BusinessIcon from '@mui/icons-material/Business';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
// import api from '../../api';

interface AnalysisTabProps {
  analysis: AnalysisResult | null;
  isLoading: boolean;
  onRefresh: () => void;
}

// 短縮されたビジネス分析プロンプト（一時的にコメントアウト）
// const BUSINESS_ANALYSIS_PROMPT = `あなたは業務改善コンサルタントです。チャットボットの利用データから、実行可能なビジネス改善提案を行ってください。
// 
// 以下の6項目で分析し、各項目は300文字以内で簡潔に回答してください：
// 
// 【1. 頻出トピック分析】
// 最多質問パターンと業務課題を特定し、標準化の機会を示してください。
// 
// 【2. 効率化機会】  
// 繰り返し質問から自動化可能な業務を特定し、ROIの高い改善案を提案してください。
// 
// 【3. フラストレーション要因】
// ネガティブ感情の原因と未解決問題のパターンを分析し、優先改善点を明示してください。
// 
// 【4. システム改善案】
// 機能追加・改善の具体提案と管理者ニーズの優先順位を示してください。
// 
// 【5. 情報共有課題】
// 部門間の情報ギャップとドキュメント化が必要な領域を特定してください。
// 
// 【6. 実行計画】
// 短期（1-3ヶ月）・中期（3-6ヶ月）・長期（6ヶ月-1年）の改善提案を投資対効果と共に提示してください。
// 
// データに基づく具体的な数値を使用し、実装可能な提案を心がけてください。`;

const AnalysisTab: React.FC<AnalysisTabProps> = ({
  analysis,
  isLoading,
  onRefresh
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  // 分析モード (標準/ビジネス)（一時的にコメントアウト）
  // const [analysisMode, setAnalysisMode] = useState<string>('standard');

  // ビジネス分析の読み込み状態（一時的にコメントアウト）
  // const [isBusinessAnalysisLoading, setIsBusinessAnalysisLoading] = useState<boolean>(false);

  // 詳細なビジネス分析を取得する関数（一時的にコメントアウト）
  // const fetchBusinessAnalysis = async () => {
  //   if (!analysis) return;
  // 
  //   // 既にビジネス分析が完了している場合はスキップ
  //   if (analysis.business_analysis_completed) {
  //     setAnalysisMode('business');
  //     return;
  //   }
  // 
  //   try {
  //     setIsBusinessAnalysisLoading(true);
  //     console.log('高精度ビジネス詳細分析を開始...');
  // 
  //     // バックエンドAPIに詳細分析をリクエスト
  //     const response = await api.post('/admin/detailed-analysis', {
  //       prompt: BUSINESS_ANALYSIS_PROMPT
  //     });
  // 
  //     console.log('ビジネス詳細分析レスポンス:', response.data);
  // 
  //     // レスポンスから詳細分析結果とメタデータを取得
  //     if (response.data && response.data.detailed_analysis) {
  //       const {
  //         detailed_topic_analysis,
  //         efficiency_opportunities,
  //         frustration_points,
  //         improvement_suggestions,
  //         communication_gaps,
  //         specific_recommendations
  //       } = response.data.detailed_analysis;
  // 
  //       // 分析メタデータも取得
  //       const metadata = response.data.analysis_metadata || {};
  // 
  //       // 分析結果を既存の分析データにマージ
  //       Object.assign(analysis, {
  //         detailed_topic_analysis,
  //         efficiency_opportunities,
  //         frustration_points,
  //         improvement_suggestions,
  //         communication_gaps,
  //         specific_recommendations,
  //         business_analysis_completed: true,
  //         analysis_metadata: metadata
  //       });
  // 
  //       console.log('高精度ビジネス詳細分析結果をマージ完了');
  //       console.log('分析品質スコア:', metadata.data_quality_score || 'N/A');
  //       console.log('分析対象会話数:', metadata.total_conversations || 'N/A');
  //     } else {
  //       console.error('詳細分析レスポンスの形式が不正です:', response.data);
  //       throw new Error('詳細分析レスポンスの形式が不正です');
  //     }
  // 
  //     // ビジネス分析モードに切り替え
  //     setAnalysisMode('business');
  //   } catch (error: any) {
  //     console.error('詳細ビジネス分析の取得エラー:', error);
  //     
  //     // より詳細なエラーメッセージ
  //     let errorMessage = '高精度ビジネス詳細分析の取得中にエラーが発生しました。';
  //     if (error.response) {
  //       if (error.response.status === 500) {
  //         errorMessage += '\nサーバーエラーが発生しました。Geminiモデルが初期化されていない可能性があります。';
  //       } else if (error.response.status === 401) {
  //         errorMessage += '\n認証エラーです。ログインし直してください。';
  //       } else {
  //         errorMessage += `\nエラーコード: ${error.response.status}`;
  //       }
  //     } else if (error.request) {
  //       errorMessage += '\nサーバーに接続できませんでした。';
  //     }
  //     
  //     alert(errorMessage);
  //   } finally {
  //     setIsBusinessAnalysisLoading(false);
  //   }
  // };

  // タブの変更ハンドラ（一時的にコメントアウト）
  // const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
  //   if (newValue === 'business' && !analysis?.business_analysis_completed) {
  //     fetchBusinessAnalysis();
  //   } else {
  //     setAnalysisMode(newValue);
  //   }
  // };

  return (
    <Fade in={true} timeout={400}>
      <Box>
        <Box
          sx={{
            mb: 3,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            px: { xs: 1, sm: 0 }
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <InsightsIcon
              sx={{
                mr: 1.5,
                color: 'primary.main',
                fontSize: { xs: '1.8rem', sm: '2rem' }
              }}
            />
            <Typography
              variant={isMobile ? "h6" : "h5"}
              sx={{
                fontWeight: 600,
                color: 'text.primary'
              }}
            >
              チャット分析ダッシュボード
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: 'text.secondary',
                mt: 0.5,
                fontSize: '0.9rem'
              }}
            >
              チャットボットの利用状況を詳細に分析し、ビジネス改善の洞察を提供
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
            {/* CSV出力ボタン */}
            <Tooltip title="分析データをCSV形式で出力">
              <span>
                <Button
                  variant="outlined"
                  color="secondary"
                  onClick={() => analysis && exportAnalysisToCSV(analysis)}
                  disabled={isLoading || !analysis}
                  startIcon={<FileDownloadIcon />}
                  size={isMobile ? "small" : "medium"}
                  sx={{
                    borderRadius: 2,
                    px: { xs: 1.5, sm: 2.5 },
                    fontWeight: 600,
                    '&:hover': {
                      backgroundColor: 'rgba(156, 39, 176, 0.08)',
                    }
                  }}
                >
                  {!isMobile && 'CSV出力'}
                </Button>
              </span>
            </Tooltip>

            {/* 更新ボタン */}
            <Tooltip title="最新データに更新">
              <span>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={onRefresh}
                  disabled={isLoading}
                  startIcon={<RefreshIcon />}
                  size={isMobile ? "small" : "medium"}
                  sx={{
                    borderRadius: 2,
                    px: { xs: 1.5, sm: 2.5 },
                    fontWeight: 600,
                    boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
                    '&:hover': {
                      boxShadow: '0 6px 16px rgba(37, 99, 235, 0.4)',
                    }
                  }}
                >
                  {!isMobile && '更新'}
                </Button>
              </span>
            </Tooltip>
          </Box>
        </Box>

        {/* 分析モード切り替えタブ（一時的にコメントアウト） */}
        {/* {analysis && (
          <Box sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
              value={analysisMode}
              onChange={handleTabChange}
              aria-label="分析モード"
              variant={isMobile ? "fullWidth" : "standard"}
            >
              <Tab
                label="標準分析"
                value="standard"
                icon={<InsightsIcon />}
                iconPosition="start"
              />
              <Tab
                label="ビジネス詳細分析"
                value="business"
                icon={<BusinessIcon />}
                iconPosition="start"
                disabled={isLoading || isBusinessAnalysisLoading}
              />
            </Tabs>
          </Box>
        )} */}

        {isLoading ? (
          <LoadingIndicator />
        ) : !analysis ? (
          <EmptyState message="分析データがありません" />
        ) /* : isBusinessAnalysisLoading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
            <CircularProgress size={60} sx={{ mb: 3 }} />
            <Typography variant="h6" color="text.secondary">
              ビジネス詳細分析を実行中...
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              チャットデータの分析にはしばらく時間がかかる場合があります
            </Typography>
          </Box>
        ) */ : (
          <Grid container spacing={3}>
            {/* 標準分析モード */}
            {/* {analysisMode === 'standard' ? ( */}
              <>
                {/* AI洞察カード */}
                <Grid item xs={12}>
                  <Card
                    elevation={0}
                    sx={{
                      mb: 3,
                      borderRadius: 2,
                      border: '1px solid rgba(37, 99, 235, 0.12)',
                      position: 'relative',
                      overflow: 'hidden',
                      background: 'linear-gradient(to right, rgba(37, 99, 235, 0.05), rgba(37, 99, 235, 0.01))',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '4px',
                        background: 'linear-gradient(90deg, #2563eb, #3b82f6)',
                        opacity: 0.8
                      }
                    }}
                  >
                    <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <TrendingUpIcon
                          sx={{
                            mr: 1.5,
                            color: 'primary.main',
                            fontSize: '1.5rem'
                          }}
                        />
                        <Typography
                          variant="h6"
                          sx={{
                            fontWeight: 600,
                            color: 'primary.main',
                            display: 'flex',
                            alignItems: 'center'
                          }}
                        >
                          AI分析による洞察
                        </Typography>
                      </Box>
                      <Divider sx={{ mb: 2 }} />
                      <Paper
                        elevation={0}
                        sx={{
                          p: 2,
                          backgroundColor: alpha(theme.palette.background.paper, 0.7),
                          borderRadius: 1.5,
                          border: '1px solid rgba(0, 0, 0, 0.05)'
                        }}
                      >
                        <Typography
                          variant="body1"
                          sx={{
                            whiteSpace: 'pre-line',
                            lineHeight: 1.6,
                            color: 'text.primary'
                          }}
                        >
                          {analysis.insights}
                        </Typography>
                      </Paper>
                    </CardContent>
                  </Card>
                </Grid>

                {/* グラフセクション */}
                <Grid item xs={12} md={6}>
                  <Card
                    elevation={3}
                    sx={{
                      borderRadius: 3,
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                      position: 'relative',
                      overflow: 'hidden',
                      border: '1px solid rgba(59, 130, 246, 0.08)',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '3px',
                        background: 'linear-gradient(90deg, #3b82f6, #1e40af, #6366f1)',
                        opacity: 1
                      },
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: '0 20px 40px rgba(59, 130, 246, 0.15), 0 12px 24px rgba(59, 130, 246, 0.1)',
                        border: '1px solid rgba(59, 130, 246, 0.15)',
                      }
                    }}
                  >
                    <CardContent sx={{ p: { xs: 3, sm: 4 }, flex: 1, display: 'flex', flexDirection: 'column' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <Box
                          sx={{
                            mr: 2,
                            p: 1.5,
                            borderRadius: 2.5,
                            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05))',
                            border: '1px solid rgba(59, 130, 246, 0.2)',
                            boxShadow: '0 4px 12px rgba(59, 130, 246, 0.1)'
                          }}
                        >
                          <CategoryIcon
                            sx={{
                              color: '#3b82f6',
                              fontSize: '1.4rem'
                            }}
                          />
                        </Box>
                        <Box>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 700,
                              color: '#1e293b',
                              fontSize: '1.2rem',
                              mb: 0.5
                            }}
                          >
                            カテゴリ別分布
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              color: '#64748b',
                              fontSize: '0.875rem'
                            }}
                          >
                            質問のカテゴリ別統計
                          </Typography>
                        </Box>
                      </Box>

                      <Divider sx={{ mb: 3, borderColor: 'rgba(59, 130, 246, 0.1)' }} />

                      <Box sx={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        minHeight: { xs: 280, md: 300 }
                      }}>
                        {(Array.isArray(analysis.category_distribution) && analysis.category_distribution.length > 0) ||
                         (!Array.isArray(analysis.category_distribution) && Object.keys(analysis.category_distribution).length > 0) ? (
                          <Bar
                            data={getCategoryChartData(
                              Array.isArray(analysis.category_distribution)
                                ? analysis.category_distribution.reduce((acc, item) => {
                                    acc[item.category] = item.count;
                                    return acc;
                                  }, {} as Record<string, number>)
                                : analysis.category_distribution,
                              categoryColors
                            )}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              interaction: {
                                intersect: false,
                                mode: 'index'
                              },
                              plugins: {
                                legend: {
                                  display: false
                                },
                                tooltip: {
                                  backgroundColor: 'rgba(30, 41, 59, 0.95)',
                                  titleColor: '#f1f5f9',
                                  bodyColor: '#e2e8f0',
                                  borderColor: 'rgba(59, 130, 246, 0.3)',
                                  borderWidth: 1,
                                  padding: 16,
                                  titleFont: {
                                    size: 14,
                                    weight: 'bold'
                                  },
                                  bodyFont: {
                                    size: 13
                                  },
                                  cornerRadius: 12,
                                  displayColors: true,
                                  boxPadding: 8,
                                  usePointStyle: true,
                                  callbacks: {
                                    title: (tooltipItems) => {
                                      return tooltipItems[0].label;
                                    },
                                    label: (context) => {
                                      return ` ${context.dataset.label}: ${context.parsed.y.toLocaleString()} 件`;
                                    }
                                  }
                                }
                              },
                              scales: {
                                y: {
                                  beginAtZero: true,
                                  grid: {
                                    color: 'rgba(148, 163, 184, 0.3)',
                                    lineWidth: 1,
                                    drawTicks: false
                                  },
                                  ticks: {
                                    color: '#475569',
                                    font: {
                                      size: 13,
                                      weight: 600,
                                      family: "'Inter', sans-serif"
                                    },
                                    padding: 15,
                                    callback: function(value) {
                                      return value.toLocaleString() + '件';
                                    }
                                  },
                                  border: {
                                    display: false
                                  }
                                },
                                x: {
                                  grid: {
                                    display: false
                                  },
                                  ticks: {
                                    color: '#475569',
                                    font: {
                                      size: 12,
                                      weight: 600,
                                      family: "'Inter', sans-serif"
                                    },
                                    padding: 15,
                                    maxRotation: 45
                                  },
                                  border: {
                                    color: 'rgba(148, 163, 184, 0.3)',
                                    width: 1
                                  }
                                }
                              },
                              animation: {
                                duration: 1200,
                                easing: 'easeInOutCubic'
                              },
                              elements: {
                                bar: {
                                  borderRadius: {
                                    topLeft: 6,
                                    topRight: 6,
                                    bottomLeft: 0,
                                    bottomRight: 0
                                  },
                                  borderWidth: 0
                                }
                              },
                              layout: {
                                padding: {
                                  top: 20,
                                  bottom: 10,
                                  left: 10,
                                  right: 10
                                }
                              }
                            }}
                          />
                        ) : (
                          <Box sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%',
                            py: 4
                          }}>
                            <Box sx={{
                              p: 3,
                              borderRadius: '50%',
                              backgroundColor: 'rgba(59, 130, 246, 0.1)',
                              mb: 3
                            }}>
                              <CategoryIcon sx={{ fontSize: '2.5rem', color: '#3b82f6' }} />
                            </Box>
                            <Typography variant="h6" sx={{ color: '#374151', mb: 1, fontWeight: 600 }}>
                              データがありません
                            </Typography>
                            <Typography variant="body2" sx={{ color: '#6b7280', textAlign: 'center' }}>
                              カテゴリ分析を表示するために<br />十分なデータを収集中です
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card
                    elevation={3}
                    sx={{
                      borderRadius: 3,
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                      position: 'relative',
                      overflow: 'hidden',
                      border: '1px solid rgba(16, 185, 129, 0.08)',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '3px',
                        background: 'linear-gradient(90deg, #10b981, #059669, #34d399)',
                        opacity: 1
                      },
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: '0 20px 40px rgba(16, 185, 129, 0.15), 0 12px 24px rgba(16, 185, 129, 0.1)',
                        border: '1px solid rgba(16, 185, 129, 0.15)',
                      }
                    }}
                  >
                    <CardContent sx={{ p: { xs: 3, sm: 4 }, flex: 1, display: 'flex', flexDirection: 'column' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <Box
                          sx={{
                            mr: 2,
                            p: 1.5,
                            borderRadius: 2.5,
                            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(34, 197, 94, 0.05))',
                            border: '1px solid rgba(16, 185, 129, 0.2)',
                            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.1)'
                          }}
                        >
                          <MoodIcon
                            sx={{
                              color: '#10b981',
                              fontSize: '1.4rem'
                            }}
                          />
                        </Box>
                        <Box>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 700,
                              color: '#1e293b',
                              fontSize: '1.2rem',
                              mb: 0.5
                            }}
                          >
                            感情分析結果
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              color: '#64748b',
                              fontSize: '0.875rem'
                            }}
                          >
                            管理者の感情分布
                          </Typography>
                        </Box>
                      </Box>

                      <Divider sx={{ mb: 3, borderColor: 'rgba(16, 185, 129, 0.1)' }} />

                      <Box sx={{
                        flex: 1,
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        minHeight: { xs: 280, md: 300 }
                      }}>
                        {(Array.isArray(analysis.sentiment_distribution) && analysis.sentiment_distribution.length > 0) ||
                         (!Array.isArray(analysis.sentiment_distribution) && Object.keys(analysis.sentiment_distribution).length > 0) ? (
                          <Pie
                            data={getSentimentChartData(
                              Array.isArray(analysis.sentiment_distribution)
                                ? analysis.sentiment_distribution.reduce((acc, item) => {
                                    acc[item.sentiment] = item.count;
                                    return acc;
                                  }, {} as Record<string, number>)
                                : analysis.sentiment_distribution,
                              sentimentColors
                            )}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              interaction: {
                                intersect: false
                              },
                              plugins: {
                                tooltip: {
                                  backgroundColor: 'rgba(30, 41, 59, 0.95)',
                                  titleColor: '#f1f5f9',
                                  bodyColor: '#e2e8f0',
                                  borderColor: 'rgba(59, 130, 246, 0.3)',
                                  borderWidth: 1,
                                  padding: 16,
                                  titleFont: {
                                    size: 14,
                                    weight: 'bold'
                                  },
                                  bodyFont: {
                                    size: 13
                                  },
                                  cornerRadius: 12,
                                  displayColors: true,
                                  boxPadding: 8,
                                  usePointStyle: true,
                                  callbacks: {
                                    label: (context) => {
                                      const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                                      const percentage = ((context.parsed / total) * 100).toFixed(1);
                                      return ` ${context.label}: ${context.parsed.toLocaleString()} 件 (${percentage}%)`;
                                    }
                                  }
                                },
                                legend: {
                                  position: 'bottom',
                                  labels: {
                                    usePointStyle: true,
                                    pointStyle: 'circle',
                                    padding: 25,
                                    font: {
                                      size: 14,
                                      weight: 600,
                                      family: "'Inter', sans-serif"
                                    },
                                    color: '#374151',
                                    boxWidth: 12,
                                    boxHeight: 12
                                  },
                                  align: 'center'
                                }
                              },
                              animation: {
                                animateRotate: true,
                                animateScale: true,
                                duration: 1500,
                                easing: 'easeInOutCubic'
                              },
                              elements: {
                                arc: {
                                  borderWidth: 4,
                                  borderColor: '#ffffff',
                                  hoverBorderWidth: 6
                                }
                              },
                              layout: {
                                padding: {
                                  top: 20,
                                  bottom: 20,
                                  left: 20,
                                  right: 20
                                }
                              }
                            }}
                          />
                        ) : (
                          <Box sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%',
                            py: 4
                          }}>
                            <Box sx={{
                              p: 3,
                              borderRadius: '50%',
                              backgroundColor: 'rgba(16, 185, 129, 0.1)',
                              mb: 3
                            }}>
                              <MoodIcon sx={{ fontSize: '2.5rem', color: '#10b981' }} />
                            </Box>
                            <Typography variant="h6" sx={{ color: '#374151', mb: 1, fontWeight: 600 }}>
                              データがありません
                            </Typography>
                            <Typography variant="body2" sx={{ color: '#6b7280', textAlign: 'center' }}>
                              感情分析を表示するために<br />十分なデータを収集中です
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {/* よくある質問セクション */}
                <Grid item xs={12}>
                  <Card
                    elevation={0}
                    sx={{
                      borderRadius: 2,
                      border: '1px solid rgba(0, 0, 0, 0.12)',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                      }
                    }}
                  >
                    <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <LiveHelpIcon
                          sx={{
                            mr: 1.5,
                            color: theme.palette.warning.main,
                            fontSize: '1.4rem'
                          }}
                        />
                        <Typography
                          variant="h6"
                          sx={{
                            fontWeight: 600,
                            color: 'text.primary'
                          }}
                        >
                          よくある質問
                        </Typography>
                      </Box>

                      <Divider sx={{ mb: 2 }} />

                      {!analysis.common_questions ||
                       (Array.isArray(analysis.common_questions) && analysis.common_questions.length === 0) ? (
                        <Box sx={{
                          py: 4,
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}>
                          <ChatIcon sx={{ fontSize: '3rem', color: 'text.disabled', mb: 2 }} />
                          <Typography variant="body1" color="text.secondary">
                            よくある質問のデータがありません
                          </Typography>
                        </Box>
                      ) : (
                        <TableContainer
                          component={Paper}
                          elevation={0}
                          sx={{
                            border: '1px solid rgba(0, 0, 0, 0.08)',
                            borderRadius: 1.5,
                            overflow: 'hidden'
                          }}
                        >
                          <Table>
                            <TableHead>
                              <TableRow sx={{ bgcolor: 'rgba(0, 0, 0, 0.02)' }}>
                                <TableCell sx={{ fontWeight: 'bold', py: 2 }}>質問</TableCell>
                                <TableCell align="right" sx={{ fontWeight: 'bold', py: 2 }}>回数</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {analysis.common_questions.map((item, index) => (
                                <TableRow
                                  key={index}
                                  hover
                                  sx={{
                                    transition: 'background-color 0.2s',
                                    '&:last-child td, &:last-child th': { border: 0 }
                                  }}
                                >
                                  <TableCell
                                    sx={{
                                      py: 1.8,
                                      maxWidth: { xs: '200px', sm: '400px', md: '600px' },
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: { xs: 'nowrap', md: 'normal' }
                                    }}
                                  >
                                    <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                                      <ChatIcon
                                        fontSize="small"
                                        sx={{
                                          mt: 0.3,
                                          mr: 1,
                                          color: theme.palette.primary.main,
                                          opacity: 0.7
                                        }}
                                      />
                                      <Typography variant="body2">
                                        {typeof item === 'string' ? item : item.question}
                                      </Typography>
                                    </Box>
                                  </TableCell>
                                  <TableCell align="right">
                                    <Chip
                                      size="small"
                                      label={typeof item === 'string' ? '1' : item.count.toString()}
                                      sx={{
                                        fontWeight: 'bold',
                                        bgcolor: theme.palette.primary.main,
                                        color: 'white',
                                        minWidth: '40px'
                                      }}
                                    />
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              </>
            {/* ビジネス詳細分析モード（一時的にコメントアウト） */}
            {/* ) : (
              <Grid item xs={12}>
                <Card
                  elevation={0}
                  sx={{
                    mb: 3,
                    borderRadius: 2,
                    border: '1px solid rgba(25, 118, 210, 0.2)',
                    position: 'relative',
                    overflow: 'hidden',
                    background: 'linear-gradient(to right, rgba(25, 118, 210, 0.03), rgba(25, 118, 210, 0.01))',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '4px',
                      background: 'linear-gradient(90deg, #1976d2, #42a5f5)',
                      opacity: 0.8
                    }
                  }}
                >
                  <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <BusinessIcon
                        sx={{
                          mr: 1.5,
                          color: 'primary.main',
                          fontSize: '1.5rem'
                        }}
                      />
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 600,
                          color: 'primary.main',
                          display: 'flex',
                          alignItems: 'center'
                        }}
                      >
                        ビジネス詳細分析レポート
                      </Typography>
                    </Box>
                    <Divider sx={{ mb: 2 }} />

                    ビジネス分析セクション
                    {[
                      { title: '1. 頻出トピック/質問とその傾向分析', content: analysis.detailed_topic_analysis },
                      { title: '2. 業務効率化の機会', content: analysis.efficiency_opportunities },
                      { title: '3. 社員のフラストレーションポイント', content: analysis.frustration_points },
                      { title: '4. 製品/サービス改善の示唆', content: analysis.improvement_suggestions },
                      { title: '5. コミュニケーションギャップ', content: analysis.communication_gaps },
                      { title: '具体的な改善提案', content: analysis.specific_recommendations }
                    ].map((section, index) => (
                      <Accordion
                        key={index}
                        defaultExpanded={index === 0}
                        sx={{
                          mb: 1.5,
                          boxShadow: 'none',
                          border: '1px solid rgba(0, 0, 0, 0.08)',
                          '&:before': { display: 'none' },
                          borderRadius: '8px !important',
                          overflow: 'hidden'
                        }}
                      >
                        <AccordionSummary
                          expandIcon={<ExpandMoreIcon />}
                          sx={{
                            backgroundColor: 'rgba(0, 0, 0, 0.02)',
                            borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
                            '&.Mui-expanded': {
                              minHeight: 48,
                            },
                          }}
                        >
                          <Typography
                            sx={{
                              fontWeight: 600,
                              color: 'text.primary',
                              fontSize: { xs: '0.9rem', sm: '1rem' }
                            }}
                          >
                            {section.title}
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails sx={{ p: { xs: 2, sm: 3 } }}>
                          <Typography
                            variant="body1"
                            sx={{
                              whiteSpace: 'pre-line',
                              lineHeight: 1.6
                            }}
                          >
                            {section.content || '分析データがありません'}
                          </Typography>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            ) */}
          </Grid>
        )}
      </Box>
    </Fade>
  );
};

export default AnalysisTab;