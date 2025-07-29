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
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Alert,
  Stack,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Avatar,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import SearchIcon from '@mui/icons-material/Search';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import GroupIcon from '@mui/icons-material/Group';
import DashboardIcon from '@mui/icons-material/Dashboard';
import InsightsIcon from '@mui/icons-material/Insights';
import SecurityIcon from '@mui/icons-material/Security';
import TouchAppIcon from '@mui/icons-material/TouchApp';
import HistoryIcon from '@mui/icons-material/History';
import NotificationsIcon from '@mui/icons-material/Notifications';
import DescriptionIcon from '@mui/icons-material/Description';
import PostAddIcon from '@mui/icons-material/PostAdd';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import SpeedIcon from '@mui/icons-material/Speed';
import CategoryIcon from '@mui/icons-material/Category';
import FavoriteIcon from '@mui/icons-material/Favorite';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import IntegrationInstructionsIcon from '@mui/icons-material/IntegrationInstructions';
import PsychologyIcon from '@mui/icons-material/Psychology';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import WarningIcon from '@mui/icons-material/Warning';
import BuildIcon from '@mui/icons-material/Build';

const GuideBook = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [activeTab, setActiveTab] = useState('overview');

  const renderSection = (title: string, icon: React.ReactNode, children: React.ReactNode) => (
    <Paper 
      elevation={2} 
      sx={{ 
        p: { xs: 2, sm: 3, md: 4 }, 
        mb: 4,
        borderRadius: 4,
        border: `1px solid ${theme.palette.primary.light}`,
        boxShadow: '0 8px 32px rgba(37, 99, 235, 0.08)',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 12px 40px rgba(37, 99, 235, 0.12)'
        }
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, pb: 2, borderBottom: `2px solid ${theme.palette.primary.main}` }}>
        {icon}
        <Typography variant="h5" component="h2" sx={{ fontWeight: 700, color: 'primary.dark', ml: 1.5 }}>
          {title}
        </Typography>
      </Box>
      {children}
    </Paper>
  );

  const renderFeatureCard = (title: string, description: string, icon: React.ReactNode, isNew = false) => (
    <Grid item xs={12} sm={6} md={4}>
      <Card elevation={0} sx={{ 
        height: '100%', 
        borderRadius: 4,
        border: '1px solid rgba(37, 99, 235, 0.1)',
        bgcolor: 'rgba(37, 99, 235, 0.02)',
        p: 1,
        position: 'relative',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-5px)',
          boxShadow: '0 10px 30px rgba(37, 99, 235, 0.08)'
        }
      }}>
        {isNew && (
          <Chip 
            label="NEW" 
            size="small" 
            color="error" 
            sx={{ 
              position: 'absolute', 
              top: 8, 
              right: 8, 
              fontSize: '0.7rem',
              fontWeight: 700
            }} 
          />
        )}
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, color: 'primary.main' }}>
            {icon}
            <Typography variant="h6" fontWeight={600} sx={{ ml: 1.5 }}>{title}</Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">{description}</Typography>
        </CardContent>
      </Card>
    </Grid>
  );

  return (
    <Box sx={{ 
      minHeight: '100vh',
      backgroundColor: '#f8fafc',
    }}>
      {/* Header */}
      <AppBar 
        position="sticky" 
        elevation={1}
        sx={{ 
          background: 'white', 
          borderBottom: '1px solid rgba(0, 0, 0, 0.1)'
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between', p: { xs: '0.5rem 1rem', md: '0.5rem 2rem' } }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton edge="start" color="primary" sx={{ mr: 1 }} onClick={() => navigate(-1)}>
              <ArrowBackIcon fontSize="medium" />
            </IconButton>
            <img 
              src="/images/queue-logo.png" 
              alt="ワークメイトAI Logo" 
              style={{ height: 'auto', width: 'auto', maxHeight: 80, maxWidth: '100%', marginRight: 12 }}
            />
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main' }}>
              完全ガイドブック 2025
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
                ワークメイトAI
                <br />完全ガイドブック
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
                最新の拡張RAGシステム、プロンプトテンプレート、通知機能など、すべての機能を網羅した完全ガイドです。
                初心者から上級者まで、効率的にワークメイトAIを活用できます。
              </Typography>
              <Stack direction="row" spacing={2} flexWrap="wrap">
                <Button 
                  variant="contained" 
                  size="large"
                  onClick={() => navigate('/')}
                  startIcon={<RocketLaunchIcon />}
                  sx={{ 
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
                  今すぐ始める
                </Button>
                <Button 
                  variant="outlined" 
                  size="large"
                  onClick={() => setActiveTab('overview')}
                  startIcon={<HelpOutlineIcon />}
                  sx={{ 
                    px: 4,
                    py: 1.5,
                    borderRadius: 3,
                    fontWeight: 600,
                    fontSize: '1rem',
                    textTransform: 'none',
                  }}
                >
                  機能を見る
                </Button>
              </Stack>
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
      <Container maxWidth="lg" sx={{ py: { xs: 4, md: 6 } }}>
        {/* Tabs Section */}
        <Box sx={{ mb: 4, borderBottom: 1, borderColor: 'divider', bgcolor: 'white', borderRadius: 2, p: 1 }}>
          <Tabs
            value={activeTab}
            onChange={(event, newValue) => setActiveTab(newValue)}
            centered
            indicatorColor="primary"
            textColor="primary"
            variant={isMobile ? "scrollable" : "fullWidth"}
            scrollButtons="auto"
          >
            <Tab value="overview" label="システム概要" icon={<SmartToyIcon />} iconPosition="start" />
            <Tab value="users" label="全従業員向け" icon={<GroupIcon />} iconPosition="start" />
            <Tab value="admin" label="管理者向け" icon={<AdminPanelSettingsIcon />} iconPosition="start" />
            <Tab value="advanced" label="高度な機能" icon={<AutoAwesomeIcon />} iconPosition="start" />
          </Tabs>
        </Box>

        {/* システム概要タブ */}
        {activeTab === 'overview' && (
          <Box>
            {/* 最新機能ハイライト */}
            <Alert 
              severity="info" 
              icon={<AutoAwesomeIcon />}
              sx={{ mb: 4, borderRadius: 3, fontSize: '1rem' }}
            >
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                🎉 2025年最新アップデート
              </Typography>
              拡張RAGシステム、プロンプトテンプレート機能、リアルタイム通知システムが新たに追加されました！
            </Alert>

            {renderSection("ワークメイトAIとは", <SmartToyIcon color="primary" />, 
              <>
                <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.8, mb: 3 }}>
                  ワークメイトAIは、企業の知識を学習し、従業員の質問に自動回答する次世代AIアシスタントです。
                  最新の拡張RAG（Retrieval-Augmented Generation）技術により、複雑な質問も段階的に分析し、
                  より正確で詳細な回答を提供します。
                </Typography>
                <Grid container spacing={3}>
                  {renderFeatureCard(
                    "拡張RAGシステム", 
                    "複雑な質問を自動分析し、段階的に処理することで、より正確で包括的な回答を生成", 
                    <PsychologyIcon sx={{ fontSize: '2rem' }} />,
                    true
                  )}
                  {renderFeatureCard(
                    "プロンプトテンプレート", 
                    "よく使う質問パターンをテンプレート化し、ワンクリックで効率的な質問が可能", 
                    <PostAddIcon sx={{ fontSize: '2rem' }} />,
                    true
                  )}
                  {renderFeatureCard(
                    "リアルタイム通知", 
                    "重要な更新情報やシステムからのお知らせをリアルタイムで受信", 
                    <NotificationsIcon sx={{ fontSize: '2rem' }} />,
                    true
                  )}
                  {renderFeatureCard(
                    "多形式文書対応", 
                    "PDF、Excel、Word、PowerPointなど様々な形式の文書を自動処理", 
                    <CloudUploadIcon sx={{ fontSize: '2rem' }} />
                  )}
                  {renderFeatureCard(
                    "高度な分析機能", 
                    "利用状況の分析、感情分析、カテゴリ分析など豊富な分析機能", 
                    <AnalyticsIcon sx={{ fontSize: '2rem' }} />
                  )}
                  {renderFeatureCard(
                    "セキュアな権限管理", 
                    "4段階の権限システムで、適切な情報アクセス制御を実現", 
                    <SecurityIcon sx={{ fontSize: '2rem' }} />
                  )}
                </Grid>
              </>
            )}

            {renderSection("効果的な質問のコツ", <TipsAndUpdatesIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  ワークメイトAIからより良い回答を得るための質問テクニックをご紹介します。
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, borderRadius: 3, bgcolor: '#f8fbff' }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'primary.main' }}>
                        具体的な質問
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="5W1Hを意識する" secondary="いつ、どこで、誰が、何を、なぜ、どのように" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="背景情報を含める" secondary="状況や前提条件を明確に" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="期待する回答形式を指定" secondary="箇条書き、手順、表形式など" />
                        </ListItem>
                      </List>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, borderRadius: 3, bgcolor: '#f0f8ff' }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'primary.main' }}>
                        質問例
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="良い例" secondary="「新入社員向けの研修計画を3ヶ月分、週単位で教えて」" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="改善前" secondary="「研修について教えて」" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="プロンプトテンプレート活用" secondary="定型的な質問はテンプレートを使用" />
                        </ListItem>
                      </List>
                    </Paper>
                  </Grid>
                </Grid>
              </>
            )}
          </Box>
        )}

        {/* 全従業員向けタブ */}
        {activeTab === 'users' && (
          <Box>
            {renderSection("権限システム", <SecurityIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  ワークメイトAIでは、セキュリティと情報管理のため、4段階の権限が設定されています。
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{ height: '100%', borderRadius: 3, border: '2px solid #f44336' }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: '#f44336', mx: 'auto', mb: 2, width: 56, height: 56 }}>
                          <AdminPanelSettingsIcon sx={{ fontSize: '2rem' }} />
                        </Avatar>
                        <Typography variant="h6" sx={{ fontWeight: 700, color: '#f44336', mb: 1 }}>
                          運営者
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          システム全体の最高管理者。全機能へのアクセスが可能
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{ height: '100%', borderRadius: 3, border: '2px solid #ff9800' }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: '#ff9800', mx: 'auto', mb: 2, width: 56, height: 56 }}>
                          <AdminPanelSettingsIcon sx={{ fontSize: '2rem' }} />
                        </Avatar>
                        <Typography variant="h6" sx={{ fontWeight: 700, color: '#ff9800', mb: 1 }}>
                          社長
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          自社の管理者を追加・管理。会社のすべての情報にアクセス可能
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{ height: '100%', borderRadius: 3, border: '2px solid #2196f3' }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: '#2196f3', mx: 'auto', mb: 2, width: 56, height: 56 }}>
                          <AdminPanelSettingsIcon sx={{ fontSize: '2rem' }} />
                        </Avatar>
                        <Typography variant="h6" sx={{ fontWeight: 700, color: '#2196f3', mb: 1 }}>
                          管理者
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          管理画面にアクセス。資料のアップロードや従業員の招待が可能
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{ height: '100%', borderRadius: 3, border: '2px solid #4caf50' }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: '#4caf50', mx: 'auto', mb: 2, width: 56, height: 56 }}>
                          <GroupIcon sx={{ fontSize: '2rem' }} />
                        </Avatar>
                        <Typography variant="h6" sx={{ fontWeight: 700, color: '#4caf50', mb: 1 }}>
                          従業員
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          チャット機能を利用してAIに質問することができる
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </>
            )}

            {renderSection("基本的な使い方", <TouchAppIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  ワークメイトAIの基本的な操作方法を段階的に説明します。
                </Typography>
                <Stepper orientation="vertical">
                  <Step active={true}>
                    <StepLabel>
                      <Typography variant="h6" fontWeight={600}>ログイン</Typography>
                    </StepLabel>
                    <StepContent>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        管理者から送られた招待メールのリンクをクリックし、パスワードを設定してログインします。
                      </Typography>
                    </StepContent>
                  </Step>
                  <Step active={true}>
                    <StepLabel>
                      <Typography variant="h6" fontWeight={600}>チャット画面の確認</Typography>
                    </StepLabel>
                    <StepContent>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        画面中央にチャット履歴、下部に入力欄、右上にメニューボタンがあります。
                        新機能として、プロンプトテンプレートボタンと通知ボタンも追加されています。
                      </Typography>
                    </StepContent>
                  </Step>
                  <Step active={true}>
                    <StepLabel>
                      <Typography variant="h6" fontWeight={600}>質問の入力</Typography>
                    </StepLabel>
                    <StepContent>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        画面下部の入力欄に質問を入力し、送信ボタンを押します。
                        プロンプトテンプレートを使用すると、より効率的に質問できます。
                      </Typography>
                    </StepContent>
                  </Step>
                  <Step active={true}>
                    <StepLabel>
                      <Typography variant="h6" fontWeight={600}>回答の確認</Typography>
                    </StepLabel>
                    <StepContent>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        AIが拡張RAGシステムを使用して回答を生成します。
                        複雑な質問の場合、自動的に段階的に処理され、より詳細な回答が得られます。
                        回答の下には参照元の資料情報が表示されます。
                      </Typography>
                    </StepContent>
                  </Step>
                </Stepper>
              </>
            )}

            {renderSection("新機能：プロンプトテンプレート", <PostAddIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  よく使用する質問パターンをテンプレート化し、効率的に質問できる新機能です。
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, borderRadius: 3, bgcolor: '#e3f2fd' }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'primary.main' }}>
                        <PostAddIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                        使用方法
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="ヘッダーのテンプレートボタンをクリック" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="カテゴリから適切なテンプレートを選択" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="プレビューで内容を確認" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="「使用」ボタンで入力欄に挿入" />
                        </ListItem>
                      </List>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, borderRadius: 3, bgcolor: '#f3e5f5' }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'secondary.main' }}>
                        <CategoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                        利用可能なカテゴリ
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="ビジネス文書作成" secondary="メール、報告書など" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="データ分析依頼" secondary="統計、グラフ作成など" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="プロジェクト管理" secondary="計画、進捗管理など" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="技術サポート" secondary="トラブルシューティングなど" />
                        </ListItem>
                      </List>
                    </Paper>
                  </Grid>
                </Grid>
              </>
            )}

            {renderSection("新機能：通知システム", <NotificationsIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  重要な更新情報やシステムからのお知らせをリアルタイムで受信できます。
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%', borderRadius: 3 }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <NotificationsIcon sx={{ fontSize: '3rem', color: 'primary.main', mb: 2 }} />
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                          リアルタイム通知
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          新しい資料の追加、システム更新、重要なお知らせを即座に受信
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%', borderRadius: 3 }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <HistoryIcon sx={{ fontSize: '3rem', color: 'secondary.main', mb: 2 }} />
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                          通知履歴
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          過去の通知を確認し、重要な情報を見逃さない
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%', borderRadius: 3 }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <TipsAndUpdatesIcon sx={{ fontSize: '3rem', color: 'warning.main', mb: 2 }} />
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                          カスタム設定
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          通知の種類や頻度を個人の好みに合わせて設定可能
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </>
            )}
          </Box>
        )}

        {/* 管理者向けタブ */}
        {activeTab === 'admin' && (
          <Box>
            {renderSection("管理画面へのアクセス", <DashboardIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  管理者権限を持つユーザーは、専用の管理画面から様々な設定や管理業務を行うことができます。
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, borderRadius: 3, bgcolor: '#fff3e0' }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'warning.dark' }}>
                        <CloudUploadIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                        文書管理
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="PDF、Excel、Word、PowerPointのアップロード" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="文書の分類とタグ付け" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="文書の削除と更新" />
                        </ListItem>
                      </List>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, borderRadius: 3, bgcolor: '#e8f5e8' }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'success.dark' }}>
                        <GroupIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                        ユーザー管理
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="従業員の招待とアカウント作成" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="権限の設定と変更" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText primary="アカウントの無効化" />
                        </ListItem>
                      </List>
                    </Paper>
                  </Grid>
                </Grid>
              </>
            )}

            {renderSection("新機能：テンプレート管理", <PostAddIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  管理者は組織専用のプロンプトテンプレートを作成・管理できます。
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%', borderRadius: 3, border: '1px solid #e3f2fd' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <PostAddIcon sx={{ fontSize: '2rem', color: 'primary.main', mr: 1 }} />
                          <Typography variant="h6" fontWeight={600}>テンプレート作成</Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          業務に特化したテンプレートを作成し、従業員の作業効率を向上
                        </Typography>
                        <List dense>
                          <ListItem sx={{ px: 0 }}>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="カテゴリ別分類" />
                          </ListItem>
                          <ListItem sx={{ px: 0 }}>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="変数の設定" />
                          </ListItem>
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%', borderRadius: 3, border: '1px solid #f3e5f5' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <AnalyticsIcon sx={{ fontSize: '2rem', color: 'secondary.main', mr: 1 }} />
                          <Typography variant="h6" fontWeight={600}>使用状況分析</Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          テンプレートの利用状況を分析し、改善点を特定
                        </Typography>
                        <List dense>
                          <ListItem sx={{ px: 0 }}>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="利用頻度統計" />
                          </ListItem>
                          <ListItem sx={{ px: 0 }}>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="効果測定" />
                          </ListItem>
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%', borderRadius: 3, border: '1px solid #fff3e0' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <CategoryIcon sx={{ fontSize: '2rem', color: 'warning.main', mr: 1 }} />
                          <Typography variant="h6" fontWeight={600}>カテゴリ管理</Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          テンプレートを整理し、従業員が見つけやすくする
                        </Typography>
                        <List dense>
                          <ListItem sx={{ px: 0 }}>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="カスタムカテゴリ" />
                          </ListItem>
                          <ListItem sx={{ px: 0 }}>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="階層構造" />
                          </ListItem>
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </>
            )}

            {renderSection("システム分析とレポート", <InsightsIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  詳細な利用統計とパフォーマンス分析により、システムの効果を測定できます。
                </Typography>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6" fontWeight={600}>利用統計レポート</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 600 }}>基本統計</Typography>
                        <List dense>
                          <ListItem>
                            <ListItemText primary="総質問数" secondary="期間別の質問数推移" />
                          </ListItem>
                          <ListItem>
                            <ListItemText primary="アクティブユーザー数" secondary="日次・月次のユーザー活動" />
                          </ListItem>
                        </List>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 600 }}>詳細分析</Typography>
                        <List dense>
                          <ListItem>
                            <ListItemText primary="質問カテゴリ分析" secondary="どの分野の質問が多いか" />
                          </ListItem>
                          <ListItem>
                            <ListItemText primary="回答満足度" secondary="ユーザーフィードバック分析" />
                          </ListItem>
                        </List>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              </>
            )}
          </Box>
        )}

        {/* 高度な機能タブ */}
        {activeTab === 'advanced' && (
          <Box>
            {renderSection("拡張RAGシステムの詳細", <PsychologyIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  ワークメイトAIの最新機能である拡張RAGシステムは、複雑な質問を段階的に処理し、より正確で包括的な回答を提供します。
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Paper sx={{ p: 3, borderRadius: 3, bgcolor: '#f8f9ff' }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 3, color: 'primary.main' }}>
                        4段階処理プロセス
                      </Typography>
                      <Stepper orientation="vertical">
                        <Step active={true}>
                          <StepLabel>
                            <Typography variant="h6" fontWeight={600}>Step 1: 質問分析・分割</Typography>
                          </StepLabel>
                          <StepContent>
                            <Typography variant="body2" sx={{ mb: 2 }}>
                              複雑な質問を自動分析し、複数のサブタスクに分割。各サブタスクの優先度と複雑度を評価します。
                            </Typography>
                          </StepContent>
                        </Step>
                        <Step active={true}>
                          <StepLabel>
                            <Typography variant="h6" fontWeight={600}>Step 2: 個別検索・取得</Typography>
                          </StepLabel>
                          <StepContent>
                            <Typography variant="body2" sx={{ mb: 2 }}>
                              各サブタスクに対して独立したベクトル検索を実行し、関連する文書チャンクを取得します。
                            </Typography>
                          </StepContent>
                        </Step>
                        <Step active={true}>
                          <StepLabel>
                            <Typography variant="h6" fontWeight={600}>Step 3: サブ回答生成</Typography>
                          </StepLabel>
                          <StepContent>
                            <Typography variant="body2" sx={{ mb: 2 }}>
                              取得した情報を基に、各サブタスクに対する詳細な回答を生成します。
                            </Typography>
                          </StepContent>
                        </Step>
                        <Step active={true}>
                          <StepLabel>
                            <Typography variant="h6" fontWeight={600}>Step 4: 最終統合</Typography>
                          </StepLabel>
                          <StepContent>
                            <Typography variant="body2" sx={{ mb: 2 }}>
                              すべてのサブ回答を統合し、元の質問に対する包括的で一貫性のある最終回答を生成します。
                            </Typography>
                          </StepContent>
                        </Step>
                      </Stepper>
                    </Paper>
                  </Grid>
                </Grid>
              </>
            )}

            {renderSection("データ活用とレポート機能", <AnalyticsIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  ワークメイトAIの利用データを活用して、組織の知識活用状況を把握し、改善に役立てることができます。
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card sx={{ height: '100%', borderRadius: 3 }}>
                      <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'primary.main' }}>
                          利用状況分析
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          従業員の質問パターンや利用頻度を分析し、知識共有の効果を測定
                        </Typography>
                        <List dense>
                          <ListItem>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="質問カテゴリ分析" secondary="どの分野の質問が多いか" />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="時間帯別利用状況" secondary="ピーク時間の把握" />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="部署別利用率" secondary="組織全体の活用度" />
                          </ListItem>
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card sx={{ height: '100%', borderRadius: 3 }}>
                      <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'secondary.main' }}>
                          知識ギャップ分析
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          よく質問される内容から、組織に不足している知識を特定
                        </Typography>
                        <List dense>
                          <ListItem>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="未回答質問の分析" secondary="新しい資料が必要な分野" />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="満足度の低い回答" secondary="改善が必要な知識領域" />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                            <ListItemText primary="トレンド分析" secondary="新しい質問傾向の発見" />
                          </ListItem>
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </>
            )}

            {renderSection("トラブルシューティング", <BuildIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.8 }}>
                  よくある問題とその解決方法をまとめました。
                </Typography>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6" fontWeight={600}>ログインできない</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      <ListItem>
                        <ListItemIcon><WarningIcon color="warning" fontSize="small" /></ListItemIcon>
                        <ListItemText
                          primary="招待メールを確認"
                          secondary="管理者から送られた招待メールのリンクを使用してください"
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon><WarningIcon color="warning" fontSize="small" /></ListItemIcon>
                        <ListItemText
                          primary="パスワードリセット"
                          secondary="パスワードを忘れた場合は、ログイン画面からリセットできます"
                        />
                      </ListItem>
                    </List>
                  </AccordionDetails>
                </Accordion>
                
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6" fontWeight={600}>AIが適切に回答しない</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      <ListItem>
                        <ListItemIcon><TipsAndUpdatesIcon color="info" fontSize="small" /></ListItemIcon>
                        <ListItemText
                          primary="質問を具体的に"
                          secondary="より詳細で具体的な質問をすると、精度の高い回答が得られます"
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon><TipsAndUpdatesIcon color="info" fontSize="small" /></ListItemIcon>
                        <ListItemText
                          primary="プロンプトテンプレートを活用"
                          secondary="適切なテンプレートを使用することで、より良い結果が得られます"
                        />
                      </ListItem>
                    </List>
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6" fontWeight={600}>文書がアップロードできない</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      <ListItem>
                        <ListItemIcon><WarningIcon color="warning" fontSize="small" /></ListItemIcon>
                        <ListItemText
                          primary="ファイル形式を確認"
                          secondary="PDF、Excel、Word、PowerPointファイルのみサポートしています"
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon><WarningIcon color="warning" fontSize="small" /></ListItemIcon>
                        <ListItemText
                          primary="ファイルサイズ制限"
                          secondary="1ファイルあたり最大50MBまでアップロード可能です"
                        />
                      </ListItem>
                    </List>
                  </AccordionDetails>
                </Accordion>
              </>
            )}
          </Box>
        )}
      </Container>
    </Box>
  );
};

export default GuideBook;