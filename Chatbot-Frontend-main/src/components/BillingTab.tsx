import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  Grid,
  Slider,
  TextField,
  Button,
  Fade,
  useTheme,
  useMediaQuery,
  Divider,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  MonetizationOn as MoneyIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Calculate as CalculateIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import api from '../api';

interface TokenUsageData {
  total_tokens_used: number;
  basic_plan_limit: number;
  current_month_cost: number;
  cost_breakdown: {
    basic_plan: number;
    tier1_cost: number;
    tier2_cost: number;
    tier3_cost: number;
    total_cost: number;
  };
  usage_percentage: number;
  remaining_tokens: number;
  warning_level: 'safe' | 'warning' | 'critical';
  company_users_count: number;
  company_name: string;
}

interface SimulationData {
  simulated_tokens: number;
  cost_breakdown: {
    total_cost: number;
    basic_plan: number;
    tier1_cost: number;
    tier2_cost: number;
    tier3_cost: number;
    effective_rate: number;
  };
  tokens_in_millions: number;
  cost_per_million: number;
}

const BillingTab: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [tokenUsage, setTokenUsage] = useState<TokenUsageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [simulationTokens, setSimulationTokens] = useState(30000000); // 30M tokens
  const [simulationData, setSimulationData] = useState<SimulationData | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // トークン使用量データを取得
  const fetchTokenUsage = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/company-token-usage');
      setTokenUsage(response.data);
    } catch (error: any) {
      console.error('トークン使用量取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 料金シミュレーションを実行
  const simulateCost = async (tokens: number) => {
    try {
      setIsSimulating(true);
      const response = await api.post('/simulate-cost', { tokens });
      setSimulationData(response.data);
    } catch (error: any) {
      console.error('料金シミュレーションエラー:', error);
    } finally {
      setIsSimulating(false);
    }
  };

  useEffect(() => {
    fetchTokenUsage();
  }, []);

  useEffect(() => {
    simulateCost(simulationTokens);
  }, [simulationTokens]);

  // 数値のフォーマット関数
  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat('ja-JP').format(Math.round(num));
  };

  const formatTokens = (tokens: number): string => {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(1)}M`;
    }
    return formatNumber(tokens);
  };

  const formatCurrency = (amount: number): string => {
    return `¥${formatNumber(amount)}`;
  };

  // 警告レベルに応じた色を取得
  const getWarningColor = (level: string) => {
    switch (level) {
      case 'critical': return theme.palette.error.main;
      case 'warning': return theme.palette.warning.main;
      default: return theme.palette.success.main;
    }
  };

  // 進捗バーの色を取得
  const getProgressColor = (percentage: number) => {
    if (percentage >= 95) return 'error';
    if (percentage >= 80) return 'warning';
    return 'primary';
  };

  if (isLoading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>料金情報を読み込み中...</Typography>
      </Box>
    );
  }

  return (
    <Fade in={true} timeout={400}>
      <Box>
        {/* ヘッダー */}
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
            <MoneyIcon
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
              料金管理
            </Typography>
          </Box>

          <Button
            variant="outlined"
            color="primary"
            onClick={fetchTokenUsage}
            disabled={isLoading}
            startIcon={<RefreshIcon />}
            size={isMobile ? "small" : "medium"}
            sx={{ borderRadius: 2 }}
          >
            {!isMobile && '更新'}
          </Button>
        </Box>

        {tokenUsage && (
          <Grid container spacing={3}>
            {/* 使用状況概要 */}
            <Grid item xs={12}>
              <Card
                elevation={0}
                sx={{
                  borderRadius: 2,
                  border: '1px solid rgba(0, 0, 0, 0.12)',
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
                    background: `linear-gradient(90deg, ${getWarningColor(tokenUsage.warning_level)}, ${getWarningColor(tokenUsage.warning_level)}80)`,
                    opacity: 0.8
                  }
                }}
              >
                <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <TrendingUpIcon sx={{ mr: 1.5, color: 'primary.main', fontSize: '1.5rem' }} />
                    <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
                      {tokenUsage.company_name} - 今月の使用状況
                    </Typography>
                    <Chip
                      label={`${tokenUsage.company_users_count}名`}
                      size="small"
                      sx={{ ml: 2, fontWeight: 600 }}
                    />
                  </Box>

                  <Divider sx={{ mb: 3 }} />

                  {/* 使用量ゲージ */}
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        トークン使用量
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {formatTokens(tokenUsage.total_tokens_used)} / {formatTokens(tokenUsage.basic_plan_limit)} ({tokenUsage.usage_percentage}%)
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(100, tokenUsage.usage_percentage)}
                      color={getProgressColor(tokenUsage.usage_percentage)}
                      sx={{
                        height: 12,
                        borderRadius: 6,
                        backgroundColor: 'rgba(0, 0, 0, 0.08)',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 6,
                        }
                      }}
                    />
                  </Box>

                  {/* 警告バナー */}
                  {tokenUsage.warning_level !== 'safe' && (
                    <Alert
                      severity={tokenUsage.warning_level === 'critical' ? 'error' : 'warning'}
                      sx={{ mb: 3 }}
                      icon={<WarningIcon />}
                    >
                      {tokenUsage.warning_level === 'critical' 
                        ? `残り${formatTokens(tokenUsage.remaining_tokens)}で従量課金に移行します！` 
                        : `あと${formatTokens(tokenUsage.remaining_tokens)}で従量課金開始`}
                    </Alert>
                  )}

                  {/* 料金内訳 */}
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(25, 118, 210, 0.05)', borderRadius: 2 }}>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                          {formatCurrency(tokenUsage.current_month_cost)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          今月の料金
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(76, 175, 80, 0.05)', borderRadius: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {formatCurrency(tokenUsage.cost_breakdown.basic_plan)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          基本プラン
                        </Typography>
                      </Box>
                    </Grid>
                    {tokenUsage.cost_breakdown.tier1_cost > 0 && (
                      <Grid item xs={12} sm={6} md={3}>
                        <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(255, 152, 0, 0.05)', borderRadius: 2 }}>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            {formatCurrency(tokenUsage.cost_breakdown.tier1_cost)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            第1段階従量
                          </Typography>
                        </Box>
                      </Grid>
                    )}
                    {tokenUsage.cost_breakdown.tier2_cost > 0 && (
                      <Grid item xs={12} sm={6} md={3}>
                        <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(255, 87, 34, 0.05)', borderRadius: 2 }}>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            {formatCurrency(tokenUsage.cost_breakdown.tier2_cost)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            第2段階従量
                          </Typography>
                        </Box>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* 料金シミュレータ */}
            <Grid item xs={12} md={6}>
              <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid rgba(0, 0, 0, 0.12)', height: '100%' }}>
                <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <CalculateIcon sx={{ mr: 1.5, color: 'secondary.main', fontSize: '1.5rem' }} />
                    <Typography variant="h6" sx={{ fontWeight: 600, color: 'secondary.main' }}>
                      料金シミュレータ
                    </Typography>
                  </Box>

                  <Divider sx={{ mb: 3 }} />

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    月間使用量（M tokens）
                  </Typography>
                  
                  <Slider
                    value={simulationTokens / 1000000}
                    onChange={(_, value) => setSimulationTokens((value as number) * 1000000)}
                    min={10}
                    max={150}
                    step={5}
                    marks={[
                      { value: 25, label: '25M' },
                      { value: 50, label: '50M' },
                      { value: 100, label: '100M' }
                    ]}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${value}M`}
                    sx={{ mb: 3 }}
                  />

                  <TextField
                    label="詳細な値を入力（M tokens）"
                    type="number"
                    value={simulationTokens / 1000000}
                    onChange={(e) => setSimulationTokens(parseFloat(e.target.value) * 1000000 || 0)}
                    variant="outlined"
                    size="small"
                    fullWidth
                    sx={{ mb: 3 }}
                    inputProps={{ step: 0.1, min: 0 }}
                  />

                  {simulationData && (
                    <Box sx={{ p: 2, backgroundColor: 'rgba(156, 39, 176, 0.05)', borderRadius: 2 }}>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: 'secondary.main', mb: 1 }}>
                        {formatCurrency(simulationData.cost_breakdown.total_cost)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        月額料金（{simulationData.tokens_in_millions.toFixed(1)}M tokens使用時）
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        実効レート: {simulationData.cost_breakdown.effective_rate.toFixed(2)}円/1,000tokens
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* 料金体系説明 */}
            <Grid item xs={12} md={6}>
              <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid rgba(0, 0, 0, 0.12)', height: '100%' }}>
                <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <InfoIcon sx={{ mr: 1.5, color: 'info.main', fontSize: '1.5rem' }} />
                    <Typography variant="h6" sx={{ fontWeight: 600, color: 'info.main' }}>
                      料金体系
                    </Typography>
                  </Box>

                  <Divider sx={{ mb: 3 }} />

                  <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(0, 0, 0, 0.12)' }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                          <TableCell><strong>プラン</strong></TableCell>
                          <TableCell><strong>使用量</strong></TableCell>
                          <TableCell><strong>料金</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>基本プラン</TableCell>
                          <TableCell>0 ～ 25M</TableCell>
                          <TableCell>{formatCurrency(150000)}/月</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>第1段階</TableCell>
                          <TableCell>25M ～ 50M</TableCell>
                          <TableCell>15円/1,000tokens</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>第2段階</TableCell>
                          <TableCell>50M ～ 100M</TableCell>
                          <TableCell>12円/1,000tokens</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>第3段階</TableCell>
                          <TableCell>100M超</TableCell>
                          <TableCell>10円/1,000tokens</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>

                  <Box sx={{ mt: 2, p: 2, backgroundColor: 'rgba(76, 175, 80, 0.05)', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      💡 <strong>メリット:</strong> 25Mまでは定額制で安心、超過分は段階的に安くなります
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </Box>
    </Fade>
  );
};

export default BillingTab; 