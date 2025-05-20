import React from 'react';
import { Box, CircularProgress, Typography, Paper, useTheme } from '@mui/material';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';

interface LoadingIndicatorProps {
  size?: number;
  message?: string;
  fullHeight?: boolean;
}

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ 
  size = 40, 
  message = 'データを読み込み中...',
  fullHeight = false
}) => {
  const theme = useTheme();
  
  return (
    <Box 
      sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center',
        p: 4,
        height: fullHeight ? '100%' : 'auto',
        minHeight: fullHeight ? '300px' : '200px',
      }}
    >
      <Paper
        elevation={0}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          py: 4,
          px: 6,
          borderRadius: 2,
          backgroundColor: 'rgba(255, 255, 255, 0.7)',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '3px',
            background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.primary.light})`,
          }
        }}
      >
        <Box 
          sx={{ 
            position: 'relative',
            mb: 2,
            '& .MuiCircularProgress-root': {
              color: theme.palette.primary.main,
            }
          }}
        >
          <CircularProgress 
            size={size} 
            thickness={4}
            sx={{
              boxShadow: '0 0 10px rgba(37, 99, 235, 0.2)',
            }}
          />
          <HourglassEmptyIcon 
            sx={{ 
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              color: theme.palette.primary.main,
              fontSize: size * 0.5,
              opacity: 0.7,
              animation: 'pulse 1.5s infinite'
            }}
          />
        </Box>
        <Typography 
          variant="body1" 
          sx={{ 
            color: 'text.secondary',
            fontWeight: 500,
            textAlign: 'center',
            '@keyframes pulse': {
              '0%': {
                opacity: 0.4,
              },
              '50%': {
                opacity: 1,
              },
              '100%': {
                opacity: 0.4,
              },
            }
          }}
        >
          {message}
        </Typography>
      </Paper>
    </Box>
  );
};

export default LoadingIndicator;