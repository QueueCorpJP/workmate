import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Paper,
  Stack,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Collapse,
  IconButton,
  Grid,
  Tab,
  Tabs,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import HistoryIcon from "@mui/icons-material/History";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import BusinessIcon from "@mui/icons-material/Business";
import PeopleIcon from "@mui/icons-material/People";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import api from "../../api";
import { formatDate } from "./utils";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";
import { useAuth } from "../../contexts/AuthContext";

interface PlanHistoryItem {
  id: string;
  user_id: string;
  user_name?: string;
  user_email?: string;
  from_plan: string;
  to_plan: string;
  changed_at: string;
  duration_days: number | null;
}

interface UserPlanHistory {
  user_id: string;
  user_name?: string;
  user_email?: string;
  company_id?: string;
  current_plan: string;
  latest_change: string;
  total_changes: number;
  changes: {
    id: string;
    from_plan: string;
    to_plan: string;
    changed_at: string;
    duration_days: number | null;
  }[];
}

interface AnalyticsData {
  company_usage_periods: Array<{
    company_name: string;
    user_count: number;
    usage_days: number;
    start_date: string;
    usage_months: number;
  }>;
  user_usage_periods: Array<{
    user_id: string;
    email: string;
    name: string;
    company_name: string;
    usage_days: number;
    start_date: string;
    usage_months: number;
  }>;
  active_users: {
    total_active_users: number;
    active_users_by_company: { [key: string]: number };
    active_users_list: Array<{
      user_id: string;
      name: string;
      company_name: string;
      chat_count: number;
      last_chat: string;
    }>;
    analysis_period: string;
  };
  plan_continuity: {
    total_users: number;
    continuity_stats: {
      never_changed: number;
      changed_once: number;
      changed_multiple: number;
      demo_to_prod_stayed: number;
      prod_to_demo_returned: number;
    };
    plan_retention: {
      demo_users: number;
      production_users: number;
      demo_avg_duration: number;
      production_avg_duration: number;
    };
    duration_analysis: {
      demo_duration_samples: number;
      production_duration_samples: number;
    };
  };
}

interface PlanHistoryTabProps {
  // 必要に応じてプロパティを追加
}

const PlanHistoryTab: React.FC<PlanHistoryTabProps> = () => {
  const { user } = useAuth();
  const [userPlanHistories, setUserPlanHistories] = useState<UserPlanHistory[]>([]);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [currentTab, setCurrentTab] = useState(0);
  
  // 管理者用の特別表示判定
  const isAdmin = user?.role === "admin" || user?.email === "queue@queueu-tech.jp" || user?.email === "queue@queuefood.co.jp";

  const fetchPlanHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      console.log("プラン履歴を取得中...");
      const response = await api.get("/plan-history");
      console.log("プラン履歴取得結果:", response.data);
      
      if (response.data && response.data.success && response.data.data) {
        if (response.data.data.users) {
          setUserPlanHistories(response.data.data.users);
        }
        
        // 管理者用の分析データを設定
        if (isAdmin && response.data.data.analytics) {
          setAnalyticsData(response.data.data.analytics);
        }
      } else {
        setUserPlanHistories([]);
        setAnalyticsData(null);
      }
    } catch (error) {
      console.error("プラン履歴の取得に失敗しました:", error);
      setError("プラン履歴の取得に失敗しました");
      setUserPlanHistories([]);
      setAnalyticsData(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPlanHistory();
  }, []);

  const getPlanDisplayName = (plan: string) => {
    switch (plan) {
      case "demo":
        return "デモ版";
      case "production":
        return "本番版";
      case "starter":
        return "スタータープラン";
      case "business":
        return "ビジネスプラン";
      case "enterprise":
        return "エンタープライズプラン";
      default:
        return plan;
    }
  };

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case "demo":
        return "warning";
      case "production":
        return "success";
      case "starter":
        return "info";
      case "business":
        return "primary";
      case "enterprise":
        return "secondary";
      default:
        return "default";
    }
  };

  const getChangeIcon = (fromPlan: string, toPlan: string) => {
    if (fromPlan === "demo" && toPlan === "production") {
      return <TrendingUpIcon color="success" />;
    } else if (fromPlan === "production" && toPlan === "demo") {
      return <TrendingDownIcon color="warning" />;
    }
    return <HistoryIcon color="primary" />;
  };

  const formatDuration = (durationDays: number | null) => {
    if (!durationDays) return "期間不明";
    if (durationDays === 1) return "1日間";
    if (durationDays < 7) return `${durationDays}日間`;
    if (durationDays < 30) {
      const weeks = Math.floor(durationDays / 7);
      const days = durationDays % 7;
      return days > 0 ? `${weeks}週間${days}日間` : `${weeks}週間`;
    }
    const months = Math.floor(durationDays / 30);
    const remainingDays = durationDays % 30;
    return remainingDays > 0 ? `${months}ヶ月${remainingDays}日間` : `${months}ヶ月間`;
  };

  const formatDetailedDuration = (durationDays: number | null) => {
    if (!durationDays) return "期間不明";
    
    const years = Math.floor(durationDays / 365);
    const months = Math.floor((durationDays % 365) / 30);
    const weeks = Math.floor(((durationDays % 365) % 30) / 7);
    const days = ((durationDays % 365) % 30) % 7;
    
    const parts = [];
    if (years > 0) parts.push(`${years}年`);
    if (months > 0) parts.push(`${months}ヶ月`);
    if (weeks > 0) parts.push(`${weeks}週間`);
    if (days > 0) parts.push(`${days}日間`);
    
    if (parts.length === 0) return "1日未満";
    return `${parts.join('')} (合計${durationDays}日間)`;
  };

  const formatRelativeTime = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return "1日前";
    if (diffDays < 7) return `${diffDays}日前`;
    if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7);
      return `${weeks}週間前`;
    }
    if (diffDays < 365) {
      const months = Math.floor(diffDays / 30);
      return `${months}ヶ月前`;
    }
    const years = Math.floor(diffDays / 365);
    return `${years}年前`;
  };

  const calculateStatistics = () => {
    const allChanges: PlanHistoryItem[] = [];
    userPlanHistories.forEach(user => {
      user.changes.forEach(change => {
        allChanges.push({
          id: change.id,
          user_id: user.user_id,
          user_name: user.user_name,
          user_email: user.user_email,
          from_plan: change.from_plan,
          to_plan: change.to_plan,
          changed_at: change.changed_at,
          duration_days: change.duration_days
        });
      });
    });

    const demoToProd = allChanges.filter(item => item.from_plan === "demo" && item.to_plan === "production");
    const prodToDemo = allChanges.filter(item => item.from_plan === "production" && item.to_plan === "demo");
    
    const demoToProdDurations = demoToProd.filter(item => item.duration_days).map(item => item.duration_days!);
    const avgDemoUsage = demoToProdDurations.length > 0 
      ? Math.round(demoToProdDurations.reduce((sum, days) => sum + days, 0) / demoToProdDurations.length)
      : null;
    
    const prodToDemoDurations = prodToDemo.filter(item => item.duration_days).map(item => item.duration_days!);
    const avgProdUsage = prodToDemoDurations.length > 0
      ? Math.round(prodToDemoDurations.reduce((sum, days) => sum + days, 0) / prodToDemoDurations.length)
      : null;

    const totalPlanUsageDays = allChanges
      .filter(item => item.duration_days)
      .reduce((total, item) => total + item.duration_days!, 0);

    return {
      demoToProdCount: demoToProd.length,
      prodToDemoCount: prodToDemo.length,
      avgDemoUsage,
      avgProdUsage,
      totalPlanUsageDays,
      totalUsers: userPlanHistories.length,
      totalChanges: allChanges.length
    };
  };

  const getCurrentPlanDuration = (user: UserPlanHistory) => {
    if (user.changes.length === 0) return null;
    
    const latestChange = user.changes[0];
    const now = new Date();
    const changeDate = new Date(latestChange.changed_at);
    const daysSinceChange = Math.floor((now.getTime() - changeDate.getTime()) / (1000 * 60 * 60 * 24));
    
    return {
      currentPlan: latestChange.to_plan,
      daysSinceChange
    };
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const toggleRowExpansion = (userId: string) => {
    const newExpandedRows = new Set(expandedRows);
    if (expandedRows.has(userId)) {
      newExpandedRows.delete(userId);
    } else {
      newExpandedRows.add(userId);
    }
    setExpandedRows(newExpandedRows);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  // 分析データ表示用のコンポーネント
  const renderAnalytics = () => {
    if (!analyticsData) return null;

    return (
      <Box>
        <Tabs value={currentTab} onChange={handleTabChange} sx={{ mb: 3 }}>
          <Tab label="プラン履歴" icon={<HistoryIcon />} />
          <Tab label="会社別利用期間" icon={<BusinessIcon />} />
          <Tab label="管理者別利用期間" icon={<PeopleIcon />} />
          <Tab label="アクティブ管理者" icon={<AnalyticsIcon />} />
          <Tab label="プラン継続性分析" icon={<TrendingUpIcon />} />
        </Tabs>

        {currentTab === 1 && (
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                会社別累計利用期間
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.50' }}>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>会社名</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>管理者数</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>利用期間</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>開始日</Typography></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analyticsData.company_usage_periods.map((company, index) => (
                      <TableRow key={index} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <BusinessIcon sx={{ mr: 1, color: 'primary.main' }} />
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {company.company_name}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {company.user_count}名
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {company.usage_months}ヶ月
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ({company.usage_days}日間)
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(company.start_date)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        )}

        {currentTab === 2 && (
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                管理者別累計利用期間
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.50' }}>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>管理者</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>会社</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>利用期間</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>開始日</Typography></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analyticsData.user_usage_periods.slice(0, 50).map((user, index) => (
                      <TableRow key={index} hover>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {user.name || user.email.split('@')[0]}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {user.email}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {user.company_name || user.email.split('@')[1]}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {user.usage_months}ヶ月
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ({user.usage_days}日間)
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(user.start_date)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        )}

        {currentTab === 3 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                    アクティブ管理者概要
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {analyticsData.active_users.analysis_period}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <PeopleIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
                        {analyticsData.active_users.total_active_users}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        アクティブ管理者
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                    会社別アクティブ管理者
                  </Typography>
                  <List>
                    {Object.entries(analyticsData.active_users.active_users_by_company).map(([company, count]) => (
                      <ListItem key={company}>
                        <ListItemIcon>
                          <BusinessIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={company}
                          secondary={`${count}名がアクティブ`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {currentTab === 4 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                    プラン変更パターン
                  </Typography>
                  <Stack spacing={2}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">変更なし</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {analyticsData.plan_continuity.continuity_stats.never_changed}名
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">1回変更</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {analyticsData.plan_continuity.continuity_stats.changed_once}名
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">複数回変更</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {analyticsData.plan_continuity.continuity_stats.changed_multiple}名
                      </Typography>
                    </Box>
                    <Divider />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="success.main">デモ→本番継続</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                        {analyticsData.plan_continuity.continuity_stats.demo_to_prod_stayed}名
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="warning.main">本番→デモ戻り</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'warning.main' }}>
                        {analyticsData.plan_continuity.continuity_stats.prod_to_demo_returned}名
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                    プラン保持状況
                  </Typography>
                  <Stack spacing={2}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">デモ版管理者</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'warning.main' }}>
                        {analyticsData.plan_continuity.plan_retention.demo_users}名
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">本番版管理者</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                        {analyticsData.plan_continuity.plan_retention.production_users}名
                      </Typography>
                    </Box>
                    <Divider />
                    {analyticsData.plan_continuity.plan_retention.demo_avg_duration > 0 && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">デモ版平均利用期間</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {Math.round(analyticsData.plan_continuity.plan_retention.demo_avg_duration)}日
                        </Typography>
                      </Box>
                    )}
                    {analyticsData.plan_continuity.plan_retention.production_avg_duration > 0 && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">本番版平均利用期間</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {Math.round(analyticsData.plan_continuity.plan_retention.production_avg_duration)}日
                        </Typography>
                      </Box>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </Box>
    );
  };

  if (isLoading) {
    return <LoadingIndicator message="プラン履歴を読み込み中..." />;
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchPlanHistory}
        >
          再試行
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* ヘッダー */}
      <Box
        sx={{
          mb: 3,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          {isAdmin ? "利用状況分析・プラン履歴" : "プラン変更履歴"}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchPlanHistory}
          disabled={isLoading}
        >
          更新
        </Button>
      </Box>

              {/* 管理者用の分析表示 */}
        {isAdmin && analyticsData && renderAnalytics()}

        {/* 通常のプラン履歴表示（管理者の場合はタブ0の時のみ） */}
              {(!isAdmin || currentTab === 0) && (
        <Box>
          {/* プラン履歴テーブル */}
          {userPlanHistories.length === 0 ? (
            <EmptyState
              icon="custom"
              customIcon={<HistoryIcon sx={{ fontSize: '4rem', color: 'text.secondary' }} />}
              message="プラン変更履歴がありません。まだプランの変更が行われていません。"
            />
          ) : (
            <Card>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.50' }}>
                      <TableCell></TableCell>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>管理者</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>現在のプラン</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>変更回数</Typography></TableCell>
                      <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>最終変更日</Typography></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {userPlanHistories
                      .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                      .map((user) => (
                        <React.Fragment key={user.user_id}>
                          <TableRow 
                            hover 
                            sx={{ 
                              cursor: 'pointer',
                              '&:hover': { bgcolor: 'grey.50' }
                            }}
                          >
                            <TableCell>
                              <IconButton
                                size="small"
                                onClick={() => toggleRowExpansion(user.user_id)}
                              >
                                {expandedRows.has(user.user_id) ? 
                                  <KeyboardArrowUpIcon /> : 
                                  <KeyboardArrowDownIcon />
                                }
                              </IconButton>
                            </TableCell>
                            <TableCell>
                              <Box>
                                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                  {user.user_name || "管理者"}
                                </Typography>
                                {user.user_email && (
                                  <Typography variant="caption" color="text.secondary">
                                    {user.user_email}
                                  </Typography>
                                )}
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={getPlanDisplayName(user.current_plan)}
                                color={getPlanColor(user.current_plan) as any}
                                size="small"
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {user.total_changes}回
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {formatRelativeTime(user.latest_change)}
                              </Typography>
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell sx={{ py: 0 }} colSpan={5}>
                              <Collapse in={expandedRows.has(user.user_id)} timeout="auto" unmountOnExit>
                                <Box sx={{ py: 2, px: 2, bgcolor: 'grey.25' }}>
                                  <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                                    変更履歴詳細
                                  </Typography>
                                  <Table size="small">
                                    <TableHead>
                                      <TableRow>
                                        <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>変更前</Typography></TableCell>
                                        <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>変更後</Typography></TableCell>
                                        <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>変更日時</Typography></TableCell>
                                        <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>利用期間</Typography></TableCell>
                                      </TableRow>
                                    </TableHead>
                                    <TableBody>
                                      {user.changes.map((change, changeIndex) => (
                                        <TableRow key={change.id}>
                                          <TableCell>
                                            <Chip
                                              label={getPlanDisplayName(change.from_plan)}
                                              color={getPlanColor(change.from_plan) as any}
                                              size="small"
                                              variant="outlined"
                                            />
                                          </TableCell>
                                          <TableCell>
                                            <Stack direction="row" spacing={1} alignItems="center">
                                              {getChangeIcon(change.from_plan, change.to_plan)}
                                              <Chip
                                                label={getPlanDisplayName(change.to_plan)}
                                                color={getPlanColor(change.to_plan) as any}
                                                size="small"
                                              />
                                            </Stack>
                                          </TableCell>
                                          <TableCell>
                                            <Tooltip title={`詳細: ${formatDate(change.changed_at)}`}>
                                              <Typography variant="caption">
                                                {formatRelativeTime(change.changed_at)}
                                              </Typography>
                                            </Tooltip>
                                          </TableCell>
                                          <TableCell>
                                            <Typography variant="caption">
                                              {change.duration_days ? 
                                                formatDetailedDuration(change.duration_days) : 
                                                "期間不明"
                                              }
                                            </Typography>
                                            {changeIndex === 0 && (() => {
                                              const currentPlanInfo = getCurrentPlanDuration(user);
                                              if (currentPlanInfo) {
                                                return (
                                                  <Typography variant="caption" color="primary.main" sx={{ display: 'block', fontWeight: 500 }}>
                                                    現在: {formatDetailedDuration(currentPlanInfo.daysSinceChange)}
                                                  </Typography>
                                                );
                                              }
                                              return null;
                                            })()}
                                          </TableCell>
                                        </TableRow>
                                      ))}
                                    </TableBody>
                                  </Table>
                                </Box>
                              </Collapse>
                            </TableCell>
                          </TableRow>
                        </React.Fragment>
                      ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                rowsPerPageOptions={[5, 10, 25]}
                component="div"
                count={userPlanHistories.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
                labelRowsPerPage="ページ当たりの行数:"
                labelDisplayedRows={({ from, to, count }) => `${from}–${to} / ${count !== -1 ? count : `more than ${to}`}`}
              />
            </Card>
          )}
        </Box>
      )}

      {/* 基本統計情報（管理者でない場合のみ表示） */}
      {(userPlanHistories.length > 0 && !isAdmin) && (
        <Paper sx={{ mt: 3, p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            統計情報
          </Typography>
          {(() => {
            const stats = calculateStatistics();
            return (
              <Stack spacing={3}>
                {/* 基本統計 */}
                <Stack direction="row" spacing={3} flexWrap="wrap">
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      総変更回数
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 600 }}>
                      {stats.totalChanges}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      対象管理者数
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 600 }}>
                      {stats.totalUsers}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      デモ→本番への変更
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 600, color: "success.main" }}>
                      {stats.demoToProdCount}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      本番→デモへの変更
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 600, color: "warning.main" }}>
                      {stats.prodToDemoCount}
                    </Typography>
                  </Box>
                </Stack>

                <Divider />

                {/* 利用期間統計 */}
                <Stack direction="row" spacing={3} flexWrap="wrap">
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      累計利用期間
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {formatDetailedDuration(stats.totalPlanUsageDays)}
                    </Typography>
                  </Box>
                  {stats.avgDemoUsage && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        デモ版平均利用期間
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: "warning.main" }}>
                        {formatDetailedDuration(stats.avgDemoUsage)}
                      </Typography>
                    </Box>
                  )}
                  {stats.avgProdUsage && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        本番版平均利用期間
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: "success.main" }}>
                        {formatDetailedDuration(stats.avgProdUsage)}
                      </Typography>
                    </Box>
                  )}
                </Stack>

                {/* 効率性指標 */}
                {stats.demoToProdCount > 0 && (
                  <>
                    <Divider />
                    <Stack direction="row" spacing={3} flexWrap="wrap">
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          本番移行率
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 600, color: "info.main" }}>
                          {Math.round((stats.demoToProdCount / (stats.demoToProdCount + stats.prodToDemoCount)) * 100)}%
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          管理者あたり平均変更回数
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {(stats.totalChanges / stats.totalUsers).toFixed(1)}回
                        </Typography>
                      </Box>
                    </Stack>
                  </>
                )}
              </Stack>
            );
          })()}
        </Paper>
      )}
    </Box>
  );
};

export default PlanHistoryTab;