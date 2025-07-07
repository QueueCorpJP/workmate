import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
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
  AppBar,
  Toolbar,
  IconButton,
  FormHelperText,
} from "@mui/material";
import { useAuth } from "./contexts/AuthContext";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SaveIcon from "@mui/icons-material/Save";
import PersonIcon from "@mui/icons-material/Person";
import { validateEmail } from "./utils/validation";

function ProfilePage() {
  const { user, updateProfile } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  const [name, setName] = useState(user?.name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string>("");
  const [emailError, setEmailError] = useState<string>("");
  const [showValidation, setShowValidation] = useState(false);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setName(value);
    
    if (showValidation) {
      if (!value.trim()) {
        setNameError("名前を入力してください");
      } else if (value.trim().length < 1) {
        setNameError("名前は1文字以上で入力してください");
      } else {
        setNameError("");
      }
    }
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmail(value);
    
    if (showValidation) {
      const validation = validateEmail(value);
      setEmailError(validation.isValid ? "" : validation.message);
    }
  };

  const validateForm = () => {
    const emailValidation = validateEmail(email);
    
    setEmailError(emailValidation.isValid ? "" : emailValidation.message);
    
    if (!name.trim()) {
      setNameError("名前を入力してください");
      return false;
    } else if (name.trim().length < 1) {
      setNameError("名前は1文字以上で入力してください");
      return false;
    } else {
      setNameError("");
    }
    
    return emailValidation.isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setShowValidation(true);
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    if (!validateForm()) {
      setIsLoading(false);
      return;
    }

    try {
      await updateProfile(name.trim(), email);
      setSuccess("プロフィールが正常に更新されました。");
      setTimeout(() => {
        navigate("/");
      }, 2000);
    } catch (err: any) {
      console.error("Profile update error:", err);
      setError(
        err.response?.data?.detail ||
          "プロフィールの更新に失敗しました。入力内容を確認してください。"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoBack = () => {
    navigate("/");
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
          background: "linear-gradient(135deg, #2563eb, #3b82f6)",
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
            minHeight: { xs: "64px", sm: "70px", md: "80px" },
            alignItems: "center",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <IconButton
              edge="start"
              color="inherit"
              onClick={handleGoBack}
              sx={{
                mr: 2,
                backgroundColor: "rgba(255, 255, 255, 0.1)",
                "&:hover": {
                  backgroundColor: "rgba(255, 255, 255, 0.2)",
                },
              }}
            >
              <ArrowBackIcon />
            </IconButton>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <PersonIcon sx={{ fontSize: "1.5rem" }} />
              <Typography
                variant="h6"
                component="div"
                sx={{
                  fontWeight: 600,
                  color: "white",
                }}
              >
                プロフィール編集
              </Typography>
            </Box>
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
              p: { xs: 3, sm: 4 },
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

            {/* Title Section */}
            <Box
              sx={{
                mb: 4,
                width: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                pt: 2,
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: "rgba(37, 99, 235, 0.06)",
                  borderRadius: 3,
                  py: 1,
                  px: 2.5,
                  mb: 2,
                }}
              >
                <PersonIcon
                  sx={{
                    fontSize: "1.5rem",
                    color: "#2563EB",
                    mr: 1,
                  }}
                />
                <Typography
                  variant="h5"
                  sx={{
                    fontWeight: 700,
                    color: "#2563EB",
                  }}
                >
                  プロフィール情報
                </Typography>
              </Box>
              <Typography
                variant="body2"
                sx={{
                  color: "text.secondary",
                  textAlign: "center",
                  maxWidth: "400px",
                }}
              >
                お名前とメールアドレスを編集できます
              </Typography>
            </Box>

            {/* Form */}
            <Box
              component="form"
              onSubmit={handleSubmit}
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
                id="name"
                label="お名前"
                name="name"
                autoComplete="name"
                autoFocus={!isMobile}
                value={name}
                onChange={handleNameChange}
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
              {nameError && (
                <FormHelperText error sx={{ mt: -2.5, mb: 2 }}>
                  {nameError}
                </FormHelperText>
              )}
              
              <TextField
                required
                fullWidth
                id="email"
                label="メールアドレス"
                name="email"
                autoComplete="email"
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
              
              <Box sx={{ display: "flex", gap: 2, mt: 3 }}>
                <Button
                  onClick={handleGoBack}
                  fullWidth
                  variant="outlined"
                  sx={{
                    py: 1.6,
                    borderRadius: 10,
                    fontSize: "1rem",
                    fontWeight: 600,
                    borderColor: "rgba(37, 99, 235, 0.3)",
                    color: "#2563EB",
                    "&:hover": {
                      borderColor: "#2563EB",
                      backgroundColor: "rgba(37, 99, 235, 0.04)",
                    },
                    transition: "all 0.3s ease",
                  }}
                  disabled={isLoading}
                >
                  キャンセル
                </Button>
                
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  sx={{
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
                  endIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                >
                  {isLoading ? "更新中..." : "保存"}
                </Button>
              </Box>
            </Box>

            {/* Success Message */}
            {success && (
              <Alert
                severity="success"
                sx={{
                  width: "100%",
                  mt: 3,
                  borderRadius: 2,
                  border: "1px solid rgba(76, 175, 80, 0.1)",
                }}
              >
                {success}
              </Alert>
            )}

            {/* Error Message */}
            {error && (
              <Alert
                severity="error"
                sx={{
                  width: "100%",
                  mt: 3,
                  borderRadius: 2,
                  border: "1px solid rgba(211, 47, 47, 0.1)",
                }}
              >
                {error}
              </Alert>
            )}
          </Paper>
        </Container>
      </Box>
    </Box>
  );
}

export default ProfilePage; 