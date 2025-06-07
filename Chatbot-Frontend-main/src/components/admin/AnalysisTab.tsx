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
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress
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
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import BusinessIcon from '@mui/icons-material/Business';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import api from '../../api';

interface AnalysisTabProps {
  analysis: AnalysisResult | null;
  isLoading: boolean;
  onRefresh: () => void;
}

// ビジネス分析のプロンプト
const BUSINESS_ANALYSIS_PROMPT = `あなたはプロフェッショナルな業務改善コンサルタントです。以下の社内チャットログを分析し、ビジネス的な観点から以下の各項目を出力してください。

【目的】
本分析は、社内向けチャットボットの改善点、業務上のボトルネック、社員のニーズを可視化し、今後のプロダクト改善や業務最適化に繋げるためのものです。

【分析項目】
1. 頻出トピック/質問とその傾向分析
   - 最も多く質問されている話題とその背景にある可能性のある業務課題
   - 時間帯/曜日による質問パターンの変化

2. 業務効率化の機会
   - チャットボットに頻繁に質問されることで特定される非効率なプロセスや情報格差
   - 自動化や標準化が可能な業務領域の提案

3. 社員のフラストレーションポイント
   - 否定的な感情を伴う質問から推測される不満点
   - 回答に対する満足度が低い領域

4. 製品/サービス改善の示唆
   - 製品やサービスに関する質問から得られる改善点
   - 顧客視点での懸念事項

5. コミュニケーションギャップ
   - 部門間で情報共有が不足している可能性のある領域
   - 公式なドキュメント化が必要な知識領域

【具体的な改善提案】
- 短期的に実施可能な対策（3ヶ月以内）
- 中長期的な戦略的取り組み（6ヶ月〜1年）
- 必要なリソースと期待される効果`;

const AnalysisTab: React.FC<AnalysisTabProps> = ({
  analysis,
  isLoading,
  onRefresh
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  // 分析モード (標準/ビジネス)
  const [analysisMode, setAnalysisMode] = useState<string>('standard');

  // ビジネス分析の読み込み状態
  const [isBusinessAnalysisLoading, setIsBusinessAnalysisLoading] = useState<boolean>(false);

  // 詳細なビジネス分析を取得する関数
  const fetchBusinessAnalysis = async () => {
    if (!analysis) return;

    // 既にビジネス分析が完了している場合はスキップ
    if (analysis.business_analysis_completed) {
      setAnalysisMode('business');
      return;
    }

    try {
      setIsBusinessAnalysisLoading(true);
      console.log('ビジネス詳細分析を開始...');

      // バックエンドAPIに詳細分析をリクエスト
      const response = await api.post(`${import.meta.env.VITE_API_URL}/admin/detailed-analysis`, {
        prompt: BUSINESS_ANALYSIS_PROMPT
      });

      console.log('ビジネス詳細分析レスポンス:', response.data);

      // レスポンスから詳細分析結果を取得
      if (response.data && response.data.detailed_analysis) {
        const {
          detailed_topic_analysis,
          efficiency_opportunities,
          frustration_points,
          improvement_suggestions,
          communication_gaps,
          specific_recommendations
        } = response.data.detailed_analysis;

        // 分析結果を既存の分析データにマージ
        Object.assign(analysis, {
          detailed_topic_analysis,
          efficiency_opportunities,
          frustration_points,
          improvement_suggestions,
          communication_gaps,
          specific_recommendations,
          business_analysis_completed: true
        });

        console.log('ビジネス詳細分析結果をマージ完了');
      } else {
        console.error('詳細分析レスポンスの形式が不正です:', response.data);
        throw new Error('詳細分析レスポンスの形式が不正です');
      }

      // ビジネス分析モードに切り替え
      setAnalysisMode('business');
    } catch (error: any) {
      console.error('詳細ビジネス分析の取得エラー:', error);
      
      // より詳細なエラーメッセージ
      let errorMessage = '詳細ビジネス分析の取得中にエラーが発生しました。';
      if (error.response) {
        if (error.response.status === 500) {
          errorMessage += '\nサーバーエラーが発生しました。Geminiモデルが初期化されていない可能性があります。';
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
      setIsBusinessAnalysisLoading(false);
    }
  };

  // タブの変更ハンドラ
  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    if (newValue === 'business' && !analysis?.business_analysis_completed) {
      fetchBusinessAnalysis();
    } else {
      setAnalysisMode(newValue);
    }
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
            <Typography
              variant={isMobile ? "h6" : "h5"}
              sx={{
                fontWeight: 600,
                color: 'text.primary'
              }}
            >
              チャット分析
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            {/* CSV出力ボタン */}
            <Tooltip title="CSV形式で出力">
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
                    px: { xs: 1.5, sm: 2 },
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
            <Tooltip title="データを更新">
              <Button
                variant="outlined"
                color="primary"
                onClick={onRefresh}
                disabled={isLoading}
                startIcon={<RefreshIcon />}
                size={isMobile ? "small" : "medium"}
                sx={{
                  borderRadius: 2,
                  px: { xs: 1.5, sm: 2 },
                  '&:hover': {
                    backgroundColor: 'rgba(25, 118, 210, 0.08)',
                  }
                }}
              >
                {!isMobile && '更新'}
              </Button>
            </Tooltip>
          </Box>
        </Box>

        {/* 分析モード切り替えタブ */}
        {analysis && (
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
        )}

        {isLoading ? (
          <LoadingIndicator />
        ) : !analysis ? (
          <EmptyState message="分析データがありません" />
        ) : isBusinessAnalysisLoading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
            <CircularProgress size={60} sx={{ mb: 3 }} />
            <Typography variant="h6" color="text.secondary">
              ビジネス詳細分析を実行中...
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              チャットデータの分析にはしばらく時間がかかる場合があります
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={3}>
            {/* 標準分析モード */}
            {analysisMode === 'standard' ? (
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
                    elevation={0}
                    sx={{
                      borderRadius: 2,
                      border: '1px solid rgba(0, 0, 0, 0.12)',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                      }
                    }}
                  >
                    <CardContent sx={{ p: { xs: 2, sm: 3 }, flex: 1, display: 'flex', flexDirection: 'column' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <CategoryIcon
                          sx={{
                            mr: 1.5,
                            color: theme.palette.primary.main,
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
                          カテゴリ分布
                        </Typography>
                      </Box>

                      <Divider sx={{ mb: 2 }} />

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
                              plugins: {
                                legend: {
                                  display: false
                                },
                                tooltip: {
                                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                  padding: 12,
                                  titleFont: {
                                    size: 14,
                                    weight: 'bold'
                                  },
                                  bodyFont: {
                                    size: 13
                                  },
                                  cornerRadius: 8
                                }
                              },
                              scales: {
                                y: {
                                  beginAtZero: true,
                                  grid: {
                                    color: 'rgba(0, 0, 0, 0.04)'
                                  }
                                },
                                x: {
                                  grid: {
                                    display: false
                                  }
                                }
                              },
                              animation: {
                                duration: 1000,
                                easing: 'easeInOutQuart'
                              }
                            }}
                          />
                        ) : (
                          <Box sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%'
                          }}>
                            <CategoryIcon sx={{ fontSize: '3rem', color: 'text.disabled', mb: 2 }} />
                            <Typography variant="body1" color="text.secondary">
                              カテゴリデータがありません
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card
                    elevation={0}
                    sx={{
                      borderRadius: 2,
                      border: '1px solid rgba(0, 0, 0, 0.12)',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                      }
                    }}
                  >
                    <CardContent sx={{ p: { xs: 2, sm: 3 }, flex: 1, display: 'flex', flexDirection: 'column' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <MoodIcon
                          sx={{
                            mr: 1.5,
                            color: theme.palette.secondary.main,
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
                          感情分布
                        </Typography>
                      </Box>

                      <Divider sx={{ mb: 2 }} />

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
                              plugins: {
                                tooltip: {
                                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                  padding: 12,
                                  titleFont: {
                                    size: 14,
                                    weight: 'bold'
                                  },
                                  bodyFont: {
                                    size: 13
                                  },
                                  cornerRadius: 8
                                },
                                legend: {
                                  position: 'bottom',
                                  labels: {
                                    usePointStyle: true,
                                    padding: 20,
                                    font: {
                                      size: 12
                                    }
                                  }
                                }
                              },
                              animation: {
                                duration: 1000,
                                easing: 'easeInOutQuart'
                              }
                            }}
                          />
                        ) : (
                          <Box sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%'
                          }}>
                            <MoodIcon sx={{ fontSize: '3rem', color: 'text.disabled', mb: 2 }} />
                            <Typography variant="body1" color="text.secondary">
                              感情データがありません
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
            ) : (
              // ビジネス詳細分析モード
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

                    {/* ビジネス分析セクション */}
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
            )}
          </Grid>
        )}
      </Box>
    </Fade>
  );
};

export default AnalysisTab;