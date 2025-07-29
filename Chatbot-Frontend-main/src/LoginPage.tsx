import React, { useState } from "react";
import { useNavigate, Link as RouterLink } from "react-router-dom";
import {
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Alert,
  useMediaQuery,
  useTheme,
  Avatar,
  Link,
  AppBar,
  Toolbar,
  FormHelperText,
} from "@mui/material";
import { useAuth } from "./contexts/AuthContext";
import { useCompany } from "./contexts/CompanyContext";
import ChatIcon from "@mui/icons-material/Chat";
import HomeIcon from "@mui/icons-material/Home";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import { validateEmail, validatePassword } from "./utils/validation";

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string>("");
  const [passwordError, setPasswordError] = useState<string>("");
  const [showValidation, setShowValidation] = useState(false);
  
  const { login } = useAuth();
  const { companyName, setCompanyName } = useCompany();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isTablet = useMediaQuery(theme.breakpoints.between("sm", "md"));

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmail(value);
    
    if (showValidation) {
      const validation = validateEmail(value);
      setEmailError(validation.isValid ? "" : validation.message);
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPassword(value);
    
    if (showValidation) {
      const validation = validatePassword(value);
      setPasswordError(validation.isValid ? "" : validation.message);
    }
  };

  const validateForm = () => {
    const emailValidation = validateEmail(email);
    const passwordValidation = validatePassword(password);
    
    setEmailError(emailValidation.isValid ? "" : emailValidation.message);
    setPasswordError(passwordValidation.isValid ? "" : passwordValidation.message);
    
    return emailValidation.isValid && passwordValidation.isValid;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setShowValidation(true);
    setIsLoading(true);
    setError(null);

    // フォームバリデーション
    if (!validateForm()) {
      setIsLoading(false);
      return;
    }

    try {
      await login(email, password);
      setCompanyName(localStorage.getItem("companyName") || "");
      navigate("/");
    } catch (err: any) {
      console.error("Login error:", err);
      setError(
        err.response?.data?.detail ||
          "ログインに失敗しました。メールアドレスとパスワードを確認してください。"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "white",
        backgroundImage:
          "radial-gradient(rgba(37, 99, 235, 0.02) 1px, transparent 0)",
        backgroundSize: "20px 20px",
      }}
    >
      {/* Header */}
      <AppBar
        position="static"
        elevation={0}
        sx={{
          background: "white",
          borderBottom: "1px solid rgba(37, 99, 235, 0.08)",
        }}
      >
        <Toolbar
          sx={{
            justifyContent: "space-between",
            padding: {
              xs: "0.6rem 1rem",
              sm: "0.7rem 1.5rem",
              md: "0.8rem 2rem",
            },
            minHeight: { xs: "80px", sm: "90px", md: "120px" },
            flexDirection: { xs: "column", sm: "row" },
            alignItems: "center",
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: { xs: "center", sm: "flex-start" },
              flexGrow: 0,
              mr: { sm: 2, md: 4 },
              mb: { xs: 1, sm: 0 },
            }}
          >
            <img
              src="/images/queue-logo.png"
              alt="ワークメイトAI Logo"
              style={{
                height: "auto",
                width: "auto",
                maxHeight: 110,
                maxWidth: "100%",
                marginRight: 16,
              }}
            />
          </Box>
          <Box
            sx={{
              display: "flex",
              flexDirection: { xs: "column", sm: "row" },
              gap: { xs: 1, sm: 2 },
              width: { xs: "100%", sm: "auto" },
            }}
          >
            <Button
              variant="outlined"
              color="primary"
              startIcon={<HomeIcon />}
              fullWidth={isMobile}
              sx={{
                borderRadius: 2.5,
                textTransform: "none",
                fontWeight: 600,
                px: 2.5,
                py: 1,
                borderColor: "rgba(37, 99, 235, 0.3)",
                "&:hover": {
                  borderColor: "primary.main",
                  backgroundColor: "rgba(37, 99, 235, 0.04)",
                },
              }}
              onClick={() =>
                window.open("https://www.workmate-ai.com", "_blank")
              }
            >
              ホームページ
            </Button>
            <Button
              variant="contained"
              color="primary"
              startIcon={<InfoOutlinedIcon />}
              fullWidth={isMobile}
              sx={{
                borderRadius: 2.5,
                textTransform: "none",
                fontWeight: 600,
                px: 2.5,
                py: 1,
                background: "linear-gradient(45deg, #2563eb, #3b82f6)",
                boxShadow: "0 4px 10px rgba(37, 99, 235, 0.2)",
                "&:hover": {
                  background: "linear-gradient(45deg, #1d4ed8, #2563eb)",
                  boxShadow: "0 6px 15px rgba(37, 99, 235, 0.25)",
                },
              }}
              component={RouterLink}
              to="/guide"
            >
              ガイドブック
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          padding: { xs: 2, sm: 3, md: 4 },
          pt: { xs: 3, sm: 5, md: 6 },
          pb: { xs: 3, sm: 5, md: 6 },
        }}
      >
        <Container
          maxWidth="sm"
          sx={{
            width: "100%",
            animation: "fadeIn 0.5s ease-out",
          }}
        >
          <Paper
            elevation={0}
            sx={{
              p: { xs: 2.5, sm: 3.5 },
              width: "100%",
              borderRadius: { xs: 3, sm: 4 },
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              overflow: "hidden",
              boxShadow: "0 10px 40px rgba(37, 99, 235, 0.08)",
              background: "white",
              border: "1px solid rgba(37, 99, 235, 0.06)",
              position: "relative",
            }}
          >
            {/* Blue bar at top */}
            <Box
              sx={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                height: "4px",
                background: "linear-gradient(to right, #2563eb, #60a5fa)",
              }}
            />

            <Box
              sx={{
                mb: 4,
                width: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}
            >
              {/* Logo Section */}
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  width: "100%",
                  mb: 4,
                  pt: 2,
                }}
              >
                {/* Company Name */}
                <Typography
                  variant="h3"
                  component="div"
                  sx={{
                    fontWeight: 800,
                    color: "#2563EB",
                    textAlign: "center",
                    background:
                      "linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)",
                    backgroundClip: "text",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    mb: 2,
                    letterSpacing: "0.5px",
                  }}
                >
                  ワークメイトAI
                </Typography>

                {/* AI Assistant Badge */}
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: "rgba(37, 99, 235, 0.06)",
                    borderRadius: 3,
                    py: 0.8,
                    px: 2,
                    mt: 1,
                  }}
                >
                  <Avatar
                    sx={{
                      width: 24,
                      height: 24,
                      bgcolor: "#2563EB",
                      mr: 1,
                    }}
                  >
                    <ChatIcon sx={{ fontSize: "1rem" }} />
                  </Avatar>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 600,
                      color: "#2563EB",
                    }}
                  >
                    AIアシスタント
                  </Typography>
                </Box>
              </Box>

              {/* Login Title */}
              <Typography
                variant="h5"
                component="h2"
                sx={{
                  fontWeight: 600,
                  color: "#2563EB",
                  mb: 3,
                  textAlign: "center",
                }}
              >
                ログイン
              </Typography>
            </Box>

            <Box
              component="form"
              onSubmit={handleLogin}
              sx={{
                width: "100%",
                "& .MuiTextField-root": {
                  mb: 3,
                },
              }}
            >
              <TextField
                required
                fullWidth
                id="email"
                label="メールアドレス"
                name="email"
                autoComplete="email"
                autoFocus={!isMobile}
                value={email}
                onChange={handleEmailChange}
                InputProps={{
                  sx: {
                    borderRadius: 2,
                    backgroundColor: "rgba(255, 255, 255, 0.8)",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      boxShadow: "0 0 0 1px rgba(37, 99, 235, 0.15)",
                    },
                    "&.Mui-focused": {
                      boxShadow: "0 0 0 2px rgba(37, 99, 235, 0.2)",
                      backgroundColor: "white",
                    },
                  },
                }}
              />
              {emailError && (
                <FormHelperText error sx={{ mt: -2.5, mb: 2 }}>
                  {emailError}
                </FormHelperText>
              )}
              
              <TextField
                required
                fullWidth
                name="password"
                label="パスワード"
                type="password"
                id="password"
                autoComplete="current-password"
                value={password}
                onChange={handlePasswordChange}
                InputProps={{
                  sx: {
                    borderRadius: 2,
                    backgroundColor: "rgba(255, 255, 255, 0.8)",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      boxShadow: "0 0 0 1px rgba(37, 99, 235, 0.15)",
                    },
                    "&.Mui-focused": {
                      boxShadow: "0 0 0 2px rgba(37, 99, 235, 0.2)",
                      backgroundColor: "white",
                    },
                  },
                }}
              />
              {passwordError && (
                <FormHelperText error sx={{ mt: -2.5, mb: 2 }}>
                  {passwordError}
                </FormHelperText>
              )}
              
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{
                  mt: 1,
                  mb: 2,
                  py: 1.6,
                  borderRadius: 10,
                  fontSize: "1rem",
                  fontWeight: 600,
                  boxShadow: "0 4px 12px rgba(37, 99, 235, 0.2)",
                  background: "#2563EB",
                  "&:hover": {
                    boxShadow: "0 6px 16px rgba(37, 99, 235, 0.25)",
                    background: "#1D4ED8",
                  },
                  transition: "all 0.3s ease",
                }}
                disabled={isLoading}
                endIcon={<ArrowForwardIcon />}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  "ログイン"
                )}
              </Button>
            </Box>

            {error && (
              <Alert
                severity="error"
                sx={{
                  width: "100%",
                  mt: 2,
                  borderRadius: 2,
                  border: "1px solid rgba(211, 47, 47, 0.1)",
                }}
              >
                {error}
              </Alert>
            )}

            {/* Footer Links */}
            <Box
              sx={{
                mt: 4,
                width: "100%",
                display: "flex",
                justifyContent: "center",
                flexDirection: { xs: "column", sm: "row" },
                alignItems: "center",
                gap: { xs: 2, sm: 3 },
              }}
            >
              <Link
                href="https://www.workmate-ai.com"
                target="_blank"
                rel="noopener"
                sx={{
                  color: "#64748b",
                  textDecoration: "none",
                  fontSize: "0.875rem",
                  transition: "color 0.2s",
                  "&:hover": {
                    color: "#2563EB",
                  },
                }}
              >
                ホームページ
              </Link>
              <Link
                component={RouterLink}
                to="/guide"
                sx={{
                  color: "#64748b",
                  textDecoration: "none",
                  fontSize: "0.875rem",
                  transition: "color 0.2s",
                  "&:hover": {
                    color: "#2563EB",
                  },
                }}
              >
                ガイドブック
              </Link>
              <Link
                component={RouterLink}
                to="/password-reset"
                sx={{
                  color: "#64748b",
                  textDecoration: "none",
                  fontSize: "0.875rem",
                  transition: "color 0.2s",
                  "&:hover": {
                    color: "#2563EB",
                  },
                }}
              >
                パスワードリセット
              </Link>
              <Link
                href="#"
                sx={{
                  color: "#64748b",
                  textDecoration: "none",
                  fontSize: "0.875rem",
                  transition: "color 0.2s",
                  "&:hover": {
                    color: "#2563EB",
                  },
                }}
              >
                お問い合わせ対応
              </Link>
            </Box>
          </Paper>
        </Container>
      </Box>
    </Box>
  );
}

export default LoginPage;
