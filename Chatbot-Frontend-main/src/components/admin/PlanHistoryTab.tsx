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
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import HistoryIcon from "@mui/icons-material/History";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
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
                          <Stack direction="row" spacing={2} alignItems="center">
                            <Typography variant="body2" color="text.secondary">
                              変更日時: {formatDate(item.changed_at)}
                            </Typography>
                            {item.duration_days && (
                              <Typography variant="body2" color="text.secondary">
                                利用期間: {formatDuration(item.duration_days)}
                              </Typography>
                            )}
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
          <Stack direction="row" spacing={3}>
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
                デモ→本番への変更
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600, color: "success.main" }}>
                {planHistory.filter(item => item.from_plan === "demo" && item.to_plan === "production").length}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                本番→デモへの変更
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600, color: "warning.main" }}>
                {planHistory.filter(item => item.from_plan === "production" && item.to_plan === "demo").length}
              </Typography>
            </Box>
          </Stack>
        </Paper>
      )}
    </Box>
  );
};

export default PlanHistoryTab;