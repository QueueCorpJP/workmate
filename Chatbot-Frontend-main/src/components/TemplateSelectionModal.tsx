import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardActions,
  TextField,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Divider,
  Grid,
  useTheme,
  useMediaQuery,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  AppBar,
  Toolbar,
  Collapse,
} from '@mui/material';
import {
  Close as CloseIcon,

  Description as DescriptionIcon,
  Send as SendIcon,
  Refresh as RefreshIcon,
  Menu as MenuIcon,
  ExpandLess,
  ExpandMore,
  FilterList as FilterListIcon,
} from '@mui/icons-material';
import api from '../api';

// TypeScript interfaces
interface TemplateCategory {
  id: string;
  name: string;
  description: string;
  icon?: string;
  display_order: number;
  is_active: boolean;
}



interface Template {
  id: string;
  title: string;
  description: string;
  template_content: string;
  category_id: string;
  template_type: 'system' | 'company' | 'user';
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  usage_count: number;
  is_public: boolean;
  is_active: boolean;
  created_by?: string;
  company_id?: string;
  created_at: string;
  updated_at: string;

}

interface TemplateSelectionModalProps {
  open: boolean;
  onClose: () => void;
  onTemplateSelect: (processedTemplate: string) => void;
}

const TemplateSelectionModal: React.FC<TemplateSelectionModalProps> = ({
  open,
  onClose,
  onTemplateSelect,
}) => {
  // Theme and responsive hooks
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const isSmallMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // State management
  const [categories, setCategories] = useState<TemplateCategory[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [currentTab, setCurrentTab] = useState(0);
  
  // Responsive state
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [categoryCollapsed, setCategoryCollapsed] = useState(!isMobile);

  // Fetch categories on component mount
  useEffect(() => {
    if (open) {
      fetchCategories();
    }
  }, [open]);

  // Fetch templates when category changes
  useEffect(() => {
    if (selectedCategory) {
      fetchTemplates(selectedCategory);
    }
  }, [selectedCategory]);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const response = await api.get('/templates/categories');
      setCategories(response.data.categories || []);
      if (response.data.categories && response.data.categories.length > 0) {
        setSelectedCategory(response.data.categories[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      setError('カテゴリの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async (categoryId: string) => {
    try {
      setLoading(true);
      const response = await api.get(`/templates/category/${categoryId}`);
      setTemplates(response.data.templates || []);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      setError('テンプレートの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };





  const handleTemplateSelect = async (template: Template) => {
    try {
      setSelectedTemplate(template);
      setCurrentTab(1); // Switch to preview tab
    } catch (error) {
      console.error('Failed to select template:', error);
      setError('テンプレートの選択に失敗しました');
    }
  };



  const processTemplate = (template: Template): string => {
    return template.template_content;
  };

  const handleUseTemplate = async () => {
    if (!selectedTemplate) return;

    try {
      // Process the template
      const processedTemplate = processTemplate(selectedTemplate);
      
      // Record template usage
      await api.post('/templates/usage', {
        template_id: selectedTemplate.id,
        variable_values: {},
      });

      // Call the callback with processed template
      onTemplateSelect(processedTemplate);
      
      // Close modal and reset state
      handleClose();
    } catch (error) {
      console.error('Failed to use template:', error);
      setError('テンプレートの使用に失敗しました');
    }
  };



  const handleClose = () => {
    setSelectedTemplate(null);
    setCurrentTab(0);
    setError('');
    setMobileDrawerOpen(false);
    onClose();
  };

  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'beginner': return '#4caf50';
      case 'intermediate': return '#ff9800';
      case 'advanced': return '#f44336';
      default: return '#757575';
    }
  };

  const getDifficultyLabel = (level: string) => {
    switch (level) {
      case 'beginner': return '初級';
      case 'intermediate': return '中級';
      case 'advanced': return '上級';
      default: return level;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth={isMobile ? false : "lg"}
      fullWidth={!isMobile}
      fullScreen={isMobile}
      PaperProps={{
        sx: {
          borderRadius: isMobile ? 0 : 3,
          height: isMobile ? '100vh' : '700px',
          width: isMobile ? '100vw' : '900px',
          maxWidth: isMobile ? '100vw' : '95vw',
          maxHeight: isMobile ? '100vh' : '90vh',
          margin: isMobile ? 0 : 'auto',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
          color: 'white',
          py: isSmallMobile ? 1 : 2,
          px: isSmallMobile ? 2 : 3,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DescriptionIcon sx={{ fontSize: isSmallMobile ? 20 : 24 }} />
          <Typography 
            variant={isSmallMobile ? "subtitle1" : "h6"} 
            fontWeight={600}
            sx={{
              fontSize: isSmallMobile ? '1rem' : '1.25rem',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {isSmallMobile ? 'テンプレート' : 'プロンプトテンプレート'}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {isMobile && currentTab === 0 && (
            <IconButton 
              onClick={() => setMobileDrawerOpen(true)} 
              sx={{ color: 'white', p: isSmallMobile ? 1 : 1.5 }}
              size={isSmallMobile ? 'small' : 'medium'}
            >
              <FilterListIcon />
            </IconButton>
          )}
          <IconButton 
            onClick={handleClose} 
            sx={{ color: 'white', p: isSmallMobile ? 1 : 1.5 }}
            size={isSmallMobile ? 'small' : 'medium'}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ 
        p: 0, 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        minHeight: 0,
      }}>
        <Tabs
          value={currentTab}
          onChange={(_, newValue) => setCurrentTab(newValue)}
          sx={{ 
            borderBottom: 1, 
            borderColor: 'divider',
            minHeight: isSmallMobile ? 44 : 48,
            '& .MuiTab-root': {
              fontSize: isSmallMobile ? '0.8rem' : '0.875rem',
              minHeight: isSmallMobile ? 44 : 48,
              px: isSmallMobile ? 1 : 3,
            }
          }}
          variant={isSmallMobile ? "fullWidth" : "standard"}
        >
          <Tab label={isSmallMobile ? "選択" : "テンプレート選択"} />
          <Tab label="プレビュー" disabled={!selectedTemplate} />
        </Tabs>

        {error && (
          <Alert 
            severity="error" 
            sx={{ 
              m: isSmallMobile ? 1 : 2,
              fontSize: isSmallMobile ? '0.75rem' : '0.875rem',
            }} 
            onClose={() => setError('')}
          >
            {error}
          </Alert>
        )}

        {/* Mobile Category Drawer */}
        <Drawer
          anchor="left"
          open={mobileDrawerOpen}
          onClose={() => setMobileDrawerOpen(false)}
          sx={{
            '& .MuiDrawer-paper': {
              width: 280,
              maxWidth: '80vw',
            },
          }}
        >
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" fontWeight={600} mb={2} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FilterListIcon />
              カテゴリ
            </Typography>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                <CircularProgress size={24} />
              </Box>
            ) : (
              <List sx={{ p: 0 }}>
                {categories.map((category) => (
                  <ListItem key={category.id} sx={{ p: 0, mb: 1 }}>
                    <ListItemButton
                      selected={selectedCategory === category.id}
                      onClick={() => {
                        setSelectedCategory(category.id);
                        setMobileDrawerOpen(false);
                      }}
                      sx={{
                        borderRadius: 1,
                        border: selectedCategory === category.id ? 2 : 1,
                        borderColor: selectedCategory === category.id ? 'primary.main' : 'divider',
                        '&:hover': { borderColor: 'primary.main' },
                      }}
                    >
                      <ListItemText
                        primary={category.name}
                        secondary={category.description}
                        primaryTypographyProps={{
                          fontWeight: selectedCategory === category.id ? 600 : 400,
                          fontSize: '0.875rem',
                        }}
                        secondaryTypographyProps={{
                          fontSize: '0.75rem',
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </Drawer>

        {/* Template Selection Tab */}
        {currentTab === 0 && (
          <Box sx={{ 
            display: 'flex', 
            flex: 1,
            minHeight: 0,
            flexDirection: isMobile ? 'column' : 'row',
          }}>
            {/* Desktop Category Sidebar */}
            {!isMobile && (
              <Box
                sx={{
                  width: isTablet ? 200 : 250,
                  borderRight: 1,
                  borderColor: 'divider',
                  p: 2,
                  overflow: 'auto',
                }}
              >
                <Typography 
                  variant="subtitle2" 
                  fontWeight={600} 
                  mb={2}
                  sx={{ fontSize: isTablet ? '0.8rem' : '0.875rem' }}
                >
                  カテゴリ
                </Typography>
                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                    <CircularProgress size={24} />
                  </Box>
                ) : (
                  categories.map((category) => (
                    <Card
                      key={category.id}
                      sx={{
                        mb: 1,
                        cursor: 'pointer',
                        border: selectedCategory === category.id ? 2 : 1,
                        borderColor: selectedCategory === category.id ? 'primary.main' : 'divider',
                        '&:hover': { borderColor: 'primary.main' },
                      }}
                      onClick={() => setSelectedCategory(category.id)}
                    >
                      <CardContent sx={{ p: isTablet ? 1.5 : 2, '&:last-child': { pb: isTablet ? 1.5 : 2 } }}>
                        <Typography 
                          variant="body2" 
                          fontWeight={600}
                          sx={{ fontSize: isTablet ? '0.75rem' : '0.875rem' }}
                        >
                          {category.name}
                        </Typography>
                        <Typography 
                          variant="caption" 
                          color="text.secondary"
                          sx={{ fontSize: isTablet ? '0.7rem' : '0.75rem' }}
                        >
                          {category.description}
                        </Typography>
                      </CardContent>
                    </Card>
                  ))
                )}
              </Box>
            )}

            {/* Template List */}
            <Box sx={{ 
              flex: 1, 
              p: isSmallMobile ? 1 : 2, 
              overflow: 'hidden',
              width: isMobile ? '100%' : 'auto',
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0,
            }}>
              {/* Mobile Category Filter Button */}
              {isMobile && (
                <Box sx={{ mb: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={<FilterListIcon />}
                    onClick={() => setMobileDrawerOpen(true)}
                    size={isSmallMobile ? 'small' : 'medium'}
                    sx={{ 
                      fontSize: isSmallMobile ? '0.75rem' : '0.875rem',
                      mb: 1,
                    }}
                  >
                    {selectedCategory ? 
                      categories.find(c => c.id === selectedCategory)?.name || 'カテゴリを選択' 
                      : 'カテゴリを選択'}
                  </Button>
                </Box>
              )}

              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between', 
                mb: isSmallMobile ? 1 : 2,
                flexWrap: 'wrap',
                gap: 1,
              }}>
                <Typography 
                  variant="subtitle2" 
                  fontWeight={600}
                  sx={{ fontSize: isSmallMobile ? '0.8rem' : '0.875rem' }}
                >
                  テンプレート一覧
                </Typography>
                <IconButton 
                  onClick={() => fetchTemplates(selectedCategory)} 
                  size={isSmallMobile ? 'small' : 'medium'}
                >
                  <RefreshIcon sx={{ fontSize: isSmallMobile ? 18 : 20 }} />
                </IconButton>
              </Box>
              
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress size={isSmallMobile ? 32 : 40} />
                </Box>
              ) : (
                <Box sx={{ 
                  flex: 1, 
                  overflow: 'auto',
                  minHeight: 0,
                }}>
                  {templates.length === 0 ? (
                    <Box sx={{ 
                      textAlign: 'center', 
                      py: isSmallMobile ? 3 : 4,
                      color: 'text.secondary',
                    }}>
                      <Typography 
                        variant="body2"
                        sx={{ fontSize: isSmallMobile ? '0.8rem' : '0.875rem' }}
                      >
                        テンプレートが見つかりません
                      </Typography>
                    </Box>
                  ) : (
                    <Grid container spacing={isSmallMobile ? 1 : 2}>
                      {templates.map((template) => (
                    <Grid 
                      item 
                      xs={12} 
                      sm={6} 
                      md={isMobile ? 12 : 6}
                      lg={isMobile ? 12 : 4}
                      key={template.id}
                    >
                      <Card
                        sx={{
                          cursor: 'pointer',
                          border: 1,
                          borderColor: 'divider',
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            borderColor: 'primary.main',
                            boxShadow: 2,
                            transform: 'translateY(-2px)',
                          },
                        }}
                        onClick={() => handleTemplateSelect(template)}
                      >
                        <CardContent sx={{ 
                          flex: 1, 
                          p: isSmallMobile ? 1.5 : 2,
                          '&:last-child': { pb: isSmallMobile ? 1.5 : 2 }
                        }}>
                                                     <Box sx={{ mb: 1 }}>
                             <Typography
                               variant="h6"
                               fontWeight={600}
                               sx={{
                                 fontSize: isSmallMobile ? '0.9rem' : '1rem',
                                 lineHeight: 1.3,
                                 overflow: 'hidden',
                                 textOverflow: 'ellipsis',
                                 display: '-webkit-box',
                                 WebkitLineClamp: 2,
                                 WebkitBoxOrient: 'vertical',
                               }}
                             >
                               {template.title}
                             </Typography>
                           </Box>

                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                              mb: 2,
                              fontSize: isSmallMobile ? '0.75rem' : '0.875rem',
                              lineHeight: 1.4,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              display: '-webkit-box',
                              WebkitLineClamp: isSmallMobile ? 2 : 3,
                              WebkitBoxOrient: 'vertical',
                            }}
                          >
                            {template.description}
                          </Typography>

                          <Box sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 1,
                            flexWrap: 'wrap',
                            mt: 'auto',
                          }}>
                            <Chip
                              label={getDifficultyLabel(template.difficulty_level)}
                              size={isSmallMobile ? 'small' : 'medium'}
                              sx={{
                                backgroundColor: getDifficultyColor(template.difficulty_level),
                                color: 'white',
                                fontWeight: 500,
                                fontSize: isSmallMobile ? '0.65rem' : '0.75rem',
                              }}
                            />
                            <Chip
                              label={`${template.usage_count}回使用`}
                              variant="outlined"
                              size={isSmallMobile ? 'small' : 'medium'}
                              sx={{
                                fontSize: isSmallMobile ? '0.65rem' : '0.75rem',
                              }}
                            />
                          </Box>
                        </CardContent>
                      </Card>
                                           </Grid>
                     ))}
                   </Grid>
                 )}
               </Box>
             )}
            </Box>
          </Box>
        )}

        {/* Template Preview Tab */}
        {currentTab === 1 && selectedTemplate && (
          <Box sx={{ 
            p: isSmallMobile ? 2 : 3, 
            flex: 1,
            overflow: 'auto',
            minHeight: 0,
          }}>
            <Typography 
              variant="h6" 
              fontWeight={600} 
              mb={2}
              sx={{
                fontSize: isSmallMobile ? '1rem' : '1.25rem',
                lineHeight: 1.3,
              }}
            >
              {selectedTemplate.title}
            </Typography>
            <Typography 
              variant="body2" 
              color="text.secondary" 
              mb={3}
              sx={{
                fontSize: isSmallMobile ? '0.8rem' : '0.875rem',
                lineHeight: 1.4,
              }}
            >
              {selectedTemplate.description}
            </Typography>

            <Box>
              <Typography 
                variant="subtitle2" 
                fontWeight={600} 
                mb={2}
                sx={{ fontSize: isSmallMobile ? '0.85rem' : '0.9rem' }}
              >
                テンプレート内容
              </Typography>
              <Box
                sx={{
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  p: isSmallMobile ? 1.5 : 2,
                  bgcolor: 'grey.50',
                  minHeight: isSmallMobile ? 200 : 120,
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'monospace',
                  fontSize: isSmallMobile ? '0.75rem' : '0.875rem',
                  lineHeight: 1.4,
                  overflow: 'auto',
                  maxHeight: isSmallMobile ? '60vh' : '50vh',
                }}
              >
                {processTemplate(selectedTemplate)}
              </Box>
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ 
        p: isSmallMobile ? 2 : 3, 
        borderTop: 1, 
        borderColor: 'divider',
        gap: isSmallMobile ? 1 : 2,
        flexWrap: 'wrap',
      }}>
        <Button 
          onClick={handleClose} 
          variant="outlined"
          size={isSmallMobile ? 'small' : 'medium'}
          sx={{ 
            fontSize: isSmallMobile ? '0.8rem' : '0.875rem',
            minWidth: isSmallMobile ? 80 : 100,
          }}
        >
          キャンセル
        </Button>
        {currentTab === 1 && selectedTemplate && (
          <Button
            onClick={handleUseTemplate}
            variant="contained"
            startIcon={<SendIcon sx={{ fontSize: isSmallMobile ? 16 : 20 }} />}
            size={isSmallMobile ? 'small' : 'medium'}
            sx={{ 
              fontSize: isSmallMobile ? '0.8rem' : '0.875rem',
              minWidth: isSmallMobile ? 120 : 140,
              ml: isSmallMobile ? 0 : 1,
            }}
          >
            {isSmallMobile ? '使用' : 'テンプレートを使用'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default TemplateSelectionModal;