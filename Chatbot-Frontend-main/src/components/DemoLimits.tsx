import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  LinearProgress,
  Tooltip,
  Alert,
  Snackbar,
  useTheme,
  useMediaQuery,
  Chip,
  Fade,
  Button,
  IconButton,
  Badge,
  Drawer,
  Stack,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  Divider,
} from "@mui/material";
import ErrorIcon from "@mui/icons-material/Error";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import InfoIcon from "@mui/icons-material/Info";
import CloseIcon from "@mui/icons-material/Close";
import BarChartIcon from "@mui/icons-material/BarChart";
import UpgradeIcon from "@mui/icons-material/Upgrade";
import HistoryIcon from "@mui/icons-material/History";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import { useAuth } from "../contexts/AuthContext";
import ApplicationForm from "./ApplicationForm";
import api from "../api";

interface DemoLimitsProps {
  showTitle?: boolean;
  remainingQuestions?: number | null;
  showAlert?: boolean;
  onCloseAlert?: () => void;
}

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

const DemoLimits: React.FC<DemoLimitsProps> = ({
  showTitle = true,
  remainingQuestions: propRemainingQuestions,
  showAlert = false,
  onCloseAlert,
}) => {
  const {
    remainingQuestions: authRemainingQuestions,
    remainingUploads,
    isUnlimited,
    refreshUserData,
    user,
  } = useAuth();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isTablet = useMediaQuery(theme.breakpoints.between("sm", "md"));
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const [animate, setAnimate] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [applicationOpen, setApplicationOpen] = useState(false);
  const [upgradeSuccess, setUpgradeSuccess] = useState(false);
  const [planHistory, setPlanHistory] = useState<PlanHistoryItem[]>([]);
  const [isPlanHistoryLoading, setIsPlanHistoryLoading] = useState(false);

  useEffect(() => {
    // マウント時にアニメーションを開始
    setAnimate(true);
  }, []);

  // プロパティから渡された値を優先して使用
  const remainingQuestions =
    propRemainingQuestions !== undefined
      ? propRemainingQuestions
      : authRemainingQuestions;

  // プラン履歴を取得する関数
  const fetchPlanHistory = async () => {
    if (!user) return;
    
    setIsPlanHistoryLoading(true);
    try {
      console.log("プラン履歴を取得中...");
      console.log("API URL:", `${api.defaults.baseURL}/plan-history`);
      
      const response = await api.get("/plan-history");
      console.log("プラン履歴取得結果:", response.data);
      console.log("レスポンスステータス:", response.status);
      
      if (response.data && response.data.history) {
        // 自分の履歴のみフィルタリング
        const userHistory = response.data.history.filter(
          (item: PlanHistoryItem) => item.user_id === user.id
        );
        setPlanHistory(userHistory);
      } else {
        setPlanHistory([]);
      }
    } catch (error: any) {
      console.error("プラン履歴の取得に失敗しました:", error);
      if (error.response) {
        console.error("エラーレスポンス:", error.response.status, error.response.data);
        console.error("エラーヘッダー:", error.response.headers);
      } else if (error.request) {
        console.error("リクエストエラー:", error.request);
      } else {
        console.error("設定エラー:", error.message);
      }
      setPlanHistory([]);
    } finally {
      setIsPlanHistoryLoading(false);
    }
  };

  // ドロワー開いた時にプラン履歴を取得
  useEffect(() => {
    if (drawerOpen) {
      fetchPlanHistory();
    }
  }, [drawerOpen, user]);

  // 無制限アカウントの場合はプラン履歴のみ表示
  if (isUnlimited) {
    return (
      <>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setDrawerOpen(true)}
          startIcon={<HistoryIcon fontSize="small" />}
          sx={{
            borderRadius: "20px",
            fontSize: { xs: "0.7rem", sm: "0.75rem", md: "0.8rem" },
            py: { xs: 0.3, sm: 0.4, md: 0.5 },
            px: { xs: 1, sm: 1.2, md: 1.5 },
            minHeight: 0,
            minWidth: 0,
            textTransform: "none",
            color: theme.palette.success.main,
            borderColor: "rgba(46, 125, 50, 0.3)",
            backgroundColor: "rgba(255, 255, 255, 0.9)",
            backdropFilter: "blur(8px)",
            boxShadow: "0 2px 8px rgba(0, 0, 0, 0.05)",
            position: "relative",
            "&:hover": {
              backgroundColor: "rgba(255, 255, 255, 0.95)",
              borderColor: theme.palette.success.main,
              boxShadow: "0 3px 10px rgba(46, 125, 50, 0.12)",
            },
            mx: "auto",
          }}
        >
          {isDesktop ? "プラン履歴" : isMobile ? "履歴" : "プラン履歴"}
        </Button>

        {/* プラン履歴用ドロワー */}
        <Drawer anchor="right" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
          <Box sx={{ width: { xs: "90vw", sm: "400px", md: "450px" }, p: 2 }}>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                mb: 3,
              }}
            >
              <Typography
                variant="h6"
                sx={{ fontWeight: 600, color: "success.main" }}
              >
                🎉 本番版をご利用中
              </Typography>
              <IconButton onClick={() => setDrawerOpen(false)} size="small">
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>

                         <Alert severity="success" sx={{ mb: 2 }}>
               本番版では質問・アップロード制限はありません
             </Alert>

             {/* プラン履歴セクション */}
             <Paper
               elevation={0}
               sx={{
                 p: 2,
                 borderRadius: 2,
                 background: "linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)",
                 border: "1px solid rgba(37, 99, 235, 0.08)",
                 boxShadow: "0 3px 15px rgba(37, 99, 235, 0.08)",
                 mb: 2,
               }}
             >
               <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                 <HistoryIcon sx={{ mr: 1, color: "primary.main" }} />
                 <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                   プラン変更履歴
                 </Typography>
               </Box>

               {isPlanHistoryLoading ? (
                 <Box sx={{ textAlign: "center", py: 3 }}>
                   <Typography variant="body2" color="text.secondary">
                     履歴を読み込み中...
                   </Typography>
                 </Box>
               ) : planHistory.length === 0 ? (
                 <Box sx={{ textAlign: "center", py: 3 }}>
                   <Typography variant="body2" color="text.secondary">
                     プラン変更履歴がありません
                   </Typography>
                 </Box>
               ) : (
                 <List dense sx={{ maxHeight: 200, overflow: "auto" }}>
                   {planHistory.slice(0, 5).map((item, index) => (
                     <React.Fragment key={item.id}>
                       <ListItem
                         sx={{
                           py: 1,
                           px: 0,
                           alignItems: "flex-start",
                         }}
                       >
                         <ListItemIcon sx={{ minWidth: 40, mt: 0.5 }}>
                           <Avatar
                             sx={{
                               width: 32,
                               height: 32,
                               bgcolor: "success.main",
                               color: "white",
                             }}
                           >
                             <CheckCircleIcon />
                           </Avatar>
                         </ListItemIcon>
                         <ListItemText
                           primary={
                             <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                               <Chip
                                 label={item.from_plan === "demo" ? "デモ版" : "本番版"}
                                 size="small"
                                 color={item.from_plan === "demo" ? "warning" : "success"}
                                 variant="outlined"
                                 sx={{ fontSize: "0.7rem" }}
                               />
                               <Typography variant="body2" color="text.secondary">
                                 →
                               </Typography>
                               <Chip
                                 label={item.to_plan === "demo" ? "デモ版" : "本番版"}
                                 size="small"
                                 color={item.to_plan === "demo" ? "warning" : "success"}
                                 sx={{ fontSize: "0.7rem" }}
                               />
                             </Box>
                           }
                           secondary={
                             <Typography variant="caption" color="text.secondary">
                               {new Date(item.changed_at).toLocaleString("ja-JP")}
                             </Typography>
                           }
                         />
                       </ListItem>
                       {index < Math.min(planHistory.length, 5) - 1 && (
                         <Divider variant="inset" component="li" />
                       )}
                     </React.Fragment>
                   ))}
                 </List>
               )}
             </Paper>
          </Box>
        </Drawer>
      </>
    );
  }

  // 質問の残り回数のパーセンテージを計算
  const questionsPercentage =
    remainingQuestions !== null ? (remainingQuestions / 10) * 100 : 0;

  // アップロードの残り回数のパーセンテージを計算
  const uploadsPercentage =
    remainingUploads !== null ? (remainingUploads / 2) * 100 : 0;

  // 残り質問回数のステータスを判定
  const getQuestionsStatus = () => {
    if (remainingQuestions === null || remainingQuestions === 0) return "error";
    if (remainingQuestions <= 4) return "warning";
    return "success";
  };

  // 残りアップロード回数のステータスを判定
  const getUploadsStatus = () => {
    if (remainingUploads === null || remainingUploads === 0) return "error";
    return "success";
  };

  const questionsStatus = getQuestionsStatus();
  const uploadsStatus = getUploadsStatus();

  // ステータスに応じた色を取得
  const getStatusColors = (status: "error" | "warning" | "success") => {
    switch (status) {
      case "error":
        return {
          light: "#ffebee",
          main: "#f44336",
          dark: "#c62828",
          text: "#d32f2f",
          progress: "#ff5252",
        };
      case "warning":
        return {
          light: "#fff8e1",
          main: "#ff9800",
          dark: "#ef6c00",
          text: "#ed6c02",
          progress: "#ffb74d",
        };
      case "success":
      default:
        return {
          light: "#e8f5e9",
          main: "#4caf50",
          dark: "#2e7d32",
          text: "#2e7d32",
          progress: "#66bb6a",
        };
    }
  };

  const questionsColors = getStatusColors(questionsStatus);
  const uploadsColors = getStatusColors(uploadsStatus);

  const handleOpenDrawer = () => {
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
  };

  const handleOpenApplication = () => {
    setApplicationOpen(true);
  };

  const handleCloseApplication = () => {
    setApplicationOpen(false);
  };

  // 統合されたボタン表示 (PC, タブレット, モバイル共通)
  const renderStatusButton = () => (
    <Button
      variant="outlined"
      size="small"
      onClick={handleOpenDrawer}
      startIcon={
        <Badge
          color={
            remainingQuestions === 0 || remainingUploads === 0
              ? "error"
              : "primary"
          }
          variant="dot"
          invisible={remainingQuestions !== 0 && remainingUploads !== 0}
        >
          <BarChartIcon fontSize="small" />
        </Badge>
      }
      sx={{
        borderRadius: "20px",
        fontSize: { xs: "0.7rem", sm: "0.75rem", md: "0.8rem" },
        py: { xs: 0.3, sm: 0.4, md: 0.5 },
        px: { xs: 1, sm: 1.2, md: 1.5 },
        minHeight: 0,
        minWidth: 0,
        textTransform: "none",
        color: theme.palette.primary.main,
        borderColor: "rgba(37, 99, 235, 0.3)",
        backgroundColor: "rgba(255, 255, 255, 0.9)",
        backdropFilter: "blur(8px)",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.05)",
        position: "relative",
        "&:hover": {
          backgroundColor: "rgba(255, 255, 255, 0.95)",
          borderColor: theme.palette.primary.main,
          boxShadow: "0 3px 10px rgba(37, 99, 235, 0.12)",
        },
        mx: "auto",
      }}
    >
      {isDesktop ? "デモ版利用状況" : isMobile ? "利用状況" : "デモ版利用状況"}
    </Button>
  );

  // ミニマムステータス表示（バッジのみ）
  const renderMiniStatus = () => (
    <Stack
      direction="row"
      spacing={1.5}
      sx={{
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <Tooltip title={`残り質問回数: ${remainingQuestions}/10`}>
        <Chip
          size="small"
          icon={
            <HelpOutlineIcon
              sx={{ fontSize: "0.9rem", color: questionsColors.text }}
            />
          }
          label={`${remainingQuestions}/10`}
          sx={{
            fontSize: "0.7rem",
            height: "24px",
            bgcolor: "rgba(255, 255, 255, 0.9)",
            color: questionsColors.text,
            border: `1px solid ${questionsColors.text}20`,
            "& .MuiChip-icon": {
              ml: 0.5,
            },
          }}
        />
      </Tooltip>

      <Tooltip title={`残りアップロード回数: ${remainingUploads}/2`}>
        <Chip
          size="small"
          icon={
            <UploadFileIcon
              sx={{ fontSize: "0.9rem", color: uploadsColors.text }}
            />
          }
          label={`${remainingUploads}/2`}
          sx={{
            fontSize: "0.7rem",
            height: "24px",
            bgcolor: "rgba(255, 255, 255, 0.9)",
            color: uploadsColors.text,
            border: `1px solid ${uploadsColors.text}20`,
            "& .MuiChip-icon": {
              ml: 0.5,
            },
          }}
        />
      </Tooltip>

      <IconButton
        size="small"
        onClick={handleOpenDrawer}
        color="primary"
        sx={{
          width: 24,
          height: 24,
          bgcolor: "rgba(255, 255, 255, 0.9)",
          boxShadow: "0 1px 4px rgba(0, 0, 0, 0.05)",
          "&:hover": {
            bgcolor: "rgba(255, 255, 255, 1)",
            boxShadow: "0 2px 8px rgba(37, 99, 235, 0.15)",
          },
        }}
      >
        <InfoIcon sx={{ fontSize: "0.9rem" }} />
      </IconButton>
    </Stack>
  );



  // 詳細表示のコンテンツ（ドロワー用）
  const renderDetailContent = () => (
    <Box sx={{ width: { xs: "90vw", sm: "400px", md: "450px" }, p: 2 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography
          variant="h6"
          sx={{ fontWeight: 600, color: "primary.main" }}
        >
          デモ版利用状況
        </Typography>
        <IconButton onClick={handleCloseDrawer} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      <Paper
        elevation={0}
        sx={{
          p: { xs: 2, sm: 2.5 },
          borderRadius: 2,
          background: "linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)",
          border: "1px solid rgba(37, 99, 235, 0.08)",
          boxShadow: "0 3px 15px rgba(37, 99, 235, 0.08)",
          overflow: "hidden",
          position: "relative",
          mb: 2,
          "&::before": {
            content: '""',
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: "2px",
            background: "linear-gradient(90deg, #2563eb, #3b82f6)",
            opacity: 0.8,
          },
        }}
      >
        <Box
          sx={{
            p: 1.5,
            bgcolor: "rgba(255, 255, 255, 0.7)",
            borderRadius: 1.5,
            border: "1px solid rgba(25, 118, 210, 0.1)",
            boxShadow: "inset 0 1px 3px rgba(0, 0, 0, 0.02)",
            mb: 2,
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 0.8,
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center" }}>
              <HelpOutlineIcon
                fontSize="small"
                sx={{
                  mr: 1,
                  color: questionsColors.text,
                  fontSize: { xs: "0.9rem", sm: "1.1rem" },
                }}
              />
              <Typography
                variant="subtitle2"
                sx={{
                  fontWeight: 600,
                  fontSize: { xs: "0.8rem", sm: "0.9rem" },
                  color: "text.secondary",
                }}
              >
                質問回数制限
              </Typography>
            </Box>

            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: "bold",
                fontSize: { xs: "0.8rem", sm: "0.9rem" },
                color: questionsColors.text,
                display: "flex",
                alignItems: "center",
                gap: 0.5,
              }}
            >
              {remainingQuestions !== null
                ? `${remainingQuestions}/10`
                : "0/10"}
              {remainingQuestions === 0 && (
                <ErrorIcon
                  fontSize="small"
                  color="error"
                  sx={{ ml: 0.5, fontSize: "1rem" }}
                />
              )}
            </Typography>
          </Box>

          <Tooltip
            title={
              remainingQuestions === 0
                ? "質問回数の上限に達しました"
                : `あと${remainingQuestions}回質問できます`
            }
          >
            <Box sx={{ position: "relative" }}>
              <LinearProgress
                variant="determinate"
                value={questionsPercentage}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: "rgba(0, 0, 0, 0.08)",
                  "& .MuiLinearProgress-bar": {
                    backgroundColor: questionsColors.progress,
                    borderRadius: 4,
                    transition: "transform 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
                  },
                }}
              />

              {/* プログレスバーのセグメントマーク */}
              {[20, 40, 60, 80].map((segment) => (
                <Box
                  key={segment}
                  sx={{
                    position: "absolute",
                    top: 0,
                    left: `${segment}%`,
                    height: 8,
                    width: 1,
                    backgroundColor: "rgba(255, 255, 255, 0.6)",
                    zIndex: 1,
                  }}
                />
              ))}
            </Box>
          </Tooltip>

          <Typography
            variant="caption"
            sx={{
              display: "block",
              textAlign: "right",
              mt: 0.5,
              color: "text.secondary",
              fontSize: "0.7rem",
            }}
          >
            {remainingQuestions === 0
              ? "制限に達しました"
              : remainingQuestions === 1
              ? "残り2回のみ"
              : `残り${remainingQuestions}回まで利用可能`}
          </Typography>
        </Box>

        <Box
          sx={{
            p: 1.5,
            bgcolor: "rgba(255, 255, 255, 0.7)",
            borderRadius: 1.5,
            border: "1px solid rgba(25, 118, 210, 0.1)",
            boxShadow: "inset 0 1px 3px rgba(0, 0, 0, 0.02)",
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 0.8,
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center" }}>
              <UploadFileIcon
                fontSize="small"
                sx={{
                  mr: 1,
                  color: uploadsColors.text,
                  fontSize: { xs: "0.9rem", sm: "1.1rem" },
                }}
              />
              <Typography
                variant="subtitle2"
                sx={{
                  fontWeight: 600,
                  fontSize: { xs: "0.8rem", sm: "0.9rem" },
                  color: "text.secondary",
                }}
              >
                資料アップロード制限
              </Typography>
            </Box>

            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: "bold",
                fontSize: { xs: "0.8rem", sm: "0.9rem" },
                color: uploadsColors.text,
                display: "flex",
                alignItems: "center",
                gap: 0.5,
              }}
            >
              {remainingUploads !== null ? `${remainingUploads}/2` : "0/2"}
              {remainingUploads === 0 && (
                <ErrorIcon
                  fontSize="small"
                  color="error"
                  sx={{ ml: 0.5, fontSize: "1rem" }}
                />
              )}
            </Typography>
          </Box>

          <Tooltip
            title={
              remainingUploads === 0
                ? "資料アップロードの上限に達しました"
                : "あと2回資料をアップロードできます"
            }
          >
            <LinearProgress
              variant="determinate"
              value={uploadsPercentage}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: "rgba(0, 0, 0, 0.08)",
                "& .MuiLinearProgress-bar": {
                  backgroundColor: uploadsColors.progress,
                  borderRadius: 4,
                  transition: "transform 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
                },
              }}
            />
          </Tooltip>

          <Typography
            variant="caption"
            sx={{
              display: "block",
              textAlign: "right",
              mt: 0.5,
              color: "text.secondary",
              fontSize: "0.7rem",
            }}
          >
            {remainingUploads === 0
              ? "制限に達しました"
              : "残り2回まで利用可能"}
          </Typography>
        </Box>
      </Paper>

      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ mt: 2, textAlign: "center", fontSize: "0.8rem" }}
      >
        無制限で利用するには、本番版への移行をご検討ください。
      </Typography>

      {/* 制限に達した場合はアップグレードボタンを表示 */}
      {(remainingQuestions === 0 || remainingUploads === 0) && (
        <Button
          variant="contained"
          fullWidth
          size="large"
          startIcon={<UpgradeIcon />}
          onClick={handleOpenApplication}
          sx={{
            mt: 2,
            py: 1.5,
            borderRadius: 2,
            fontWeight: 600,
            textTransform: "none",
            background: "linear-gradient(135deg, #f59e0b, #eab308)",
            "&:hover": {
              background: "linear-gradient(135deg, #d97706, #ca8a04)",
            },
          }}
        >
          本番版にアップグレード
        </Button>
      )}

      {/* プラン履歴セクション */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderRadius: 2,
          background: "linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)",
          border: "1px solid rgba(37, 99, 235, 0.08)",
          boxShadow: "0 3px 15px rgba(37, 99, 235, 0.08)",
          mb: 2,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <HistoryIcon sx={{ mr: 1, color: "primary.main" }} />
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            プラン変更履歴
          </Typography>
        </Box>

        {isPlanHistoryLoading ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <Typography variant="body2" color="text.secondary">
              履歴を読み込み中...
            </Typography>
          </Box>
        ) : planHistory.length === 0 ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <Typography variant="body2" color="text.secondary">
              プラン変更履歴がありません
            </Typography>
          </Box>
        ) : (
          <List dense sx={{ maxHeight: 200, overflow: "auto" }}>
            {planHistory.slice(0, 5).map((item, index) => (
              <React.Fragment key={item.id}>
                <ListItem
                  sx={{
                    py: 1,
                    px: 0,
                    alignItems: "flex-start",
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40, mt: 0.5 }}>
                    <Avatar
                      sx={{
                        width: 32,
                        height: 32,
                        bgcolor: "primary.main",
                        color: "white",
                      }}
                    >
                      <HistoryIcon />
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Chip
                          label={item.from_plan === "demo" ? "デモ版" : "本番版"}
                          size="small"
                          color={item.from_plan === "demo" ? "warning" : "success"}
                          variant="outlined"
                          sx={{ fontSize: "0.7rem" }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          →
                        </Typography>
                        <Chip
                          label={item.to_plan === "demo" ? "デモ版" : "本番版"}
                          size="small"
                          color={item.to_plan === "demo" ? "warning" : "success"}
                          sx={{ fontSize: "0.7rem" }}
                        />
                      </Box>
                    }
                    secondary={
                      <Typography variant="caption" color="text.secondary">
                        {new Date(item.changed_at).toLocaleString("ja-JP")}
                      </Typography>
                    }
                  />
                </ListItem>
                {index < Math.min(planHistory.length, 5) - 1 && (
                  <Divider variant="inset" component="li" />
                )}
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>
    </Box>
  );

  return (
    <Fade in={animate} timeout={800}>
      <div>
        {/* デバイスに応じた表示\ */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            mb: { xs: 0.5, sm: 0.75, md: 1 },
            position: isDesktop ? "absolute" : "relative",
            right: isDesktop ? "20px" : "auto",
            top: isDesktop ? "10px" : "auto",
            zIndex: 5,
          }}
        >
          {isMobile ? renderMiniStatus() : renderStatusButton()}
        </Box>

        {/* サイドドロワー */}
        <Drawer
          anchor="right"
          open={drawerOpen}
          onClose={handleCloseDrawer}
          PaperProps={{
            sx: {
              borderTopLeftRadius: "16px",
              borderBottomLeftRadius: "16px",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.12)",
            },
          }}
        >
          {renderDetailContent()}
        </Drawer>

        {/* アラート通知 */}
        {showAlert && (
          <Snackbar
            open={showAlert}
            autoHideDuration={6000}
            onClose={onCloseAlert}
            anchorOrigin={{ vertical: "top", horizontal: "center" }}
          >
            <Alert
              onClose={onCloseAlert}
              severity="error"
              variant="filled"
              sx={{
                width: "100%",
                boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
                borderRadius: 2,
              }}
              icon={<ErrorIcon />}
            >
              デモ版の質問回数制限に達しました
            </Alert>
          </Snackbar>
        )}

        {/* アップグレード成功メッセージ */}
        {upgradeSuccess && (
          <Snackbar
            open={upgradeSuccess}
            autoHideDuration={5000}
            onClose={() => setUpgradeSuccess(false)}
            anchorOrigin={{ vertical: "top", horizontal: "center" }}
          >
            <Alert
              onClose={() => setUpgradeSuccess(false)}
              severity="success"
              variant="filled"
              sx={{
                width: "100%",
                boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
                borderRadius: 2,
              }}
            >
              🎉 アップグレードが完了しました！無制限にご利用いただけます。
            </Alert>
          </Snackbar>
        )}

        {        /* 申請フォームダイアログ */}
        <ApplicationForm
          open={applicationOpen}
          onClose={handleCloseApplication}
        />
      </div>
    </Fade>
  );
};

export default DemoLimits;
