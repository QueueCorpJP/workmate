import React, { useState } from "react";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  Alert,
  Grid,
  Divider,
  Paper,
  IconButton,
  Tooltip,
  alpha,
  useTheme,
  useMediaQuery,
  InputAdornment,
  Fade,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Collapse,
  Stack,
} from "@mui/material";
import PersonAddIcon from "@mui/icons-material/PersonAdd";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import GroupIcon from "@mui/icons-material/Group";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import EmailIcon from "@mui/icons-material/Email";
import BusinessIcon from "@mui/icons-material/Business";
import HistoryIcon from "@mui/icons-material/History";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import LoadingIndicator from "./LoadingIndicator";
import api from "../../api";

interface UserManagementTabProps {
  isSpecialAdmin: boolean;
  newUserEmail: string;
  onNewUserEmailChange: (email: string) => void;
  newUserPassword: string;
  onNewUserPasswordChange: (password: string) => void;
  isUserCreating: boolean;
  userCreateError: string | null;
  userCreateSuccess: string | null;
  onCreateUser: (role: string) => void;
  onOpenCompanyDetails?: () => void;
  companies?: any[];
  selectedCompanyId?: string;
  onSelectedCompanyIdChange?: (companyId: string) => void;
  isCompaniesLoading?: boolean;
  user?: any;
  newCompanyName?: string;
  onNewCompanyNameChange?: (name: string) => void;
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

const UserManagementTab: React.FC<UserManagementTabProps> = ({
  isSpecialAdmin,
  newUserEmail,
  onNewUserEmailChange,
  newUserPassword,
  onNewUserPasswordChange,
  isUserCreating,
  userCreateError,
  userCreateSuccess,
  onCreateUser,
  onOpenCompanyDetails,
  companies,
  selectedCompanyId,
  onSelectedCompanyIdChange,
  isCompaniesLoading,
  user,
  newCompanyName,
  onNewCompanyNameChange,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isTablet = useMediaQuery(theme.breakpoints.between("sm", "md"));
  const [showPassword, setShowPassword] = useState(false);

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  // employeeロールの場合はアクセス権限なしを表示
  if (user?.role === "employee") {
    return (
      <Fade in={true} timeout={400}>
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "400px",
            textAlign: "center",
            p: 4,
          }}
        >
          <PersonAddIcon
            sx={{
              fontSize: "4rem",
              color: "text.disabled",
              mb: 2,
            }}
          />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: "text.secondary",
              mb: 1,
            }}
          >
            アクセス権限がありません
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ maxWidth: "400px" }}
          >
            社員アカウントには管理者作成権限がありません。<br />
            管理者にお問い合わせください。
          </Typography>
        </Box>
      </Fade>
    );
  }

  return (
    <Fade in={true} timeout={400}>
      <Box>
        <Box
          sx={{
            mb: 3,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            px: { xs: 1, sm: 0 },
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <PersonAddIcon
              sx={{
                mr: 1.5,
                color: theme.palette.primary.main,
                fontSize: { xs: "1.8rem", sm: "2rem" },
              }}
            />
            <Typography
              variant={isMobile ? "h6" : "h5"}
              sx={{
                fontWeight: 600,
                color: "text.primary",
              }}
            >
              管理者管理
            </Typography>
          </Box>

          {isSpecialAdmin && onOpenCompanyDetails && (
            <Tooltip title="会社情報詳細を表示">
              <Button
                variant="outlined"
                color="secondary"
                onClick={onOpenCompanyDetails}
                startIcon={<AdminPanelSettingsIcon />}
                size={isMobile ? "small" : "medium"}
                sx={{
                  borderRadius: 2,
                  px: { xs: 1.5, sm: 2 },
                  "&:hover": {
                    backgroundColor: "rgba(156, 39, 176, 0.08)",
                  },
                }}
              >
                {!isMobile && "会社詳細"}
              </Button>
            </Tooltip>
          )}
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card
              elevation={0}
              sx={{
                borderRadius: 2,
                border: "1px solid rgba(0, 0, 0, 0.12)",
                position: "relative",
                overflow: "hidden",
                transition: "all 0.3s ease",
                "&:hover": {
                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
                },
                "&::before": {
                  content: '""',
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "100%",
                  height: "4px",
                  background: "linear-gradient(135deg, #1976d2, #64b5f6)",
                  opacity: 0.9,
                },
              }}
            >
              <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
                <Box sx={{ display: "flex", alignItems: "center", mb: 1.5 }}>
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 600,
                      color: "#424242",
                      display: "flex",
                      alignItems: "center",
                    }}
                  >
                    新規アカウント作成
                  </Typography>

                  {isSpecialAdmin && (
                    <Chip
                      label="特別管理者権限"
                      color="secondary"
                      size="small"
                      sx={{
                        ml: 2,
                        fontWeight: "medium",
                      }}
                    />
                  )}
                </Box>

                <Divider sx={{ mb: 2 }} />

                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    backgroundColor: alpha(theme.palette.background.paper, 0.7),
                    borderRadius: 2,
                    border: "1px solid rgba(0, 0, 0, 0.05)",
                    mb: 2,
                  }}
                >
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      fontSize: "0.85rem",
                    }}
                  >
                    <svg
                      style={{
                        width: "0.9rem",
                        height: "0.9rem",
                        color: "#FF9800",
                        marginRight: "8px",
                        flexShrink: 0,
                      }}
                      viewBox="0 0 24 24"
                    >
                      <path
                        fill="currentColor"
                        d="M12,2C6.48,2 2,6.48 2,12C2,17.52 6.48,22 12,22C17.52,22 22,17.52 22,12C22,6.48 17.52,2 12,2ZM12,17C11.45,17 11,16.55 11,16V12C11,11.45 11.45,11 12,11C12.55,11 13,11.45 13,12V16C13,16.55 12.55,17 12,17ZM13,9H11V7H13V9Z"
                      />
                    </svg>
                    {isSpecialAdmin
                      ? "特別管理者として、新しい会社の社長用アカウントを作成できます"
                      : "社長として、自分の会社の社員アカウント（管理画面アクセス不可）を作成できます"}
                  </Typography>
                </Paper>

                <Box
                  component="form"
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 2,
                  }}
                >
                  <TextField
                    label="メールアドレス"
                    variant="outlined"
                    fullWidth
                    size="small"
                    value={newUserEmail}
                    onChange={(e) => onNewUserEmailChange(e.target.value)}
                    placeholder="例: user@example.com"
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <EmailIcon
                            sx={{
                              color: theme.palette.primary.main,
                              fontSize: "1.2rem",
                            }}
                          />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      "& .MuiOutlinedInput-root": {
                        borderRadius: 1.5,
                        transition: "all 0.3s",
                        "&:hover": {
                          "& .MuiOutlinedInput-notchedOutline": {
                            borderColor: theme.palette.primary.main,
                          },
                        },
                      },
                      "& .MuiInputLabel-root": {
                        fontSize: "0.9rem",
                      },
                    }}
                  />

                  <TextField
                    label="パスワード"
                    variant="outlined"
                    fullWidth
                    size="small"
                    type={showPassword ? "text" : "password"}
                    value={newUserPassword}
                    onChange={(e) => onNewUserPasswordChange(e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <svg
                            style={{
                              width: "1.1rem",
                              height: "1.1rem",
                              color: "#FF9800",
                            }}
                            viewBox="0 0 24 24"
                          >
                            <path
                              fill="currentColor"
                              d="M12,17C10.89,17 10,16.1 10,15C10,13.89 10.89,13 12,13A2,2 0 0,1 14,15A2,2 0 0,1 12,17M18,20V10H6V20H18M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6C4.89,22 4,21.1 4,20V10C4,8.89 4.89,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"
                            />
                          </svg>
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            aria-label="toggle password visibility"
                            onClick={handleClickShowPassword}
                            edge="end"
                            size="small"
                          >
                            {showPassword ? (
                              <VisibilityOffIcon fontSize="small" />
                            ) : (
                              <VisibilityIcon fontSize="small" />
                            )}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      "& .MuiOutlinedInput-root": {
                        borderRadius: 1.5,
                        transition: "all 0.3s",
                        "&:hover": {
                          "& .MuiOutlinedInput-notchedOutline": {
                            borderColor: "#FF9800",
                          },
                        },
                      },
                      "& .MuiInputLabel-root": {
                        fontSize: "0.9rem",
                      },
                    }}
                  />

                  

                  {/* 特別管理者の場合は会社名入力を表示 */}
                  {isSpecialAdmin && (
                    <TextField
                      label="会社名"
                      variant="outlined"
                      fullWidth
                      size="small"
                      value={newCompanyName || ""}
                      onChange={(e) => onNewCompanyNameChange?.(e.target.value)}
                      placeholder="例: 新しい会社"
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <BusinessIcon
                              sx={{
                                color: "#9C27B0",
                                fontSize: "1.2rem",
                              }}
                            />
                          </InputAdornment>
                        ),
                      }}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          borderRadius: 1.5,
                          transition: "all 0.3s",
                          "&:hover": {
                            "& .MuiOutlinedInput-notchedOutline": {
                              borderColor: "#9C27B0",
                            },
                          },
                        },
                        "& .MuiInputLabel-root": {
                          fontSize: "0.9rem",
                        },
                      }}
                      helperText="新しい会社名を入力してください（空白の場合は自動生成されます）"
                    />
                  )}

                  {/* アカウント作成ボタン */}
                  <Box sx={{ mt: 1 }}>
                      <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2, fontSize: "0.85rem" }}
                      >
                      {isSpecialAdmin 
                        ? "社長用アカウントは管理画面にアクセスできます" 
                        : "社員アカウントは管理画面にアクセスできません"
                      }
                            </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      size="small"
                      onClick={() => onCreateUser(isSpecialAdmin ? "user" : "employee")}
                      disabled={
                        isUserCreating || !newUserEmail || !newUserPassword
                      }
                      startIcon={isUserCreating ? null : (isSpecialAdmin ? <AdminPanelSettingsIcon /> : <GroupIcon />)}
                      sx={{
                        py: 0.8,
                        mt: 0.5,
                        borderRadius: 1.5,
                        fontSize: "0.85rem",
                        bgcolor: theme.palette.primary.main,
                        boxShadow: "0 2px 4px rgba(0, 0, 0, 0.15)",
                        transition: "all 0.3s",
                        "&:hover": {
                          bgcolor: theme.palette.primary.dark,
                          boxShadow: "0 3px 6px rgba(0, 0, 0, 0.2)",
                        },
                      }}
                    >
                      {isUserCreating ? (
                        <LoadingIndicator size={24} message="" />
                      ) : (
                        isSpecialAdmin 
                          ? "社長用アカウントを作成"
                          : "社員アカウントを作成"
                      )}
                    </Button>
                  </Box>

                  {userCreateError && (
                    <Alert
                      severity="error"
                      variant="filled"
                      sx={{
                        mt: 2,
                        borderRadius: 2,
                        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                      }}
                    >
                      {userCreateError}
                    </Alert>
                  )}

                  {userCreateSuccess && (
                    <Alert
                      severity="success"
                      variant="filled"
                      sx={{
                        mt: 2,
                        borderRadius: 2,
                        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                      }}
                    >
                      {userCreateSuccess}
                    </Alert>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* プラン履歴セクション - 特別管理者のみ */}
          {isSpecialAdmin && (
            <Grid item xs={12}>
              <PlanHistorySection />
            </Grid>
          )}
        </Grid>
      </Box>
    </Fade>
  );
};

const PlanHistorySection: React.FC = () => {
  const [userPlanHistories, setUserPlanHistories] = React.useState<UserPlanHistory[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(5);
  const [expandedRows, setExpandedRows] = React.useState<Set<string>>(new Set());

  const fetchPlanHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get("/plan-history");
      if (response.data && response.data.success && response.data.data && response.data.data.users) {
        setUserPlanHistories(response.data.data.users);
      } else {
        setUserPlanHistories([]);
      }
    } catch (error) {
      console.error("プラン履歴の取得に失敗しました:", error);
      setError("プラン履歴の取得に失敗しました");
      setUserPlanHistories([]);
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
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
      return <TrendingUpIcon color="success" fontSize="small" />;
    } else if (fromPlan === "production" && toPlan === "demo") {
      return <TrendingDownIcon color="warning" fontSize="small" />;
    }
    return <HistoryIcon color="primary" fontSize="small" />;
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

  const formatDetailedDuration = (durationDays: number | null) => {
    if (!durationDays) return "期間不明";
    
    const years = Math.floor(durationDays / 365);
    const months = Math.floor((durationDays % 365) / 30);
    const weeks = Math.floor(((durationDays % 365) % 30) / 7);
    const days = ((durationDays % 365) % 30) % 7;
    
    const parts: string[] = [];
    if (years > 0) parts.push(`${years}年`);
    if (months > 0) parts.push(`${months}ヶ月`);
    if (weeks > 0) parts.push(`${weeks}週間`);
    if (days > 0) parts.push(`${days}日間`);
    
    if (parts.length === 0) return "1日未満";
    return `${parts.join('')} (${durationDays}日間)`;
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

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <LoadingIndicator message="プラン履歴を読み込み中..." />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
          <Button
            variant="outlined"
            startIcon={<HistoryIcon />}
            onClick={fetchPlanHistory}
          >
            再試行
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      elevation={0}
      sx={{
        borderRadius: 2,
        border: "1px solid rgba(0, 0, 0, 0.12)",
        position: "relative",
        overflow: "hidden",
        transition: "all 0.3s ease",
        "&:hover": {
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
        },
        "&::before": {
          content: '""',
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "4px",
          background: "linear-gradient(135deg, #9C27B0, #E1BEE7)",
          opacity: 0.9,
        },
      }}
    >
      <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <HistoryIcon sx={{ mr: 1.5, color: "#9C27B0", fontSize: "1.8rem" }} />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: "#424242",
              flex: 1,
            }}
          >
            プラン履歴
          </Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={<HistoryIcon />}
            onClick={fetchPlanHistory}
            disabled={isLoading}
            sx={{ 
              borderRadius: 1.5,
              fontSize: "0.75rem",
            }}
          >
            更新
          </Button>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {userPlanHistories.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <HistoryIcon sx={{ fontSize: '3rem', color: 'text.disabled', mb: 1 }} />
            <Typography variant="body2" color="text.secondary">
              プラン変更履歴がありません
            </Typography>
          </Box>
        ) : (
          <>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'grey.50' }}>
                    <TableCell></TableCell>
                    <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>管理者</Typography></TableCell>
                    <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>現在のプラン</Typography></TableCell>
                    <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>変更回数</Typography></TableCell>
                    <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>最終変更日</Typography></TableCell>
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
                          <TableCell sx={{ width: 48 }}>
                            <IconButton
                              size="small"
                              onClick={() => toggleRowExpansion(user.user_id)}
                            >
                              {expandedRows.has(user.user_id) ? 
                                <KeyboardArrowUpIcon fontSize="small" /> : 
                                <KeyboardArrowDownIcon fontSize="small" />
                              }
                            </IconButton>
                          </TableCell>
                          <TableCell>
                            <Box>
                              <Typography variant="caption" sx={{ fontWeight: 500 }}>
                                {user.user_name || "管理者"}
                              </Typography>
                              {user.user_email && (
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.7rem' }}>
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
                              sx={{ fontSize: '0.7rem' }}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption">
                              {user.total_changes}回
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption">
                              {formatRelativeTime(user.latest_change)}
                            </Typography>
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell sx={{ py: 0 }} colSpan={5}>
                            <Collapse in={expandedRows.has(user.user_id)} timeout="auto" unmountOnExit>
                              <Box sx={{ py: 1, px: 1, bgcolor: 'grey.25' }}>
                                <Typography variant="caption" sx={{ mb: 1, fontWeight: 600, display: 'block' }}>
                                  変更履歴詳細
                                </Typography>
                                <Table size="small">
                                  <TableHead>
                                    <TableRow>
                                      <TableCell sx={{ py: 0.5 }}><Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.7rem' }}>変更前</Typography></TableCell>
                                      <TableCell sx={{ py: 0.5 }}><Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.7rem' }}>変更後</Typography></TableCell>
                                      <TableCell sx={{ py: 0.5 }}><Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.7rem' }}>変更日時</Typography></TableCell>
                                      <TableCell sx={{ py: 0.5 }}><Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.7rem' }}>利用期間</Typography></TableCell>
                                    </TableRow>
                                  </TableHead>
                                  <TableBody>
                                    {user.changes.slice(0, 3).map((change) => (
                                      <TableRow key={change.id}>
                                        <TableCell sx={{ py: 0.5 }}>
                                          <Chip
                                            label={getPlanDisplayName(change.from_plan)}
                                            color={getPlanColor(change.from_plan) as any}
                                            size="small"
                                            variant="outlined"
                                            sx={{ fontSize: '0.65rem', height: '20px' }}
                                          />
                                        </TableCell>
                                        <TableCell sx={{ py: 0.5 }}>
                                          <Stack direction="row" spacing={0.5} alignItems="center">
                                            {getChangeIcon(change.from_plan, change.to_plan)}
                                            <Chip
                                              label={getPlanDisplayName(change.to_plan)}
                                              color={getPlanColor(change.to_plan) as any}
                                              size="small"
                                              sx={{ fontSize: '0.65rem', height: '20px' }}
                                            />
                                          </Stack>
                                        </TableCell>
                                        <TableCell sx={{ py: 0.5 }}>
                                          <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                                            {formatRelativeTime(change.changed_at)}
                                          </Typography>
                                        </TableCell>
                                        <TableCell sx={{ py: 0.5 }}>
                                          <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                                            {change.duration_days ? 
                                              formatDetailedDuration(change.duration_days) : 
                                              "期間不明"
                                            }
                                          </Typography>
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
              rowsPerPageOptions={[5, 10]}
              component="div"
              count={userPlanHistories.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              labelRowsPerPage="行数:"
              labelDisplayedRows={({ from, to, count }) => `${from}–${to} / ${count}`}
              sx={{
                '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                  fontSize: '0.75rem',
                },
              }}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default UserManagementTab;
