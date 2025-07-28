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
      </Box>
    </Fade>
  );
};

export default TemplateManagementTab;
                                    