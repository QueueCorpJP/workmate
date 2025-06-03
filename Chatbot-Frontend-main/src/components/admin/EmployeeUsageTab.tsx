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
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import EditIcon from "@mui/icons-material/Edit";
import { EmployeeUsageItem, CompanyEmployee, categoryColors } from "./types";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";
import { formatDate } from "./utils";
import EmployeeDetailsDialog from "./EmployeeDetailsDialog";
import api from "../../api";
import { validateEmail, validatePassword, getPasswordStrength } from "../../utils/validation";

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
  const [emailError, setEmailError] = useState<string>("");
  const [passwordError, setPasswordError] = useState<string>("");
  const [showValidation, setShowValidation] = useState(false);

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
    setShowValidation(true);
    
    if (validateForm()) {
      onCreateEmployee(role);
    }
  };

  const passwordStrength = getPasswordStrength(newEmployeePassword);

  const handleToggleDemo = async (employee: CompanyEmployee) => {
    try {
      const newIsUnlimited = !!employee.is_demo || !employee.usage_limits?.is_unlimited;
      
      await api.post(`/admin/update-user-status/${employee.id}`, {
        is_unlimited: newIsUnlimited
      });
      
      // 社員一覧を再読み込み
      onRefreshCompanyEmployees();
    } catch (error) {
      console.error("ステータス変更エラー:", error);
    }
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

      {/* 社員作成フォーム */}
      {showEmployeeCreateForm && (
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
                        <Tooltip title={`クリックで${employee.is_demo || !employee.usage_limits?.is_unlimited ? '本番版' : 'デモ版'}に切り替え`}>
                          <Checkbox
                            checked={!!employee.is_demo || !employee.usage_limits?.is_unlimited}
                            onChange={() => handleToggleDemo(employee)}
                            size="small"
                            sx={{
                              color: employee.is_demo || !employee.usage_limits?.is_unlimited ? "warning.main" : "success.main",
                              '&.Mui-checked': {
                                color: employee.is_demo || !employee.usage_limits?.is_unlimited ? "warning.main" : "success.main",
                              }
                            }}
                          />
                        </Tooltip>
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            ml: 0.5, 
                            color: employee.is_demo || !employee.usage_limits?.is_unlimited ? "warning.main" : "success.main",
                            fontWeight: 500
                          }}
                        >
                          {employee.is_demo || !employee.usage_limits?.is_unlimited ? "デモ版" : "本番版"}
                        </Typography>
                      </Box>
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
    </>
  );
};

export default EmployeeUsageTab;
