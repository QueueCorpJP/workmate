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
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import HistoryIcon from "@mui/icons-material/History";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import api from "../../api";
import { formatDate } from "./utils";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";

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

interface PlanHistoryTabProps {
  // 必要に応じてプロパティを追加
}

const PlanHistoryTab: React.FC<PlanHistoryTabProps> = () => {
  const [planHistory, setPlanHistory] = useState<PlanHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPlanHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      console.log("プラン履歴を取得中...");
      const response = await api.get("/plan-history");
      console.log("プラン履歴取得結果:", response.data);
      
      if (response.data && response.data.history) {
        setPlanHistory(response.data.history);
      } else {
        setPlanHistory([]);
      }
    } catch (error) {
      console.error("プラン履歴の取得に失敗しました:", error);
      setError("プラン履歴の取得に失敗しました");
      setPlanHistory([]);
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
    const demoToProd = planHistory.filter(item => item.from_plan === "demo" && item.to_plan === "production");
    const prodToDemo = planHistory.filter(item => item.from_plan === "production" && item.to_plan === "demo");
    
    const demoToProdDurations = demoToProd.filter(item => item.duration_days).map(item => item.duration_days!);
    const avgDemoUsage = demoToProdDurations.length > 0 
      ? Math.round(demoToProdDurations.reduce((sum, days) => sum + days, 0) / demoToProdDurations.length)
      : null;
    
    const prodToDemoDurations = prodToDemo.filter(item => item.duration_days).map(item => item.duration_days!);
    const avgProdUsage = prodToDemoDurations.length > 0
      ? Math.round(prodToDemoDurations.reduce((sum, days) => sum + days, 0) / prodToDemoDurations.length)
      : null;

    const totalPlanUsageDays = planHistory
      .filter(item => item.duration_days)
      .reduce((total, item) => total + item.duration_days!, 0);

    return {
      demoToProdCount: demoToProd.length,
      prodToDemoCount: prodToDemo.length,
      avgDemoUsage,
      avgProdUsage,
      totalPlanUsageDays,
      totalUsers: new Set(planHistory.map(item => item.user_id)).size
    };
  };

  const getCurrentPlanDuration = (userId: string) => {
    const userChanges = planHistory
      .filter(item => item.user_id === userId)
      .sort((a, b) => new Date(b.changed_at).getTime() - new Date(a.changed_at).getTime());
    
    if (userChanges.length === 0) return null;
    
    const latestChange = userChanges[0];
    const now = new Date();
    const changeDate = new Date(latestChange.changed_at);
    const daysSinceChange = Math.floor((now.getTime() - changeDate.getTime()) / (1000 * 60 * 60 * 24));
    
    return {
      currentPlan: latestChange.to_plan,
      daysSinceChange
    };
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
          プラン変更履歴
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

      {/* プラン履歴リスト */}
      {planHistory.length === 0 ? (
        <EmptyState
          icon="custom"
          customIcon={<HistoryIcon sx={{ fontSize: '4rem', color: 'text.secondary' }} />}
          message="プラン変更履歴がありません。まだプランの変更が行われていません。"
        />
      ) : (
        <Card>
          <CardContent sx={{ p: 0 }}>
            <List sx={{ py: 0 }}>
              {planHistory.map((item, index) => (
                <React.Fragment key={item.id}>
                  <ListItem
                    sx={{
                      py: 2,
                      px: 3,
                      "&:hover": {
                        bgcolor: "rgba(0, 0, 0, 0.02)",
                      },
                    }}
                  >
                    <ListItemIcon>
                      {getChangeIcon(item.from_plan, item.to_plan)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Typography variant="body1" sx={{ fontWeight: 600 }}>
                            {item.user_name || item.user_email || "ユーザー"}
                          </Typography>
                          {item.user_email && item.user_name && (
                            <Typography variant="body2" color="text.secondary">
                              ({item.user_email})
                            </Typography>
                          )}
                        </Stack>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                            <Chip
                              label={getPlanDisplayName(item.from_plan)}
                              color={getPlanColor(item.from_plan) as any}
                              size="small"
                              variant="outlined"
                            />
                            <Typography variant="body2" color="text.secondary">
                              →
                            </Typography>
                            <Chip
                              label={getPlanDisplayName(item.to_plan)}
                              color={getPlanColor(item.to_plan) as any}
                              size="small"
                            />
                          </Stack>
                          <Stack direction="column" spacing={0.5}>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <AccessTimeIcon sx={{ fontSize: '0.875rem', color: 'text.secondary' }} />
                              <Tooltip title={`詳細: ${formatDate(item.changed_at)}`}>
                                <Typography variant="body2" color="text.secondary">
                                  {formatRelativeTime(item.changed_at)}に変更
                                </Typography>
                              </Tooltip>
                            </Stack>
                            {item.duration_days && (
                              <Typography variant="body2" color="text.secondary" sx={{ pl: 2.5 }}>
                                📅 {getPlanDisplayName(item.from_plan)}利用期間: {formatDetailedDuration(item.duration_days)}
                              </Typography>
                            )}
                            {(() => {
                              const currentPlanInfo = getCurrentPlanDuration(item.user_id);
                              const isLastChange = planHistory
                                .filter(change => change.user_id === item.user_id)
                                .sort((a, b) => new Date(b.changed_at).getTime() - new Date(a.changed_at).getTime())[0]?.id === item.id;
                              
                              if (isLastChange && currentPlanInfo) {
                                return (
                                  <Typography variant="body2" color="primary.main" sx={{ pl: 2.5, fontWeight: 500 }}>
                                    🔄 現在{getPlanDisplayName(currentPlanInfo.currentPlan)}: {formatDetailedDuration(currentPlanInfo.daysSinceChange)}
                                  </Typography>
                                );
                              }
                              return null;
                            })()}
                          </Stack>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < planHistory.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* 統計情報 */}
      {planHistory.length > 0 && (
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
                      {planHistory.length}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      対象ユーザー数
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
                          ユーザーあたり平均変更回数
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {(planHistory.length / stats.totalUsers).toFixed(1)}回
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