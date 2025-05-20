import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  List,
  Divider,
  Chip
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { ChatHistoryItem, EmployeeUsageItem, categoryColors, sentimentColors } from './types';
import LoadingIndicator from './LoadingIndicator';
import EmptyState from './EmptyState';
import { formatDate } from './utils';

interface EmployeeDetailsDialogProps {
  open: boolean;
  onClose: () => void;
  selectedEmployee: EmployeeUsageItem | null;
  employeeDetails: ChatHistoryItem[];
  isLoading: boolean;
}

const EmployeeDetailsDialog: React.FC<EmployeeDetailsDialogProps> = ({
  open,
  onClose,
  selectedEmployee,
  employeeDetails,
  isLoading
}) => {
  if (!selectedEmployee) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1 }}>
        <Box>
          <Typography variant="h6" component="span">
            {selectedEmployee.employee_name || '名前なし'}
          </Typography>
          <Typography variant="body2" component="span" sx={{ ml: 1, color: 'text.secondary' }}>
            (ID: {selectedEmployee.employee_id})
          </Typography>
        </Box>
        <IconButton edge="end" color="inherit" onClick={onClose} aria-label="close">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        {isLoading ? (
          <LoadingIndicator />
        ) : employeeDetails.length === 0 ? (
          <EmptyState message="詳細データがありません" />
        ) : (
          <>
            <Box sx={{ mb: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        利用回数
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 500, color: 'primary.main' }}>
                        {selectedEmployee.message_count}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={8}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">
                        最終利用
                      </Typography>
                      <Typography variant="body1">
                        {formatDate(selectedEmployee.last_activity)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>

            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              質問履歴
            </Typography>
            <List sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
              {employeeDetails.map((chat) => (
                <React.Fragment key={chat.id}>
                  <Box sx={{ p: 2 }}>
                    <Box sx={{ width: '100%', display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Chip
                          label={chat.category || '未分類'}
                          size="small"
                          sx={{
                            mr: 1,
                            bgcolor: categoryColors[0],
                            color: 'white'
                          }}
                        />
                        <Chip
                          label={chat.sentiment || 'neutral'}
                          size="small"
                          sx={{
                            bgcolor: sentimentColors[chat.sentiment as keyof typeof sentimentColors] || sentimentColors.neutral,
                            color: 'white'
                          }}
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(chat.timestamp)}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ width: '100%' }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        質問:
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1, pl: 1 }}>
                        {chat.user_message}
                      </Typography>
                      
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        回答:
                      </Typography>
                      <Typography variant="body2" sx={{ pl: 1 }}>
                        {chat.bot_response}
                      </Typography>
                    </Box>
                  </Box>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>閉じる</Button>
      </DialogActions>
    </Dialog>
  );
};

export default EmployeeDetailsDialog;