import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "./api";
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  AppBar,
  Toolbar,
  IconButton,
  Alert,
  Snackbar,
  CircularProgress,
  useTheme,
  useMediaQuery,
  Card,
  Grid,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import BusinessIcon from "@mui/icons-material/Business";
import SaveIcon from "@mui/icons-material/Save";
import InfoIcon from "@mui/icons-material/Info";
import { useCompany } from "./contexts/CompanyContext";
import { useAuth } from "./contexts/AuthContext";

function CompanySettings() {
  const { companyName, setCompanyName } = useCompany();
  const { isEmployee } = useAuth();
  const [newCompanyName, setNewCompanyName] = useState(companyName);
  const [showSuccess, setShowSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  // コンポーネントマウント時にバックエンドから会社名を取得
  useEffect(() => {
    const fetchCompanyName = async () => {
      try {
        const response = await api.get(`${import.meta.env.VITE_API_URL}/company-name`);
        if (response.data && response.data.company_name) {
          setCompanyName(response.data.company_name);
          setNewCompanyName(response.data.company_name);
        }
      } catch (error) {
        console.error("会社名の取得に失敗しました:", error);
        setError("会社名の取得に失敗しました。");
      }
    };

    fetchCompanyName();
  }, [setCompanyName]);

  const handleSave = async () => {
    if (!newCompanyName.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post(`${import.meta.env.VITE_API_URL}/company-name`, {
        company_name: newCompanyName.trim(),
      });

      if (response.data && response.data.company_name) {
        setCompanyName(response.data.company_name);
        setShowSuccess(true);
      }
    } catch (error: any) {
      console.error("会社名の更新に失敗しました:", error);

      // エラーメッセージの詳細を取得
      let errorMessage = "会社名の更新に失敗しました。";
      if (error.response?.data?.detail) {
        errorMessage += ` ${error.response.data.detail}`;
      } else if (error.message) {
        errorMessage += ` ${error.message}`;
      }

      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToChat = () => {
    // URLのreferrerパラメータをチェックして、どこから来たかを判断
    const params = new URLSearchParams(location.search);
    const referrer = params.get('referrer');
    
    // 管理者画面から来た場合は管理者画面に戻る
    if (referrer === 'admin') {
      navigate('/admin');
    } else {
      // それ以外の場合はホーム画面に戻る
      navigate('/');
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "background.default",
        backgroundImage:
          "linear-gradient(to bottom, rgba(37, 99, 235, 0.03), rgba(37, 99, 235, 0.01))",
      }}
    >
      {/* ヘッダー */}
      <AppBar
        position="static"
        color="inherit"
        elevation={0}
        sx={{
          borderBottom: "1px solid rgba(0, 0, 0, 0.05)",
          backgroundColor: "background.paper",
          backdropFilter: "blur(10px)",
        }}
      >
        <Toolbar
          sx={{ minHeight: { xs: "56px", sm: "64px" }, px: { xs: 2, sm: 3 } }}
        >
          <IconButton
            edge="start"
            color="primary"
            onClick={handleBackToChat}
            sx={{
              mr: 1,
              backgroundColor: "rgba(37, 99, 235, 0.08)",
              "&:hover": {
                backgroundColor: "rgba(37, 99, 235, 0.15)",
              },
              transition: "all 0.2s",
            }}
            aria-label="戻る"
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography
            variant={isMobile ? "subtitle1" : "h6"}
            component="div"
            sx={{
              fontWeight: 600,
              color: "primary.main",
              display: "flex",
              alignItems: "center",
            }}
          >
            <BusinessIcon
              sx={{ mr: 1, display: { xs: "none", sm: "inline" } }}
            />
            会社管理
          </Typography>
        </Toolbar>
      </AppBar>

      {/* メインコンテンツ */}
      <Container
        maxWidth="lg"
        sx={{
          flexGrow: 1,
          py: { xs: 3, sm: 4, md: 5 },
          px: { xs: 2, sm: 3, md: 4 },
        }}
      >
        <Paper
          elevation={0}
          sx={{
            borderRadius: 3,
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.08)",
            overflow: "hidden",
            border: "1px solid rgba(37, 99, 235, 0.1)",
            background: "linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)",
            position: "relative",
            "&::before": {
              content: '""',
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              height: "4px",
              background: "linear-gradient(to right, #2563eb, #60a5fa)",
            },
          }}
        >
          {/* コンテンツ */}
          <Box sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
            <Typography
              variant={isMobile ? "h5" : "h4"}
              sx={{
                mb: 4,
                fontWeight: 700,
                color: "text.primary",
                textAlign: "center",
                position: "relative",
                "&:after": {
                  content: '""',
                  position: "absolute",
                  bottom: -12,
                  left: "50%",
                  width: "60px",
                  height: "3px",
                  backgroundColor: "primary.main",
                  transform: "translateX(-50%)",
                  borderRadius: "10px",
                },
              }}
            >
              会社情報設定
            </Typography>

            <Grid container spacing={4}>
              {/* 現在の会社名 */}
              <Grid item xs={12}>
                <Card
                  elevation={0}
                  sx={{
                    p: 3,
                    borderRadius: 2.5,
                    border: "1px solid rgba(37, 99, 235, 0.1)",
                    backgroundColor: "rgba(37, 99, 235, 0.03)",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      boxShadow: "0 8px 24px rgba(37, 99, 235, 0.12)",
                      transform: "translateY(-2px)",
                    },
                  }}
                >
                  <Typography
                    variant="subtitle1"
                    sx={{
                      mb: 1.5,
                      fontWeight: 600,
                      color: "primary.main",
                      display: "flex",
                      alignItems: "center",
                    }}
                  >
                    <BusinessIcon sx={{ mr: 1, fontSize: "1.2rem" }} />
                    現在の会社名
                  </Typography>
                  <Typography
                    variant="h6"
                    sx={{
                      p: 2.5,
                      backgroundColor: "white",
                      borderRadius: 2,
                      border: "1px solid rgba(37, 99, 235, 0.15)",
                      fontWeight: 500,
                      textAlign: "center",
                      color: "text.primary",
                      wordBreak: "break-word",
                      boxShadow: "inset 0 2px 4px rgba(0, 0, 0, 0.02)",
                    }}
                  >
                    {companyName || "未設定"}
                  </Typography>
                </Card>
              </Grid>

              {/* 会社名変更フォーム */}
              <Grid item xs={12}>
                <Card
                  elevation={0}
                  sx={{
                    p: 3,
                    borderRadius: 2.5,
                    border: "1px solid rgba(37, 99, 235, 0.1)",
                    backgroundColor: "white",
                    transition: "all 0.3s ease",
                    position: "relative",
                    overflow: "visible",
                    "&:hover": {
                      boxShadow: "0 8px 24px rgba(0, 0, 0, 0.08)",
                      transform: "translateY(-2px)",
                    },
                  }}
                >
                  <Typography
                    variant="subtitle1"
                    sx={{
                      mb: 1.5,
                      fontWeight: 600,
                      color: "primary.main",
                    }}
                  >
                    新しい会社名
                  </Typography>
                  <TextField
                    fullWidth
                    variant="outlined"
                    placeholder="新しい会社名を入力してください"
                    value={newCompanyName}
                    onChange={(e) => setNewCompanyName(e.target.value)}
                    sx={{
                      mb: 3,
                      "& .MuiOutlinedInput-root": {
                        borderRadius: 2,
                        backgroundColor: "rgba(0, 0, 0, 0.01)",
                        transition: "all 0.3s ease",
                        border: "1px solid rgba(37, 99, 235, 0.1)",
                        "&:hover": {
                          boxShadow: "0 0 0 2px rgba(37, 99, 235, 0.15)",
                        },
                        "&.Mui-focused": {
                          boxShadow: "0 0 0 2px rgba(37, 99, 235, 0.25)",
                        },
                      },
                    }}
                  />
                  {!isEmployee && (
                    <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={handleSave}
                        disabled={
                          isLoading ||
                          !newCompanyName.trim() ||
                          newCompanyName === companyName
                        }
                        startIcon={
                          isLoading ? (
                            <CircularProgress size={20} color="inherit" />
                          ) : (
                            <SaveIcon />
                          )
                        }
                        sx={{
                          py: 1.2,
                          px: 3,
                          fontWeight: 600,
                          borderRadius: 2,
                          boxShadow: "0 4px 14px rgba(37, 99, 235, 0.25)",
                          background:
                            "linear-gradient(to right, #2563eb, #3b82f6)",
                          "&:hover": {
                            boxShadow: "0 6px 20px rgba(37, 99, 235, 0.35)",
                            background:
                              "linear-gradient(to right, #1d4ed8, #2563eb)",
                          },
                          transition: "all 0.3s ease",
                        }}
                      >
                        {isLoading ? "保存中..." : "保存する"}
                      </Button>
                    </Box>
                  )}

                  {error && (
                    <Alert
                      severity="error"
                      sx={{
                        mt: 3,
                        borderRadius: 2,
                        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
                      }}
                    >
                      {error}
                    </Alert>
                  )}
                </Card>
              </Grid>

              {/* 情報 */}
              <Grid item xs={12}>
                <Alert
                  severity="info"
                  icon={<InfoIcon />}
                  sx={{
                    borderRadius: 2,
                    boxShadow: "0 4px 12px rgba(37, 99, 235, 0.08)",
                    border: "1px solid rgba(37, 99, 235, 0.1)",
                    backgroundColor: "rgba(37, 99, 235, 0.03)",
                    "& .MuiAlert-message": {
                      fontSize: "0.95rem",
                    },
                    "& .MuiAlert-icon": {
                      color: "primary.main",
                    },
                  }}
                >
                  会社名は、チャットボットのカスタマイズや社内向けレポートに使用されます。いつでも変更できます。
                </Alert>
              </Grid>
            </Grid>
          </Box>
        </Paper>
      </Container>

      {/* 成功メッセージ */}
      <Snackbar
        open={showSuccess}
        autoHideDuration={6000}
        onClose={() => setShowSuccess(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          onClose={() => setShowSuccess(false)}
          severity="success"
          sx={{
            borderRadius: 2,
            boxShadow: "0 8px 24px rgba(76, 175, 80, 0.2)",
            border: "1px solid rgba(76, 175, 80, 0.3)",
          }}
        >
          会社名を正常に更新しました！
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default CompanySettings;
