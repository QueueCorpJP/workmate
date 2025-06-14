import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Typography,
  Box,
  Button,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  Alert,
  CircularProgress,
  Divider,
  useTheme,
  useMediaQuery,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Stack,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PersonIcon from "@mui/icons-material/Person";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import GroupIcon from "@mui/icons-material/Group";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";
import { formatDate } from "./utils";

interface CompanyUser {
  id: string;
  email: string;
  name: string;
  created_at: string;
  role: string;
  company_name?: string;
  company_id?: string;
}

interface CompanyDetailsDialogProps {
  open: boolean;
  onClose: () => void;
  companyDetails: CompanyUser[];
  isLoading: boolean;
  onDeleteUser: (userId: string, userEmail: string) => void;
  isDeleting: boolean;
  deleteError: string | null;
  deleteSuccess: string | null;
  PaperProps?: {
    sx?: React.CSSProperties | any;
  };
}

const CompanyDetailsDialog: React.FC<CompanyDetailsDialogProps> = ({
  open,
  onClose,
  companyDetails,
  isLoading,
  onDeleteUser,
  isDeleting,
  deleteError,
  deleteSuccess,
  PaperProps,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(new Set());

  // 会社別にユーザーをグループ化
  const groupedByCompany = React.useMemo(() => {
    console.log("CompanyDetailsDialog - companyDetails:", companyDetails);
    const groups: { [key: string]: { admins: CompanyUser[], employees: CompanyUser[] } } = {};
    
    companyDetails.forEach(user => {
      console.log("Processing user:", user);
      // 会社名を取得、なければ会社IDまたはデフォルト名を使用
      let companyName = user.company_name;
      if (!companyName) {
        if (user.company_id) {
          companyName = `会社ID: ${user.company_id}`;
        } else {
          companyName = "不明な会社";
        }
      }
      
      if (!groups[companyName]) {
        groups[companyName] = { admins: [], employees: [] };
      }
      
      if (user.role === "admin" || user.role === "user") {
        groups[companyName].admins.push(user);
      } else if (user.role === "employee") {
        groups[companyName].employees.push(user);
      }
    });
    
    console.log("CompanyDetailsDialog - groupedByCompany:", groups);
    return groups;
  }, [companyDetails]);

  const toggleCompanyExpansion = (companyName: string) => {
    const newExpanded = new Set(expandedCompanies);
    if (expandedCompanies.has(companyName)) {
      newExpanded.delete(companyName);
    } else {
      newExpanded.add(companyName);
    }
    setExpandedCompanies(newExpanded);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      fullScreen={isMobile}
      PaperProps={
        PaperProps || {
          sx: {
            borderRadius: { xs: "12px", sm: "16px" },
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
            overflow: "hidden",
            backgroundImage:
              "linear-gradient(to bottom, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 1))",
            backdropFilter: "blur(16px)",
            p: { xs: 1, sm: 2 },
          },
        }
      }
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="h6">会社詳細情報</Typography>
        <IconButton edge="end" color="inherit" onClick={onClose}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        {deleteSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {deleteSuccess}
          </Alert>
        )}

        {deleteError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {deleteError}
          </Alert>
        )}

        {isLoading ? (
          <LoadingIndicator />
        ) : companyDetails.length === 0 ? (
          <EmptyState message="会社情報がありません" />
        ) : (
          <Box sx={{ mt: 2 }}>
            {Object.entries(groupedByCompany).map(([companyName, users]) => (
              <Accordion
                key={companyName}
                expanded={expandedCompanies.has(companyName)}
                onChange={() => toggleCompanyExpansion(companyName)}
                sx={{
                  mb: 1,
                  boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                  border: "1px solid rgba(0,0,0,0.08)",
                  "&:before": { display: "none" },
                  borderRadius: "8px !important",
                }}
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  sx={{
                    backgroundColor: "rgba(37, 99, 235, 0.04)",
                    borderRadius: "8px",
                    "&.Mui-expanded": {
                      borderBottomLeftRadius: 0,
                      borderBottomRightRadius: 0,
                    },
                  }}
                >
                  <Stack direction="row" spacing={2} alignItems="center" sx={{ width: "100%" }}>
                    <Box sx={{ display: "flex", alignItems: "center" }}>
                      <AdminPanelSettingsIcon sx={{ mr: 1, color: "primary.main" }} />
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {companyName}
                      </Typography>
                    </Box>
                    <Box sx={{ display: "flex", gap: 1 }}>
                      <Chip
                        icon={<PersonIcon />}
                        label={`社長: ${users.admins.length}人`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Chip
                        icon={<GroupIcon />}
                        label={`社員: ${users.employees.length}人`}
                        size="small"
                        color="secondary"
                        variant="outlined"
                      />
                    </Box>
                  </Stack>
                </AccordionSummary>
                <AccordionDetails sx={{ pt: 0 }}>
                  <Box>
                    {/* 社長/管理者セクション */}
                    {users.admins.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600, color: "primary.main" }}>
                          <PersonIcon sx={{ fontSize: "1rem", mr: 0.5, verticalAlign: "middle" }} />
                          社長・管理者
                        </Typography>
                        <List sx={{ py: 0 }}>
                          {users.admins.map((user) => (
                            <ListItem
                              key={user.id}
                              sx={{
                                border: "1px solid rgba(0,0,0,0.08)",
                                borderRadius: 1,
                                mb: 1,
                                bgcolor: "rgba(25, 118, 210, 0.04)",
                              }}
                            >
                              <ListItemText
                                primary={
                                  <Stack direction="row" spacing={1} alignItems="center">
                                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                      {user.name}
                                    </Typography>
                                    <Chip label="管理者" size="small" color="primary" />
                                  </Stack>
                                }
                                secondary={
                                  <Stack spacing={0.5}>
                                    <Typography variant="caption" color="text.secondary">
                                      📧 {user.email}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      🗓️ 作成日: {formatDate(user.created_at)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      🆔 ID: {user.id}
                                    </Typography>
                                  </Stack>
                                }
                              />
                              <ListItemSecondaryAction>
                                {user.email !== "queue@queueu-tech.jp" && user.email !== "queue@queuefood.co.jp" && (
                                  <Button
                                    variant="outlined"
                                    color="error"
                                    size="small"
                                    onClick={() => onDeleteUser(user.id, user.email)}
                                    disabled={isDeleting}
                                    sx={{ fontSize: "0.7rem" }}
                                  >
                                    削除
                                  </Button>
                                )}
                              </ListItemSecondaryAction>
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}

                    {/* 社員セクション */}
                    {users.employees.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600, color: "secondary.main" }}>
                          <GroupIcon sx={{ fontSize: "1rem", mr: 0.5, verticalAlign: "middle" }} />
                          社員
                        </Typography>
                        <List sx={{ py: 0 }}>
                          {users.employees.map((user) => (
                            <ListItem
                              key={user.id}
                              sx={{
                                border: "1px solid rgba(0,0,0,0.08)",
                                borderRadius: 1,
                                mb: 1,
                                bgcolor: "rgba(156, 39, 176, 0.04)",
                              }}
                            >
                              <ListItemText
                                primary={
                                  <Stack direction="row" spacing={1} alignItems="center">
                                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                      {user.name}
                                    </Typography>
                                    <Chip label="社員" size="small" color="secondary" />
                                  </Stack>
                                }
                                secondary={
                                  <Stack spacing={0.5}>
                                    <Typography variant="caption" color="text.secondary">
                                      📧 {user.email}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      🗓️ 作成日: {formatDate(user.created_at)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      🆔 ID: {user.id}
                                    </Typography>
                                    <Typography variant="caption" color="orange" sx={{ fontWeight: 500 }}>
                                      ⚠️ 管理画面アクセス不可
                                    </Typography>
                                  </Stack>
                                }
                              />
                              <ListItemSecondaryAction>
                                <Button
                                  variant="outlined"
                                  color="error"
                                  size="small"
                                  onClick={() => onDeleteUser(user.id, user.email)}
                                  disabled={isDeleting}
                                  sx={{ fontSize: "0.7rem" }}
                                >
                                  削除
                                </Button>
                              </ListItemSecondaryAction>
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}

                    {users.admins.length === 0 && users.employees.length === 0 && (
                      <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 2 }}>
                        この会社にはユーザーがいません
                      </Typography>
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          閉じる
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CompanyDetailsDialog;
