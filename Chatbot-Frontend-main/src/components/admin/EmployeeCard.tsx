import React from "react";
import {
  Card,
  CardContent,
  Avatar,
  Typography,
  Chip,
  Box,
  IconButton,
  Tooltip,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import HistoryIcon from "@mui/icons-material/History";
import DeleteIcon from "@mui/icons-material/Delete";
import { CompanyEmployee } from "./types";

interface EmployeeCardProps {
  employee: CompanyEmployee;
  onToggleDemo: (employee: CompanyEmployee) => void;
  onOpenPlanHistory: (employee: CompanyEmployee) => void;
  onDeleteEmployee?: (employee: CompanyEmployee) => void;
  canShowDeleteButton: boolean;
  isUnlimited: boolean;
}

const EmployeeCard: React.FC<EmployeeCardProps> = ({
  employee,
  onToggleDemo,
  onOpenPlanHistory,
  onDeleteEmployee,
  canShowDeleteButton,
  isUnlimited
}) => {
  return (
    <Card
      sx={{
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
          borderColor: 'primary.main',
        },
        border: '2px solid rgba(0,0,0,0.08)',
        borderRadius: 3,
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56, mr: 2 }}>
            {(employee.name || employee.email).charAt(0).toUpperCase()}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
              {employee.name || employee.email.split('@')[0]}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {employee.email}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Chip
            label={
              employee.role === "admin_user"
                ? "社長"
                : employee.role === "user"
                ? "管理者"
                : employee.role === "admin"
                ? "管理者"
                : "社員"
            }
            size="small"
            color={
              employee.role === "admin_user"
                ? "warning"
                : employee.role === "user"
                ? "primary"
                : employee.role === "admin"
                ? "primary"
                : "secondary"
            }
            variant="outlined"
          />
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            作成日
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {new Date(employee.created_at).toLocaleDateString('ja-JP')}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
          <Chip
            label={isUnlimited ? "本番版" : "デモ版"}
            color={isUnlimited ? "success" : "warning"}
            size="small"
          />
        </Box>

        <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          <Tooltip title={`${isUnlimited ? 'デモ版' : '本番版'}に切り替え`}>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onToggleDemo(employee);
              }}
              color="primary"
            >
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="プラン変更履歴を表示">
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onOpenPlanHistory(employee);
              }}
              color="primary"
            >
              <HistoryIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {canShowDeleteButton && onDeleteEmployee && (
            <Tooltip title="社員を削除">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteEmployee(employee);
                }}
                color="error"
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default EmployeeCard; 