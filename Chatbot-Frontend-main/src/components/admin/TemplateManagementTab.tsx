import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  Alert,
  Grid,
  Divider,
  Paper,
  IconButton,
  Tooltip,
  alpha,
  useTheme,
  useMediaQuery,
  InputAdornment,
  Fade,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Stack,
} from "@mui/material";
import DescriptionIcon from "@mui/icons-material/Description";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import CategoryIcon from "@mui/icons-material/Category";

import SaveIcon from "@mui/icons-material/Save";
import CancelIcon from "@mui/icons-material/Cancel";
import VisibilityIcon from "@mui/icons-material/Visibility";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import FavoriteIcon from "@mui/icons-material/Favorite";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import InfoIcon from "@mui/icons-material/Info";
import TipsAndUpdatesIcon from "@mui/icons-material/TipsAndUpdates";
import MenuBookIcon from "@mui/icons-material/MenuBook";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import LoadingIndicator from "./LoadingIndicator";
import api from "../../api";

interface Template {
  id: string;
  title: string;
  description: string;
  content: string;
  category_id: string;
  category_name?: string;
  template_type: 'system' | 'company' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  usage_count?: number;
}



interface Category {
  id: string;
  name: string;
  description: string;
  display_order: number;
  is_active: boolean;
  category_type: 'system' | 'company';
  company_id?: string;
  created_at: string;
  updated_at: string;
}

interface TemplateManagementTabProps {
  user?: any;
}

const TemplateManagementTab: React.FC<TemplateManagementTabProps> = ({ user }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isTablet = useMediaQuery(theme.breakpoints.between("sm", "md"));

  // State management
  const [templates, setTemplates] = useState<Template[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Tab management
  const [activeTab, setActiveTab] = useState<'templates' | 'categories'>('templates');

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Category dialog states
  const [createCategoryDialogOpen, setCreateCategoryDialogOpen] = useState(false);
  const [editCategoryDialogOpen, setEditCategoryDialogOpen] = useState(false);
  const [deleteCategoryDialogOpen, setDeleteCategoryDialogOpen] = useState(false);

  // Form states
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    content: '',
    category_id: '',
    is_active: true,
  });


  // Category form states
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [categoryFormData, setCategoryFormData] = useState({
    name: '',
    description: '',
    display_order: 0,
    is_active: true,
    category_type: 'company', // デフォルトは会社カテゴリ
  });

  // Loading states
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [helpDialogOpen, setHelpDialogOpen] = useState(false);

  // Access control - only allow user and admin roles
  if (user?.role === "employee") {
    return (
      <Fade in={true} timeout={400}>
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "400px",
            textAlign: "center",
            p: 4,
          }}
        >
          <DescriptionIcon
            sx={{
              fontSize: "4rem",
              color: "text.disabled",
              mb: 2,
            }}
          />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: "text.secondary",
              mb: 1,
            }}
          >
            アクセス権限がありません
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ maxWidth: "400px" }}
          >
            社員アカウントにはテンプレート管理権限がありません。<br />
            管理者にお問い合わせください。
          </Typography>
        </Box>
      </Fade>
    );
  }

  // Fetch data
  useEffect(() => {
    fetchTemplates();
    fetchCategories();
  }, []);

  const fetchTemplates = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/templates');
      const templates = response.data.templates || [];
      
      // カテゴリ名が設定されていないテンプレートに対してカテゴリ名を補完
      const enrichedTemplates = templates.map((template: Template) => {
        if (!template.category_name && template.category_id && categories.length > 0) {
          const category = categories.find(cat => cat.id === template.category_id);
          if (category) {
            template.category_name = category.name;
          }
        }
        return template;
      });
      
      setTemplates(enrichedTemplates);
      setError(null);
    } catch (error: any) {
      console.error('テンプレート取得エラー:', error);
      setError('テンプレートの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get('/templates/categories');
      setCategories(response.data.categories || []);
    } catch (error: any) {
      console.error('カテゴリ取得エラー:', error);
    }
  };

  // Form handlers
  const handleCreateTemplate = async () => {
    if (!formData.title || !formData.content || !formData.category_id) {
      setError('必須項目を入力してください');
      return;
    }

    setIsCreating(true);
    try {
      const templateData = {
        title: formData.title,
        description: formData.description,
        template_content: formData.content,
        category_id: formData.category_id,
        template_type: 'company',
        is_public: formData.is_active
      };

      await api.post('/templates', templateData);
      setSuccess('テンプレートが作成されました');
      setCreateDialogOpen(false);
      resetForm();
      // テンプレートを再取得
      await fetchTemplates();
    } catch (error: any) {
      console.error('テンプレート作成エラー:', error);
      setError(error.response?.data?.detail || 'テンプレートの作成に失敗しました');
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateTemplate = async () => {
    if (!selectedTemplate || !formData.title || !formData.content || !formData.category_id) {
      setError('必須項目を入力してください');
      return;
    }

    setIsUpdating(true);
    try {
      const templateData = {
        title: formData.title,
        description: formData.description,
        template_content: formData.content,
        category_id: formData.category_id,
        is_public: formData.is_active
      };

      await api.put(`/templates/${selectedTemplate.id}`, templateData);
      setSuccess('テンプレートが更新されました');
      setEditDialogOpen(false);
      resetForm();
      // テンプレートを再取得
      await fetchTemplates();
    } catch (error: any) {
      console.error('テンプレート更新エラー:', error);
      setError(error.response?.data?.detail || 'テンプレートの更新に失敗しました');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteTemplate = async () => {
    if (!selectedTemplate) return;

    setIsDeleting(true);
    try {
      await api.delete(`/templates/${selectedTemplate.id}`);
      setSuccess('テンプレートが削除されました');
      setDeleteDialogOpen(false);
      setSelectedTemplate(null);
      fetchTemplates();
    } catch (error: any) {
      console.error('テンプレート削除エラー:', error);
      setError(error.response?.data?.detail || 'テンプレートの削除に失敗しました');
    } finally {
      setIsDeleting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      content: '',
      category_id: '',
      is_active: true,
    });

    setSelectedTemplate(null);
  };

  const openEditDialog = (template: Template) => {
    setSelectedTemplate(template);
    setFormData({
      title: template.title,
      description: template.description,
      content: template.content,
      category_id: template.category_id,
      is_active: template.is_active,
    });

    setEditDialogOpen(true);
  };

  const openPreviewDialog = (template: Template) => {
    setSelectedTemplate(template);
    setPreviewDialogOpen(true);
  };

  const openDeleteDialog = (template: Template) => {
    setSelectedTemplate(template);
    setDeleteDialogOpen(true);
  };



  // Category management functions
  const handleCreateCategory = async () => {
    if (!categoryFormData.name) {
      setError('カテゴリ名は必須です');
      return;
    }

    setIsCreating(true);
    try {
      await api.post('/templates/categories', categoryFormData);
      setSuccess('カテゴリが正常に作成されました');
      setCreateCategoryDialogOpen(false);
      resetCategoryForm();
      await fetchCategories();
    } catch (error: any) {
      setError(`カテゴリ作成エラー: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateCategory = async () => {
    if (!selectedCategory || !categoryFormData.name) {
      setError('カテゴリ名は必須です');
      return;
    }

    setIsUpdating(true);
    try {
      await api.put(`/templates/categories/${selectedCategory.id}`, categoryFormData);
      setSuccess('カテゴリが正常に更新されました');
      setEditCategoryDialogOpen(false);
      resetCategoryForm();
      await fetchCategories();
    } catch (error: any) {
      setError(`カテゴリ更新エラー: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteCategory = async () => {
    if (!selectedCategory) return;

    setIsDeleting(true);
    try {
      await api.delete(`/templates/categories/${selectedCategory.id}`);
      setSuccess('カテゴリが正常に削除されました');
      setDeleteCategoryDialogOpen(false);
      setSelectedCategory(null);
      await fetchCategories();
    } catch (error: any) {
      setError(`カテゴリ削除エラー: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  const resetCategoryForm = () => {
    setCategoryFormData({
      name: '',
      description: '',
      display_order: 0,
      is_active: true,
      category_type: 'company', // デフォルトは会社カテゴリ
    });
    setSelectedCategory(null);
  };

  const openCreateCategoryDialog = () => {
    resetCategoryForm();
    setCreateCategoryDialogOpen(true);
  };

  const openEditCategoryDialog = (category: Category) => {
    setSelectedCategory(category);
    setCategoryFormData({
      name: category.name,
      description: category.description,
      display_order: category.display_order,
      is_active: category.is_active,
      category_type: category.category_type || 'company', // カテゴリタイプを保持
    });
    setEditCategoryDialogOpen(true);
  };

  const openDeleteCategoryDialog = (category: Category) => {
    setSelectedCategory(category);
    setDeleteCategoryDialogOpen(true);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getTemplateTypeColor = (type: string) => {
    switch (type) {
      case 'system': return 'primary';
      case 'company': return 'secondary';
      case 'user': return 'info';
      default: return 'default';
    }
  };

  const getTemplateTypeLabel = (type: string) => {
    switch (type) {
      case 'system': return 'システム';
      case 'company': return '会社';
      case 'user': return 'ユーザー';
      default: return type;
    }
  };

  // Filter templates to show only company templates for this user
  const companyTemplates = templates.filter(t => t.template_type === 'company');

  return (
    <Fade in={true} timeout={400}>
      <Box>
        {/* Header */}
        <Box
          sx={{
            mb: 3,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            px: { xs: 1, sm: 0 },
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <DescriptionIcon
              sx={{
                mr: 1.5,
                color: theme.palette.primary.main,
                fontSize: { xs: "1.8rem", sm: "2rem" },
              }}
            />
            <Typography
              variant={isMobile ? "h6" : "h5"}
              sx={{
                fontWeight: 600,
                color: "text.primary",
              }}
            >
              テンプレート管理
            </Typography>
            <Tooltip title="プロンプトテンプレートガイドを見る">
              <IconButton
                onClick={() => setHelpDialogOpen(true)}
                sx={{
                  ml: 1,
                  color: theme.palette.primary.main,
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.primary.main, 0.2),
                  },
                }}
              >
                <HelpOutlineIcon />
              </IconButton>
            </Tooltip>
          </Box>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={activeTab === 'templates' ? () => setCreateDialogOpen(true) : openCreateCategoryDialog}
            size={isMobile ? "small" : "medium"}
            sx={{
              borderRadius: 2,
              px: { xs: 1.5, sm: 2 },
              "&:hover": {
                backgroundColor: "primary.dark",
              },
            }}
          >
            {!isMobile && (activeTab === 'templates' ? "テンプレート作成" : "カテゴリ作成")}
            {isMobile && "新規作成"}
          </Button>
        </Box>

        {/* Tab Navigation */}
        <Box sx={{ mb: 3 }}>
          <Stack direction="row" spacing={1}>
            <Button
              variant={activeTab === 'templates' ? 'contained' : 'outlined'}
              startIcon={<DescriptionIcon />}
              onClick={() => setActiveTab('templates')}
              sx={{
                borderRadius: 2,
                px: 3,
                py: 1,
                textTransform: 'none',
                fontWeight: activeTab === 'templates' ? 600 : 400,
              }}
            >
              テンプレート
            </Button>
            <Button
              variant={activeTab === 'categories' ? 'contained' : 'outlined'}
              startIcon={<CategoryIcon />}
              onClick={() => setActiveTab('categories')}
              sx={{
                borderRadius: 2,
                px: 3,
                py: 1,
                textTransform: 'none',
                fontWeight: activeTab === 'categories' ? 600 : 400,
              }}
            >
              カテゴリ
            </Button>
          </Stack>
        </Box>

        {/* Error/Success Messages */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {/* Content based on active tab */}
        {activeTab === 'templates' && (
          <>
            {/* Templates Table */}
            <Card
          elevation={0}
          sx={{
            borderRadius: 2,
            border: "1px solid rgba(0, 0, 0, 0.12)",
            position: "relative",
            overflow: "hidden",
            transition: "all 0.3s ease",
            "&:hover": {
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
            },
            "&::before": {
              content: '""',
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "4px",
              background: "linear-gradient(135deg, #1976d2, #64b5f6)",
              opacity: 0.9,
            },
          }}
        >
          <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
            {isLoading ? (
              <LoadingIndicator message="テンプレートを読み込み中..." />
            ) : companyTemplates.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <DescriptionIcon sx={{ fontSize: '3rem', color: 'text.disabled', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  テンプレートがありません
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={() => setCreateDialogOpen(true)}
                  sx={{ mt: 2 }}
                >
                  最初のテンプレートを作成
                </Button>
              </Box>
            ) : (
              <>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'grey.50' }}>
                        <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>タイトル</Typography></TableCell>
                        <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>カテゴリ</Typography></TableCell>
                        <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>ステータス</Typography></TableCell>
                        <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>利用回数</Typography></TableCell>
                        <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>更新日</Typography></TableCell>
                        <TableCell><Typography variant="caption" sx={{ fontWeight: 600 }}>操作</Typography></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {companyTemplates
                        .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                        .map((template) => (
                          <TableRow key={template.id} hover>
                            <TableCell>
                              <Box>
                                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                  {template.title}
                                </Typography>
                                {template.description && (
                                  <Typography variant="caption" color="text.secondary">
                                    {template.description.length > 50 
                                      ? `${template.description.substring(0, 50)}...` 
                                      : template.description}
                                  </Typography>
                                )}
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={template.category_name || 'カテゴリなし'}
                                size="small"
                                variant="outlined"
                                icon={<CategoryIcon />}
                              />
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={template.is_active ? '有効' : '無効'}
                                color={template.is_active ? 'success' : 'default'}
                                size="small"
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {template.usage_count || 0}回
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="caption">
                                {new Date(template.updated_at).toLocaleDateString('ja-JP')}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Stack direction="row" spacing={0.5}>
                                <Tooltip title="プレビュー">
                                  <IconButton
                                    size="small"
                                    onClick={() => openPreviewDialog(template)}
                                  >
                                    <VisibilityIcon fontSize="small" />
                                  </IconButton>
                                </Tooltip>
                                <Tooltip title="編集">
                                  <IconButton
                                    size="small"
                                    onClick={() => openEditDialog(template)}
                                  >
                                    <EditIcon fontSize="small" />
                                  </IconButton>
                                </Tooltip>
                                <Tooltip title="削除">
                                  <IconButton
                                    size="small"
                                    onClick={() => openDeleteDialog(template)}
                                    color="error"
                                  >
                                    <DeleteIcon fontSize="small" />
                                  </IconButton>
                                </Tooltip>
                              </Stack>
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <TablePagination
                  rowsPerPageOptions={[5, 10, 25]}
                  component="div"
                  count={companyTemplates.length}
                  rowsPerPage={rowsPerPage}
                  page={page}
                  onPageChange={handleChangePage}
                  onRowsPerPageChange={handleChangeRowsPerPage}
                  labelRowsPerPage="行数:"
                  labelDisplayedRows={({ from, to, count }) => `${from}–${to} / ${count}`}
                />
              </>
            )}
          </CardContent>
        </Card>

        {/* Create Template Dialog */}
        <Dialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          maxWidth="md"
          fullWidth
          fullScreen={isMobile}
        >
          <DialogTitle>新規テンプレート作成</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="タイトル"
                  fullWidth
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>カテゴリ</InputLabel>
                  <Select
                    value={formData.category_id}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                    label="カテゴリ"
                  >
                    {categories.map((category) => (
                      <MenuItem key={category.id} value={category.id}>
                        {category.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="説明"
                  fullWidth
                  multiline
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="テンプレート内容"
                  fullWidth
                  multiline
                  rows={6}
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  required

                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                  }
                  label="有効"
                />
              </Grid>


            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateDialogOpen(false)}>
              キャンセル
            </Button>
            <Button
              variant="contained"
              onClick={handleCreateTemplate}
              disabled={isCreating}
              startIcon={isCreating ? null : <SaveIcon />}
            >
              {isCreating ? <LoadingIndicator size={20} message="" /> : '作成'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Edit Template Dialog */}
        <Dialog
          open={editDialogOpen}
          onClose={() => setEditDialogOpen(false)}
          maxWidth="md"
          fullWidth
          fullScreen={isMobile}
        >
          <DialogTitle>テンプレート編集</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="タイトル"
                  fullWidth
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>カテゴリ</InputLabel>
                  <Select
                    value={formData.category_id}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                    label="カテゴリ"
                  >
                    {categories.map((category) => (
                      <MenuItem key={category.id} value={category.id}>
                        {category.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="説明"
                  fullWidth
                  multiline
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="テンプレート内容"
                  fullWidth
                  multiline
                  rows={6}
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  required

                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                  }
                  label="有効"
                />
              </Grid>


            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditDialogOpen(false)}>
              キャンセル
            </Button>
            <Button
              variant="contained"
              onClick={handleUpdateTemplate}
              disabled={isUpdating}
              startIcon={isUpdating ? null : <SaveIcon />}
            >
              {isUpdating ? <LoadingIndicator size={20} message="" /> : '更新'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Preview Template Dialog */}
        <Dialog
          open={previewDialogOpen}
          onClose={() => setPreviewDialogOpen(false)}
          maxWidth="md"
          fullWidth
          fullScreen={isMobile}
        >
          <DialogTitle>テンプレートプレビュー</DialogTitle>
          <DialogContent>
            {selectedTemplate && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  {selectedTemplate.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {selectedTemplate.description}
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" gutterBottom>
                  テンプレート内容:
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.50', mb: 2 }}>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                    {selectedTemplate.content}
                  </Typography>
                </Paper>

              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setPreviewDialogOpen(false)}>
              閉じる
            </Button>
          </DialogActions>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog
          open={deleteDialogOpen}
          onClose={() => setDeleteDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>テンプレート削除の確認</DialogTitle>
          <DialogContent>
            {selectedTemplate && (
              <Typography>
                「{selectedTemplate.title}」を削除してもよろしいですか？
                <br />
                この操作は取り消すことができません。
              </Typography>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteDialogOpen(false)}>
              キャンセル
            </Button>
            <Button
              variant="contained"
              color="error"
              onClick={handleDeleteTemplate}
              disabled={isDeleting}
              startIcon={isDeleting ? null : <DeleteIcon />}
            >
              {isDeleting ? <LoadingIndicator size={20} message="" /> : '削除'}
            </Button>
          </DialogActions>
        </Dialog>
          </>
        )}

        {/* Categories Table */}
        {activeTab === 'categories' && (
          <Card
            elevation={0}
            sx={{
              borderRadius: 2,
              border: "1px solid rgba(0, 0, 0, 0.12)",
              position: "relative",
              overflow: "hidden",
              transition: "all 0.3s ease",
              "&:hover": {
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
              },
            }}
          >
            <CardContent sx={{ p: 0 }}>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ backgroundColor: "grey.50" }}>
                      <TableCell sx={{ fontWeight: 600, fontSize: "0.9rem" }}>
                        カテゴリ名
                      </TableCell>
                      <TableCell sx={{ fontWeight: 600, fontSize: "0.9rem" }}>
                        説明
                      </TableCell>
                      <TableCell sx={{ fontWeight: 600, fontSize: "0.9rem" }}>
                        表示順
                      </TableCell>
                      <TableCell sx={{ fontWeight: 600, fontSize: "0.9rem" }}>
                        状態
                      </TableCell>
                      <TableCell sx={{ fontWeight: 600, fontSize: "0.9rem" }}>
                        操作
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {isLoading ? (
                      <TableRow>
                        <TableCell colSpan={5} sx={{ textAlign: "center", py: 4 }}>
                          <LoadingIndicator message="カテゴリを読み込み中..." />
                        </TableCell>
                      </TableRow>
                    ) : categories.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} sx={{ textAlign: "center", py: 4 }}>
                          <Typography color="text.secondary">
                            カテゴリが見つかりません
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      categories.map((category) => (
                        <TableRow key={category.id} hover>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {category.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {category.description || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {category.display_order}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={category.is_active ? "有効" : "無効"}
                              color={category.is_active ? "success" : "default"}
                              size="small"
                              sx={{ borderRadius: 1 }}
                            />
                          </TableCell>
                          <TableCell>
                            <Stack direction="row" spacing={1}>
                              <Tooltip title="編集">
                                <IconButton
                                  size="small"
                                  onClick={() => openEditCategoryDialog(category)}
                                  sx={{ color: "primary.main" }}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="削除">
                                <IconButton
                                  size="small"
                                  onClick={() => openDeleteCategoryDialog(category)}
                                  sx={{ color: "error.main" }}
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </Stack>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        )}

        {/* Category Create Dialog */}
        <Dialog
          open={createCategoryDialogOpen}
          onClose={() => setCreateCategoryDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>新しいカテゴリを作成</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                label="カテゴリ名"
                value={categoryFormData.name}
                onChange={(e) => setCategoryFormData({ ...categoryFormData, name: e.target.value })}
                fullWidth
                required
              />
              <TextField
                label="説明"
                value={categoryFormData.description}
                onChange={(e) => setCategoryFormData({ ...categoryFormData, description: e.target.value })}
                fullWidth
                multiline
                rows={2}
              />
              <TextField
                label="表示順"
                type="number"
                value={categoryFormData.display_order}
                onChange={(e) => setCategoryFormData({ ...categoryFormData, display_order: parseInt(e.target.value) || 0 })}
                fullWidth
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={categoryFormData.is_active}
                    onChange={(e) => setCategoryFormData({ ...categoryFormData, is_active: e.target.checked })}
                  />
                }
                label="有効"
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateCategoryDialogOpen(false)}>
              キャンセル
            </Button>
            <Button
              variant="contained"
              onClick={handleCreateCategory}
              disabled={isCreating}
              startIcon={isCreating ? null : <SaveIcon />}
            >
              {isCreating ? <LoadingIndicator size={20} message="" /> : '作成'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Category Edit Dialog */}
        <Dialog
          open={editCategoryDialogOpen}
          onClose={() => setEditCategoryDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>カテゴリを編集</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                label="カテゴリ名"
                value={categoryFormData.name}
                onChange={(e) => setCategoryFormData({ ...categoryFormData, name: e.target.value })}
                fullWidth
                required
              />
              <TextField
                label="説明"
                value={categoryFormData.description}
                onChange={(e) => setCategoryFormData({ ...categoryFormData, description: e.target.value })}
                fullWidth
                multiline
                rows={2}
              />
              <TextField
                label="表示順"
                type="number"
                value={categoryFormData.display_order}
                onChange={(e) => setCategoryFormData({ ...categoryFormData, display_order: parseInt(e.target.value) || 0 })}
                fullWidth
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={categoryFormData.is_active}
                    onChange={(e) => setCategoryFormData({ ...categoryFormData, is_active: e.target.checked })}
                  />
                }
                label="有効"
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditCategoryDialogOpen(false)}>
              キャンセル
            </Button>
            <Button
              variant="contained"
              onClick={handleUpdateCategory}
              disabled={isUpdating}
              startIcon={isUpdating ? null : <SaveIcon />}
            >
              {isUpdating ? <LoadingIndicator size={20} message="" /> : '更新'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Category Delete Dialog */}
        <Dialog
          open={deleteCategoryDialogOpen}
          onClose={() => setDeleteCategoryDialogOpen(false)}
          maxWidth="xs"
        >
          <DialogTitle>カテゴリを削除</DialogTitle>
          <DialogContent>
            {selectedCategory && (
              <Typography>
                「{selectedCategory.name}」を削除してもよろしいですか？
                <br />
                この操作は取り消すことができません。
              </Typography>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteCategoryDialogOpen(false)}>
              キャンセル
            </Button>
            <Button
              variant="contained"
              color="error"
              onClick={handleDeleteCategory}
              disabled={isDeleting}
              startIcon={isDeleting ? null : <DeleteIcon />}
            >
              {isDeleting ? <LoadingIndicator size={20} message="" /> : '削除'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Help Guide Dialog */}
        <Dialog
          open={helpDialogOpen}
          onClose={() => setHelpDialogOpen(false)}
          maxWidth="lg"
          fullWidth
          fullScreen={isMobile}
          PaperProps={{
            sx: {
              borderRadius: isMobile ? 0 : 3,
              maxHeight: '90vh',
              background: 'linear-gradient(135deg, #f8fbff 0%, #e3f2fd 100%)',
            },
          }}
        >
          <DialogTitle
            sx={{
              background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
              color: 'white',
              textAlign: 'center',
              py: 3,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
              <MenuBookIcon sx={{ fontSize: 32 }} />
              <Typography variant="h4" component="div" sx={{ fontWeight: 700 }}>
                プロンプトテンプレート完全ガイド
              </Typography>
            </Box>
          </DialogTitle>
          
          <DialogContent sx={{ p: 0 }}>
            <Box sx={{ 
              maxHeight: isMobile ? 'calc(100vh - 120px)' : '70vh', 
              overflowY: 'auto',
              p: 3,
            }}>
              {/* 概要セクション */}
              <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 3, background: 'rgba(255,255,255,0.9)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <InfoIcon sx={{ color: 'primary.main', mr: 1, fontSize: 28 }} />
                  <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    プロンプトテンプレートとは？
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ lineHeight: 1.8, mb: 2 }}>
                  プロンプトテンプレートは、AIチャットボットとの対話を効率化するための事前定義された質問パターンです。
                  よく使用する質問や指示を保存し、ワンクリックで呼び出すことができます。
                </Typography>
                <Box sx={{ bgcolor: '#e3f2fd', p: 2, borderRadius: 2, borderLeft: '4px solid #2196f3' }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: '#1976d2' }}>
                    💡 効果：作業効率が最大70%向上し、一貫性のある質問が可能になります
                  </Typography>
                </Box>
              </Paper>

              {/* 作成方法セクション */}
              <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 3, background: 'rgba(255,255,255,0.9)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TipsAndUpdatesIcon sx={{ color: '#1976d2', mr: 1, fontSize: 28 }} />
                  <Typography variant="h5" sx={{ fontWeight: 700, color: '#1976d2' }}>
                    テンプレート作成の手順
                  </Typography>
                </Box>
                
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: 'text.primary' }}>
                    ステップ1: 基本情報の入力
                  </Typography>
                  <Stack spacing={1} sx={{ ml: 2 }}>
                    <Typography variant="body2">• <strong>タイトル</strong>: テンプレートの目的がわかる名前を付ける</Typography>
                    <Typography variant="body2">• <strong>説明</strong>: どんな場面で使うかを詳しく記載</Typography>
                    <Typography variant="body2">• <strong>カテゴリ</strong>: 整理しやすいカテゴリを選択</Typography>
                  </Stack>
                </Box>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: 'text.primary' }}>
                    ステップ2: テンプレート内容の作成
                  </Typography>
                  <Stack spacing={1} sx={{ ml: 2 }}>
                    <Typography variant="body2">• 具体的で明確な指示を記載</Typography>
                    <Typography variant="body2">• 文脈を含めて詳細に説明</Typography>
                    <Typography variant="body2">• 期待する回答形式を指定</Typography>
                  </Stack>
                </Box>

                <Box sx={{ bgcolor: '#e3f2fd', p: 2, borderRadius: 2, borderLeft: '4px solid #1976d2' }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: '#1565c0' }}>
                    ⭐ コツ：「5W1H」を意識して、具体的で実行可能な指示を作成しましょう
                  </Typography>
                </Box>
              </Paper>

              {/* 効果的な使い方セクション */}
              <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 3, background: 'rgba(255,255,255,0.9)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TipsAndUpdatesIcon sx={{ color: '#1976d2', mr: 1, fontSize: 28 }} />
                  <Typography variant="h5" sx={ { fontWeight: 700, color: '#1976d2' }}>
                    効果的なテンプレート作成のポイント
                  </Typography>
                </Box>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ bgcolor: '#e3f2fd', p: 2, borderRadius: 2, height: '100%' }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: '#1976d2', mb: 1 }}>
                        ✅ 良い例
                      </Typography>
                      <Stack spacing={1}>
                        <Typography variant="body2">• 具体的な指示を含む</Typography>
                        <Typography variant="body2">• 期待する回答形式を明記</Typography>
                        <Typography variant="body2">• 文脈情報を提供</Typography>
                        <Typography variant="body2">• 専門用語を定義</Typography>
                      </Stack>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ bgcolor: '#ffebee', p: 2, borderRadius: 2, height: '100%' }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: 'error.main', mb: 1 }}>
                        ❌ 避けるべき例
                      </Typography>
                      <Stack spacing={1}>
                        <Typography variant="body2">• 曖昧で抽象的な指示</Typography>
                        <Typography variant="body2">• 一般的すぎる質問</Typography>
                        <Typography variant="body2">• 文脈のない短い質問</Typography>
                        <Typography variant="body2">• 複数の質問を混在</Typography>
                      </Stack>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>

              {/* 実用例セクション */}
              <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 3, background: 'rgba(255,255,255,0.9)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <DescriptionIcon sx={{ color: '#1976d2', mr: 1, fontSize: 28 }} />
                  <Typography variant="h5" sx={{ fontWeight: 700, color: '#1976d2' }}>
                    実用的なテンプレート例
                  </Typography>
                </Box>
                
                <Stack spacing={3}>
                  <Box sx={{ bgcolor: '#e3f2fd', p: 2, borderRadius: 2 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#1976d2', mb: 1 }}>
                      📧 ビジネスメール作成
                    </Typography>
                    <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                      「以下の内容でプロフェッショナルなビジネスメールを作成してください：
                      <br />• 宛先: [相手の名前・役職]
                      <br />• 目的: [メールの目的]
                      <br />• 要点: [伝えたい内容]
                      <br />• トーン: 丁寧かつ簡潔に」
                    </Typography>
                  </Box>

                  <Box sx={{ bgcolor: '#e8f4fd', p: 2, borderRadius: 2 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#1565c0', mb: 1 }}>
                      📊 データ分析依頼
                    </Typography>
                    <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                      「以下のデータを分析し、実用的な改善提案を提供してください：
                      <br />• データ内容: [データの説明]
                      <br />• 分析目的: [何を知りたいか]
                      <br />• 期待する結果: [具体的な成果物]
                      <br />• 形式: 箇条書きで3つの改善案を提示」
                    </Typography>
                  </Box>

                  <Box sx={{ bgcolor: '#f0f8ff', p: 2, borderRadius: 2 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#1976d2', mb: 1 }}>
                      🎯 プロジェクト計画
                    </Typography>
                    <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                      「以下のプロジェクトの詳細な実行計画を作成してください：
                      <br />• プロジェクト名: [プロジェクト名]
                      <br />• 目標: [達成したい目標]
                      <br />• 期間: [実行期間]
                      <br />• 制約条件: [制約やリスク]
                      <br />• 成果物: タスクリスト、スケジュール、リスク対策を含む」
                    </Typography>
                  </Box>
                </Stack>
              </Paper>

              {/* 初心者向けテンプレートフォーマット例セクション */}
              <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 3, background: 'rgba(255,255,255,0.9)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TipsAndUpdatesIcon sx={{ color: '#1976d2', mr: 1, fontSize: 28 }} />
                  <Typography variant="h5" sx={{ fontWeight: 700, color: '#1976d2' }}>
                    初心者向け：コピー&ペーストで使えるテンプレートフォーマット
                  </Typography>
                </Box>
                
                <Alert severity="info" sx={{ mb: 3 }}>
                  <Typography variant="body2">
                    以下のフォーマットをコピーして、テンプレート作成時の「テンプレート内容」欄に貼り付けてください。
                    【】内の部分を具体的な内容に置き換えるだけで、効果的なプロンプトが完成します。
                  </Typography>
                </Alert>

                <Stack spacing={3}>
                  <Box sx={{ bgcolor: '#f8fbff', p: 3, borderRadius: 2, border: '1px solid #e3f2fd' }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: '#1976d2', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ContentCopyIcon sx={{ fontSize: 20 }} />
                      📋 基本フォーマット（汎用）
                    </Typography>
                    <Box sx={{ bgcolor: '#ffffff', p: 2, borderRadius: 1, fontFamily: 'monospace', fontSize: '0.9rem', border: '1px solid #ddd' }}>
                      <Typography component="pre" sx={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
{`【役割】
あなたは【専門分野】の専門家です。

【タスク】
以下の内容について【具体的な作業内容】してください。

【入力情報】
・【項目1】: 【内容】
・【項目2】: 【内容】
・【項目3】: 【内容】

【出力形式】
【希望する回答の形式や構造を指定】

【注意事項】
・【重要なポイント1】
・【重要なポイント2】
・【避けるべきこと】`}
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ mt: 1, display: 'block', color: '#666' }}>
                      💡 使用例：「あなたは営業の専門家です」「メール文章を作成してください」など
                    </Typography>
                  </Box>

                  <Box sx={{ bgcolor: '#f0f8ff', p: 3, borderRadius: 2, border: '1px solid #e3f2fd' }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: '#1565c0', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ContentCopyIcon sx={{ fontSize: 20 }} />
                      💼 ビジネス文書作成フォーマット
                    </Typography>
                    <Box sx={{ bgcolor: '#ffffff', p: 2, borderRadius: 1, fontFamily: 'monospace', fontSize: '0.9rem', border: '1px solid #ddd' }}>
                      <Typography component="pre" sx={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
{`【文書の種類】
【メール/提案書/報告書/議事録など】を作成してください。

【基本情報】
・宛先：【相手の名前・役職】
・件名：【メールの件名】
・目的：【文書を作成する目的】

【内容詳細】
・背景：【なぜこの文書が必要か】
・要点：【伝えたい主要なポイント】
・期待する結果：【相手にどう行動してほしいか】

【スタイル要件】
・トーン：【丁寧/カジュアル/フォーマル】
・文字数：【約○○文字】
・構成：【挨拶→本文→締め】`}
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ bgcolor: '#fff8f0', p: 3, borderRadius: 2, border: '1px solid #ffe0b2' }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: '#f57c00', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ContentCopyIcon sx={{ fontSize: 20 }} />
                      📊 分析・調査フォーマット
                    </Typography>
                    <Box sx={{ bgcolor: '#ffffff', p: 2, borderRadius: 1, fontFamily: 'monospace', fontSize: '0.9rem', border: '1px solid #ddd' }}>
                      <Typography component="pre" sx={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
{`【分析対象】
【データ/資料/状況】について詳しく分析してください。

【分析の観点】
・【観点1】：【具体的な分析ポイント】
・【観点2】：【具体的な分析ポイント】
・【観点3】：【具体的な分析ポイント】

【提供データ】
【ここに分析対象のデータや情報を記載】

【求める成果物】
1. 【結果1】：【詳細な説明】
2. 【結果2】：【詳細な説明】
3. 【結果3】：【詳細な説明】

【制約条件】
・期限：【いつまでに】
・形式：【表/グラフ/文章など】`}
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ bgcolor: '#f0fff0', p: 3, borderRadius: 2, border: '1px solid #c8e6c8' }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: '#2e7d32', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ContentCopyIcon sx={{ fontSize: 20 }} />
                      🎯 問題解決フォーマット
                    </Typography>
                    <Box sx={{ bgcolor: '#ffffff', p: 2, borderRadius: 1, fontFamily: 'monospace', fontSize: '0.9rem', border: '1px solid #ddd' }}>
                      <Typography component="pre" sx={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
{`【現在の問題】
【具体的な問題の内容】

【問題の背景】
・発生時期：【いつから】
・関係者：【誰が関わっているか】
・影響範囲：【どこまで影響があるか】

【制約条件】
・予算：【使える費用】
・期限：【解決期限】
・リソース：【使える人員・ツール】

【求める解決策】
以下の形式で3つの解決案を提示してください：
1. 【解決案1】
   - 実行方法：【具体的な手順】
   - 期待効果：【どんな改善が見込めるか】
   - リスク：【考えられるデメリット】

2. 【解決案2】（同様の形式）
3. 【解決案3】（同様の形式）`}
                      </Typography>
                    </Box>
                  </Box>
                </Stack>

                <Box sx={{ mt: 3, p: 2, bgcolor: '#e8f5e8', borderRadius: 2, border: '1px solid #4caf50' }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: '#2e7d32', mb: 1 }}>
                    🚀 使い方のコツ
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#2e7d32' }}>
                    1. 上記フォーマットをコピーして「テンプレート内容」に貼り付け<br/>
                    2. 【】内の部分を具体的な内容に置き換え<br/>
                    3. 必要に応じて項目を追加・削除してカスタマイズ<br/>
                    4. テストして効果的な結果が得られるまで調整
                  </Typography>
                </Box>
              </Paper>

              {/* 管理のコツセクション */}
              <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 3, background: 'rgba(255,255,255,0.9)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CategoryIcon sx={{ color: '#1976d2', mr: 1, fontSize: 28 }} />
                  <Typography variant="h5" sx={{ fontWeight: 700, color: '#1976d2' }}>
                    テンプレート管理のベストプラクティス
                  </Typography>
                </Box>
                
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <CategoryIcon sx={{ fontSize: 48, color: '#1976d2', mb: 1 }} />
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                        カテゴリ分類
                      </Typography>
                      <Typography variant="body2">
                        目的別にカテゴリを作成し、整理された状態を保つ
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <EditIcon sx={{ fontSize: 48, color: '#1565c0', mb: 1 }} />
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                        定期的な見直し
                      </Typography>
                      <Typography variant="body2">
                        月1回程度でテンプレートの効果を検証し、改善する
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <ContentCopyIcon sx={{ fontSize: 48, color: '#42a5f5', mb: 1 }} />
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                        チーム共有
                      </Typography>
                      <Typography variant="body2">
                        効果的なテンプレートをチーム内で共有し、ナレッジを蓄積
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>

              {/* サポート情報 */}
              <Paper elevation={3} sx={{ p: 3, borderRadius: 3, background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)', color: 'white' }}>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, textAlign: 'center' }}>
                  🚀 今すぐ始めましょう！
                </Typography>
                <Typography variant="body1" sx={{ textAlign: 'center', mb: 2 }}>
                  効果的なプロンプトテンプレートで、AI活用の生産性を最大化しましょう。
                  わからないことがあれば、いつでもこのガイドを参照してください。
                </Typography>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    💡 ヒント: このガイドは随時更新されます。定期的にチェックして最新情報をご確認ください。
                  </Typography>
                </Box>
              </Paper>
            </Box>
          </DialogContent>
          
          <DialogActions sx={{ p: 3, background: 'rgba(255,255,255,0.95)' }}>
            <Button
              onClick={() => setHelpDialogOpen(false)}
              variant="contained"
              size="large"
              sx={{
                borderRadius: 3,
                px: 4,
                background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #1565c0 0%, #0d47a1 100%)',
                },
              }}
            >
              理解しました
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Fade>
  );
};

export default TemplateManagementTab;
                                    