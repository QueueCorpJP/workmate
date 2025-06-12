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

} from "@mui/material";
import PersonAddIcon from "@mui/icons-material/PersonAdd";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import GroupIcon from "@mui/icons-material/Group";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import EmailIcon from "@mui/icons-material/Email";
import BusinessIcon from "@mui/icons-material/Business";
import LoadingIndicator from "./LoadingIndicator";

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
            社員アカウントにはユーザー作成権限がありません。<br />
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
              ユーザー管理
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
        </Grid>
      </Box>
    </Fade>
  );
};

export default UserManagementTab;
