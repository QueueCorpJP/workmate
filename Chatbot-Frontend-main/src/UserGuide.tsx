import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Divider,
  AppBar,
  Toolbar,
  IconButton,
  Avatar,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import SearchIcon from '@mui/icons-material/Search';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ChatIcon from '@mui/icons-material/Chat';
import InsightsIcon from '@mui/icons-material/Insights';
import SettingsIcon from '@mui/icons-material/Settings';
import InfoIcon from '@mui/icons-material/Info';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import FormatQuoteIcon from '@mui/icons-material/FormatQuote';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';

const UserGuide: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  const handleBackToChat = () => {
    navigate('/');
  };

  const featureCards = [
    {
      title: "簡単な質問回答",
      icon: <QuestionAnswerIcon sx={{ color: 'primary.main', fontSize: '2.5rem' }} />,
      description: "必要な情報を自然な対話形式で質問するだけで、会社のデータから最適な回答を提供します。",
      example: "「今月の営業目標について教えて」「休暇申請の手続きはどうすればいい？」"
    },
    {
      title: "管理画面でのリソース管理",
      icon: <CloudUploadIcon sx={{ color: 'primary.main', fontSize: '2.5rem' }} />,
      description: "管理者は管理画面のリソースタブで、Excel、PDF、Word、URLなどのファイルをアップロードして、AIがデータを分析・理解します。",
      example: "社内規定書、マニュアル、報告書、Google Driveファイルなど様々な文書に対応"
    },
    {
      title: "管理パネル",
      icon: <AdminPanelSettingsIcon sx={{ color: 'primary.main', fontSize: '2.5rem' }} />,
      description: "管理者（運営者・社長・管理者）は管理画面でチャット履歴の分析、ユーザー管理、リソース管理などの機能を使用できます。リソースタブでファイルアップロードも可能です。",
      example: "リソースタブでPDF/Excel/Word文書をアップロード、Google Driveファイルの追加、URL情報の取得、社員の利用状況確認"
    },
    {
      title: "情報ソースの確認",
      icon: <InfoIcon sx={{ color: 'primary.main', fontSize: '2.5rem' }} />,
      description: "AIが提供する情報のソースを確認でき、信頼性の高い回答を得られます。",
      example: "回答の下に表示されるソース情報をクリックして詳細を確認できます"
    }
  ];

  const steps = [
    {
      label: 'ログイン',
      description: 'メールアドレスとパスワードでログインします。新規ユーザーは管理者から招待を受けてください。権限は運営者→社長→管理者→社員の4段階です。',
    },
    {
      label: '質問入力',
      description: '画面下部の入力フィールドに質問を入力します。自然な言葉で質問できます。Viteによる高速レスポンスで快適に操作できます。',
    },
    {
      label: '回答の確認',
      description: 'AIが会社のデータベースから情報を検索し、最適な回答を提供します。情報源も表示され、信頼性の高い回答を得られます。',
    },
    {
      label: 'リソースのアップロード（管理者）',
      description: '管理者は管理画面のリソースタブで会社の資料やデータをアップロードできます。PDF、Excel、Word、Google Drive、URLに対応しています。',
    },
    {
      label: '分析と管理（管理者）',
      description: '管理パネルでチャット履歴の分析、よくある質問のパターン、ユーザー管理、リソース管理などが可能です。会社ごとの利用状況も確認できます。',
    },
  ];

  const tips = [
    "具体的に質問すると、より正確な回答が得られます",
    "複数の質問は分けて入力すると、それぞれに詳しく回答します",
    "情報ソースが表示されない場合は、AIが一般的な知識から回答しています",
    "特定の文書について質問する場合は、文書名を含めるとより正確です",
    "管理者は管理画面のリソースタブで定期的にデータを更新して、AIの知識を最新に保ちましょう",
    "権限は運営者→社長→管理者→社員の順で階層になっています",
    "このアプリはViteで構築されており、高速で効率的な動作を実現しています",
    "ファイルアップロードは管理者のみが管理画面から行えるセキュアな設計です"
  ];

  return (
    <Box 
      sx={{ 
        minHeight: '100vh', 
        display: 'flex', 
        flexDirection: 'column',
        backgroundColor: 'background.default',
        backgroundImage: 'linear-gradient(to bottom, rgba(37, 99, 235, 0.02), rgba(37, 99, 235, 0.001))',
      }}
    >
      {/* ヘッダー */}
      <AppBar 
        position="static" 
        color="inherit" 
        elevation={0} 
        sx={{ 
          borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
          backgroundColor: 'background.paper',
          backdropFilter: 'blur(10px)',
        }}
      >
        <Toolbar sx={{ minHeight: { xs: '56px', sm: '64px' }, px: { xs: 2, sm: 3 } }}>
          <IconButton
            edge="start"
            color="primary"
            onClick={handleBackToChat}
            sx={{ 
              mr: 1,
              backgroundColor: 'rgba(37, 99, 235, 0.08)',
              '&:hover': {
                backgroundColor: 'rgba(37, 99, 235, 0.15)',
              },
              transition: 'all 0.2s',
            }}
            aria-label="戻る"
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography 
            variant={isMobile ? 'subtitle1' : 'h6'} 
            component="div" 
            sx={{ 
              fontWeight: 600, 
              color: 'primary.main',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <HelpOutlineIcon sx={{ mr: 1, display: { xs: 'none', sm: 'inline' } }} />
            使い方ガイド
          </Typography>
        </Toolbar>
      </AppBar>

      {/* メインコンテンツ */}
      <Container 
        maxWidth="lg" 
        sx={{ 
          flexGrow: 1, 
          py: { xs: 3, sm: 4, md: 5 },
          px: { xs: 2, sm: 3, md: 4 }
        }}
      >
        {/* ヒーローセクション */}
        <Paper
          elevation={0}
          sx={{
            p: { xs: 3, sm: 4, md: 5 },
            mb: 4,
            borderRadius: 3,
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.08)',
            overflow: 'hidden',
            border: '1px solid rgba(37, 99, 235, 0.1)',
            background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
            position: 'relative',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '4px',
              background: 'linear-gradient(to right, #2563eb, #60a5fa)',
            },
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Avatar
            sx={{
              width: { xs: 60, sm: 80 },
              height: { xs: 60, sm: 80 },
              bgcolor: 'primary.main',
              mb: 2,
              boxShadow: '0 4px 20px rgba(37, 99, 235, 0.2)',
            }}
          >
            <ChatIcon sx={{ fontSize: { xs: '2rem', sm: '2.5rem' } }} />
          </Avatar>

          <Typography 
            variant={isMobile ? "h4" : "h3"} 
            component="h1"
            sx={{ 
              fontWeight: 700, 
              mb: 2,
              background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
              backgroundClip: 'text',
              textFillColor: 'transparent',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            ワークメイトAIの使い方
          </Typography>
          
          <Typography 
            variant="h6" 
            color="text.secondary" 
            sx={{ 
              maxWidth: '800px',
              mb: 3,
              lineHeight: 1.6,
              fontWeight: 400,
            }}
          >
            ワークメイトAIは、Viteで構築された高速なWebアプリケーションです。
            会社の情報を簡単に質問・検索できるAIアシスタントとして、
            自然な会話形式で質問するだけで、必要な情報を素早く見つけることができます。
          </Typography>
          
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              gap: 2,
              alignItems: 'center',
              mb: 2
            }}
          >
            <Button
              variant="contained"
              color="primary"
              size="large"
              onClick={handleBackToChat}
              sx={{
                borderRadius: 2,
                px: 4,
                py: 1.2,
                fontWeight: 600,
                boxShadow: '0 4px 14px rgba(37, 99, 235, 0.25)',
                background: 'linear-gradient(to right, #2563eb, #3b82f6)',
                '&:hover': {
                  boxShadow: '0 6px 20px rgba(37, 99, 235, 0.35)',
                  background: 'linear-gradient(to right, #1d4ed8, #2563eb)',
                },
              }}
            >
              チャットを始める
            </Button>
            
            <Typography
              variant="caption"
              sx={{
                color: 'text.secondary',
                fontStyle: 'italic',
                textAlign: 'center'
              }}
            >
              ⚡ Viteによる高速レスポンス対応
            </Typography>
          </Box>
        </Paper>

        {/* 主な機能セクション */}
        <Typography 
          variant="h4" 
          component="h2" 
          sx={{ 
            mb: 3, 
            fontWeight: 700,
            textAlign: 'center',
            position: 'relative',
            '&:after': {
              content: '""',
              position: 'absolute',
              bottom: -10,
              left: '50%',
              width: 60,
              height: 3,
              backgroundColor: 'primary.main',
              transform: 'translateX(-50%)',
              borderRadius: '10px'
            }
          }}
        >
          主な機能
        </Typography>

        <Grid container spacing={3} sx={{ mb: 6 }}>
          {featureCards.map((card, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card
                elevation={0}
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 3,
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.06)',
                  border: '1px solid rgba(37, 99, 235, 0.1)',
                  overflow: 'hidden',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-5px)',
                    boxShadow: '0 12px 30px rgba(37, 99, 235, 0.12)',
                  },
                }}
              >
                <Box
                  sx={{
                    p: 3,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    textAlign: 'center',
                  }}
                >
                  <Box 
                    sx={{ 
                      mb: 2,
                      p: 1.5,
                      borderRadius: '50%',
                      backgroundColor: 'rgba(37, 99, 235, 0.08)',
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                    }}
                  >
                    {card.icon}
                  </Box>
                  <Typography variant="h6" component="h3" sx={{ mb: 1, fontWeight: 600 }}>
                    {card.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2, flexGrow: 1 }}>
                    {card.description}
                  </Typography>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      backgroundColor: 'rgba(37, 99, 235, 0.04)',
                      width: '100%',
                      border: '1px dashed rgba(37, 99, 235, 0.2)',
                    }}
                  >
                    <Typography variant="caption" sx={{ display: 'block', fontStyle: 'italic', color: 'text.secondary' }}>
                      例:
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500, color: 'text.primary' }}>
                      {card.example}
                    </Typography>
                  </Box>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* 使い方ステップ */}
        <Paper
          elevation={0}
          sx={{
            p: { xs: 3, sm: 4 },
            mb: 4,
            borderRadius: 3,
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.05)',
            border: '1px solid rgba(37, 99, 235, 0.1)',
            background: 'white',
          }}
        >
          <Typography 
            variant="h4" 
            component="h2" 
            sx={{ 
              mb: 4, 
              fontWeight: 700,
              textAlign: 'center',
              position: 'relative',
              '&:after': {
                content: '""',
                position: 'absolute',
                bottom: -10,
                left: '50%',
                width: 60,
                height: 3,
                backgroundColor: 'primary.main',
                transform: 'translateX(-50%)',
                borderRadius: '10px'
              }
            }}
          >
            使い方ステップ
          </Typography>

          <Stepper 
            orientation="vertical" 
            sx={{ 
              ml: { xs: 0, md: 4 },
              '& .MuiStepConnector-line': {
                borderColor: 'rgba(37, 99, 235, 0.2)',
                borderLeftWidth: 2,
                minHeight: 20,
              },
              '& .MuiStepLabel-iconContainer': {
                bgcolor: 'primary.main',
                borderRadius: '50%',
                width: 36,
                height: 36,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                zIndex: 1,
                boxShadow: '0 2px 10px rgba(37, 99, 235, 0.2)',
              },
              '& .MuiStepIcon-root': {
                color: 'white',
                fontSize: '1.5rem',
              },
              '& .MuiStepLabel-label': {
                fontWeight: 600,
                mt: 0.5,
              },
              '& .MuiStepContent-root': {
                borderColor: 'rgba(37, 99, 235, 0.2)',
                borderLeftWidth: 2,
                ml: 2.25,
                pl: 2.75,
              }
            }}
          >
            {steps.map((step, index) => (
              <Step key={index} active={true}>
                <StepLabel>
                  {step.label}
                </StepLabel>
                <StepContent>
                  <Typography>{step.description}</Typography>
                  <Box sx={{ mb: 2, mt: 1 }} />
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </Paper>

        {/* ヒントセクション */}
        <Paper
          elevation={0}
          sx={{
            p: { xs: 3, sm: 4 },
            borderRadius: 3,
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.05)',
            border: '1px solid rgba(37, 99, 235, 0.1)',
            background: 'linear-gradient(to right, rgba(37, 99, 235, 0.03), rgba(37, 99, 235, 0.01))',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <LightbulbIcon sx={{ color: 'primary.main', mr: 1, fontSize: '2rem' }} />
            <Typography variant="h5" component="h2" sx={{ fontWeight: 700 }}>
              便利なヒント
            </Typography>
          </Box>

          <Grid container spacing={2}>
            {tips.map((tip, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Box
                  sx={{
                    display: 'flex',
                    p: 2,
                    borderRadius: 2,
                    backgroundColor: 'white',
                    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.03)',
                    border: '1px solid rgba(37, 99, 235, 0.08)',
                  }}
                >
                  <Box
                    sx={{
                      mr: 2,
                      minWidth: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      bgcolor: 'primary.main',
                      color: 'white',
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      fontWeight: 'bold',
                      fontSize: '0.8rem',
                      flexShrink: 0,
                    }}
                  >
                    {index + 1}
                  </Box>
                  <Typography variant="body1">{tip}</Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>

        {/* Vite技術情報セクション */}
        <Paper
          elevation={0}
          sx={{
            p: { xs: 3, sm: 4 },
            mb: 4,
            borderRadius: 3,
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.05)',
            border: '1px solid rgba(37, 99, 235, 0.1)',
            background: 'linear-gradient(to right, rgba(37, 99, 235, 0.03), rgba(37, 99, 235, 0.01))',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Box
              sx={{
                mr: 2,
                p: 1.5,
                borderRadius: '50%',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                ⚡
              </Typography>
            </Box>
            <Typography variant="h5" component="h2" sx={{ fontWeight: 700 }}>
              Vite技術による高速化
            </Typography>
          </Box>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box sx={{ p: 2, borderRadius: 2, backgroundColor: 'white', border: '1px solid rgba(37, 99, 235, 0.08)' }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                  🚀 高速な開発サーバー
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  ESModulesを活用したネイティブESMによる高速な起動とホットリロード機能で、開発効率が大幅に向上しています。
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ p: 2, borderRadius: 2, backgroundColor: 'white', border: '1px solid rgba(37, 99, 235, 0.08)' }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                  📦 最適化されたビルド
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Rollupベースの本番ビルドにより、最小限のバンドルサイズと最適なパフォーマンスを実現しています。
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ p: 2, borderRadius: 2, backgroundColor: 'white', border: '1px solid rgba(37, 99, 235, 0.08)' }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                  🔧 TypeScript統合
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  TypeScriptのネイティブサポートにより、型安全性を保ちながら高速なトランスパイルを実現しています。
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ p: 2, borderRadius: 2, backgroundColor: 'white', border: '1px solid rgba(37, 99, 235, 0.08)' }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                  🎯 モダンブラウザ対応
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  最新のWeb標準に準拠し、モダンブラウザでの最適なパフォーマンスを提供しています。
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </Container>

      {/* フッター */}
      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: 'auto',
          textAlign: 'center',
          borderTop: '1px solid rgba(0, 0, 0, 0.05)',
          bgcolor: 'background.paper',
        }}
      >
        <Typography variant="body2" color="text.secondary">
          さらに詳しいサポートが必要な場合は、管理者にお問い合わせください。
        </Typography>
      </Box>
    </Box>
  );
};

export default UserGuide; 