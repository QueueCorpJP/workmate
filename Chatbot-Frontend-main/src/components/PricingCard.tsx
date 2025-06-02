import React, { useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
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
} from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import StarIcon from "@mui/icons-material/Star";
import BusinessIcon from "@mui/icons-material/Business";
import GroupIcon from "@mui/icons-material/Group";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import QuestionAnswerIcon from "@mui/icons-material/QuestionAnswer";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import SecurityIcon from "@mui/icons-material/Security";

interface PricingPlan {
  id: string;
  name: string;
  price: number;
  period: string;
  description: string;
  features: string[];
  popular?: boolean;
  color: string;
  icon: React.ReactNode;
}

interface PricingCardProps {
  open: boolean;
  onClose: () => void;
  onUpgrade: (planId: string) => void;
}

const pricingPlans: PricingPlan[] = [
  {
    id: "starter",
    name: "スタータープラン",
    price: 2980,
    period: "月",
    description: "小規模チーム向けの基本プラン",
    features: [
      "質問回数無制限",
      "ドキュメントアップロード 10件/月", 
      "基本サポート",
      "1チーム（5名まで）",
    ],
    color: "#3b82f6",
    icon: <GroupIcon />,
  },
  {
    id: "business",
    name: "ビジネスプラン",
    price: 9800,
    period: "月",
    description: "中規模企業向けの高機能プラン",
    features: [
      "質問回数無制限",
      "ドキュメントアップロード 100件/月",
      "優先サポート",
      "5チーム（25名まで）",
      "管理者機能",
      "チャット履歴分析",
    ],
    popular: true,
    color: "#f59e0b",
    icon: <BusinessIcon />,
  },
  {
    id: "enterprise",
    name: "エンタープライズプラン",
    price: 29800,
    period: "月",
    description: "大企業向けのフル機能プラン",
    features: [
      "質問回数無制限",
      "ドキュメントアップロード無制限",
      "24/7専用サポート",
      "無制限チーム・ユーザー",
      "高度な管理者機能",
      "詳細な分析・レポート",
      "カスタムインテグレーション",
      "セキュリティ強化",
    ],
    color: "#8b5cf6",
    icon: <SecurityIcon />,
  },
];

const PricingCard: React.FC<PricingCardProps> = ({ open, onClose, onUpgrade }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async (planId: string) => {
    setLoading(true);
    try {
      await onUpgrade(planId);
    } catch (error) {
      console.error("アップグレードエラー:", error);
    } finally {
      setLoading(false);
    }
  };

  const renderPlanCard = (plan: PricingPlan) => (
    <Card
      key={plan.id}
      sx={{
        position: "relative",
        border: plan.popular ? `2px solid ${plan.color}` : "1px solid rgba(0, 0, 0, 0.1)",
        borderRadius: 3,
        transition: "all 0.2s ease",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        "&:hover": {
          transform: "translateY(-4px)",
          boxShadow: `0 8px 24px ${plan.color}40`,
        },
        ...(plan.popular && {
          "&::before": {
            content: '""',
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: "4px",
            background: `linear-gradient(90deg, ${plan.color}, ${plan.color}80)`,
            borderRadius: "12px 12px 0 0",
          },
        }),
      }}
    >
      {plan.popular && (
        <Chip
          label="人気"
          size="small"
          icon={<StarIcon sx={{ fontSize: "1rem" }} />}
          sx={{
            position: "absolute",
            top: 16,
            right: 16,
            bgcolor: plan.color,
            color: "white",
            fontWeight: 600,
            zIndex: 1,
            "& .MuiChip-icon": {
              color: "white",
            },
          }}
        />
      )}

      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              bgcolor: `${plan.color}20`,
              color: plan.color,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              mr: 2,
            }}
          >
            {plan.icon}
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
              {plan.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {plan.description}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: "flex", alignItems: "baseline", mb: 1 }}>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                color: plan.color,
                mr: 0.5,
              }}
            >
              ¥{plan.price.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              /{plan.period}
            </Typography>
          </Box>
        </Box>

        <List dense sx={{ mb: 2 }}>
          {plan.features.map((feature, index) => (
            <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
              <ListItemIcon sx={{ minWidth: 28 }}>
                <CheckCircleIcon
                  sx={{ fontSize: "1.2rem", color: plan.color }}
                />
              </ListItemIcon>
              <ListItemText
                primary={feature}
                sx={{
                  "& .MuiListItemText-primary": {
                    fontSize: "0.9rem",
                    fontWeight: 500,
                  },
                }}
              />
            </ListItem>
          ))}
        </List>

        <Button
          fullWidth
          variant={plan.popular ? "contained" : "outlined"}
          size="large"
          onClick={() => handleUpgrade(plan.id)}
          disabled={loading}
          sx={{
            mt: "auto",
            borderRadius: 2,
            py: 1.5,
            fontWeight: 600,
            textTransform: "none",
            ...(plan.popular ? {
              bgcolor: plan.color,
              "&:hover": {
                bgcolor: `${plan.color}dd`,
              },
            } : {
              color: plan.color,
              borderColor: plan.color,
              "&:hover": {
                bgcolor: `${plan.color}08`,
                borderColor: plan.color,
              },
            }),
          }}
          startIcon={loading ? <CircularProgress size={16} /> : null}
        >
          {loading ? "処理中..." : "このプランを選択"}
        </Button>
      </CardContent>
    </Card>
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
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
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            🚀 デモ版から本格運用へ
          </Typography>
          <Typography variant="body1" color="text.secondary">
            より多くの機能と無制限の質問で、チームの生産性を向上させましょう
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ px: 3 }}>
        <Box sx={{ mb: 4 }}>
          <Stack
            direction="row"
            spacing={2}
            sx={{
              justifyContent: "center",
              mb: 3,
              flexWrap: "wrap",
              gap: 2,
            }}
          >
            <Chip
              icon={<QuestionAnswerIcon />}
              label="質問回数無制限"
              color="primary"
              variant="outlined"
            />
            <Chip
              icon={<UploadFileIcon />}
              label="大容量アップロード"
              color="primary"
              variant="outlined"
            />
            <Chip
              icon={<SupportAgentIcon />}
              label="優先サポート"
              color="primary"
              variant="outlined"
            />
          </Stack>
        </Box>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "1fr",
              md: "repeat(3, 1fr)",
            },
            gap: 3,
          }}
        >
          {pricingPlans.map(renderPlanCard)}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button
          onClick={onClose}
          variant="outlined"
          sx={{
            borderRadius: 2,
            textTransform: "none",
            fontWeight: 600,
          }}
        >
          後で検討する
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PricingCard; 