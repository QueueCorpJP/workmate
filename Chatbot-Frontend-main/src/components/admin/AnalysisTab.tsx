import React, { useState, useEffect } from 'react';
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
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  LinearProgress,
  Alert
} from '@mui/material';
import { Bar, Pie, Line } from 'react-chartjs-2';
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
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import BusinessIcon from '@mui/icons-material/Business';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import DescriptionIcon from '@mui/icons-material/Description';
import PeopleIcon from '@mui/icons-material/People';
import TimelineIcon from '@mui/icons-material/Timeline';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import api from '../../api';

// 強化分析結果の型定義
interface EnhancedAnalysisResult {
  resource_reference_count: {
    resources: Array<{
      name: string;
      type: string;
      reference_count: number;
      unique_users: number;
      unique_days: number;
      last_referenced: string | null;
      avg_satisfaction: number;
      usage_intensity: number;
    }>;
    total_references: number;
    most_referenced: any;
    least_referenced: any;
    active_resources: number;
    summary: string;
  };
  category_distribution_analysis: {
    categories: Array<{
      category: string;
      count: number;
      unique_users: number;
      unique_days: number;
      avg_sentiment_score: number;
      positive_count: number;
      neutral_count: number;
      negative_count: number;
    }>;
    distribution: Record<string, { count: number; percentage: number }>;
    bias_analysis: Record<string, {
      bias_score: number;
      is_over_represented: boolean;
      is_under_represented: boolean;
      sentiment_bias: string;
    }>;
    top_categories: any[];
    bottom_categories: any[];
    total_questions: number;
    category_diversity: number;
    summary: string;
  };
  active_user_trends: {
    daily_trends: Array<{
      date: string;
      active_users: number;
      total_messages: number;
      unique_names: number;
      positive_ratio: number;
    }>;
    weekly_trends: Array<{
      week_start: string;
      week_end: string;
      avg_active_users: number;
      total_messages: number;
      days_with_activity: number;
    }>;
    trend_analysis: {
      direction: string;
      percentage_change: number;
      period: string;
    };
    peak_day: any;
    total_unique_users: number;
    summary: string;
  };
  unresolved_and_repeat_analysis: {
    repeat_questions: Array<{
      employee_id: string;
      employee_name: string;
      first_question: string;
      repeat_question: string;
      time_between: string;
      similarity_score: number;
      first_sentiment: string;
      repeat_sentiment: string;
      category: string;
    }>;
    unresolved_patterns: Array<{
      employee_id: string;
      employee_name: string;
      question: string;
      response: string;
      timestamp: string;
      sentiment: string;
      category: string;
      response_length: number;
      issue_type: string;
    }>;
    statistics: {
      total_conversations: number;
      repeat_questions_count: number;
      unresolved_patterns_count: number;
      repeat_rate: number;
      unresolved_rate: number;
    };
    summary: string;
  };
  sentiment_analysis: {
    sentiment_distribution: Record<string, number>;
    sentiment_by_category: Record<string, Record<string, number>>;
    temporal_sentiment: Array<{
      date: string;
      sentiments: Record<string, number>;
    }>;
    overall_sentiment_score: number;
    total_responses: number;
    summary: string;
  };
  ai_insights: string;
  analysis_metadata: {
    generated_at: string;
    analysis_type: string;
    company_id?: string;
  };
}

interface AnalysisTabProps {
  analysis: AnalysisResult | null;
  isLoading: boolean;
  onRefresh: () => void;
}

const AnalysisTab: React.FC<AnalysisTabProps> = ({
  analysis,
  isLoading,
  onRefresh
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  // 分析モード (標準/強化)
  const [analysisMode, setAnalysisMode] = useState<string>('standard');
  const [enhancedAnalysis, setEnhancedAnalysis] = useState<EnhancedAnalysisResult | null>(null);
  const [isEnhancedLoading, setIsEnhancedLoading] = useState<boolean>(false);

  // 強化分析データを取得する関数
  const fetchEnhancedAnalysis = async () => {
    try {
      setIsEnhancedLoading(true);
      console.log('強化分析データ取得開始...');

      const response = await api.get('/admin/enhanced-analysis');
      console.log('強化分析レスポンス:', response.data);

      if (response.data) {
        setEnhancedAnalysis(response.data);
        console.log('強化分析データ設定完了');
      } else {
        console.error('強化分析レスポンスのデータが空です');
      }
    } catch (error: any) {
      console.error('強化分析データ取得エラー:', error);
      
      let errorMessage = '強化分析データの取得中にエラーが発生しました。';
      if (error.response) {
        if (error.response.status === 500) {
          errorMessage += '\nサーバーエラーが発生しました。';
        } else if (error.response.status === 401) {
          errorMessage += '\n認証エラーです。ログインし直してください。';
        } else {
          errorMessage += `\nエラーコード: ${error.response.status}`;
        }
      } else if (error.request) {
        errorMessage += '\nサーバーに接続できませんでした。';
      }
      
      alert(errorMessage);
    } finally {
      setIsEnhancedLoading(false);
    }
  };

  // タブの変更ハンドラ
  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    if (newValue === 'enhanced' && !enhancedAnalysis) {
      fetchEnhancedAnalysis();
    }
    setAnalysisMode(newValue);
  };

  // 資料参照回数チャートのデータを生成
  const getResourceReferenceChartData = (resources: any[]) => {
    if (!resources || resources.length === 0) return null;

    const top10Resources = resources.slice(0, 10);
    
    return {
      labels: top10Resources.map(r => r.name.length > 20 ? r.name.substring(0, 20) + '...' : r.name),
      datasets: [
        {
          label: '参照回数',
          data: top10Resources.map(r => r.reference_count),
          backgroundColor: 'rgba(54, 162, 235, 0.6)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 2,
        },
      ],
    };
  };

  // アクティブユーザー推移チャートのデータを生成
  const getUserTrendsChartData = (dailyTrends: any[]) => {
    if (!dailyTrends || dailyTrends.length === 0) return null;

    const last30Days = dailyTrends.slice(-30);
    
    return {
      labels: last30Days.map(d => new Date(d.date).toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' })),
      datasets: [
        {
          label: 'アクティブユーザー数',
          data: last30Days.map(d => d.active_users),
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          fill: true,
          tension: 0.4,
        },
        {
          label: 'メッセージ数',
          data: last30Days.map(d => d.total_messages),
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          fill: false,
          yAxisID: 'y1',
        },
      ],
    };
  };

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
            <Box>
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
                  onClick={() => {
                    onRefresh();
                    if (analysisMode === 'enhanced') {
                      fetchEnhancedAnalysis();
                    }
                  }}
                  disabled={isLoading || isEnhancedLoading}
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

        {/* 分析モード切り替えタブ */}
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
              label="強化分析"
              value="enhanced"
              icon={<BusinessIcon />}
              iconPosition="start"
              disabled={isLoading || isEnhancedLoading}
            />
          </Tabs>
        </Box>

        {isLoading || isEnhancedLoading ? (
          <LoadingIndicator />
        ) : analysisMode === 'standard' && !analysis ? (
          <EmptyState message="分析データがありません" />
        ) : analysisMode === 'enhanced' && !enhancedAnalysis ? (
          <EmptyState message="強化分析データがありません" />
        ) : (
          <Grid container spacing={3}>
            {/* 標準分析モード */}
            {analysisMode === 'standard' && analysis ? (
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
            ) : analysisMode === 'enhanced' && enhancedAnalysis ? (
              <>
                {/* Gemini AI洞察カード */}
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
                          Gemini AI による強化分析レポート
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
                          {enhancedAnalysis.ai_insights}
                        </Typography>
                      </Paper>
                    </CardContent>
                  </Card>
                </Grid>

                {/* 強化分析セクション */}
                {[
                  { 
                    title: '1. 資料の参照回数分析', 
                    icon: <DescriptionIcon />,
                    content: enhancedAnalysis.resource_reference_count,
                    color: 'rgba(54, 162, 235, 0.1)'
                  },
                  { 
                    title: '2. 質問カテゴリ分布と偏り', 
                    icon: <CategoryIcon />,
                    content: enhancedAnalysis.category_distribution_analysis,
                    color: 'rgba(255, 99, 132, 0.1)'
                  },
                  { 
                    title: '3. アクティブユーザー推移', 
                    icon: <TimelineIcon />,
                    content: enhancedAnalysis.active_user_trends,
                    color: 'rgba(75, 192, 192, 0.1)'
                  },
                  { 
                    title: '4. 未解決・再質問の傾向分析', 
                    icon: <HelpOutlineIcon />,
                    content: enhancedAnalysis.unresolved_and_repeat_analysis,
                    color: 'rgba(255, 159, 64, 0.1)'
                  },
                  { 
                    title: '5. 詳細感情分析', 
                    icon: <MoodIcon />,
                    content: enhancedAnalysis.sentiment_analysis,
                    color: 'rgba(153, 102, 255, 0.1)'
                  }
                ].map((section, index) => (
                  <Grid item xs={12} key={index}>
                    <Accordion
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
                          backgroundColor: section.color,
                          borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
                          '&.Mui-expanded': {
                            minHeight: 48,
                          },
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {section.icon}
                          <Typography
                            sx={{
                              ml: 1.5,
                              fontWeight: 600,
                              color: 'text.primary',
                              fontSize: { xs: '0.9rem', sm: '1rem' }
                            }}
                          >
                            {section.title}
                          </Typography>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails sx={{ p: { xs: 2, sm: 3 } }}>
                        {/* セクション別の詳細表示 */}
                        {index === 0 && (
                          <Box>
                            <Typography variant="body1" sx={{ mb: 2 }}>
                              {section.content.summary}
                            </Typography>
                            {section.content.resources.length > 0 && (
                              <Box sx={{ height: 400, mt: 2 }}>
                                <Bar
                                  data={getResourceReferenceChartData(section.content.resources)}
                                  options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: {
                                      title: {
                                        display: true,
                                        text: '資料別参照回数'
                                      }
                                    }
                                  }}
                                />
                              </Box>
                            )}
                          </Box>
                        )}
                        {index === 2 && (
                          <Box>
                            <Typography variant="body1" sx={{ mb: 2 }}>
                              {section.content.summary}
                            </Typography>
                            {section.content.daily_trends.length > 0 && (
                              <Box sx={{ height: 400, mt: 2 }}>
                                <Line
                                  data={getUserTrendsChartData(section.content.daily_trends)}
                                  options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: {
                                      title: {
                                        display: true,
                                        text: 'アクティブユーザー数推移（過去30日）'
                                      }
                                    },
                                    scales: {
                                      y: {
                                        type: 'linear',
                                        display: true,
                                        position: 'left',
                                      },
                                      y1: {
                                        type: 'linear',
                                        display: true,
                                        position: 'right',
                                        grid: {
                                          drawOnChartArea: false,
                                        },
                                      },
                                    }
                                  }}
                                />
                              </Box>
                            )}
                          </Box>
                        )}
                        {(index === 1 || index === 3 || index === 4) && (
                          <Typography
                            variant="body1"
                            sx={{
                              whiteSpace: 'pre-line',
                              lineHeight: 1.6
                            }}
                          >
                            {section.content.summary || 'データを解析中です...'}
                          </Typography>
                        )}
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                ))}
              </>
            ) : null}
          </Grid>
        )}
      </Box>
    </Fade>
  );
};

export default AnalysisTab;