import React, { useState } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Paper, 
  Grid, 
  Button, 
  Card, 
  CardContent, 
  CardMedia,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  useMediaQuery,
  useTheme,
  AppBar,
  Toolbar,
  IconButton,
  Tabs,
  Tab
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ArticleIcon from '@mui/icons-material/Article';
import SearchIcon from '@mui/icons-material/Search';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

const GuideBook = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const [activeTab, setActiveTab] = useState(0); // 0: 管理者向け, 1: ユーザー向け

  return (
    <Box sx={{ 
      minHeight: '100vh',
      backgroundColor: 'white',
      backgroundImage: 'radial-gradient(rgba(37, 99, 235, 0.02) 1px, transparent 0)',
      backgroundSize: '20px 20px',
    }}>
      {/* Header */}
      <AppBar 
        position="sticky" 
        elevation={0}
        sx={{ 
          background: 'white', 
          borderBottom: '1px solid rgba(37, 99, 235, 0.08)'
        }}
      >
        <Toolbar sx={{ 
          padding: { xs: '0.6rem 1rem', sm: '0.7rem 1.5rem', md: '0.8rem 2rem' }, 
          minHeight: { xs: '80px', sm: '90px', md: '120px' },
          display: 'flex',
          justifyContent: 'flex-start',
          alignItems: 'center'
        }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center',
            flexGrow: 0
          }}>
            <IconButton 
              edge="start" 
              color="primary" 
              sx={{ mr: { xs: 1, sm: 2 } }}
              onClick={() => navigate(-1)}
            >
              <ArrowBackIcon fontSize="large" />
            </IconButton>
            <img 
              src="/images/queue-logo.png" 
              alt="ワークメイトAI Logo" 
              style={{ 
                height: 'auto',
                width: 'auto',
                maxHeight: 110,
                maxWidth: '100%',
                marginRight: 16
              }}
            />
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                color: theme.palette.primary.main,
                background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                letterSpacing: '0.5px'
              }}
            >
              ガイドブック
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Hero Section */}
      <Box
        sx={{
          pt: { xs: 6, md: 10 },
          pb: { xs: 6, md: 8 },
          background: 'linear-gradient(180deg, rgba(37, 99, 235, 0.02) 0%, rgba(255, 255, 255, 0) 100%)',
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography 
                variant="h2" 
                component="h1" 
                sx={{ 
                  fontWeight: 800, 
                  mb: 2,
                  fontSize: { xs: '2.5rem', md: '3.5rem' },
                  background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                ワークメイトAI ガイドブック
              </Typography>
              <Typography 
                variant="h5" 
                sx={{ 
                  mb: 4, 
                  color: 'text.secondary',
                  fontWeight: 500,
                  lineHeight: 1.5,
                  fontSize: { xs: '1.1rem', md: '1.25rem' }
                }}
              >
                AIアシスタントを最大限に活用するためのガイドです。資料のアップロード、質問の仕方、得られる回答の理解など、基本的な使い方から高度なテクニックまで解説します。
              </Typography>
              <Button 
                variant="contained" 
                size="large"
                onClick={() => navigate('/')}
                sx={{ 
                  mr: 2, 
                  px: 4,
                  py: 1.5,
                  borderRadius: 3,
                  fontWeight: 600,
                  fontSize: '1rem',
                  textTransform: 'none',
                  boxShadow: '0 6px 18px rgba(37, 99, 235, 0.2)',
                  background: 'linear-gradient(to right, #2563eb, #3b82f6)',
                  '&:hover': {
                    boxShadow: '0 8px 25px rgba(37, 99, 235, 0.25)',
                    background: 'linear-gradient(to right, #1d4ed8, #2563eb)',
                    transform: 'translateY(-2px)'
                  },
                  transition: 'all 0.3s ease'
                }}
              >
                チャットボットを使ってみる
              </Button>
            </Grid>
            <Grid item xs={12} md={6} sx={{ display: 'flex', justifyContent: 'center' }}>
              <Box
                component="img"
                src="/images/queue-logo.png"
                alt="ワークメイトAI Illustration"
                sx={{
                  width: { xs: '70%', md: '80%' },
                  maxWidth: 500,
                  filter: 'drop-shadow(0 10px 20px rgba(37, 99, 235, 0.2))',
                }}
              />
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Main content */}
      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 10 } }}>
        {/* Feature Cards */}
        <Typography 
          variant="h4" 
          component="h2" 
          sx={{ 
            fontWeight: 700, 
            mb: 4, 
            textAlign: 'center',
            color: theme.palette.primary.main
          }}
        >
          主な機能
        </Typography>
        
        <Grid container spacing={3} sx={{ mb: 8 }}>
          <Grid item xs={12} sm={6} md={4}>
            <Card elevation={0} sx={{ 
              height: '100%', 
              borderRadius: 4,
              border: '1px solid rgba(37, 99, 235, 0.08)',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-5px)',
                boxShadow: '0 10px 30px rgba(37, 99, 235, 0.1)'
              }
            }}>
              <CardContent sx={{ p: 3 }}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    mb: 2,
                    color: theme.palette.primary.main
                  }}
                >
                  <CloudUploadIcon sx={{ fontSize: 28, mr: 1.5 }} />
                  <Typography variant="h6" fontWeight={600}>
                    リソース管理
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  管理者は管理画面のリソースタブで、PDFやWordなどの資料をアップロードできます。AIがその内容を理解し、質問に回答できるようになります。
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <Card elevation={0} sx={{ 
              height: '100%', 
              borderRadius: 4,
              border: '1px solid rgba(37, 99, 235, 0.08)',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-5px)',
                boxShadow: '0 10px 30px rgba(37, 99, 235, 0.1)'
              }
            }}>
              <CardContent sx={{ p: 3 }}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    mb: 2,
                    color: theme.palette.primary.main
                  }}
                >
                  <ChatBubbleOutlineIcon sx={{ fontSize: 28, mr: 1.5 }} />
                  <Typography variant="h6" fontWeight={600}>
                    AI会話
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  自然な対話形式でAIに質問できます。複雑な質問や追加の質問にも対応し、会話の流れを理解しながら回答します。
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <Card elevation={0} sx={{ 
              height: '100%',
              borderRadius: 4,
              border: '1px solid rgba(37, 99, 235, 0.08)',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-5px)',
                boxShadow: '0 10px 30px rgba(37, 99, 235, 0.1)'
              }
            }}>
              <CardContent sx={{ p: 3 }}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    mb: 2,
                    color: theme.palette.primary.main
                  }}
                >
                  <SearchIcon sx={{ fontSize: 28, mr: 1.5 }} />
                  <Typography variant="h6" fontWeight={600}>
                    詳細な分析
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  アップロードした資料の内容を詳細に分析し、重要なポイントをハイライトします。複雑な情報も分かりやすく整理して提示します。
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
        
        {/* Tabs Section */}
        <Box sx={{ mb: 6, borderBottom: 1, borderColor: 'divider' }}>
          <Container maxWidth="lg">
            <Tabs
              value={activeTab}
              onChange={(event, newValue) => setActiveTab(newValue)}
              centered
              sx={{
                '& .MuiTab-root': {
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '1.1rem',
                  minWidth: 160,
                  px: 4,
                  py: 2,
                },
                '& .Mui-selected': {
                  color: theme.palette.primary.main,
                },
                '& .MuiTabs-indicator': {
                  height: 3,
                  borderRadius: '2px 2px 0 0',
                },
              }}
            >
              <Tab label="管理者向け" />
              <Tab label="ユーザー向け" />
            </Tabs>
          </Container>
        </Box>

        {/* How to Use Section */}
        <Box sx={{ mb: 8 }}>
          <Typography 
            variant="h4" 
            component="h2" 
            sx={{ 
              fontWeight: 700, 
              mb: 4, 
              textAlign: 'center',
              color: theme.palette.primary.main
            }}
          >
            {activeTab === 0 ? '管理者向け' : 'ユーザー向け'}使い方ガイド
          </Typography>
          
{activeTab === 0 && (
            <Paper 
              elevation={0} 
              sx={{ 
                p: 4, 
                borderRadius: 4,
                border: '1px solid rgba(37, 99, 235, 0.08)',
                mb: 4
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box 
                  sx={{ 
                    width: 36, 
                    height: 36, 
                    borderRadius: '50%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    mr: 2,
                    bgcolor: theme.palette.primary.main,
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                >
                  1
                </Box>
                <Typography variant="h6" fontWeight={600}>
                  リソースのアップロード（管理者）
                </Typography>
              </Box>
              <Typography variant="body1" sx={{ mb: 2, ml: 7 }}>
                管理者は管理画面のリソースタブで、分析したい資料をアップロードします。PDFやWord、Excel、URLなど様々な形式に対応しています。
              </Typography>
              <List sx={{ ml: 7 }}>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="管理画面→リソースタブ→「新規アップロード」でファイルを追加" />
                </ListItem>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="Google DriveファイルやウェブページのURLも取り込み可能" />
                </ListItem>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="アップロードが完了すると、AIが自動的に内容を分析" />
                </ListItem>
              </List>
            </Paper>
          )}
          
{activeTab === 0 && (
            <Paper 
              elevation={0} 
              sx={{ 
                p: 4, 
                borderRadius: 4,
                border: '1px solid rgba(37, 99, 235, 0.08)',
                mb: 4
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box 
                  sx={{ 
                    width: 36, 
                    height: 36, 
                    borderRadius: '50%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    mr: 2,
                    bgcolor: theme.palette.primary.main,
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                >
                  2
                </Box>
                <Typography variant="h6" fontWeight={600}>
                  管理者設定の確認
                </Typography>
              </Box>
              <Typography variant="body1" sx={{ mb: 2, ml: 7 }}>
                アップロードしたリソースの管理者指令を設定し、AIの動作をカスタマイズします。
              </Typography>
              <List sx={{ ml: 7 }}>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="各リソースに対して「管理者指令」を設定" />
                </ListItem>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="機密情報の取り扱い方法を指定" />
                </ListItem>
              </List>
            </Paper>
          )}

          {activeTab === 1 && (
            <Paper 
              elevation={0} 
              sx={{ 
                p: 4, 
                borderRadius: 4,
                border: '1px solid rgba(37, 99, 235, 0.08)',
                mb: 4
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box 
                  sx={{ 
                    width: 36, 
                    height: 36, 
                    borderRadius: '50%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    mr: 2,
                    bgcolor: theme.palette.primary.main,
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                >
                  1
                </Box>
                <Typography variant="h6" fontWeight={600}>
                  質問をする
                </Typography>
              </Box>
              <Typography variant="body1" sx={{ mb: 2, ml: 7 }}>
                チャット画面で質問を入力します。資料の内容に関する質問や、要約、分析の依頼など、自然な言葉で問いかけてください。
              </Typography>
              <List sx={{ ml: 7 }}>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="質問は具体的に、明確に入力することでより正確な回答が得られます" />
                </ListItem>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="追加質問や詳細な説明を求めることも可能です" />
                </ListItem>
              </List>
            </Paper>
          )}
          
{activeTab === 0 && (
            <Paper 
              elevation={0} 
              sx={{ 
                p: 4, 
                borderRadius: 4,
                border: '1px solid rgba(37, 99, 235, 0.08)'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box 
                  sx={{ 
                    width: 36, 
                    height: 36, 
                    borderRadius: '50%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    mr: 2,
                    bgcolor: theme.palette.primary.main,
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                >
                  3
                </Box>
                <Typography variant="h6" fontWeight={600}>
                  運用とメンテナンス
                </Typography>
              </Box>
              <Typography variant="body1" sx={{ mb: 2, ml: 7 }}>
                システムの継続的な改善と効果的な運用のためのポイントを把握しましょう。
              </Typography>
              <List sx={{ ml: 7 }}>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="定期的なリソースの見直しと更新" />
                </ListItem>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="ユーザーのフィードバックに基づく改善" />
                </ListItem>
              </List>
            </Paper>
          )}

          {activeTab === 1 && (
            <Paper 
              elevation={0} 
              sx={{ 
                p: 4, 
                borderRadius: 4,
                border: '1px solid rgba(37, 99, 235, 0.08)'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box 
                  sx={{ 
                    width: 36, 
                    height: 36, 
                    borderRadius: '50%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    mr: 2,
                    bgcolor: theme.palette.primary.main,
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                >
                  2
                </Box>
                <Typography variant="h6" fontWeight={600}>
                  回答の活用
                </Typography>
              </Box>
              <Typography variant="body1" sx={{ mb: 2, ml: 7 }}>
                AIからの回答を確認し、必要に応じてさらに質問を続けることができます。回答内容はコピーしたり、引用元を確認したりすることも可能です。
              </Typography>
              <List sx={{ ml: 7 }}>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="回答の根拠となる資料の該当箇所を確認できます" />
                </ListItem>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="会話の履歴は保存され、後から確認することも可能です" />
                </ListItem>
              </List>
            </Paper>
          )}
        </Box>
        
{/* Admin Resource Management Section */}
        {activeTab === 0 && (
          <Box sx={{ mb: 8 }}>
            <Typography 
              variant="h4" 
              component="h2" 
              sx={{ 
                fontWeight: 700, 
                mb: 4, 
                textAlign: 'center',
                color: theme.palette.primary.main
              }}
            >
              管理者向け高度な機能
            </Typography>
          
          <Paper 
            elevation={0} 
            sx={{ 
              p: 4, 
              borderRadius: 4,
              border: '1px solid rgba(37, 99, 235, 0.08)',
              mb: 4
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Box 
                sx={{ 
                  width: 36, 
                  height: 36, 
                  borderRadius: '50%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  mr: 2,
                  bgcolor: '#ff6b35',
                  color: 'white',
                  fontWeight: 'bold'
                }}
              >
                ★
              </Box>
              <Typography variant="h6" fontWeight={600}>
                管理者指令機能
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ mb: 2 }}>
              リソース画面で各アップロードファイルに対して個別の「管理者指令」を設定できます。これにより、AIがそのリソースを参照する際に特別な指示を与えることができます。
            </Typography>
            <List>
              <ListItem sx={{ p: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <CheckCircleIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText primary="リソース一覧で「管理者指令」列の編集ボタンをクリック" />
              </ListItem>
              <ListItem sx={{ p: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <CheckCircleIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText primary="機密情報の取り扱い注意、要約方法の指定、特定の観点での分析指示など" />
              </ListItem>
              <ListItem sx={{ p: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <CheckCircleIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText primary="例：「この資料は機密情報なので、要約時に注意喚起を含めてください」" />
              </ListItem>
            </List>
          </Paper>

          <Paper 
            elevation={0} 
            sx={{ 
              p: 4, 
              borderRadius: 4,
              border: '1px solid rgba(37, 99, 235, 0.08)',
              mb: 4
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Box 
                sx={{ 
                  width: 36, 
                  height: 36, 
                  borderRadius: '50%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  mr: 2,
                  bgcolor: '#28a745',
                  color: 'white',
                  fontWeight: 'bold'
                }}
              >
                ⚙
              </Box>
              <Typography variant="h6" fontWeight={600}>
                リソース管理機能
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ mb: 2 }}>
              リソース画面では、アップロードした資料の詳細管理が可能です。効率的な知識ベース管理のために以下の機能をご活用ください。
            </Typography>
            <List>
              <ListItem sx={{ p: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <CheckCircleIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText primary="リソースの有効/無効切り替え - 一時的に特定の資料を無効化" />
              </ListItem>
              <ListItem sx={{ p: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <CheckCircleIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText primary="Google Drive連携 - Googleドライブから直接ファイルを取り込み" />
              </ListItem>
              <ListItem sx={{ p: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <CheckCircleIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText primary="URL取り込み - ウェブページの内容を自動分析・取り込み" />
              </ListItem>
              <ListItem sx={{ p: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <CheckCircleIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText primary="アップロード進捗表示 - リアルタイムでのファイル処理状況確認" />
              </ListItem>
            </List>
          </Paper>
          </Box>
        )}

        {/* New Features Section */}
        {activeTab === 0 && (
          <Box sx={{ mb: 8 }}>
            <Typography 
              variant="h4" 
              component="h2" 
              sx={{ 
                fontWeight: 700, 
                mb: 4, 
                textAlign: 'center',
                color: theme.palette.primary.main
              }}
            >
              最新の追加機能
            </Typography>
            
            <Paper 
              elevation={0} 
              sx={{ 
                p: 4, 
                borderRadius: 4,
                border: '1px solid rgba(37, 99, 235, 0.08)',
                mb: 4,
                background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.02) 0%, rgba(255, 255, 255, 0.8) 100%)'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box 
                  sx={{ 
                    width: 36, 
                    height: 36, 
                    borderRadius: '50%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    mr: 2,
                    bgcolor: '#6f42c1',
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                >
                  🆕
                </Box>
                <Typography variant="h6" fontWeight={600}>
                  分析機能の品質向上
                </Typography>
              </Box>
              <Typography variant="body1" sx={{ mb: 2 }}>
                分析画面の品質が大幅に向上しました。より詳細で正確な分析結果を提供し、視覚的にも分かりやすい表示を実現しています。
              </Typography>
              <List>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="より詳細な分析結果の表示" />
                </ListItem>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="視覚的に分かりやすいレポート形式" />
                </ListItem>
                <ListItem sx={{ p: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="分析精度の向上とエラー処理の強化" />
                </ListItem>
              </List>
            </Paper>
          </Box>
        )}

        {/* Tips Section */}
        <Box sx={{ mb: 8 }}>
          <Typography 
            variant="h4" 
            component="h2" 
            sx={{ 
              fontWeight: 700, 
              mb: 4, 
              textAlign: 'center',
              color: theme.palette.primary.main
            }}
          >
            活用のヒント
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={0} 
                sx={{ 
                  p: 3, 
                  height: '100%',
                  borderRadius: 4,
                  border: '1px solid rgba(37, 99, 235, 0.08)'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TipsAndUpdatesIcon color="primary" sx={{ mr: 1.5 }} />
                  <Typography variant="h6" fontWeight={600}>
                    効果的な質問方法
                  </Typography>
                </Box>
                <List>
                  <ListItem sx={{ px: 0 }}>
                    <ListItemText 
                      primary="具体的な質問をする" 
                      secondary="「この資料の概要は？」よりも「この資料における重要な3つのポイントは？」などと具体的に質問するとより良い回答が得られます。" 
                    />
                  </ListItem>
                  <ListItem sx={{ px: 0 }}>
                    <ListItemText 
                      primary="質問の範囲を明確にする" 
                      secondary="「この資料の第3章に関して...」など、質問の範囲を指定すると、より正確で焦点を絞った回答が得られます。" 
                    />
                  </ListItem>
                </List>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={0} 
                sx={{ 
                  p: 3, 
                  height: '100%',
                  borderRadius: 4,
                  border: '1px solid rgba(37, 99, 235, 0.08)'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <HelpOutlineIcon color="primary" sx={{ mr: 1.5 }} />
                  <Typography variant="h6" fontWeight={600}>
                    トラブルシューティング
                  </Typography>
                </Box>
                <List>
                  <ListItem sx={{ px: 0 }}>
                    <ListItemText 
                      primary="資料が正しく読み込まれない場合" 
                      secondary="PDF形式での再アップロードを試みてください。また、画像が多い資料の場合は処理に時間がかかることがあります。" 
                    />
                  </ListItem>
                  <ListItem sx={{ px: 0 }}>
                    <ListItemText 
                      primary="回答が不正確な場合" 
                      secondary="質問の表現を変えたり、より具体的な内容に絞って再度質問してみてください。AIの理解を助けることができます。" 
                    />
                  </ListItem>
                </List>
              </Paper>
            </Grid>
          </Grid>
        </Box>
        
        {/* FAQ Section */}
        <Box>
          <Typography 
            variant="h4" 
            component="h2" 
            sx={{ 
              fontWeight: 700, 
              mb: 4, 
              textAlign: 'center',
              color: theme.palette.primary.main
            }}
          >
            よくある質問
          </Typography>
          
          <Paper 
            elevation={0} 
            sx={{ 
              p: 4, 
              borderRadius: 4,
              border: '1px solid rgba(37, 99, 235, 0.08)'
            }}
          >
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
                Q: どのような形式のファイルをアップロードできますか？
              </Typography>
              <Typography variant="body1">
                A: 管理画面のリソースタブから、PDF、Word（.docx）、Excel（.xlsx）、PowerPoint（.pptx）、テキストファイル（.txt）、Google DriveファイルやウェブページのURLなどに対応しています。画像が含まれる資料も処理可能ですが、テキスト抽出の精度は画像の品質によって異なる場合があります。
              </Typography>
            </Box>
            
            <Divider sx={{ my: 3 }} />
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
                Q: チャット画面からファイルをアップロードできますか？
              </Typography>
              <Typography variant="body1">
                A: いいえ、ファイルのアップロード機能は管理者専用の機能として管理画面のリソースタブに集約されています。これにより、会社の情報を管理者が一元管理でき、セキュリティと品質を保つことができます。
              </Typography>
            </Box>
            
            <Divider sx={{ my: 3 }} />
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
                Q: アップロードした資料は安全に保管されますか？
              </Typography>
              <Typography variant="body1">
                A: はい、すべての資料は暗号化されて安全に保管されます。資料へのアクセスは許可されたユーザーのみに制限されており、プライバシーとセキュリティを最優先に考慮しています。
              </Typography>
            </Box>
            
            <Divider sx={{ my: 3 }} />
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
                Q: ユーザーの権限はどのように分かれていますか？
              </Typography>
              <Typography variant="body1">
                A: 4つの権限レベルがあります：<br/>
                • <strong>運営者</strong>：全体管理、会社管理<br/>
                • <strong>社長</strong>：会社内の全機能、管理者作成<br/>
                • <strong>管理者</strong>：管理画面アクセス、社員作成<br/>
                • <strong>社員</strong>：チャット機能のみ
              </Typography>
            </Box>
            
            <Divider sx={{ my: 3 }} />
            


            <Box>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
                Q: デモ版の制限を超えて利用するにはどうすればよいですか？
              </Typography>
              <Typography variant="body1">
                A: 本番版への移行をご検討ください。本番版では資料のアップロード回数や質問回数の制限がなく、追加機能もご利用いただけます。詳細については、管理者にお問い合わせください。
              </Typography>
            </Box>
          </Paper>
        </Box>


      </Container>
      
      {/* CTA Section */}
      <Box
        sx={{
          py: { xs: 8, md: 12 },
          background: 'linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, rgba(37, 99, 235, 0.03) 100%)',
        }}
      >
        <Container maxWidth="md">
          <Box
            sx={{
              textAlign: 'center',
              p: { xs: 4, md: 5 },
              borderRadius: 4,
              backgroundColor: 'white',
              boxShadow: '0 10px 40px rgba(37, 99, 235, 0.08)',
              border: '1px solid rgba(37, 99, 235, 0.08)',
            }}
          >
            <Typography
              variant="h4"
              component="h2"
              sx={{
                fontWeight: 700,
                mb: 2,
                color: theme.palette.primary.main
              }}
            >
              ワークメイトAIで業務効率化を
            </Typography>
            <Typography
              variant="body1"
              sx={{
                mb: 4,
                color: 'text.secondary',
                fontSize: '1.1rem'
              }}
            >
              ワークメイトAIで、快適な操作性と高速な回答を体験してください。
              AIによる資料の分析と理解で、業務効率を次のレベルへと導きます。
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/')}
              sx={{ 
                px: 5,
                py: 1.5,
                borderRadius: 3,
                fontWeight: 600,
                fontSize: '1.1rem',
                textTransform: 'none',
                boxShadow: '0 6px 18px rgba(37, 99, 235, 0.2)',
                background: 'linear-gradient(to right, #2563eb, #3b82f6)',
                '&:hover': {
                  boxShadow: '0 8px 25px rgba(37, 99, 235, 0.25)',
                  background: 'linear-gradient(to right, #1d4ed8, #2563eb)',
                  transform: 'translateY(-2px)'
                },
                transition: 'all 0.3s ease'
              }}
            >
              チャットボットを使ってみる
            </Button>
          </Box>
        </Container>
      </Box>
      
      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 4,
          borderTop: '1px solid rgba(37, 99, 235, 0.08)',
          backgroundColor: 'white'
        }}
      >
        <Container>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: { xs: 2, sm: 0 } }}
            >
              © 2025 ワークメイトAI. All rights reserved.
            </Typography>
            <Box
              sx={{
                display: 'flex',
                gap: 3
              }}
            >
              <Typography
                variant="body2"
                component="a"
                href="https://www.workmate-ai.com"
                target="_blank"
                sx={{
                  color: 'text.secondary',
                  textDecoration: 'none',
                  '&:hover': {
                    color: 'primary.main'
                  }
                }}
              >
                ホームページ
              </Typography>
              <Typography
                variant="body2"
                component="a"
                href="#"
                sx={{
                  color: 'text.secondary',
                  textDecoration: 'none',
                  '&:hover': {
                    color: 'primary.main'
                  }
                }}
              >
                お問い合わせ
              </Typography>
            </Box>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default GuideBook; 