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
  Alert,
  Container,
  Stack,
  Badge
} from '@mui/material';
import { Bar, Pie, Line, Doughnut, PolarArea } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler,
  RadialLinearScale,
  PolarAreaController,
  defaults
} from 'chart.js';
import { AnalysisResult, categoryColors, sentimentColors } from './types';
import LoadingIndicator from './LoadingIndicator';
import EmptyState from './EmptyState';
import { getCategoryChartData, getSentimentChartData, exportAnalysisToCSV } from './utils';
import MarkdownRenderer from '../MarkdownRenderer';
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
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import RepeatIcon from '@mui/icons-material/Repeat';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import api from '../../api';

// Chart.jsのデフォルト設定をリセット
defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
defaults.color = '#374151';

// Chart.jsの必要なコンポーネントを登録
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler,
  RadialLinearScale,
  PolarAreaController
);

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

  // 強化分析データ
  const [enhancedAnalysis, setEnhancedAnalysis] = useState<EnhancedAnalysisResult | null>(null);
  const [isEnhancedLoading, setIsEnhancedLoading] = useState<boolean>(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set([0, 1, 2])); // デフォルトで最初の3つを展開

  // 初回ロード時に強化分析データを取得
  useEffect(() => {
    fetchEnhancedAnalysis();
  }, []);

  // 強化分析データを取得する関数
  const fetchEnhancedAnalysis = async () => {
    try {
      setIsEnhancedLoading(true);
      console.log('🔍 強化分析データ取得開始...');

      const response = await api.get('/admin/enhanced-analysis');
      console.log('✅ 強化分析レスポンス:', response.data);

      if (response.data) {
        setEnhancedAnalysis(response.data);
        setLastRefresh(new Date());
        console.log('🎯 強化分析データ設定完了');
      } else {
        console.error('❌ 強化分析レスポンスのデータが空です');
      }
    } catch (error: any) {
      console.error('💥 強化分析データ取得エラー:', error);
      
      // エラー処理を改善
      if (error.response?.status === 401) {
        // 認証エラーの場合、リダイレクトやログイン画面へ
        console.error('認証エラー: ログインが必要です');
      } else if (error.response?.status === 403) {
        console.error('権限エラー: 管理者権限が必要です');
      } else if (error.response?.status >= 500) {
        console.error('サーバーエラー: システム管理者に連絡してください');
      } else {
        console.error('その他のエラー:', error.message);
      }
    } finally {
      setIsEnhancedLoading(false);
    }
  };

  // セクション展開/折りたたみの処理
  const toggleSection = (index: number) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSections(newExpanded);
  };

  // 更新ボタンのハンドラ
  const handleRefresh = () => {
    onRefresh();
    fetchEnhancedAnalysis();
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
    <Fade in={true} timeout={600}>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        {/* ヘッダーセクション */}
        <Box
          sx={{
            mb: 4,
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            justifyContent: 'space-between',
            alignItems: { xs: 'flex-start', md: 'center' },
            gap: 2,
            p: 3,
            background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.05) 0%, rgba(59, 130, 246, 0.08) 100%)',
            borderRadius: 3,
            border: '1px solid rgba(37, 99, 235, 0.12)',
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '4px',
              background: 'linear-gradient(90deg, #2563eb, #3b82f6, #1d4ed8)',
            }
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                p: 2,
                borderRadius: 2,
                background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.15), rgba(59, 130, 246, 0.1))',
                border: '1px solid rgba(37, 99, 235, 0.2)',
                boxShadow: '0 4px 12px rgba(37, 99, 235, 0.15)'
              }}
            >
              <SmartToyIcon sx={{ fontSize: '2rem', color: '#2563eb' }} />
            </Box>
            <Box>
            <Typography
                variant="h4"
              sx={{
                  fontWeight: 700,
                  color: 'text.primary',
                  fontSize: { xs: '1.5rem', md: '2rem' },
                  background: 'linear-gradient(135deg, #1e293b, #475569)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                AI強化分析ダッシュボード
            </Typography>
            <Typography
                variant="body1"
              sx={{
                color: 'text.secondary',
                  fontSize: '1.1rem',
                mt: 0.5,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
              }}
            >
                <AutoFixHighIcon fontSize="small" />
                Gemini AIによる高度な分析と洞察
            </Typography>
              {lastRefresh && (
                <Typography
                  variant="caption"
                  sx={{
                    color: 'text.secondary',
                    fontSize: '0.9rem',
                    mt: 1,
                    display: 'block'
                  }}
                >
                  最終更新: {lastRefresh.toLocaleString('ja-JP')}
                </Typography>
              )}
            </Box>
          </Box>

          <Stack direction="row" spacing={2}>
            <Tooltip title="分析データをCSV形式で出力">
              <span>
                <Button
                  variant="outlined"
                  color="secondary"
                  onClick={() => enhancedAnalysis && exportAnalysisToCSV(analysis)}
                  disabled={isLoading || isEnhancedLoading || !enhancedAnalysis}
                  startIcon={<FileDownloadIcon />}
                  sx={{
                    borderRadius: 2,
                    px: 3,
                    py: 1.2,
                    fontWeight: 600,
                    textTransform: 'none',
                    fontSize: '0.95rem',
                    '&:hover': {
                      backgroundColor: 'rgba(156, 39, 176, 0.08)',
                    }
                  }}
                >
                  {!isMobile && 'CSV出力'}
                </Button>
              </span>
            </Tooltip>

            <Tooltip title="最新データに更新">
              <span>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleRefresh}
                  disabled={isLoading || isEnhancedLoading}
                  startIcon={isEnhancedLoading ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
                  sx={{
                    borderRadius: 2,
                    px: 3,
                    py: 1.2,
                    fontWeight: 600,
                    textTransform: 'none',
                    fontSize: '0.95rem',
                    boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
                    '&:hover': {
                      boxShadow: '0 6px 16px rgba(37, 99, 235, 0.4)',
                    }
                  }}
                >
                  {isEnhancedLoading ? '更新中...' : '更新'}
                </Button>
              </span>
            </Tooltip>
          </Stack>
        </Box>

        {/* ローディング状態 */}
        {isEnhancedLoading ? (
          <Box sx={{ py: 8 }}>
          <LoadingIndicator />
            <Typography
              variant="h6"
              sx={{
                textAlign: 'center',
                mt: 2,
                color: 'text.secondary'
              }}
            >
              AI分析を実行中...
            </Typography>
          </Box>
        ) : !enhancedAnalysis ? (
          <EmptyState message="強化分析データがありません。更新ボタンを押してデータを取得してください。" />
        ) : (
          <Grid container spacing={3}>
            {/* Gemini AI洞察カード */}
                <Grid item xs={12}>
                  <Card
                    elevation={0}
                    sx={{
                  borderRadius: 3,
                  border: '1px solid rgba(25, 118, 210, 0.15)',
                      position: 'relative',
                      overflow: 'hidden',
                  background: 'linear-gradient(135deg, rgba(25, 118, 210, 0.02), rgba(25, 118, 210, 0.06))',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '4px',
                    background: 'linear-gradient(90deg, #1976d2, #42a5f5, #1565c0)',
                  }
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <Box
                          sx={{
                        mr: 2,
                        p: 1.5,
                        borderRadius: 2,
                        background: 'linear-gradient(135deg, rgba(25, 118, 210, 0.1), rgba(25, 118, 210, 0.05))',
                        border: '1px solid rgba(25, 118, 210, 0.2)',
                      }}
                    >
                      <SmartToyIcon sx={{ fontSize: '1.8rem', color: '#1976d2' }} />
                    </Box>
                    <Box>
                        <Typography
                        variant="h5"
                          sx={{
                          fontWeight: 700,
                          color: '#1976d2',
                          fontSize: '1.4rem'
                        }}
                      >
                        🤖 Gemini AI 分析レポート
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{ color: 'text.secondary', mt: 0.5 }}
                      >
                        AIによる高度な分析と改善提案
                        </Typography>
                      </Box>
                  </Box>

                  <Divider sx={{ mb: 3, borderColor: 'rgba(25, 118, 210, 0.1)' }} />

                      <Paper
                        elevation={0}
                        sx={{
                      p: 3,
                      backgroundColor: 'rgba(255, 255, 255, 0.7)',
                      borderRadius: 2,
                      border: '1px solid rgba(25, 118, 210, 0.08)',
                      boxShadow: '0 2px 8px rgba(25, 118, 210, 0.08)'
                    }}
                  >
                    <MarkdownRenderer content={enhancedAnalysis.ai_insights || 'AI分析を実行中です...'} />
                      </Paper>
                    </CardContent>
                  </Card>
                </Grid>

            {/* 強化分析セクション */}
            {[
              { 
                title: '📊 資料の参照回数分析', 
                icon: <DescriptionIcon />,
                content: enhancedAnalysis.resource_reference_count,
                color: 'linear-gradient(135deg, rgba(54, 162, 235, 0.08), rgba(54, 162, 235, 0.03))',
                borderColor: 'rgba(54, 162, 235, 0.2)',
                iconColor: '#36a2eb'
              },
              { 
                title: '🏷️ 質問カテゴリ分布と偏り', 
                icon: <CategoryIcon />,
                content: enhancedAnalysis.category_distribution_analysis,
                color: 'linear-gradient(135deg, rgba(255, 99, 132, 0.08), rgba(255, 99, 132, 0.03))',
                borderColor: 'rgba(255, 99, 132, 0.2)',
                iconColor: '#ff6384'
              },
              { 
                title: '📈 アクティブユーザー推移', 
                icon: <TimelineIcon />,
                content: enhancedAnalysis.active_user_trends,
                color: 'linear-gradient(135deg, rgba(75, 192, 192, 0.08), rgba(75, 192, 192, 0.03))',
                borderColor: 'rgba(75, 192, 192, 0.2)',
                iconColor: '#4bc0c0'
              },
              { 
                title: '🔄 未解決・再質問の傾向分析', 
                icon: <RepeatIcon />,
                content: enhancedAnalysis.unresolved_and_repeat_analysis,
                color: 'linear-gradient(135deg, rgba(255, 159, 64, 0.08), rgba(255, 159, 64, 0.03))',
                borderColor: 'rgba(255, 159, 64, 0.2)',
                iconColor: '#ff9f40'
              },
              { 
                title: '😊 詳細感情分析', 
                icon: <MoodIcon />,
                content: enhancedAnalysis.sentiment_analysis,
                color: 'linear-gradient(135deg, rgba(153, 102, 255, 0.08), rgba(153, 102, 255, 0.03))',
                borderColor: 'rgba(153, 102, 255, 0.2)',
                iconColor: '#9966ff'
              }
            ].map((section, index) => (
              <Grid item xs={12} key={index}>
                  <Card
                  elevation={0}
                    sx={{
                    mb: 2,
                      borderRadius: 3,
                    border: `1px solid ${section.borderColor}`,
                    background: section.color,
                    transition: 'all 0.3s ease',
                      overflow: 'hidden',
                      '&:hover': {
                      boxShadow: `0 8px 24px ${section.borderColor}`,
                      transform: 'translateY(-2px)',
                    }
                  }}
                >
                  <Accordion
                    expanded={expandedSections.has(index)}
                    onChange={() => toggleSection(index)}
                    sx={{
                      boxShadow: 'none',
                      '&:before': { display: 'none' },
                      backgroundColor: 'transparent',
                    }}
                  >
                    <AccordionSummary
                      expandIcon={<ExpandMoreIcon sx={{ color: section.iconColor }} />}
                      sx={{
                        p: 2.5,
                        '&.Mui-expanded': {
                          minHeight: 48,
                        },
                        '& .MuiAccordionSummary-content': {
                          margin: 0,
                        }
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                        <Box
                          sx={{
                            mr: 2,
                            p: 1.5,
                            borderRadius: 2,
                            backgroundColor: `${section.iconColor}20`,
                            border: `1px solid ${section.iconColor}40`,
                          }}
                        >
                          {React.cloneElement(section.icon, { 
                            sx: { fontSize: '1.5rem', color: section.iconColor } 
                          })}
                        </Box>
                        <Box sx={{ flex: 1 }}>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 700,
                              color: 'text.primary',
                              fontSize: '1.1rem',
                              mb: 0.5
                            }}
                          >
                            {section.title}
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{ color: 'text.secondary' }}
                          >
                            {section.content.summary ? 
                              section.content.summary.substring(0, 60) + '...' : 
                              'データを解析中...'
                            }
                          </Typography>
                        </Box>
                        <Badge
                          badgeContent={expandedSections.has(index) ? '展開中' : '詳細'}
                          color={expandedSections.has(index) ? 'success' : 'primary'}
                          sx={{ ml: 2 }}
                        />
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails sx={{ p: 0 }}>
                      <Divider />
                      <Box sx={{ p: 3 }}>
                        {/* セクション別の詳細表示 */}
                        {index === 0 && (
                          <Box>
                            <Paper 
                              elevation={0}
                              sx={{ 
                                p: 2, 
                                mb: 3, 
                                backgroundColor: 'rgba(255, 255, 255, 0.7)',
                                borderRadius: 2
                              }}
                            >
                              <MarkdownRenderer content={section.content.summary || 'データを解析中です...'} />
                            </Paper>
                            {'resources' in section.content && section.content.resources.length > 0 && (
                              <Box>
                                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                                  📈 資料別参照回数チャート
                                </Typography>
                                <Box sx={{ height: 450, p: 2, backgroundColor: 'rgba(255, 255, 255, 0.5)', borderRadius: 2 }}>
                                  <Bar
                                    data={getResourceReferenceChartData(section.content.resources)}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              plugins: {
                                        title: {
                                          display: true,
                                          text: '資料別参照回数（上位10件）',
                                          font: { size: 16, weight: 'bold' }
                                        },
                                        legend: { display: false },
                                tooltip: {
                                          backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                          titleColor: 'white',
                                          bodyColor: 'white',
                                          cornerRadius: 8,
                                          padding: 12
                                }
                              },
                              scales: {
                                y: {
                                  beginAtZero: true,
                                          grid: { color: 'rgba(0, 0, 0, 0.1)' },
                                  ticks: {
                                            color: '#666',
                                            callback: function(value: any) {
                                              return value + '回';
                                            }
                                  }
                                },
                                x: {
                                          grid: { display: false },
                                  ticks: {
                                            color: '#666',
                                    maxRotation: 45
                                          }
                                        }
                              }
                            }}
                          />
                            </Box>
                          </Box>
                        )}
                      </Box>
                        )}
                        {index === 2 && (
                        <Box>
                            <Paper 
                              elevation={0}
                            sx={{
                                p: 2, 
                                mb: 3, 
                                backgroundColor: 'rgba(255, 255, 255, 0.7)',
                                borderRadius: 2
                              }}
                            >
                              <MarkdownRenderer content={section.content.summary || 'データを解析中です...'} />
                            </Paper>
                            {'daily_trends' in section.content && section.content.daily_trends.length > 0 && (
                              <Box>
                                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                                  📊 アクティブユーザー推移グラフ
                          </Typography>
                                <Box sx={{ height: 450, p: 2, backgroundColor: 'rgba(255, 255, 255, 0.5)', borderRadius: 2 }}>
                                  <Line
                                    data={getUserTrendsChartData(section.content.daily_trends)}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              plugins: {
                                        title: {
                                          display: true,
                                          text: 'アクティブユーザー数推移（過去30日）',
                                          font: { size: 16, weight: 'bold' }
                                        },
                                        legend: {
                                          position: 'top',
                                          labels: { usePointStyle: true }
                                        },
                                        tooltip: {
                                          backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                          titleColor: 'white',
                                          bodyColor: 'white',
                                          cornerRadius: 8,
                                          padding: 12
                                        }
                                      },
                                      scales: {
                                        y: {
                                          type: 'linear',
                                          display: true,
                                          position: 'left',
                                          title: {
                                            display: true,
                                            text: 'アクティブユーザー数'
                                          },
                                          grid: { color: 'rgba(0, 0, 0, 0.1)' },
                                          ticks: { color: '#666' }
                                        },
                                        y1: {
                                          type: 'linear',
                                          display: true,
                                          position: 'right',
                                          title: {
                                            display: true,
                                            text: 'メッセージ数'
                                          },
                                          grid: { drawOnChartArea: false },
                                          ticks: { color: '#666' }
                                        },
                                        x: {
                                          grid: { color: 'rgba(0, 0, 0, 0.1)' },
                                          ticks: { color: '#666' }
                                }
                              }
                            }}
                          />
                            </Box>
                          </Box>
                        )}
                      </Box>
                        )}
                        {(index === 1 || index === 3 || index === 4) && (
                          <Paper 
                  elevation={0}
                  sx={{
                              p: 3, 
                              backgroundColor: 'rgba(255, 255, 255, 0.7)',
                    borderRadius: 2,
                              border: '1px solid rgba(0, 0, 0, 0.08)'
                            }}
                          >
                            <MarkdownRenderer content={section.content.summary || 'データを解析中です...'} />
                          </Paper>
                        )}
                    </Box>
                        </AccordionDetails>
                      </Accordion>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
    </Fade>
  );
};

export default AnalysisTab;