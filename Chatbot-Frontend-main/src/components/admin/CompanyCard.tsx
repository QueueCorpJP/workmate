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
  Divider,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import HistoryIcon from "@mui/icons-material/History";
import BusinessIcon from "@mui/icons-material/Business";
import PeopleIcon from "@mui/icons-material/People";
import { CompanyEmployee } from "./types";

interface CompanyData {
  companyId: string;
  companyName: string;
  companyDomain: string;
  primaryAdmin: CompanyEmployee;
  allAdmins: CompanyEmployee[];
  employees: CompanyEmployee[];
  allMembers: CompanyEmployee[];
  totalMembers: number;
  isUnlimited: boolean;
}

interface CompanyCardProps {
  companyData: CompanyData;
  onCompanyClick: (companyData: CompanyData) => void;
  onToggleDemo: (employee: CompanyEmployee) => void;
  onOpenPlanHistory: (employee: CompanyEmployee) => void;
}

const CompanyCard: React.FC<CompanyCardProps> = ({
  companyData,
  onCompanyClick,
  onToggleDemo,
  onOpenPlanHistory,
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
      onClick={() => onCompanyClick(companyData)}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56, mr: 2 }}>
            <BusinessIcon />
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
              {companyData.companyName}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              会社名
            </Typography>
          </Box>
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            代表管理者
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ width: 24, height: 24, fontSize: '0.8rem' }}>
              {(companyData.primaryAdmin.name || companyData.primaryAdmin.email).charAt(0).toUpperCase()}
            </Avatar>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {companyData.primaryAdmin.name || companyData.primaryAdmin.email.split('@')[0]}
            </Typography>
            <Chip
              label={
                companyData.primaryAdmin.role === "admin_user"
                  ? "社長"
                  : companyData.primaryAdmin.role === "user"
                  ? "管理者"
                  : companyData.primaryAdmin.role === "admin"
                  ? "管理者"
                  : "社員"
              }
              size="small"
              color={
                companyData.primaryAdmin.role === "admin_user"
                  ? "warning"
                  : companyData.primaryAdmin.role === "user"
                  ? "primary"
                  : companyData.primaryAdmin.role === "admin"
                  ? "primary"
                  : "secondary"
              }
              variant="outlined"
            />
          </Box>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            アカウント構成
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {companyData.allAdmins.length > 0 && (
              <Chip
                label={`管理者 ${companyData.allAdmins.length}名`}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
            {companyData.employees.length > 0 && (
              <Chip
                label={`社員 ${companyData.employees.length}名`}
                size="small"
                color="secondary"
                variant="outlined"
              />
            )}
          </Box>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            作成日
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {new Date(companyData.primaryAdmin.created_at).toLocaleDateString('ja-JP')}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
          <Chip
            label={companyData.isUnlimited ? "本番版" : "デモ版"}
            color={companyData.isUnlimited ? "success" : "warning"}
            size="small"
          />
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PeopleIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="body2" color="text.secondary">
              全 {companyData.totalMembers}名
            </Typography>
          </Box>
        </Box>

        <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          <Tooltip title={`${companyData.isUnlimited ? 'デモ版' : '本番版'}に切り替え`}>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onToggleDemo(companyData.primaryAdmin);
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
                onOpenPlanHistory(companyData.primaryAdmin);
              }}
              color="primary"
            >
              <HistoryIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </CardContent>
    </Card>
  );
};

export default CompanyCard; 