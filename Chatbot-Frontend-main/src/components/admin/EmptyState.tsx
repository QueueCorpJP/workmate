import React from 'react';
import { Box, Typography, Paper, useTheme } from '@mui/material';
import InboxIcon from '@mui/icons-material/Inbox';
import SearchOffIcon from '@mui/icons-material/SearchOff';

interface EmptyStateProps {
  message: string;
  icon?: 'inbox' | 'search' | 'custom';
  customIcon?: React.ReactNode;
  fullHeight?: boolean;
}

const EmptyState: React.FC<EmptyStateProps> = ({ 
  message, 
  icon = 'inbox',
  customIcon,
  fullHeight = false
}) => {
  const theme = useTheme();
  
  const getIcon = () => {
    switch (icon) {
      case 'search':
        return <SearchOffIcon sx={{ fontSize: '4rem', color: theme.palette.grey[400] }} />;
      case 'custom':
        return customIcon;
      case 'inbox':
      default:
        return <InboxIcon sx={{ fontSize: '4rem', color: theme.palette.grey[400] }} />;
    }
  };
  
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        p: 4,
        height: fullHeight ? '100%' : 'auto',
        minHeight: fullHeight ? '300px' : '200px'
      }}
    >
      <Paper
        elevation={0}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          p: 5,
          borderRadius: 2,
          backgroundColor: 'rgba(0, 0, 0, 0.02)',
          border: '1px dashed rgba(0, 0, 0, 0.15)',
          transition: 'all 0.2s ease',
          maxWidth: '400px',
          width: '100%',
          position: 'relative',
          overflow: 'hidden',
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.03)',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)'
          }
        }}
      >
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
            mb: 2
          }}
        >
          {getIcon()}
        </Box>
        <Typography 
          variant="body1" 
          sx={{ 
            textAlign: 'center', 
            color: 'text.secondary',
            fontWeight: 500,
            fontSize: '1rem',
            maxWidth: '350px'
          }}
        >
          {message}
        </Typography>
      </Paper>
    </Box>
  );
};

export default EmptyState;