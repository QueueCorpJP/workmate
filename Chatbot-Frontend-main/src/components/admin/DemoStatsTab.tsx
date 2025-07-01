import React from "react";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  Grid,
  Divider,
  Tooltip,
  Chip,
  IconButton,
  useTheme,
  useMediaQuery,
  Fade,
  alpha,
} from "@mui/material";
import { DemoStats } from "./types";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";
import QueryStatsIcon from "@mui/icons-material/QueryStats";
import RefreshIcon from "@mui/icons-material/Refresh";
import PeopleIcon from "@mui/icons-material/People";
import PersonIcon from "@mui/icons-material/Person";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import HelpIcon from "@mui/icons-material/Help";
import ErrorIcon from "@mui/icons-material/Error";
import PercentIcon from "@mui/icons-material/Percent";
import AverageIcon from "@mui/icons-material/ShowChart";
import BusinessIcon from "@mui/icons-material/Business";

interface DemoStatsTabProps {
  demoStats: DemoStats | null;
  isLoading: boolean;
  onRefresh: () => void;
  onOpenCompanyDetails?: () => void;
  isCompanyDetailsLoading?: boolean;
}

const DemoStatsTab: React.FC<DemoStatsTabProps> = ({
  demoStats,
  isLoading,
  onRefresh,
  onOpenCompanyDetails,
  isCompanyDetailsLoading,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isTablet = useMediaQuery(theme.breakpoints.between("sm", "md"));

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
            <QueryStatsIcon
              sx={{
                mr: 1.5,
                color: "primary.main",
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
              デモ利用状況
            </Typography>
          </Box>

          <Tooltip title="データを更新">
            <span>
              <Button
                variant="outlined"
                color="primary"
                onClick={onRefresh}
                disabled={isLoading}
                startIcon={<RefreshIcon />}
                size={isMobile ? "small" : "medium"}
                sx={{
                  borderRadius: "12px",
                  px: { xs: 1.5, sm: 2 },
                  py: { xs: 0.5, sm: 0.7 },
                  boxShadow: "0 2px 5px rgba(37, 99, 235, 0.08)",
                  borderColor: "rgba(37, 99, 235, 0.3)",
                  textTransform: "none",
                  fontWeight: 600,
                  fontSize: { xs: "0.7rem", sm: "0.75rem" },
                  "&:hover": {
                    backgroundColor: "rgba(37, 99, 235, 0.04)",
                    borderColor: "rgba(37, 99, 235, 0.5)",
                    boxShadow: "0 3px 8px rgba(37, 99, 235, 0.12)",
                    transform: "translateY(-1px)",
                  },
                  transition: "all 0.2s ease",
                }}
              >
                {!isMobile && "更新"}
              </Button>
            </span>
          </Tooltip>
        </Box>

        {isLoading ? (
          <LoadingIndicator />
        ) : !demoStats ? (
          <EmptyState message="デモ利用状況データがありません" />
        ) : (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card
                elevation={0}
                sx={{
                  mb: 4,
                  borderRadius: 3,
                  border: "1px solid rgba(37, 99, 235, 0.12)",
                  position: "relative",
                  overflow: "hidden",
                  transition: "all 0.3s ease",
                  backgroundImage:
                    "linear-gradient(to bottom, rgba(255, 255, 255, 0.95), white)",
                  "&:hover": {
                    boxShadow: "0 8px 20px rgba(37, 99, 235, 0.08)",
                    transform: "translateY(-2px)",
                  },
                  "&::before": {
                    content: '""',
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "4px",
                    background:
                      "linear-gradient(90deg, #2563eb, #3b82f6, #60a5fa)",
                    opacity: 0.8,
                  },
                }}
              >
                <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      mb: 2,
                      justifyContent: "space-between",
                      flexWrap: "wrap",
                    }}
                  >
                    <Typography
                      variant="h6"
                      sx={{
                        fontWeight: 700,
                        color: "primary.main",
                        display: "flex",
                        alignItems: "center",
                        fontSize: { xs: "1.1rem", sm: "1.25rem" },
                        mb: { xs: 1, sm: 0 },
                      }}
                    >
                      <QueryStatsIcon
                        sx={{ mr: 1, fontSize: { xs: "1.2rem", sm: "1.3rem" } }}
                      />
                      デモ利用統計
                    </Typography>

                    {onOpenCompanyDetails && (
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={onOpenCompanyDetails}
                        disabled={isCompanyDetailsLoading}
                        startIcon={<BusinessIcon sx={{ fontSize: "1rem" }} />}
                        sx={{
                          borderRadius: "10px",
                          textTransform: "none",
                          fontWeight: 600,
                          fontSize: "0.75rem",
                          color: "text.secondary",
                          borderColor: "rgba(0, 0, 0, 0.12)",
                          py: 0.5,
                          px: 1.5,
                          "&:hover": {
                            borderColor: "rgba(37, 99, 235, 0.5)",
                            backgroundColor: "rgba(237, 242, 255, 0.5)",
                            transform: "translateY(-1px)",
                          },
                          transition: "all 0.2s ease",
                        }}
                      >
                        会社詳細を表示
                      </Button>
                    )}
                  </Box>

                  <Divider sx={{ mb: 3, opacity: 0.7 }} />

                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={6} sm={3}>
                      <Card
                        elevation={0}
                        sx={{
                          p: 2,
                          height: "100%",
                          borderRadius: 2,
                          backgroundImage:
                            "linear-gradient(135deg, rgba(37, 99, 235, 0.03), rgba(59, 130, 246, 0.06))",
                          border: "1px solid rgba(37, 99, 235, 0.08)",
                          "&:hover": {
                            boxShadow: "0 4px 12px rgba(37, 99, 235, 0.06)",
                            transform: "translateY(-2px)",
                          },
                          transition: "all 0.2s ease",
                        }}
                      >
                        <Box
                          sx={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            textAlign: "center",
                          }}
                        >
                          <Box
                            sx={{
                              mb: 1,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              width: { xs: 40, sm: 45 },
                              height: { xs: 40, sm: 45 },
                              borderRadius: "12px",
                              backgroundColor: "rgba(37, 99, 235, 0.08)",
                              color: "primary.main",
                            }}
                          >
                            <PeopleIcon
                              sx={{ fontSize: { xs: "1.4rem", sm: "1.6rem" } }}
                            />
                          </Box>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ mb: 0.5, fontSize: "0.75rem" }}
                          >
                            総管理者数
                          </Typography>
                          <Typography
                            variant="h6"
                            sx={{ fontWeight: 700, color: "primary.main" }}
                          >
                            {demoStats.total_users}
                          </Typography>
                        </Box>
                      </Card>
                    </Grid>

                    <Grid item xs={6} sm={3}>
                      <Card
                        elevation={0}
                        sx={{
                          p: 2,
                          height: "100%",
                          borderRadius: 2,
                          backgroundImage:
                            "linear-gradient(135deg, rgba(16, 185, 129, 0.03), rgba(5, 150, 105, 0.06))",
                          border: "1px solid rgba(16, 185, 129, 0.08)",
                          "&:hover": {
                            boxShadow: "0 4px 12px rgba(16, 185, 129, 0.06)",
                            transform: "translateY(-2px)",
                          },
                          transition: "all 0.2s ease",
                        }}
                      >
                        <Box
                          sx={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            textAlign: "center",
                          }}
                        >
                          <Box
                            sx={{
                              mb: 1,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              width: { xs: 40, sm: 45 },
                              height: { xs: 40, sm: 45 },
                              borderRadius: "12px",
                              backgroundColor: "rgba(16, 185, 129, 0.08)",
                              color: "#10b981",
                            }}
                          >
                            <PersonIcon
                              sx={{ fontSize: { xs: "1.4rem", sm: "1.6rem" } }}
                            />
                          </Box>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ mb: 0.5, fontSize: "0.75rem" }}
                          >
                            アクティブ管理者
                          </Typography>
                          <Typography
                            variant="h6"
                            sx={{ fontWeight: 700, color: "#10b981" }}
                          >
                            {demoStats.active_users}
                          </Typography>
                        </Box>
                      </Card>
                    </Grid>

                    <Grid item xs={6} sm={3}>
                      <Card
                        elevation={0}
                        sx={{
                          p: 2,
                          height: "100%",
                          borderRadius: 2,
                          backgroundImage:
                            "linear-gradient(135deg, rgba(6, 182, 212, 0.03), rgba(14, 165, 233, 0.06))",
                          border: "1px solid rgba(6, 182, 212, 0.08)",
                          "&:hover": {
                            boxShadow: "0 4px 12px rgba(6, 182, 212, 0.06)",
                            transform: "translateY(-2px)",
                          },
                          transition: "all 0.2s ease",
                        }}
                      >
                        <Box
                          sx={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            textAlign: "center",
                          }}
                        >
                          <Box
                            sx={{
                              mb: 1,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              width: { xs: 40, sm: 45 },
                              height: { xs: 40, sm: 45 },
                              borderRadius: "12px",
                              backgroundColor: "rgba(6, 182, 212, 0.08)",
                              color: "#06b6d4",
                            }}
                          >
                            <UploadFileIcon
                              sx={{ fontSize: { xs: "1.4rem", sm: "1.6rem" } }}
                            />
                          </Box>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ mb: 0.5, fontSize: "0.75rem" }}
                          >
                            ドキュメント数
                          </Typography>
                          <Typography
                            variant="h6"
                            sx={{ fontWeight: 700, color: "#06b6d4" }}
                          >
                            {demoStats.total_documents}
                          </Typography>
                        </Box>
                      </Card>
                    </Grid>

                    <Grid item xs={6} sm={3}>
                      <Card
                        elevation={0}
                        sx={{
                          p: 2,
                          height: "100%",
                          borderRadius: 2,
                          backgroundImage:
                            "linear-gradient(135deg, rgba(124, 58, 237, 0.03), rgba(139, 92, 246, 0.06))",
                          border: "1px solid rgba(124, 58, 237, 0.08)",
                          "&:hover": {
                            boxShadow: "0 4px 12px rgba(124, 58, 237, 0.06)",
                            transform: "translateY(-2px)",
                          },
                          transition: "all 0.2s ease",
                        }}
                      >
                        <Box
                          sx={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            textAlign: "center",
                          }}
                        >
                          <Box
                            sx={{
                              mb: 1,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              width: { xs: 40, sm: 45 },
                              height: { xs: 40, sm: 45 },
                              borderRadius: "12px",
                              backgroundColor: "rgba(124, 58, 237, 0.08)",
                              color: "#7c3aed",
                            }}
                          >
                            <HelpIcon
                              sx={{ fontSize: { xs: "1.4rem", sm: "1.6rem" } }}
                            />
                          </Box>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ mb: 0.5, fontSize: "0.75rem" }}
                          >
                            質問総数
                          </Typography>
                          <Typography
                            variant="h6"
                            sx={{ fontWeight: 700, color: "#7c3aed" }}
                          >
                            {demoStats.total_questions}
                          </Typography>
                        </Box>
                      </Card>
                    </Grid>
                  </Grid>

                  <TableContainer
                    component={Paper}
                    elevation={0}
                    sx={{
                      boxShadow: "none",
                      border: "1px solid rgba(0, 0, 0, 0.06)",
                      borderRadius: 3,
                      overflow: "hidden",
                      transition: "all 0.2s ease",
                      "&:hover": {
                        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
                      },
                    }}
                  >
                    <Table>
                      <TableHead>
                        <TableRow
                          sx={{
                            bgcolor: "rgba(249, 250, 252, 0.8)",
                            borderBottom: "1px solid rgba(0, 0, 0, 0.04)",
                          }}
                        >
                          <TableCell
                            sx={{
                              fontWeight: 600,
                              width: "60%",
                              color: "text.primary",
                              fontSize: "0.85rem",
                            }}
                          >
                            指標
                          </TableCell>
                          <TableCell
                            align="right"
                            sx={{
                              fontWeight: 600,
                              width: "40%",
                              color: "text.primary",
                              fontSize: "0.85rem",
                            }}
                          >
                            値
                          </TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow hover>
                          <TableCell>
                            <Box sx={{ display: "flex", alignItems: "center" }}>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  width: 28,
                                  height: 28,
                                  borderRadius: "8px",
                                  bgcolor: "rgba(37, 99, 235, 0.08)",
                                  mr: 1.5,
                                }}
                              >
                                <PercentIcon
                                  sx={{
                                    color: theme.palette.primary.main,
                                    fontSize: "1rem",
                                  }}
                                />
                              </Box>
                              <Typography
                                variant="body2"
                                sx={{ fontWeight: 500 }}
                              >
                                アクティブ管理者率
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${Math.round(
                                (demoStats.active_users /
                                  demoStats.total_users) *
                                  100
                              )}%`}
                              color={
                                demoStats.active_users / demoStats.total_users >
                                0.6
                                  ? "success"
                                  : demoStats.active_users /
                                      demoStats.total_users >
                                    0.3
                                  ? "primary"
                                  : "warning"
                              }
                              size="small"
                              sx={{
                                fontWeight: "bold",
                                minWidth: "50px",
                                fontSize: "0.75rem",
                                height: "24px",
                              }}
                            />
                          </TableCell>
                        </TableRow>

                        <TableRow
                          hover
                          sx={{ bgcolor: "rgba(249, 250, 252, 0.5)" }}
                        >
                          <TableCell>
                            <Box sx={{ display: "flex", alignItems: "center" }}>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  width: 28,
                                  height: 28,
                                  borderRadius: "8px",
                                  bgcolor: "rgba(16, 185, 129, 0.08)",
                                  mr: 1.5,
                                }}
                              >
                                <AverageIcon
                                  sx={{ color: "#10b981", fontSize: "1rem" }}
                                />
                              </Box>
                              <Typography
                                variant="body2"
                                sx={{ fontWeight: 500 }}
                              >
                                管理者あたりの質問数
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={
                                demoStats.total_users > 0
                                  ? (
                                      demoStats.total_questions /
                                      demoStats.total_users
                                    ).toFixed(1)
                                  : "0"
                              }
                              color="info"
                              size="small"
                              sx={{
                                fontWeight: "bold",
                                minWidth: "50px",
                                fontSize: "0.75rem",
                                height: "24px",
                              }}
                            />
                          </TableCell>
                        </TableRow>

                        <TableRow hover>
                          <TableCell>
                            <Box sx={{ display: "flex", alignItems: "center" }}>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  width: 28,
                                  height: 28,
                                  borderRadius: "8px",
                                  bgcolor: "rgba(234, 88, 12, 0.08)",
                                  mr: 1.5,
                                }}
                              >
                                <ErrorIcon
                                  sx={{ color: "#f97316", fontSize: "1rem" }}
                                />
                              </Box>
                              <Typography
                                variant="body2"
                                sx={{ fontWeight: 500 }}
                              >
                                エラー発生率
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${demoStats.error_rate || "0.0"}%`}
                              color={
                                parseFloat(demoStats.error_rate || "0") < 2
                                  ? "success"
                                  : parseFloat(demoStats.error_rate || "0") < 5
                                  ? "warning"
                                  : "error"
                              }
                              size="small"
                              sx={{
                                fontWeight: "bold",
                                minWidth: "50px",
                                fontSize: "0.75rem",
                                height: "24px",
                              }}
                            />
                          </TableCell>
                        </TableRow>

                        <TableRow hover>
                          <TableCell>
                            <Box sx={{ display: "flex", alignItems: "center" }}>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  width: 28,
                                  height: 28,
                                  borderRadius: "8px",
                                  bgcolor: "rgba(37, 99, 235, 0.08)",
                                  mr: 1.5,
                                }}
                              >
                                <PeopleIcon
                                  sx={{
                                    color: theme.palette.primary.main,
                                    fontSize: "1rem",
                                  }}
                                />
                              </Box>
                              <Typography
                                variant="body2"
                                sx={{ fontWeight: 500 }}
                              >
                                総管理者数
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={demoStats.total_users}
                              color="primary"
                              size="small"
                              sx={{
                                fontWeight: "bold",
                                minWidth: "50px",
                              }}
                            />
                          </TableCell>
                        </TableRow>
                        <TableRow hover>
                          <TableCell>
                            <Box sx={{ display: "flex", alignItems: "center" }}>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  width: 28,
                                  height: 28,
                                  borderRadius: "8px",
                                  bgcolor: "rgba(16, 185, 129, 0.08)",
                                  mr: 1.5,
                                }}
                              >
                                <PersonIcon
                                  sx={{
                                    color: theme.palette.success.main,
                                    fontSize: "1rem",
                                  }}
                                />
                              </Box>
                              <Typography
                                variant="body2"
                                sx={{ fontWeight: 500 }}
                              >
                                アクティブ管理者数
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={demoStats.active_users}
                              color="success"
                              size="small"
                              sx={{
                                fontWeight: "bold",
                                minWidth: "50px",
                              }}
                            />
                          </TableCell>
                        </TableRow>
                        <TableRow hover>
                          <TableCell>
                            <Box sx={{ display: "flex", alignItems: "center" }}>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  width: 28,
                                  height: 28,
                                  borderRadius: "8px",
                                  bgcolor: "rgba(6, 182, 212, 0.08)",
                                  mr: 1.5,
                                }}
                              >
                                <UploadFileIcon
                                  sx={{
                                    color: theme.palette.info.main,
                                    fontSize: "1rem",
                                  }}
                                />
                              </Box>
                              <Typography
                                variant="body2"
                                sx={{ fontWeight: 500 }}
                              >
                                アップロードされたドキュメント数
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={demoStats.total_documents}
                              color="info"
                              size="small"
                              sx={{
                                fontWeight: "bold",
                                minWidth: "50px",
                              }}
                            />
                          </TableCell>
                        </TableRow>
                        <TableRow hover>
                          <TableCell>
                            <Box sx={{ display: "flex", alignItems: "center" }}>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  width: 28,
                                  height: 28,
                                  borderRadius: "8px",
                                  bgcolor: "rgba(124, 58, 237, 0.08)",
                                  mr: 1.5,
                                }}
                              >
                                <HelpIcon
                                  sx={{
                                    color: theme.palette.secondary.main,
                                    fontSize: "1rem",
                                  }}
                                />
                              </Box>
                              <Typography
                                variant="body2"
                                sx={{ fontWeight: 500 }}
                              >
                                質問総数
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={demoStats.total_questions}
                              color="secondary"
                              size="small"
                              sx={{
                                fontWeight: "bold",
                                minWidth: "50px",
                              }}
                            />
                          </TableCell>
                        </TableRow>
                        <TableRow hover>
                          <TableCell>
                            <Box sx={{ display: "flex", alignItems: "center" }}>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  width: 28,
                                  height: 28,
                                  borderRadius: "8px",
                                  bgcolor: "rgba(234, 88, 12, 0.08)",
                                  mr: 1.5,
                                }}
                              >
                                <ErrorIcon
                                  sx={{
                                    color: theme.palette.error.main,
                                    fontSize: "1rem",
                                  }}
                                />
                              </Box>
                              <Typography
                                variant="body2"
                                sx={{ fontWeight: 500 }}
                              >
                                制限に達した管理者数
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={demoStats.limit_reached_users}
                              color="error"
                              size="small"
                              sx={{
                                fontWeight: "bold",
                                minWidth: "50px",
                              }}
                            />
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </Box>
    </Fade>
  );
};

export default DemoStatsTab;
