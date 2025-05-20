import React from "react";
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
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";
import { formatDate } from "./utils";

interface CompanyUser {
  id: string;
  email: string;
  name: string;
  created_at: string;
  role: string;
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
          <TableContainer
            component={Paper}
            sx={{
              boxShadow: "none",
              border: "1px solid",
              borderColor: "divider",
            }}
          >
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: "background.default" }}>
                  <TableCell>ID</TableCell>
                  <TableCell>メールアドレス</TableCell>
                  <TableCell>名前</TableCell>
                  <TableCell>作成日時</TableCell>
                  <TableCell>ロール</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {companyDetails.map((user) => (
                  <TableRow key={user.id} hover>
                    <TableCell>{user.id}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>{user.name}</TableCell>
                    <TableCell>{formatDate(user.created_at)}</TableCell>
                    <TableCell>
                      {user.role === "admin"
                        ? "管理者"
                        : user.role === "employee"
                        ? "社員（管理画面アクセス不可）"
                        : "ユーザー"}
                    </TableCell>
                    <TableCell>
                      {user.email !== "queue@queuefood.co.jp" && (
                        <Button
                          variant="outlined"
                          color="error"
                          size="small"
                          onClick={() => onDeleteUser(user.id, user.email)}
                          disabled={isDeleting}
                        >
                          削除
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
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
