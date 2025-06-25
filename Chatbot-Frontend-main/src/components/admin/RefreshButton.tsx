import React from "react";
import { IconButton, Tooltip, CircularProgress } from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";

interface RefreshButtonProps {
  onRefresh: () => void;
  isLoading: boolean;
  tooltip?: string;
  size?: "small" | "medium" | "large";
}

const RefreshButton: React.FC<RefreshButtonProps> = ({
  onRefresh,
  isLoading,
  tooltip = "データを更新",
  size = "medium",
}) => {
  return (
    <Tooltip title={tooltip}>
      <IconButton
        onClick={onRefresh}
        disabled={isLoading}
        size={size}
        color="primary"
        sx={{
          transition: 'transform 0.2s ease',
          '&:hover': {
            transform: 'rotate(180deg)',
          },
        }}
      >
        {isLoading ? (
          <CircularProgress size={size === "small" ? 16 : size === "large" ? 28 : 24} />
        ) : (
          <RefreshIcon />
        )}
      </IconButton>
    </Tooltip>
  );
};

export default RefreshButton; 