import React, { useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Stack,
  useTheme,
  useMediaQuery,
  CircularProgress,
  Alert,
  Snackbar,
  FormControlLabel,
  Checkbox,
  Grid,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import BusinessIcon from "@mui/icons-material/Business";
import EmailIcon from "@mui/icons-material/Email";
import PhoneIcon from "@mui/icons-material/Phone";
import GroupIcon from "@mui/icons-material/Group";
import NoteAddIcon from "@mui/icons-material/NoteAdd";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RocketLaunchIcon from "@mui/icons-material/RocketLaunch";
import api from "../api";

interface ApplicationFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit?: (formData: ApplicationFormData) => void;
}

interface ApplicationFormData {
  companyName: string;
  contactName: string;
  email: string;
  phone: string;
  expectedUsers: string;
  currentUsage: string;
  message: string;
  agreesTerms: boolean;
}

const ApplicationForm: React.FC<ApplicationFormProps> = ({ open, onClose, onSubmit }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [loading, setLoading] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const [formData, setFormData] = useState<ApplicationFormData>({
    companyName: "",
    contactName: "",
    email: "",
    phone: "",
    expectedUsers: "",
    currentUsage: "",
    message: "",
    agreesTerms: false,
  });

  const [formErrors, setFormErrors] = useState<{[key: string]: string}>({});

  const expectedUsersOptions = [
    { value: "1-5", label: "1-5名" },
    { value: "6-20", label: "6-20名" },
    { value: "21-50", label: "21-50名" },
    { value: "51-100", label: "51-100名" },
    { value: "101+", label: "101名以上" },
  ];

  const currentUsageOptions = [
    { value: "demo-only", label: "デモ版のみ利用" },
    { value: "testing", label: "評価・テスト中" },
    { value: "pilot", label: "パイロット運用中" },
    { value: "expanding", label: "利用拡大を検討" },
  ];

  const validateForm = () => {
    const errors: {[key: string]: string} = {};

    if (!formData.companyName.trim()) {
      errors.companyName = "会社名は必須です";
    }
    if (!formData.contactName.trim()) {
      errors.contactName = "担当者名は必須です";
    }
    if (!formData.email.trim()) {
      errors.email = "メールアドレスは必須です";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = "正しいメールアドレスを入力してください";
    }
    if (!formData.expectedUsers) {
      errors.expectedUsers = "予想利用者数を選択してください";
    }
    if (!formData.currentUsage) {
      errors.currentUsage = "現在の利用状況を選択してください";
    }
    if (!formData.agreesTerms) {
      errors.agreesTerms = "利用規約への同意が必要です";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (field: keyof ApplicationFormData, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // エラーをクリア
    if (formErrors[field]) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setSubmitError("");

    try {
      // APIエンドポイントに申請データを送信
      const response = await api.post("/submit-application", {
        ...formData,
        applicationType: "production-upgrade"  // 本番移行申請であることを明示
      });

      if (response.status === 200) {
        setSubmitSuccess(true);
        // onSubmitコールバックがあれば実行
        if (onSubmit) {
          onSubmit(formData);
        }
        
        // フォームをリセット
        setFormData({
          companyName: "",
          contactName: "",
          email: "",
          phone: "",
          expectedUsers: "",
          currentUsage: "",
          message: "",
          agreesTerms: false,
        });
        
        // 3秒後にダイアログを閉じる
        setTimeout(() => {
          onClose();
          setSubmitSuccess(false);
        }, 3000);
      } else {
        throw new Error("申請の送信に失敗しました");
      }
    } catch (error) {
      console.error("申請送信エラー:", error);
      setSubmitError("申請の送信中にエラーが発生しました。しばらく後にもう一度お試しください。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            maxHeight: "90vh",
          },
        }}
      >
        <DialogTitle sx={{ textAlign: "center", pb: 1 }}>
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: "flex", justifyContent: "center", mb: 2 }}>
              <RocketLaunchIcon sx={{ fontSize: 48, color: "primary.main" }} />
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: "primary.main" }}>
              🚀 本番版への移行申請
            </Typography>
            <Typography variant="body1" color="text.secondary">
              デモ版から本番版への移行をご希望の場合は、<br />
              以下のフォームよりお申し込みください。
            </Typography>
          </Box>
        </DialogTitle>

        <DialogContent sx={{ px: 3 }}>
          <Box sx={{ mb: 3 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                申請後、営業担当者よりご連絡いたします。お客様のご利用状況に応じて最適なプランをご提案させていただきます。
              </Typography>
            </Alert>
          </Box>

          <Grid container spacing={3}>
            {/* 会社情報 */}
            <Grid item xs={12}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, display: "flex", alignItems: "center" }}>
                <BusinessIcon sx={{ mr: 1, color: "primary.main" }} />
                会社情報
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="会社名"
                value={formData.companyName}
                onChange={(e) => handleInputChange("companyName", e.target.value)}
                error={!!formErrors.companyName}
                helperText={formErrors.companyName}
                required
                variant="outlined"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="担当者名"
                value={formData.contactName}
                onChange={(e) => handleInputChange("contactName", e.target.value)}
                error={!!formErrors.contactName}
                helperText={formErrors.contactName}
                required
                variant="outlined"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="メールアドレス"
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange("email", e.target.value)}
                error={!!formErrors.email}
                helperText={formErrors.email}
                required
                variant="outlined"
                InputProps={{
                  startAdornment: <EmailIcon sx={{ mr: 1, color: "text.secondary" }} />
                }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="電話番号"
                value={formData.phone}
                onChange={(e) => handleInputChange("phone", e.target.value)}
                variant="outlined"
                InputProps={{
                  startAdornment: <PhoneIcon sx={{ mr: 1, color: "text.secondary" }} />
                }}
                helperText="ご相談をスムーズに進めるため、お電話番号をお教えください"
              />
            </Grid>

            {/* 利用予定情報 */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, display: "flex", alignItems: "center" }}>
                <GroupIcon sx={{ mr: 1, color: "primary.main" }} />
                利用予定情報
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth error={!!formErrors.expectedUsers} required>
                <InputLabel>予想利用者数</InputLabel>
                <Select
                  value={formData.expectedUsers}
                  label="予想利用者数"
                  onChange={(e) => handleInputChange("expectedUsers", e.target.value)}
                >
                  {expectedUsersOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
                {formErrors.expectedUsers && (
                  <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.5 }}>
                    {formErrors.expectedUsers}
                  </Typography>
                )}
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth error={!!formErrors.currentUsage} required>
                <InputLabel>現在の利用状況</InputLabel>
                <Select
                  value={formData.currentUsage}
                  label="現在の利用状況"
                  onChange={(e) => handleInputChange("currentUsage", e.target.value)}
                >
                  {currentUsageOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
                {formErrors.currentUsage && (
                  <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.5 }}>
                    {formErrors.currentUsage}
                  </Typography>
                )}
              </FormControl>
            </Grid>

            {/* 追加情報 */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, display: "flex", alignItems: "center" }}>
                <NoteAddIcon sx={{ mr: 1, color: "primary.main" }} />
                ご要望・ご質問
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="導入予定時期、特別な要件、ご質問など"
                multiline
                rows={4}
                value={formData.message}
                onChange={(e) => handleInputChange("message", e.target.value)}
                placeholder="例：来月から本格導入予定、カスタマイズの相談がしたい、セキュリティ要件について相談したい など"
                variant="outlined"
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.agreesTerms}
                    onChange={(e) => handleInputChange("agreesTerms", e.target.checked)}
                    color="primary"
                  />
                }
                label={
                  <Typography variant="body2">
                    <Box component="span" sx={{ color: formErrors.agreesTerms ? "error.main" : "inherit" }}>
                      利用規約およびプライバシーポリシーに同意します *
                    </Box>
                  </Typography>
                }
              />
              {formErrors.agreesTerms && (
                <Typography variant="caption" color="error" sx={{ display: "block", mt: 0.5, ml: 1.5 }}>
                  {formErrors.agreesTerms}
                </Typography>
              )}
            </Grid>
          </Grid>

          {/* エラーメッセージ */}
          {submitError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {submitError}
            </Alert>
          )}
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button
            onClick={onClose}
            variant="outlined"
            sx={{
              borderRadius: 2,
              textTransform: "none",
              fontWeight: 600,
              px: 3,
            }}
          >
            キャンセル
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <RocketLaunchIcon />}
            sx={{
              borderRadius: 2,
              textTransform: "none",
              fontWeight: 600,
              px: 3,
              background: "linear-gradient(135deg, #2563eb, #3b82f6)",
              "&:hover": {
                background: "linear-gradient(135deg, #1d4ed8, #2563eb)",
              },
            }}
          >
            {loading ? "送信中..." : "本番版への移行を申請"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 送信成功メッセージ */}
      <Snackbar
        open={submitSuccess}
        autoHideDuration={3000}
        onClose={() => setSubmitSuccess(false)}
        anchorOrigin={{ vertical: "top", horizontal: "center" }}
      >
        <Alert
          onClose={() => setSubmitSuccess(false)}
          severity="success"
          variant="filled"
          sx={{
            width: "100%",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
            borderRadius: 2,
          }}
        >
          🎉 本番版への移行申請を受け付けました！営業担当者よりご連絡いたします。
        </Alert>
      </Snackbar>
    </>
  );
};

export default ApplicationForm; 