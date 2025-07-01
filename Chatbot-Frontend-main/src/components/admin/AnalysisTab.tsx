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
  enhancedAnalysis?: any;
  isEnhancedLoading?: boolean;
  onRefresh: () => void;
  onStartAnalysis?: () => void; // 手動分析開始用
  onStartAIInsights?: () => void; // AI洞察開始用
}

const AnalysisTab: React.FC<AnalysisTabProps> = ({
  analysis,
  isLoading,
  enhancedAnalysis: propEnhancedAnalysis,
  isEnhancedLoading: propIsEnhancedLoading,
  onRefresh,
  onStartAnalysis,
  onStartAIInsights
}) => {
  console.log("🎯 [ANALYSIS_TAB] コンポーネント開始");
  console.log("🎯 [ANALYSIS_TAB] analysis:", analysis);
  console.log("🎯 [ANALYSIS_TAB] isLoading:", isLoading);
  console.log("🎯 [ANALYSIS_TAB] propEnhancedAnalysis:", propEnhancedAnalysis);
  console.log("🎯 [ANALYSIS_TAB] propIsEnhancedLoading:", propIsEnhancedLoading);
  
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  // AdminPanelから渡されるデータを使用（独自API呼び出しを停止）
  const enhancedAnalysis = propEnhancedAnalysis;
  const isEnhancedLoading = propIsEnhancedLoading || false;
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set([0, 1, 2])); // デフォルトで最初の3つを展開


  console.log("🎯 [ANALYSIS_TAB] enhancedAnalysis (最終):", enhancedAnalysis);
  console.log("🎯 [ANALYSIS_TAB] isEnhancedLoading (最終):", isEnhancedLoading);

  // propsのデータが更新されたら最終更新時刻を更新
  useEffect(() => {
    console.log("🎯 [ANALYSIS_TAB] useEffect propEnhancedAnalysis変化:", propEnhancedAnalysis);
    if (propEnhancedAnalysis) {
      console.log("🎯 [ANALYSIS_TAB] lastRefresh を更新");
      setLastRefresh(new Date());
    }
  }, [propEnhancedAnalysis]);

  // レンダリング条件のデバッグ
  useEffect(() => {
    console.log("🎯 [RENDER] レンダリング条件チェック");
    console.log("🎯 [RENDER] isEnhancedLoading:", isEnhancedLoading);
    console.log("🎯 [RENDER] enhancedAnalysis:", enhancedAnalysis);
    console.log("🎯 [RENDER] !!enhancedAnalysis:", !!enhancedAnalysis);
    
    if (isEnhancedLoading) {
      console.log("🎯 [RENDER] → ローディング画面を表示予定");
    } else if (!enhancedAnalysis) {
      console.log("🎯 [RENDER] → 分析開始ボタンを表示予定");
    } else {
      console.log("🎯 [RENDER] → 分析データを表示予定");
      
      // 詳細データ構造をチェック
      console.log("🔍 [DATA_CHECK] resource_reference_count:", enhancedAnalysis.resource_reference_count);
      console.log("🔍 [DATA_CHECK] resource_reference_count.resources:", enhancedAnalysis.resource_reference_count?.resources);
      console.log("🔍 [DATA_CHECK] resource_reference_count.summary:", enhancedAnalysis.resource_reference_count?.summary);
      
      console.log("🔍 [DATA_CHECK] category_distribution_analysis:", enhancedAnalysis.category_distribution_analysis);
      console.log("🔍 [DATA_CHECK] category_distribution_analysis.summary:", enhancedAnalysis.category_distribution_analysis?.summary);
      
      console.log("🔍 [DATA_CHECK] active_user_trends:", enhancedAnalysis.active_user_trends);
      console.log("🔍 [DATA_CHECK] active_user_trends.daily_trends:", enhancedAnalysis.active_user_trends?.daily_trends);
      console.log("🔍 [DATA_CHECK] active_user_trends.summary:", enhancedAnalysis.active_user_trends?.summary);
      
      console.log("🔍 [DATA_CHECK] expandedSections:", expandedSections);
    }
  }, [isEnhancedLoading, enhancedAnalysis, expandedSections]);

  // セクション展開/折りたたみの処理
  const toggleSection = (index: number) => {
    console.log("🔀 [TOGGLE] セクション", index, "をクリック");
    console.log("🔀 [TOGGLE] 現在の expandedSections:", expandedSections);
    
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(index)) {
      console.log("🔀 [TOGGLE] セクション", index, "を折りたたみ");
      newExpanded.delete(index);
    } else {
      console.log("🔀 [TOGGLE] セクション", index, "を展開");
      newExpanded.add(index);
    }
    
    console.log("🔀 [TOGGLE] 新しい expandedSections:", newExpanded);
    setExpandedSections(newExpanded);
  };

  // 更新ボタンのハンドラ（AdminPanelのonRefreshを使用）
  const handleRefresh = () => {
    onRefresh(); // AdminPanelで基本分析と強化分析の両方を更新
  };

  // 資料参照回数チャートのデータを生成
  const getResourceReferenceChartData = (resources: any[]) => {
    console.log("📊 [CHART] getResourceReferenceChartData 呼び出し");
    console.log("📊 [CHART] resources:", resources);
    console.log("📊 [CHART] resources.length:", resources?.length);
    
    if (!resources || resources.length === 0) {
      console.log("📊 [CHART] リソースデータなし、nullを返す");
      return null;
    }

    const top10Resources = resources.slice(0, 10);
    console.log("📊 [CHART] top10Resources:", top10Resources);
    
    // 参照回数の合計をチェック
    const totalReferences = top10Resources.reduce((sum, r) => sum + (r.reference_count || 0), 0);
    console.log("📊 [CHART] totalReferences:", totalReferences);
    
    // 参照回数が0の場合はダミーデータを表示
    if (totalReferences === 0) {
      console.log("📊 [CHART] 参照回数が0のため、メッセージ表示用のnullを返す");
      return null;
    }
    
    const chartData = {
      labels: top10Resources.map(r => r.name.length > 20 ? r.name.substring(0, 20) + '...' : r.name),
      datasets: [
        {
          label: '参照回数',
          data: top10Resources.map(r => r.reference_count || 0),
          backgroundColor: 'rgba(54, 162, 235, 0.6)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 2,
        },
      ],
    };
    
    console.log("📊 [CHART] 生成されたchartData:", chartData);
    return chartData;
  };

  // アクティブユーザー推移チャートのデータを生成
  const getUserTrendsChartData = (dailyTrends: any[]) => {
    console.log("📈 [CHART] getUserTrendsChartData 呼び出し");
    console.log("📈 [CHART] dailyTrends:", dailyTrends);
    console.log("📈 [CHART] dailyTrends.length:", dailyTrends?.length);
    
    if (!dailyTrends || dailyTrends.length === 0) {
      console.log("📈 [CHART] 日次トレンドデータなし、nullを返す");
      return null;
    }

    const last30Days = dailyTrends.slice(-30);
    console.log("📈 [CHART] last30Days:", last30Days);
    
    const chartData = {
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
    
    console.log("📈 [CHART] 生成されたchartData:", chartData);
    return chartData;
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
                AI分析ダッシュボード
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
                AIによる高度な分析と洞察
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

          {enhancedAnalysis && (
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

              <Tooltip title="分析を再実行">
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
                    {isEnhancedLoading ? '分析中...' : '再分析'}
                  </Button>
                </span>
              </Tooltip>
            </Stack>
          )}
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
          // 分析データがない場合：分析開始ボタンを表示
          <Container maxWidth="md" sx={{ py: 8, textAlign: 'center' }}>
            <Box
              sx={{
                p: 4,
                borderRadius: 3,
                background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.05), rgba(59, 130, 246, 0.08))',
                border: '2px solid rgba(37, 99, 235, 0.12)',
                mb: 4
              }}
            >
              <SmartToyIcon 
                sx={{ 
                  fontSize: '4rem', 
                  color: '#2563eb', 
                  mb: 2,
                  opacity: 0.8
                }} 
              />
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 700,
                  mb: 2,
                  background: 'linear-gradient(135deg, #1e293b, #475569)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                AI分析を開始
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  color: 'text.secondary',
                  mb: 4,
                  fontSize: '1.1rem',
                  lineHeight: 1.6,
                  maxWidth: '500px',
                  mx: 'auto'
                }}
              >
                チャット履歴の高度な分析とAIによる洞察を生成します。
                <br />
                分析には数十秒かかる場合があります。
              </Typography>
              
              <Button
                variant="contained"
                size="large"
                onClick={onStartAnalysis}
                disabled={!onStartAnalysis}
                startIcon={<AutoFixHighIcon />}
                sx={{
                  px: 4,
                  py: 1.5,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  borderRadius: 3,
                  background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
                  boxShadow: '0 4px 16px rgba(37, 99, 235, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #1d4ed8, #2563eb)',
                    boxShadow: '0 6px 20px rgba(37, 99, 235, 0.4)',
                    transform: 'translateY(-2px)',
                  },
                  transition: 'all 0.3s ease'
                }}
              >
                AI分析を開始
              </Button>
              
              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  mt: 3,
                  color: 'text.secondary',
                  fontSize: '0.9rem'
                }}
              >
                ✨ 最新の AI による高度な分析
              </Typography>
            </Box>
          </Container>
        ) : (
          <Grid container spacing={3}>
            {/* AI洞察カード */}
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
                        🤖 AI 分析レポート
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
                    {!enhancedAnalysis.ai_insights || !enhancedAnalysis.ai_insights.trim() ? (
                      // AI洞察がない場合：分析開始ボタンを表示
                      <Box sx={{ textAlign: 'center', py: 4 }}>
                        <AutoFixHighIcon 
                          sx={{ 
                            fontSize: '3rem', 
                            color: '#1976d2', 
                            mb: 2,
                            opacity: 0.7
                          }} 
                        />
                        <Typography
                          variant="h6"
                          sx={{
                            fontWeight: 600,
                            mb: 2,
                            color: 'text.primary'
                          }}
                        >
                          AI分析を開始しますか？
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            color: 'text.secondary',
                            mb: 3,
                            maxWidth: '400px',
                            mx: 'auto',
                            lineHeight: 1.6
                          }}
                        >
                          AIがチャット履歴を分析して、
                          <br />
                          詳細な洞察とアドバイスを生成します。
                        </Typography>
                        <Button
                          variant="contained"
                          onClick={onStartAIInsights}
                          disabled={isEnhancedLoading || !onStartAIInsights}
                          startIcon={isEnhancedLoading ? <CircularProgress size={20} color="inherit" /> : <SmartToyIcon />}
                          sx={{
                            px: 4,
                            py: 1.2,
                            fontSize: '1rem',
                            fontWeight: 600,
                            borderRadius: 2,
                            background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
                            boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)',
                            '&:hover': {
                              background: 'linear-gradient(135deg, #1565c0, #1976d2)',
                              boxShadow: '0 6px 16px rgba(25, 118, 210, 0.4)',
                            }
                          }}
                        >
                          {isEnhancedLoading ? 'AI分析中...' : 'AI分析を開始'}
                        </Button>
                        <Typography
                          variant="caption"
                          sx={{
                            display: 'block',
                            mt: 2,
                            color: 'text.secondary',
                            fontSize: '0.85rem'
                          }}
                        >
                          ⏱️ 約20〜30秒で完了します
                        </Typography>
                      </Box>
                    ) : (
                      // AI洞察がある場合：内容を表示
                      <MarkdownRenderer content={enhancedAnalysis.ai_insights} />
                    )}
                      </Paper>
                    </CardContent>
                  </Card>
                </Grid>

            {/* 強化分析セクション */}
            {[
              { 
                title: '資料の参照回数分析', 
                icon: <DescriptionIcon />,
                content: enhancedAnalysis.resource_reference_count,
                color: '#1976d2'
              },
              { 
                title: '質問カテゴリ分布と偏り', 
                icon: <CategoryIcon />,
                content: enhancedAnalysis.category_distribution_analysis,
                color: '#d32f2f'
              },
              { 
                title: 'アクティブユーザー推移', 
                icon: <TimelineIcon />,
                content: enhancedAnalysis.active_user_trends,
                color: '#2e7d32'
              },
              { 
                title: '未解決・再質問の傾向分析', 
                icon: <RepeatIcon />,
                content: enhancedAnalysis.unresolved_and_repeat_analysis,
                color: '#ed6c02'
              },
              { 
                title: '詳細感情分析', 
                icon: <MoodIcon />,
                content: enhancedAnalysis.sentiment_analysis,
                color: '#9c27b0'
              }
            ].map((section, index) => (
              <Grid item xs={12} key={index}>
                <Card
                  elevation={1}
                  sx={{
                    mb: 2,
                    borderRadius: 2,
                    border: '1px solid rgba(0, 0, 0, 0.08)',
                    backgroundColor: '#fff',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
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
                      expandIcon={<ExpandMoreIcon sx={{ color: section.color }} />}
                      sx={{
                        p: 2,
                        '&.Mui-expanded': {
                          minHeight: 48,
                        },
                        '& .MuiAccordionSummary-content': {
                          margin: 0,
                        }
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                        <Box sx={{ mr: 2 }}>
                          {React.cloneElement(section.icon, { 
                            sx: { fontSize: '1.5rem', color: section.color } 
                          })}
                        </Box>
                        <Box sx={{ flex: 1 }}>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 600,
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
                              section.content.summary.substring(0, 80) + '...' : 
                              'データを解析中...'
                            }
                          </Typography>
                        </Box>
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
                                p: 3, 
                                mb: 3, 
                                backgroundColor: '#f8f9fa',
                                borderRadius: 1,
                                border: '1px solid rgba(0, 0, 0, 0.06)'
                              }}
                            >
                              {(() => {
                                const content = section.content.summary || 'データを解析中です...';
                                console.log(`📝 [MARKDOWN] セクション${index} summary内容:`, content);
                                console.log(`📝 [MARKDOWN] content.length:`, content.length);
                                return <MarkdownRenderer content={content} />;
                              })()}
                            </Paper>
                            {'resources' in section.content && section.content.resources.length > 0 && (
                              <Box>
                                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: section.color }}>
                                  資料別参照回数
                                </Typography>
                                <Box sx={{ 
                                  height: 400, 
                                  p: 2, 
                                  backgroundColor: '#fff', 
                                  borderRadius: 1,
                                  border: '1px solid rgba(0, 0, 0, 0.06)'
                                }}>
                                  {(() => {
                                    const chartData = getResourceReferenceChartData(section.content.resources);
                                    console.log("📊 [BAR_CHART] チャート描画:", chartData);
                                    if (!chartData) {
                                      console.log("📊 [BAR_CHART] チャートデータなし");
                                      return <div>チャートデータがありません</div>;
                                    }
                                    return (
                                      <Bar
                                        data={chartData}
                                        options={{
                                          responsive: true,
                                          maintainAspectRatio: false,
                                          plugins: {
                                            title: {
                                              display: true,
                                              text: '資料別参照回数（上位10件）',
                                              font: { size: 14, weight: 'normal' }
                                            },
                                            legend: { display: false },
                                            tooltip: {
                                              backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                              titleColor: 'white',
                                              bodyColor: 'white',
                                              cornerRadius: 4,
                                              padding: 8
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
                                    );
                                  })()}
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
                                p: 3, 
                                mb: 3, 
                                backgroundColor: '#f8f9fa',
                                borderRadius: 1,
                                border: '1px solid rgba(0, 0, 0, 0.06)'
                              }}
                            >
                              <MarkdownRenderer content={section.content.summary || 'データを解析中です...'} />
                            </Paper>
                            {'daily_trends' in section.content && section.content.daily_trends.length > 0 && (
                              <Box>
                                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: section.color }}>
                                  アクティブユーザー推移
                                </Typography>
                                <Box sx={{ 
                                  height: 400, 
                                  p: 2, 
                                  backgroundColor: '#fff', 
                                  borderRadius: 1,
                                  border: '1px solid rgba(0, 0, 0, 0.06)'
                                }}>
                                  <Line
                                    data={getUserTrendsChartData(section.content.daily_trends)}
                                    options={{
                                      responsive: true,
                                      maintainAspectRatio: false,
                                      plugins: {
                                        title: {
                                          display: true,
                                          text: 'アクティブユーザー数推移（過去30日）',
                                          font: { size: 14, weight: 'normal' }
                                        },
                                        legend: {
                                          position: 'top',
                                          labels: { usePointStyle: true }
                                        },
                                        tooltip: {
                                          backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                          titleColor: 'white',
                                          bodyColor: 'white',
                                          cornerRadius: 4,
                                          padding: 8
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
                              backgroundColor: '#f8f9fa',
                              borderRadius: 1,
                              border: '1px solid rgba(0, 0, 0, 0.06)'
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