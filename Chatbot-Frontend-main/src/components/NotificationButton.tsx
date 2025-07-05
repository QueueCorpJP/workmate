import React from 'react';
import { IconButton, Tooltip } from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';

interface NotificationButtonProps {
  onClick: () => void;
}

const NotificationButton: React.FC<NotificationButtonProps> = ({ onClick }) => {
  return (
    <Tooltip title="通知" placement="bottom">
      <IconButton
        onClick={onClick}
        sx={{
          width: { xs: 40, sm: 46 },
          height: { xs: 40, sm: 46 },
          borderRadius: "14px",
          backgroundColor: "rgba(255, 255, 255, 0.15)",
          backdropFilter: "blur(4px)",
          border: "1px solid rgba(255, 255, 255, 0.2)",
          color: "white",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
          transition: "all 0.2s ease",
          "&:hover": {
            backgroundColor: "rgba(255, 255, 255, 0.25)",
            transform: "translateY(-2px)",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
          },
        }}
      >
        <NotificationsIcon sx={{ fontSize: { xs: "1.2rem", sm: "1.4rem" } }} />
      </IconButton>
    </Tooltip>
  );
};

export default NotificationButton; 