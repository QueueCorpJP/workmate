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
import BusinessIcon from "@mui/icons-material/Business";
import PeopleIcon from "@mui/icons-material/People";
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
    (user?.email && ["queue@queuefood.co.jp", "queue@queueu-tech.jp"].includes(user.email));
  const isQueueTechAdmin = user?.email === "queue@queueu-tech.jp";
  

  
  const [emailError, setEmailError] = useState<string>("");
  const [passwordError, setPasswordError] = useState<string>("");
  const [showValidation, setShowValidation] = useState(false);
  
  // プラン履歴ダイアログの状態
  const [planHistoryOpen, setPlanHistoryOpen] = useState(false);
  const [selectedUserForHistory, setSelectedUserForHistory] = useState<CompanyEmployee | null>(null);
  const [planHistory, setPlanHistory] = useState<PlanHistoryItem[]>([]);
  const [isPlanHistoryLoading, setIsPlanHistoryLoading] = useState(false);
  
  // queue@queueu-tech.jp用の社員表示ダイアログ
  const [employeeDialogOpen, setEmployeeDialogOpen] = useState(false);  
  const [selectedCompanyAdmin, setSelectedCompanyAdmin] = useState<CompanyEmployee | null>(null);
  const [selectedCompanyEmployees, setSelectedCompanyEmployees] = useState<CompanyEmployee[]>([]);

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
      return;
    }
    
    setShowValidation(true);
    
    if (validateForm()) {
      onCreateEmployee(role);
    }
  };

  const passwordStrength = getPasswordStrength(newEmployeePassword);

  // 社長ごとに社員をグループ化する関数（queue@queueu-tech.jp用）
  const groupEmployeesByPresident = () => {
    console.log("=== 社長別グループ化開始 ===");
    console.log("全社員データ:", companyEmployees);
    
    // まず社長（userロール）を抽出
    const presidents = companyEmployees.filter(employee => 
      employee.role === 'user' || employee.role === 'admin'
    );
    
    console.log("社長一覧:", presidents);
    
    // 各社長に対して、同じ会社の社員を紐づける
    const result = presidents.map(president => {
      // 社長の会社IDを取得（emailドメインを使用）
      const presidentCompanyId = president.email.split('@')[1];
      
      // 同じ会社の社員（employeeロール）を検索
      const employees = companyEmployees.filter(employee => {
        if (employee.role !== 'employee') return false;
        
        const employeeCompanyId = employee.email.split('@')[1];
        return employeeCompanyId === presidentCompanyId;
      });
      
      return {
        president,
        employees,
        companyId: presidentCompanyId
      };
    });
    
    return result;
  };

  // 社長カードをクリックした時の処理
  const handlePresidentClick = (president: CompanyEmployee) => {
    const groupedData = groupEmployeesByPresident();
    const presidentData = groupedData.find(group => group.president.id === president.id);
    
    if (presidentData) {
      setSelectedCompanyAdmin(president);
      setSelectedCompanyEmployees(presidentData.employees);
      setEmployeeDialogOpen(true);
    }
  };

  // 社員ダイアログを閉じる
  const handleCloseEmployeeDialog = () => {
    setEmployeeDialogOpen(false);
    setSelectedCompanyAdmin(null);
    setSelectedCompanyEmployees([]);
  };

  // queue@queueu-tech.jp用の社長カード表示
  const renderPresidentCards = () => {
    const groupedData = groupEmployeesByPresident();
    
    if (groupedData.length === 0) {
      return (
        <EmptyState
          message="社長データがありません"
          icon="custom"
          customIcon={<BusinessIcon />}
        />
      );
    }

    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
          社長一覧
        </Typography>
        <Grid container spacing={3}>
          {groupedData.map((group, index) => (
            <Grid item xs={12} sm={6} md={4} key={group.president.id}>
              <Card
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
                    borderColor: 'primary.main',
                  },
                  border: '2px solid rgba(0,0,0,0.08)',
                  borderRadius: 3,
                }}
                onClick={() => handlePresidentClick(group.president)}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56, mr: 2 }}>
                      {(group.president.name || group.president.email).charAt(0).toUpperCase()}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                        {group.president.name || group.president.email.split('@')[0]}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        社長・管理者
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      メールアドレス
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {group.president.email}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      会社ドメイン
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {group.companyId}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      アカウント作成日
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {new Date(group.president.created_at).toLocaleDateString('ja-JP')}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      メッセージ数
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {group.president.message_count || 0}回
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      最終アクティビティ
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {group.president.last_activity 
                        ? new Date(group.president.last_activity).toLocaleDateString('ja-JP')
                        : '活動なし'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                    <Chip
                      label={group.president.usage_limits?.is_unlimited ? "本番版" : "デモ版"}
                      color={group.president.usage_limits?.is_unlimited ? "success" : "warning"}
                      size="small"
                    />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PeopleIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="body2" color="text.secondary">
                        社員 {group.employees.length}名
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                    <Tooltip title={`${group.president.usage_limits?.is_unlimited ? 'デモ版' : '本番版'}に切り替え`}>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleDemo(group.president);
                        }}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="プラン変更履歴を表示">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenPlanHistory(group.president);
                        }}
                        color="primary"
                      >
                        <HistoryIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  };

  const handleToggleDemo = async (employee: CompanyEmployee) => {
    // admin権限チェック
    if (!isAdmin) {
      console.log("Admin権限がありません", { user, isAdmin, isQueueTechAdmin });
      alert("管理者権限がありません");
      return;
    }
    
    try {
      // is_unlimitedの逆の値を設定（現在がfalse(デモ版)ならtrue(本番版)に、現在がtrue(本番版)ならfalse(デモ版)に）
      const newIsUnlimited = !employee.usage_limits?.is_unlimited;
      
      console.log("デモ/本番切り替え開始", {
        employeeId: employee.id,
        employeeEmail: employee.email,
        currentStatus: employee.usage_limits?.is_unlimited ? "本番版" : "デモ版",
        newStatus: newIsUnlimited ? "本番版" : "デモ版",
        currentUser: user?.email,
        isAdmin,
        isQueueTechAdmin
      });
      
      const response = await api.post(`/admin/update-user-status/${employee.id}`, {
        is_unlimited: newIsUnlimited
      });
      
      console.log("切り替え成功", response.data);
      alert(`${employee.email}を${newIsUnlimited ? "本番版" : "デモ版"}に切り替えました`);
      
      // 社員一覧を再読み込み
      onRefreshCompanyEmployees();
    } catch (error: any) {
      console.error("デモ/本番切り替えエラー", error);
      const errorMessage = error.response?.data?.detail || error.message || "切り替えに失敗しました";
      alert(`エラー: ${errorMessage}`);
    }
  };

  // プラン履歴ダイアログを開く
  const handleOpenPlanHistory = async (employee: CompanyEmployee) => {
    setSelectedUserForHistory(employee);
    setPlanHistoryOpen(true);
    setIsPlanHistoryLoading(true);
    
    try {
      const response = await api.get("/plan-history");
      
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
          会社の管理アカウント利用状況
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
        ) : isQueueTechAdmin ? (
          // queue@queueu-tech.jp専用表示
          renderPresidentCards()
        ) : (
          // 通常のテーブル表示
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
                  {isAdmin && (
                    <>
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
                    </>
                  )}
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
                    {isAdmin && (
                      <>
                        <TableCell>
                          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
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
                      </>
                    )}
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

              {/* 利用状況カード（queue@queueu-tech.jpは非表示） */}
      {!isQueueTechAdmin && (
        <>
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
        </>
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

      {/* 社員一覧ダイアログ（queue@queueu-tech.jp専用） */}
      <Dialog
        open={employeeDialogOpen}
        onClose={handleCloseEmployeeDialog}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            maxHeight: "90vh",
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
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <BusinessIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              社員一覧
            </Typography>
            {selectedCompanyAdmin && (
              <Chip
                label={selectedCompanyAdmin.email.split('@')[1]}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
          </Box>
          <IconButton onClick={handleCloseEmployeeDialog} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ pt: 1 }}>
          {selectedCompanyAdmin && (
            <>
              {/* 管理者情報 */}
              <Paper sx={{ p: 2, mb: 3, bgcolor: 'rgba(25, 118, 210, 0.04)' }}>
                <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600, color: 'primary.main' }}>
                  管理者アカウント
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    {(selectedCompanyAdmin.name || selectedCompanyAdmin.email).charAt(0).toUpperCase()}
                  </Avatar>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {selectedCompanyAdmin.name || selectedCompanyAdmin.email}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedCompanyAdmin.email}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Chip
                      label={selectedCompanyAdmin.usage_limits?.is_unlimited ? "本番版" : "デモ版"}
                      color={selectedCompanyAdmin.usage_limits?.is_unlimited ? "success" : "warning"}
                      size="small"
                    />
                    <Tooltip title={`${selectedCompanyAdmin.usage_limits?.is_unlimited ? 'デモ版' : '本番版'}に切り替え`}>
                      <IconButton
                        size="small"
                        onClick={() => handleToggleDemo(selectedCompanyAdmin)}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="プラン変更履歴を表示">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenPlanHistory(selectedCompanyAdmin)}
                        color="primary"
                      >
                        <HistoryIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
              </Paper>

              {/* 社員一覧 */}
              <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                社員アカウント ({selectedCompanyEmployees.length}名)
              </Typography>
              
              {selectedCompanyEmployees.length > 0 ? (
                <Grid container spacing={2}>
                  {selectedCompanyEmployees.map((employee) => (
                    <Grid item xs={12} sm={6} key={employee.id}>
                      <Card sx={{ 
                        transition: 'all 0.2s',
                        '&:hover': { 
                          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                        }
                      }}>
                        <CardContent sx={{ p: 2 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                            <Avatar sx={{ width: 40, height: 40, bgcolor: 'grey.400' }}>
                              {(employee.name || employee.email).charAt(0).toUpperCase()}
                            </Avatar>
                            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                              <Typography variant="body1" sx={{ fontWeight: 600 }} noWrap>
                                {employee.name || employee.email}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" noWrap>
                                {employee.email}
                              </Typography>
                            </Box>
                          </Box>
                          
                          <Box sx={{ mb: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="caption" color="text.secondary">メッセージ数:</Typography>
                              <Typography variant="caption" sx={{ fontWeight: 500 }}>
                                {employee.message_count || 0}回
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="caption" color="text.secondary">作成日:</Typography>
                              <Typography variant="caption" sx={{ fontWeight: 500 }}>
                                {new Date(employee.created_at).toLocaleDateString('ja-JP')}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="caption" color="text.secondary">最終利用:</Typography>
                              <Typography variant="caption" sx={{ fontWeight: 500 }}>
                                {employee.last_activity 
                                  ? new Date(employee.last_activity).toLocaleDateString('ja-JP')
                                  : '活動なし'}
                              </Typography>
                            </Box>
                            {!employee.usage_limits?.is_unlimited && (
                              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="caption" color="text.secondary">利用制限:</Typography>
                                <Typography variant="caption" sx={{ fontWeight: 500 }}>
                                  {employee.usage_limits?.questions_used || 0}/{employee.usage_limits?.questions_limit || 0}
                                </Typography>
                              </Box>
                            )}
                          </Box>
                          
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Chip
                              label={employee.usage_limits?.is_unlimited ? "本番版" : "デモ版"}
                              color={employee.usage_limits?.is_unlimited ? "success" : "warning"}
                              size="small"
                            />
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Tooltip title={`${employee.usage_limits?.is_unlimited ? 'デモ版' : '本番版'}に切り替え`}>
                                <IconButton
                                  size="small"
                                  onClick={() => handleToggleDemo(employee)}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="プラン変更履歴を表示">
                                <IconButton
                                  size="small"
                                  onClick={() => handleOpenPlanHistory(employee)}
                                >
                                  <HistoryIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <PeopleIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                    社員アカウントがありません
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    この会社にはまだ社員アカウントが作成されていません。
                  </Typography>
                </Box>
              )}
            </>
          )}
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleCloseEmployeeDialog} variant="outlined">
            閉じる
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default EmployeeUsageTab;
