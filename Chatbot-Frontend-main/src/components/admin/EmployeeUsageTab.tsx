import React, { useState } from "react";
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Divider,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  Avatar,
  Chip,
  TextField,
  Alert,
  Checkbox,
  IconButton,
  Tooltip,
  FormHelperText,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Stack,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import EditIcon from "@mui/icons-material/Edit";
import HistoryIcon from "@mui/icons-material/History";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import TimelineIcon from "@mui/icons-material/Timeline";
import CloseIcon from "@mui/icons-material/Close";
import { EmployeeUsageItem, CompanyEmployee, categoryColors } from "./types";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";
import { formatDate } from "./utils";
import EmployeeDetailsDialog from "./EmployeeDetailsDialog";
import api from "../../api";
import { validateEmail, validatePassword, getPasswordStrength } from "../../utils/validation";
import { useAuth } from "../../contexts/AuthContext";

interface EmployeeUsageTabProps {
  employeeUsage: EmployeeUsageItem[];
  companyEmployees: CompanyEmployee[];
  isEmployeeUsageLoading: boolean;
  isCompanyEmployeesLoading: boolean;
  isEmployeeDetailsLoading: boolean;
  employeeDetails: any[];
  onRefreshEmployeeUsage: () => void;
  onRefreshCompanyEmployees: () => void;
  onEmployeeCardClick: (employee: EmployeeUsageItem) => void;
  selectedEmployee: EmployeeUsageItem | null;
  detailsDialogOpen: boolean;
  onCloseDetailsDialog: () => void;
  showEmployeeCreateForm: boolean;
  onToggleEmployeeCreateForm: () => void;
  newEmployeeEmail: string;
  onNewEmployeeEmailChange: (email: string) => void;
  newEmployeePassword: string;
  onNewEmployeePasswordChange: (password: string) => void;
  isEmployeeCreating: boolean;
  employeeCreateError: string | null;
  employeeCreateSuccess: string | null;
  onCreateEmployee: (role: string) => void;
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

const EmployeeUsageTab: React.FC<EmployeeUsageTabProps> = ({
  employeeUsage,
  companyEmployees,
  isEmployeeUsageLoading,
  isCompanyEmployeesLoading,
  isEmployeeDetailsLoading,
  employeeDetails,
  onRefreshEmployeeUsage,
  onRefreshCompanyEmployees,
  onEmployeeCardClick,
  selectedEmployee,
  detailsDialogOpen,
  onCloseDetailsDialog,
  showEmployeeCreateForm,
  onToggleEmployeeCreateForm,
  newEmployeeEmail,
  onNewEmployeeEmailChange,
  newEmployeePassword,
  onNewEmployeePasswordChange,
  isEmployeeCreating,
  employeeCreateError,
  employeeCreateSuccess,
  onCreateEmployee,
}) => {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin" || 
    (user?.email && ["queue@queuefood.co.jp", "queue@queue-tech.jp"].includes(user.email));
  
  const [emailError, setEmailError] = useState<string>("");
  const [passwordError, setPasswordError] = useState<string>("");
  const [showValidation, setShowValidation] = useState(false);
  
  // プラン履歴ダイアログの状態
  const [planHistoryOpen, setPlanHistoryOpen] = useState(false);
  const [selectedUserForHistory, setSelectedUserForHistory] = useState<CompanyEmployee | null>(null);
  const [planHistory, setPlanHistory] = useState<PlanHistoryItem[]>([]);
  const [isPlanHistoryLoading, setIsPlanHistoryLoading] = useState(false);

  const handleEmailChange = (email: string) => {
    onNewEmployeeEmailChange(email);
    
    if (showValidation) {
      const validation = validateEmail(email);
      setEmailError(validation.isValid ? "" : validation.message);
    }
  };

  const handlePasswordChange = (password: string) => {
    onNewEmployeePasswordChange(password);
    
    if (showValidation) {
      const validation = validatePassword(password);
      setPasswordError(validation.isValid ? "" : validation.message);
    }
  };

  const validateForm = () => {
    const emailValidation = validateEmail(newEmployeeEmail);
    const passwordValidation = validatePassword(newEmployeePassword);
    
    setEmailError(emailValidation.isValid ? "" : emailValidation.message);
    setPasswordError(passwordValidation.isValid ? "" : passwordValidation.message);
    
    return emailValidation.isValid && passwordValidation.isValid;
  };

  const handleCreateEmployee = (role: string) => {
    // admin権限チェック
    if (!isAdmin) {
      console.log("admin権限がないため、アカウント作成をキャンセルしました");
      return;
    }
    
    setShowValidation(true);
    
    if (validateForm()) {
      onCreateEmployee(role);
    }
  };

  const passwordStrength = getPasswordStrength(newEmployeePassword);

  const handleToggleDemo = async (employee: CompanyEmployee) => {
    // admin権限チェック
    if (!isAdmin) {
      console.log("admin権限がないため、プラン変更をキャンセルしました");
      return;
    }
    
    try {
      console.log("=== プラン変更開始 ===");
      console.log("対象ユーザー:", employee.email, "(ID:", employee.id, ")");
      console.log("現在のステータス:", employee.usage_limits?.is_unlimited ? "本番版" : "デモ版");
      
      // is_unlimitedの逆の値を設定（現在がfalse(デモ版)ならtrue(本番版)に、現在がtrue(本番版)ならfalse(デモ版)に）
      const newIsUnlimited = !employee.usage_limits?.is_unlimited;
      console.log("新しいステータス:", newIsUnlimited ? "本番版" : "デモ版");
      
      console.log("APIリクエスト送信中...", `/admin/update-user-status/${employee.id}`);
      console.log("送信データ:", { is_unlimited: newIsUnlimited });
      
      const response = await api.post(`/admin/update-user-status/${employee.id}`, {
        is_unlimited: newIsUnlimited
      });
      
      console.log("APIレスポンス:", response.data);
      
      // 成功メッセージを表示（同期情報を含む）
      if (response.data && response.data.message) {
        console.log("ステータス変更完了:", response.data.message);
        
        // employeeユーザーの同期情報を表示
        if (response.data.updated_company_users > 0) {
          console.log(`同じ会社の ${response.data.updated_company_users} 人のemployeeユーザーも同期されました`);
        }
      }
      
      console.log("社員一覧を再読み込み中...");
      // 社員一覧を再読み込み
      onRefreshCompanyEmployees();
      console.log("=== プラン変更完了 ===");
    } catch (error: any) {
      console.error("=== プラン変更エラー ===", error);
      if (error?.response) {
        console.error("レスポンスエラー:", error.response.status, error.response.data);
      }
      if (error?.request) {
        console.error("リクエストエラー:", error.request);
      }
    }
  };

  // プラン履歴ダイアログを開く
  const handleOpenPlanHistory = async (employee: CompanyEmployee) => {
    setSelectedUserForHistory(employee);
    setPlanHistoryOpen(true);
    setIsPlanHistoryLoading(true);
    
    try {
      console.log("プラン履歴を取得中...", employee.id);
      const response = await api.get("/plan-history");
      console.log("プラン履歴取得結果:", response.data);
      
      if (response.data && response.data.history) {
        // 選択されたユーザーの履歴のみフィルタリング
        const userHistory = response.data.history.filter(
          (item: PlanHistoryItem) => item.user_id === employee.id
        );
        setPlanHistory(userHistory);
      } else {
        setPlanHistory([]);
      }
    } catch (error) {
      console.error("プラン履歴の取得に失敗しました:", error);
      setPlanHistory([]);
    } finally {
      setIsPlanHistoryLoading(false);
    }
  };

  // プラン履歴ダイアログを閉じる
  const handleClosePlanHistory = () => {
    setPlanHistoryOpen(false);
    setSelectedUserForHistory(null);
    setPlanHistory([]);
  };

  // プラン表示名を取得
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

  // プランの色を取得
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

  // 変更アイコンを取得
  const getChangeIcon = (fromPlan: string, toPlan: string) => {
    if (fromPlan === "demo" && toPlan === "production") {
      return <TrendingUpIcon color="success" />;
    } else if (fromPlan === "production" && toPlan === "demo") {
      return <TrendingDownIcon color="warning" />;
    }
    return <HistoryIcon color="primary" />;
  };

  // 期間フォーマット
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

  return (
    <>
      <Box
        sx={{
          mb: 3,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          会社の管理者用アカウント利用状況
        </Typography>
      </Box>

      {/* 社員作成フォーム - adminのみ表示 */}
      {isAdmin && showEmployeeCreateForm && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              新規社員アカウント作成
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              ここで作成した社員アカウントは管理画面にアクセスできません
            </Typography>
            <Box sx={{ mb: 2, p: 2, bgcolor: "rgba(25, 118, 210, 0.04)", borderRadius: 2, border: "1px solid rgba(25, 118, 210, 0.12)" }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: "primary.main" }}>
                入力要件
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                <strong>メールアドレス:</strong> 正しい形式で5-100文字以内
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <strong>パスワード:</strong> 8文字以上、大文字・小文字・数字を含む
              </Typography>
            </Box>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <TextField
                label="メールアドレス"
                variant="outlined"
                fullWidth
                value={newEmployeeEmail}
                onChange={(e) => handleEmailChange(e.target.value)}
                placeholder="例: employee@example.com"
                error={!!emailError}
                helperText={emailError}
              />
              <TextField
                label="パスワード"
                variant="outlined"
                fullWidth
                type="password"
                value={newEmployeePassword}
                onChange={(e) => handlePasswordChange(e.target.value)}
                error={!!passwordError}
                helperText={passwordError}
              />
              {newEmployeePassword && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    パスワード強度: {passwordStrength.label}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(passwordStrength.strength / 6) * 100}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: 'rgba(0,0,0,0.1)',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: passwordStrength.color,
                        borderRadius: 3,
                      }
                    }}
                  />
                </Box>
              )}
              <Button
                variant="contained"
                color="primary"
                onClick={() => handleCreateEmployee("employee")}
                disabled={
                  isEmployeeCreating ||
                  !newEmployeeEmail ||
                  !newEmployeePassword
                }
              >
                {isEmployeeCreating ? (
                  <LoadingIndicator size={24} />
                ) : (
                  "社員アカウントを作成"
                )}
              </Button>

              {employeeCreateError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {employeeCreateError}
                </Alert>
              )}

              {employeeCreateSuccess && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  {employeeCreateSuccess}
                </Alert>
              )}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* 社員一覧テーブル */}
      <Box sx={{ mb: 4 }}>
        <Box
          sx={{
            mb: 3,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            社員一覧
          </Typography>
          <Button
            variant="outlined"
            onClick={onRefreshCompanyEmployees}
            startIcon={<RefreshIcon />}
            disabled={isCompanyEmployeesLoading}
          >
            更新
          </Button>
        </Box>

        {isCompanyEmployeesLoading ? (
          <LoadingIndicator />
        ) : companyEmployees.length === 0 ? (
          <EmptyState message="社員データがありません" />
        ) : (
          <TableContainer component={Paper} elevation={2} sx={{ mb: 4 }}>
            <Table sx={{ minWidth: 650 }}>
              <TableHead>
                <TableRow sx={{ bgcolor: "primary.light" }}>
                  <TableCell
                    sx={{ fontWeight: "bold", color: "primary.contrastText" }}
                  >
                    名前
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", color: "primary.contrastText" }}
                  >
                    メールアドレス
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", color: "primary.contrastText" }}
                  >
                    役割
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", color: "primary.contrastText" }}
                  >
                    デモ版
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", color: "primary.contrastText" }}
                  >
                    プラン履歴
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", color: "primary.contrastText" }}
                  >
                    作成日
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", color: "primary.contrastText" }}
                  >
                    メッセージ数
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", color: "primary.contrastText" }}
                  >
                    最終アクティビティ
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: "bold", color: "primary.contrastText" }}
                  >
                    利用制限
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {companyEmployees.map((employee) => (
                  <TableRow
                    key={employee.id}
                    hover
                    sx={{
                      "&:nth-of-type(odd)": { bgcolor: "rgba(0, 0, 0, 0.02)" },
                      cursor: "pointer",
                      transition: "background-color 0.2s",
                      "&:hover": { bgcolor: "rgba(0, 0, 0, 0.04)" },
                    }}
                    onClick={() =>
                      onEmployeeCardClick({
                        employee_id: employee.id,
                        employee_name: employee.name,
                        message_count: employee.message_count || 0,
                        last_activity: employee.last_activity || "",
                        top_categories: [],
                        recent_questions: [],
                      })
                    }
                  >
                    <TableCell>
                      <Box
                        sx={{ display: "flex", alignItems: "center", gap: 1 }}
                      >
                        <Avatar
                          sx={{
                            width: 32,
                            height: 32,
                            bgcolor:
                              employee.role === "admin"
                                ? "primary.main"
                                : employee.role === "employee"
                                ? "secondary.main"
                                : "grey.500",
                          }}
                        >
                          {employee.name
                            ? employee.name.charAt(0).toUpperCase()
                            : "U"}
                        </Avatar>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {employee.name || "名前なし"}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{employee.email}</TableCell>
                    <TableCell>
                      <Chip
                        label={
                          employee.role === "admin"
                            ? "管理者"
                            : employee.role === "employee"
                            ? "社員"
                            : "ユーザー"
                        }
                        size="small"
                        color={
                          employee.role === "admin"
                            ? "primary"
                            : employee.role === "employee"
                            ? "secondary"
                            : "default"
                        }
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                        {isAdmin ? (
                          <Tooltip title={`クリックで${!employee.usage_limits?.is_unlimited ? '本番版' : 'デモ版'}に切り替え`}>
                            <Checkbox
                              checked={!employee.usage_limits?.is_unlimited}
                              onChange={() => handleToggleDemo(employee)}
                              size="small"
                              sx={{
                                color: !employee.usage_limits?.is_unlimited ? "warning.main" : "success.main",
                                '&.Mui-checked': {
                                  color: !employee.usage_limits?.is_unlimited ? "warning.main" : "success.main",
                                }
                              }}
                            />
                          </Tooltip>
                        ) : (
                          <Tooltip title="管理者のみプラン変更可能">
                            <Checkbox
                              checked={!employee.usage_limits?.is_unlimited}
                              disabled={true}
                              size="small"
                              sx={{
                                color: !employee.usage_limits?.is_unlimited ? "warning.main" : "success.main",
                                '&.Mui-checked': {
                                  color: !employee.usage_limits?.is_unlimited ? "warning.main" : "success.main",
                                }
                              }}
                            />
                          </Tooltip>
                        )}
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            ml: 0.5, 
                            color: !employee.usage_limits?.is_unlimited ? "warning.main" : "success.main",
                            fontWeight: 500
                          }}
                        >
                          {!employee.usage_limits?.is_unlimited ? "デモ版" : "本番版"}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="プラン変更履歴を表示">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenPlanHistory(employee);
                          }}
                          sx={{
                            color: "primary.main",
                            "&:hover": {
                              bgcolor: "primary.light",
                              color: "primary.dark",
                            },
                          }}
                        >
                          <TimelineIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                    <TableCell>{formatDate(employee.created_at)}</TableCell>
                    <TableCell>{employee.message_count}</TableCell>
                    <TableCell>
                      {employee.last_activity
                        ? formatDate(employee.last_activity)
                        : "活動なし"}
                    </TableCell>
                    <TableCell>
                      {employee.usage_limits?.is_unlimited ? (
                        <Chip label="無制限" size="small" color="success" />
                      ) : (
                        <Box
                          sx={{
                            display: "flex",
                            flexDirection: "column",
                            gap: 0.5,
                          }}
                        >
                          <Typography variant="caption">
                            質問: {employee.usage_limits?.questions_used || 0}/
                            {employee.usage_limits?.questions_limit || 0}
                          </Typography>
                          <Typography variant="caption">
                            アップロード:{" "}
                            {employee.usage_limits?.document_uploads_used || 0}/
                            {employee.usage_limits?.document_uploads_limit || 0}
                          </Typography>
                        </Box>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>

      {/* 利用状況カード */}
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
        詳細な利用状況
      </Typography>

      {isEmployeeUsageLoading ? (
        <LoadingIndicator />
      ) : employeeUsage.length === 0 ? (
        <EmptyState message="利用状況データがありません" />
      ) : (
        <Grid container spacing={3}>
          {employeeUsage.map((employee, index) => (
            <Grid
              item
              xs={12}
              md={6}
              lg={4}
              key={`${employee.employee_id}-${index}`}
            >
              <Card
                sx={{
                  height: "100%",
                  cursor: "pointer",
                  transition: "all 0.2s ease-in-out",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    boxShadow: "0 8px 16px rgba(0,0,0,0.1)",
                  },
                }}
                onClick={() => onEmployeeCardClick(employee)}
              >
                <CardContent>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                    }}
                  >
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                      {employee.employee_name || "名前なし"}
                      <Typography
                        component="span"
                        variant="body2"
                        sx={{ ml: 1, color: "text.secondary" }}
                      >
                        (ID: {employee.employee_id})
                      </Typography>
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      利用回数
                    </Typography>
                    <Typography
                      variant="h4"
                      sx={{ fontWeight: 500, color: "primary.main" }}
                    >
                      {employee.message_count}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      最終利用
                    </Typography>
                    <Typography variant="body1">
                      {formatDate(employee.last_activity)}
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Typography
                    variant="subtitle2"
                    sx={{ mb: 1, fontWeight: 600 }}
                  >
                    よく使うカテゴリ
                  </Typography>
                  {employee.top_categories.length > 0 ? (
                    <Box
                      sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}
                    >
                      {employee.top_categories.map((cat, idx) => (
                        <Box
                          key={idx}
                          sx={{
                            bgcolor:
                              categoryColors[idx % categoryColors.length],
                            color: "white",
                            px: 1.5,
                            py: 0.5,
                            borderRadius: 10,
                            fontSize: "0.75rem",
                            fontWeight: 500,
                            display: "flex",
                            alignItems: "center",
                          }}
                        >
                          {cat.category}
                          <Box
                            component="span"
                            sx={{
                              ml: 0.5,
                              bgcolor: "rgba(255,255,255,0.3)",
                              borderRadius: "50%",
                              width: 20,
                              height: 20,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontSize: "0.7rem",
                            }}
                          >
                            {cat.count}
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  ) : (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2 }}
                    >
                      カテゴリデータなし
                    </Typography>
                  )}

                  <Typography
                    variant="subtitle2"
                    sx={{ mb: 1, fontWeight: 600 }}
                  >
                    最近の質問
                  </Typography>
                  {employee.recent_questions.length > 0 ? (
                    <Box component="ul" sx={{ pl: 2, m: 0 }}>
                      {employee.recent_questions.map((q, idx) => (
                        <Typography
                          component="li"
                          key={idx}
                          variant="body2"
                          sx={{
                            mb: 0.5,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            display: "-webkit-box",
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: "vertical",
                          }}
                        >
                          {q}
                        </Typography>
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      質問データなし
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* 社員詳細ダイアログ */}
      <EmployeeDetailsDialog
        open={detailsDialogOpen}
        onClose={onCloseDetailsDialog}
        selectedEmployee={selectedEmployee}
        employeeDetails={employeeDetails}
        isLoading={isEmployeeDetailsLoading}
      />

      {/* プラン履歴ダイアログ */}
      <Dialog
        open={planHistoryOpen}
        onClose={handleClosePlanHistory}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            maxHeight: "80vh",
          },
        }}
      >
        <DialogTitle
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            pb: 1,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <TimelineIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              プラン変更履歴
            </Typography>
            {selectedUserForHistory && (
              <Chip
                label={selectedUserForHistory.name || selectedUserForHistory.email}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
          </Box>
          <IconButton onClick={handleClosePlanHistory} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ pt: 1 }}>
          {isPlanHistoryLoading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
              <LoadingIndicator message="プラン履歴を読み込み中..." />
            </Box>
          ) : planHistory.length === 0 ? (
            <Box sx={{ textAlign: "center", py: 4 }}>
              <HistoryIcon sx={{ fontSize: 48, color: "text.secondary", mb: 2 }} />
              <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                プラン変更履歴がありません
              </Typography>
              <Typography variant="body2" color="text.secondary">
                このユーザーのプラン変更はまだ記録されていません。
              </Typography>
            </Box>
          ) : (
            <>
              <List sx={{ py: 0 }}>
                {planHistory.map((item, index) => (
                  <React.Fragment key={item.id}>
                    <ListItem sx={{ py: 2, px: 0 }}>
                      <ListItemIcon>
                        {getChangeIcon(item.from_plan, item.to_plan)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Stack direction="row" spacing={1} alignItems="center">
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
                        }
                        secondary={
                          <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              変更日時: {formatDate(item.changed_at)}
                            </Typography>
                            {item.duration_days && (
                              <Typography variant="body2" color="text.secondary">
                                利用期間: {formatDuration(item.duration_days)}
                              </Typography>
                            )}
                          </Stack>
                        }
                      />
                    </ListItem>
                    {index < planHistory.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>

              {/* 統計情報 */}
              <Paper sx={{ mt: 2, p: 2, bgcolor: "grey.50" }}>
                <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                  統計情報
                </Typography>
                <Stack direction="row" spacing={3}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      総変更回数
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {planHistory.length}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      デモ→本番への変更
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: "success.main" }}>
                      {planHistory.filter(item => item.from_plan === "demo" && item.to_plan === "production").length}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      本番→デモへの変更
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: "warning.main" }}>
                      {planHistory.filter(item => item.from_plan === "production" && item.to_plan === "demo").length}
                    </Typography>
                  </Box>
                </Stack>
              </Paper>
            </>
          )}
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleClosePlanHistory} variant="outlined">
            閉じる
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default EmployeeUsageTab;
