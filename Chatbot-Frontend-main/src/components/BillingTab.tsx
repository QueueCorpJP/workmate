import React, { useState, useEffect, useContext } from 'react';
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
  IconButton,
  Container,
  Stack
} from '@mui/material';
import {
  MonetizationOn as MoneyIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Calculate as CalculateIcon,
  Info as InfoIcon,
  Diamond as DiamondIcon,
  CheckCircle as CheckIcon,
  Star as StarIcon
} from '@mui/icons-material';
import api from '../api';
import { useAuth } from '../contexts/AuthContext';

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
    base_cost: number;
    prompt_cost: number;
  };
  usage_percentage: number;
  remaining_tokens: number;
  warning_level: 'safe' | 'warning' | 'critical';
  company_users_count: number;
  company_name: string;
  prompt_references_total: number;
  input_tokens_total: number;
  output_tokens_total: number;
}

interface PricingInfo {
  company_id: string;
  company_name: string;
  pricing_model: string;
  pricing_description: string;
  pricing_table: any;
  cost_examples: any;
  is_premium_customer: boolean;
  is_premium_plan?: boolean;
  plan_details?: {
    monthly_price_jpy: number;
    contract_period: string;
    total_price_jpy: number;
    features: string[];
  };
  total_company_cost_jpy?: number;
}

interface MemberUsage {
  member_id: string;
  member_name: string;
  member_email: string;
  total_tokens: number;
  conversations: number;
  cost_usd: number;
  cost_jpy: number;
  avg_cost_per_conversation: number;
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
    base_cost: number;
    prompt_cost: number;
  };
  tokens_in_millions: number;
  cost_per_million: number;
  prompt_references: number;
}

const BillingTab: React.FC = () => {
  const theme = useTheme();
  const [pricingInfo, setPricingInfo] = useState<PricingInfo | null>(null);
  const [memberUsage, setMemberUsage] = useState<MemberUsage[]>([]);
  const [isPricingInfoLoading, setIsPricingInfoLoading] = useState(false);
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { user } = useAuth();
  
  const [tokenUsage, setTokenUsage] = useState<TokenUsageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [simulationTokens, setSimulationTokens] = useState(30000000); // 30M tokens
  const [simulationPrompts, setSimulationPrompts] = useState(1000); // 1000 prompt references
  const [simulationData, setSimulationData] = useState<SimulationData | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [currentCompanyId, setCurrentCompanyId] = useState<string | null>(null);

  // 旧ロジック（削除済み）
  // 新しいpricingInfo.is_premium_planでPremium Plan判定を行う

  // トークン使用量データを取得（共有サービス使用）
  const fetchTokenUsage = async () => {
    try {
      setIsLoading(true);
      
      // company_idを最初に取得
      if (user?.id) {
        try {
          const response = await api.get('/auth/user');
          const userData = response.data;
          if (userData.company_id) {
            setCurrentCompanyId(userData.company_id);
          } else {
            // authContextからもcompany_idを確認
            if (user?.company_id) {
              setCurrentCompanyId(user.company_id);
            }
          }
        } catch (companyError) {
          console.error('Company ID取得エラー:', companyError);
          // authContextからもcompany_idを確認
          if (user?.company_id) {
            setCurrentCompanyId(user.company_id);
          }
        }
      }

      const { SharedDataService } = await import('../services/sharedDataService');
      const data = await SharedDataService.getTokenUsage();
      setTokenUsage(data as any);
    } catch (error: any) {
      console.error('トークン使用量取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPricingInfo = async () => {
    setIsPricingInfoLoading(true);
    try {
      const response = await api.get('/company-pricing-info');
      setPricingInfo(response.data);
    } catch (error) {
      console.error('Error fetching pricing info:', error);
      // エラー時でも最小限のデータを設定
      setPricingInfo({
        company_id: '',
        company_name: 'Error Loading',
        pricing_model: 'error',
        pricing_description: 'エラーが発生しました',
        pricing_table: {},
        cost_examples: {},
        is_premium_customer: false,
        is_premium_plan: false
      });
    } finally {
      setIsPricingInfoLoading(false);
    }
  };

  const fetchMemberUsage = async () => {
    try {
      const response = await api.get('/company-member-usage');
      setMemberUsage(response.data.members || []);
      
      // Premium Planでない場合の料金情報も設定
      if (!response.data.is_premium_plan) {
        setPricingInfo(prev => prev ? ({
          ...prev,
          is_premium_plan: false,
          total_company_cost_jpy: response.data.total_company_cost_jpy || 0
        }) : prev);
      }
    } catch (error) {
      console.error('Error fetching member usage:', error);
    }
  };

  // 料金シミュレーションを実行
  const simulateCost = async (tokens: number, prompts: number = 0) => {
    try {
      setIsSimulating(true);
      const response = await api.post('/simulate-cost-with-prompts', { 
        tokens, 
        prompt_references: prompts 
      });
      setSimulationData(response.data);
    } catch (error: any) {
      console.error('料金シミュレーションエラー:', error);
      // フォールバック：従来のAPIを試す
      try {
        const fallbackResponse = await api.post('/simulate-cost', { tokens });
        setSimulationData({
          ...fallbackResponse.data,
          prompt_references: prompts
        });
      } catch (fallbackError) {
        console.error('フォールバックシミュレーションもエラー:', fallbackError);
      }
    } finally {
      setIsSimulating(false);
    }
  };

  useEffect(() => {
    fetchTokenUsage();
    fetchPricingInfo();
    fetchMemberUsage();
  }, []);

  useEffect(() => {
    simulateCost(simulationTokens, simulationPrompts);
  }, [simulationTokens, simulationPrompts]);

  // 自動更新機能（常に有効）
  useEffect(() => {
    const interval = setInterval(() => {
      fetchTokenUsage();
    }, 30000); // 30秒ごとに更新
    
    return () => {
      clearInterval(interval);
    };
  }, []);

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

  // 専用料金表示コンポーネント - ホワイトテーマ・コンパクト版
  const SpecialPricingDisplay = () => (
    <Box sx={{ 
      background: 'white',
      color: '#1e293b',
      py: 4
    }}>
      <Container maxWidth="md" sx={{ py: 3 }}>
        {/* シンプルなヘッダー */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 600,
              fontSize: { xs: '1.8rem', md: '2.5rem' },
              letterSpacing: '-0.02em',
              mb: 1,
              color: '#1e293b'
            }}
          >
            Premium Plan
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: '#64748b',
              fontSize: '1rem',
              fontWeight: 400
            }}
          >
            株式会社No.1 専用プラン
          </Typography>
        </Box>

        {/* メイン価格カード */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
          <Card
            elevation={0}
            sx={{
              maxWidth: 500,
              width: '100%',
              background: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: 3,
              overflow: 'hidden',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)'
            }}
          >
            <CardContent sx={{ p: 4 }}>
              {/* 価格セクション */}
              <Box sx={{ textAlign: 'center', mb: 4 }}>
                {/* 月額表示 */}
                <Box sx={{ mb: 3 }}>
                  <Typography
                    variant="h2"
                    sx={{
                      fontSize: { xs: '2.5rem', md: '3.5rem' },
                      fontWeight: 700,
                      color: '#0f172a',
                      mb: 0.5,
                      lineHeight: 1
                    }}
                  >
                    ¥30,000
                  </Typography>
                  <Typography
                    sx={{
                      color: '#64748b',
                      fontSize: '1.1rem',
                      fontWeight: 500
                    }}
                  >
                    / 月
                  </Typography>
                </Box>

                {/* 3ヶ月総額 */}
                <Box sx={{
                  background: 'linear-gradient(135deg, #f1f5f9, #e2e8f0)',
                  border: '1px solid #cbd5e1',
                  borderRadius: 2,
                  p: 2.5,
                  mb: 3
                }}>
                  <Typography
                    sx={{
                      color: '#475569',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      mb: 0.5,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em'
                    }}
                  >
                    3ヶ月契約
                  </Typography>
                  <Typography
                    variant="h4"
                    sx={{
                      color: '#0f172a',
                      fontWeight: 600,
                      fontSize: { xs: '1.8rem', md: '2.2rem' },
                      mb: 0.5
                    }}
                  >
                    ¥90,000
                  </Typography>
                  <Typography
                    sx={{
                      color: '#64748b',
                      fontSize: '0.85rem',
                      fontWeight: 500
                    }}
                  >
                    税込・固定料金
                  </Typography>
                </Box>
              </Box>

              {/* 特典リスト - シンプル版 */}
              <Box sx={{ mb: 4 }}>
                <Stack spacing={2}>
                  {[
                    'AI質問・回答 無制限',
                    '専用サポート対応',
                    'プレミアム機能フルアクセス',
                    '3ヶ月間継続利用保証'
                  ].map((feature, index) => (
                    <Box
                      key={index}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        p: 1.5,
                        borderRadius: 1.5,
                        background: '#f8fafc',
                        border: '1px solid #e2e8f0'
                      }}
                    >
                      <Box
                        sx={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                          mr: 2,
                          flexShrink: 0
                        }}
                      />
                      <Typography
                        sx={{
                          color: '#374151',
                          fontSize: '0.95rem',
                          fontWeight: 500
                        }}
                      >
                        {feature}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </Box>

              {/* シンプルなフッター */}
              <Box sx={{ textAlign: 'center', pt: 3, borderTop: '1px solid #e2e8f0' }}>
                <Typography
                  sx={{
                    color: '#64748b',
                    fontSize: '0.85rem',
                    lineHeight: 1.5
                  }}
                >
                  明朗会計・追加料金なし
                  <br />
                  継続利用でさらなる特典をご用意
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* シンプルなコンタクト */}
        <Box sx={{ textAlign: 'center' }}>
          <Typography
            sx={{
              color: '#64748b',
              fontSize: '0.9rem',
              maxWidth: '400px',
              mx: 'auto',
              lineHeight: 1.6
            }}
          >
            ご質問やサポートが必要でしたら
            <br />
            いつでもお気軽にお声がけください
          </Typography>
        </Box>
      </Container>
    </Box>
  );

  // 旧SpecialPricingDisplay条件分岐は削除
  // 新しいPremium Plan判定ロジックを使用

  const No1PremiumPricingDisplay = () => (
    <Box sx={{ 
      background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
      color: 'white',
      py: 6,
      px: 3,
      borderRadius: 3,
      mb: 4,
      boxShadow: '0 8px 32px rgba(0,0,0,0.2)'
    }}>
      <Container maxWidth="lg">
        <Box sx={{ textAlign: 'center', mb: 6 }}>
          <Chip
            icon={<StarIcon />}
            label="Premium Plan"
            sx={{
              background: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
              fontWeight: 'bold',
              fontSize: '1rem',
              mb: 3,
              px: 2,
              py: 1
            }}
          />
          <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 2 }}>
            株式会社No.1 専用プラン
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
            ¥30,000
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9, mb: 2 }}>
            / 月
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
            3ヶ月契約
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 'bold', opacity: 0.9 }}>
            ¥90,000
          </Typography>
          <Typography variant="body1" sx={{ opacity: 0.8, mt: 1 }}>
            税込・固定料金
          </Typography>
        </Box>

        {/* プラン特典 */}
        <Grid container spacing={4} sx={{ mb: 6 }}>
          <Grid item xs={12}>
            <Card sx={{ 
              background: 'rgba(255, 255, 255, 0.95)', 
              color: '#1e293b',
              backdropFilter: 'blur(10px)',
              borderRadius: 3
            }}>
              <CardContent sx={{ p: 4 }}>
                <Typography variant="h5" sx={{ mb: 4, fontWeight: 'bold', textAlign: 'center' }}>
                  プラン特典
                </Typography>
                <Grid container spacing={3}>
                  {pricingInfo?.plan_details?.features?.map((feature: string, index: number) => (
                    <Grid item xs={12} sm={6} key={index}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <CheckIcon sx={{ color: '#4caf50', mr: 2, fontSize: '1.5rem' }} />
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>
                          {feature}
                        </Typography>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
                
                <Divider sx={{ my: 3 }} />
                
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" sx={{ color: '#1976d2', fontWeight: 'bold' }}>
                    継続利用でさらなる特典をご用意
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* 料金体系の説明 */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card sx={{ 
              background: 'rgba(255, 255, 255, 0.95)', 
              color: '#1e293b',
              height: '100%',
              borderRadius: 2
            }}>
              <CardContent sx={{ textAlign: 'center', p: 3 }}>
                <MoneyIcon sx={{ fontSize: '3rem', color: '#4caf50', mb: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                  AI質問・回答 無制限
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  使用量に関係なく追加料金は発生しません
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ 
              background: 'rgba(255, 255, 255, 0.95)', 
              color: '#1e293b',
              height: '100%',
              borderRadius: 2
            }}>
              <CardContent sx={{ textAlign: 'center', p: 3 }}>
                <InfoIcon sx={{ fontSize: '3rem', color: '#2196f3', mb: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                  専用サポート対応
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  優先サポートでお困りごとを迅速に解決
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ 
              background: 'rgba(255, 255, 255, 0.95)', 
              color: '#1e293b',
              height: '100%',
              borderRadius: 2
            }}>
              <CardContent sx={{ textAlign: 'center', p: 3 }}>
                <DiamondIcon sx={{ fontSize: '3rem', color: '#9c27b0', mb: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                  プレミアム機能フルアクセス
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  全ての機能を制限なくご利用いただけます
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Premium Plan vs 従量課金制の比較 */}
        {pricingInfo?.cost_examples?.comparison_with_pay_per_use && (
          <Container maxWidth="lg" sx={{ mt: 4 }}>
            <Card sx={{ 
              background: 'rgba(255, 255, 255, 0.95)', 
              color: '#1e293b',
              borderRadius: 3
            }}>
              <CardContent sx={{ p: 4 }}>
                <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold', textAlign: 'center' }}>
                  💰 従量課金制との比較
                </Typography>
                
                <Grid container spacing={2}>
                  {pricingInfo.cost_examples.comparison_with_pay_per_use.scenarios.map((scenario: any, index: number) => (
                    <Grid item xs={12} sm={6} md={4} key={index}>
                      <Card sx={{ 
                        height: '100%', 
                        border: scenario.difference > 0 ? '2px solid #4caf50' : '1px solid rgba(0, 0, 0, 0.12)',
                        position: 'relative'
                      }}>
                        {scenario.difference > 0 && (
                          <Box sx={{ 
                            position: 'absolute', 
                            top: -8, 
                            right: 8, 
                            backgroundColor: '#4caf50', 
                            color: 'white', 
                            px: 1, 
                            py: 0.5, 
                            borderRadius: 1,
                            fontSize: '0.75rem',
                            fontWeight: 600
                          }}>
                            お得！
                          </Box>
                        )}
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                            月{scenario.monthly_questions}回利用
                          </Typography>
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="body2" color="text.secondary" sx={{ textDecoration: 'line-through' }}>
                              従量課金: ¥{scenario.pay_per_use_cost.toLocaleString()}
                            </Typography>
                            <Typography variant="h6" sx={{ fontWeight: 700, color: '#1976d2' }}>
                              Premium: ¥30,000
                            </Typography>
                          </Box>
                          <Chip 
                            label={scenario.difference > 0 ? `¥${scenario.difference.toLocaleString()}お得` : scenario.recommendation}
                            color={scenario.difference > 0 ? 'success' : 'default'}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>

                <Box sx={{ mt: 3, p: 2, backgroundColor: 'rgba(76, 175, 80, 0.05)', borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                    💡 <strong>月1,000回以上のご利用でPremium Planがお得になります！</strong>
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Container>
        )}
      </Container>
    </Box>
  );

  const PayPerUseSummary = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            従量課金制 - 料金サマリー
          </Typography>
          <Chip
            label="Pay Per Use"
            color="primary"
            sx={{ fontWeight: 'bold' }}
          />
        </Box>
        
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                {memberUsage.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                アクティブメンバー
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#ff9800' }}>
                {memberUsage.reduce((sum, member) => sum + member.conversations, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                総会話数
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#4caf50' }}>
                {memberUsage.reduce((sum, member) => sum + member.total_tokens, 0).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                総使用トークン
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#f44336' }}>
                ¥{memberUsage.reduce((sum, member) => sum + member.cost_jpy, 0).toFixed(2)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                総課金額
              </Typography>
            </Box>
          </Grid>
        </Grid>
        
        <Box sx={{ mt: 3, p: 2, backgroundColor: 'rgba(25, 118, 210, 0.05)', borderRadius: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
            <InfoIcon sx={{ color: '#1976d2', mr: 1, fontSize: '1.2rem' }} />
            <strong>従量課金制</strong>: 使用したトークン数に応じて料金が発生します
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );

  const MemberUsageDisplay = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            メンバー別使用状況
          </Typography>
          {pricingInfo?.is_premium_plan && (
            <Chip
              label="Premium Plan - 追加料金なし"
              color="success"
              sx={{ fontWeight: 'bold' }}
            />
          )}
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>メンバー名</TableCell>
                <TableCell>メールアドレス</TableCell>
                <TableCell align="right">会話数</TableCell>
                <TableCell align="right">総トークン</TableCell>
                <TableCell align="right">
                  {pricingInfo?.is_premium_plan ? '追加コスト' : 'コスト (JPY)'}
                </TableCell>
                <TableCell align="right">
                  {pricingInfo?.is_premium_plan ? '1会話あたり' : '1会話あたり平均'}
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {memberUsage.map((member) => (
                <TableRow key={member.member_id}>
                  <TableCell>{member.member_name}</TableCell>
                  <TableCell>{member.member_email}</TableCell>
                  <TableCell align="right">{member.conversations}</TableCell>
                  <TableCell align="right">{member.total_tokens.toLocaleString()}</TableCell>
                  <TableCell align="right">
                    {pricingInfo?.is_premium_plan ? (
                      <Chip label="¥0" color="success" size="small" />
                    ) : (
                      `¥${member.cost_jpy.toFixed(2)}`
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {pricingInfo?.is_premium_plan ? (
                      <Chip label="¥0" color="success" size="small" />
                    ) : (
                      `¥${member.avg_cost_per_conversation.toFixed(2)}`
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        
        {pricingInfo?.is_premium_plan && (
          <Box sx={{ mt: 3, p: 2, backgroundColor: 'rgba(76, 175, 80, 0.05)', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
              <CheckIcon sx={{ color: '#4caf50', mr: 1, fontSize: '1.2rem' }} />
              <strong>Premium Plan</strong>: 月額固定¥30,000で全メンバーの利用が無制限です
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  if (isLoading || isPricingInfoLoading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>料金情報を読み込み中...</Typography>
      </Box>
    );
  }

  return (
    <Fade in={true} timeout={400}>
      <Box>
        
        
        {/* no1株式会社専用表示 */}
        {pricingInfo?.is_premium_plan === true ? (
          <>
            <No1PremiumPricingDisplay />
            <MemberUsageDisplay />
          </>
        ) : (
          // no1以外の会社：従量課金制の詳細表示
          <>
            <PayPerUseSummary />
            <MemberUsageDisplay />
            
            {/* 従量課金制用のヘッダー */}
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

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label="自動更新中"
              color="primary"
              size="small"
              sx={{ fontWeight: 600 }}
            />
          </Box>
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

                  {/* 使用量詳細 */}
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={12} sm={4}>
                      <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(103, 58, 183, 0.05)', borderRadius: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
                          {formatTokens(tokenUsage.input_tokens_total || 0)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Input トークン
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(156, 39, 176, 0.05)', borderRadius: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, color: 'secondary.main' }}>
                          {formatTokens(tokenUsage.output_tokens_total || 0)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Output トークン
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(255, 193, 7, 0.05)', borderRadius: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, color: 'warning.main' }}>
                          {formatNumber(tokenUsage.prompt_references_total || 0)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          プロンプト参照
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>

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
                          {formatCurrency(tokenUsage.cost_breakdown.base_cost || tokenUsage.cost_breakdown.basic_plan)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          基本料金
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(255, 193, 7, 0.05)', borderRadius: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {formatCurrency(tokenUsage.cost_breakdown.prompt_cost || 0)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          プロンプト料金
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
                    sx={{ mb: 2 }}
                  />

                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        label="トークン数（M tokens）"
                        type="number"
                        value={simulationTokens / 1000000}
                        onChange={(e) => setSimulationTokens(parseFloat(e.target.value) * 1000000 || 0)}
                        variant="outlined"
                        size="small"
                        fullWidth
                        inputProps={{ step: 0.1, min: 0 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        label="プロンプト参照数"
                        type="number"
                        value={simulationPrompts}
                        onChange={(e) => setSimulationPrompts(parseInt(e.target.value) || 0)}
                        variant="outlined"
                        size="small"
                        fullWidth
                        inputProps={{ step: 1, min: 0 }}
                      />
                    </Grid>
                  </Grid>

                  {simulationData && (
                    <Box sx={{ p: 2, backgroundColor: 'rgba(156, 39, 176, 0.05)', borderRadius: 2 }}>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: 'secondary.main', mb: 1 }}>
                        {formatCurrency(simulationData.cost_breakdown.total_cost)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        月額料金（{simulationData.tokens_in_millions.toFixed(1)}M tokens + {simulationData.prompt_references}回参照）
                      </Typography>
                      
                      <Grid container spacing={1} sx={{ mb: 2 }}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            基本料金: {formatCurrency(simulationData.cost_breakdown.base_cost || 0)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            プロンプト料金: {formatCurrency(simulationData.cost_breakdown.prompt_cost || 0)}
                          </Typography>
                        </Grid>
                      </Grid>
                      
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
                          <TableCell><strong>項目</strong></TableCell>
                          <TableCell><strong>単価</strong></TableCell>
                          <TableCell><strong>説明</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>Input トークン</TableCell>
                          <TableCell>¥0.100/1,000tokens</TableCell>
                          <TableCell>ユーザーからの質問</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Output トークン</TableCell>
                          <TableCell>¥0.900/1,000tokens</TableCell>
                          <TableCell>AIからの回答</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>プロンプト参照</TableCell>
                          <TableCell>¥0.50/回</TableCell>
                          <TableCell>知識ベース参照</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>

                  <Box sx={{ mt: 2, p: 2, backgroundColor: 'rgba(76, 175, 80, 0.05)', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      💡 <strong>新料金体系の特徴:</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      • Input ¥0.100、Output ¥0.900 per 1,000 tokens
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      • プロンプト参照（知識ベース）¥0.50/回で追加料金
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • 使った分だけの従量課金制
                    </Typography>
                  </Box>

                  {/* 詳細な料金例 */}
                  {pricingInfo?.cost_examples?.detailed_scenarios && (
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                        📊 利用例と料金
                      </Typography>
                      
                      {pricingInfo.cost_examples.detailed_scenarios.map((scenario: any, index: number) => (
                        <Card key={index} sx={{ mb: 2, border: '1px solid rgba(0, 0, 0, 0.12)' }}>
                          <CardContent sx={{ pb: 2 }}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                              {scenario.category}
                            </Typography>
                            
                            {scenario.examples.map((example: any, exIndex: number) => (
                              <Box key={exIndex} sx={{ 
                                mb: 1.5, 
                                p: 2, 
                                backgroundColor: 'rgba(0, 0, 0, 0.02)', 
                                borderRadius: 1,
                                border: '1px solid rgba(0, 0, 0, 0.05)'
                              }}>
                                <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
                                  {example.question}
                                </Typography>
                                <Grid container spacing={2} alignItems="center">
                                  <Grid item xs={12} sm={6}>
                                    <Typography variant="caption" color="text.secondary">
                                      入力: {example.input_tokens}トークン / 出力: {example.output_tokens}トークン
                                      {example.prompt_references && ` / 知識ベース: ${example.prompt_references}回`}
                                    </Typography>
                                  </Grid>
                                  <Grid item xs={12} sm={6} sx={{ textAlign: { sm: 'right' } }}>
                                    <Chip 
                                      label={`¥${example.cost_jpy.toFixed(3)}`}
                                      color="primary" 
                                      size="small" 
                                      sx={{ fontWeight: 600 }}
                                    />
                                  </Grid>
                                </Grid>
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                                  内訳: {example.cost_breakdown}
                                </Typography>
                              </Box>
                            ))}
                          </CardContent>
                        </Card>
                      ))}
                    </Box>
                  )}


                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
            </>
        )}
      </Box>
    </Fade>
  );
};

export default BillingTab; 