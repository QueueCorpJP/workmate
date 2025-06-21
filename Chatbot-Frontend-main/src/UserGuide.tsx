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
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
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
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PersonIcon from '@mui/icons-material/Person';
import GroupIcon from '@mui/icons-material/Group';
import BusinessIcon from '@mui/icons-material/Business';
import SupervisorAccountIcon from '@mui/icons-material/SupervisorAccount';

const UserGuide: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleBackToChat = () => {
    navigate('/');
  };

  const userRoles = [
    {
      title: "運営者",
      icon: <SupervisorAccountIcon sx={{ color: '#d32f2f' }} />,
      description: "システム全体の管理、全ての機能へのアクセス権限",
      permissions: ["全社データの閲覧", "全ユーザーの管理", "システム設定の変更", "全リソースの管理"]
    },
    {
      title: "社長",
      icon: <BusinessIcon sx={{ color: '#ed6c02' }} />,
      description: "会社全体のデータ管理、重要な意思決定に関わる機能",
      permissions: ["会社データの閲覧", "部門間の分析", "重要文書の管理", "社員の利用状況確認"]
    },
    {
      title: "管理者",
      icon: <GroupIcon sx={{ color: '#2e7d32' }} />,
      description: "部門内のデータ管理、チームメンバーの管理",
      permissions: ["部門データの管理", "チームメンバーの招待", "リソースのアップロード", "チャット履歴の分析"]
    },
    {
      title: "社員",
      icon: <PersonIcon sx={{ color: '#1976d2' }} />,
      description: "日常業務での質問、情報検索",
      permissions: ["チャット機能の利用", "会社情報の検索", "業務に関する質問", "承認された文書の閲覧"]
    }
  ];

  const mainFeatures = [
    {
      title: "AIチャット機能",
      icon: <ChatIcon sx={{ color: '#1976d2', fontSize: '2rem' }} />,
      description: "会社の情報を自然な対話で質問できます",
      details: [
        "業務に関する質問を普通の会話のように入力",
        "社内規定、マニュアル、報告書から自動で回答を生成",
        "24時間いつでも利用可能",
        "質問回数の制限あり（プランにより異なる）"
      ]
    },
    {
      title: "文書管理システム",
      icon: <CloudUploadIcon sx={{ color: '#2e7d32', fontSize: '2rem' }} />,
      description: "様々な形式の文書をAIが理解できる形で保存",
      details: [
        "PDF、Excel、Word、PowerPointファイルに対応",
        "Google Driveとの連携",
        "ウェブページの情報取得",
        "文書の有効/無効の切り替え"
      ]
    },
    {
      title: "管理画面",
      icon: <AdminPanelSettingsIcon sx={{ color: '#ed6c02', fontSize: '2rem' }} />,
      description: "チーム管理と分析機能",
      details: [
        "チャット履歴の確認と分析",
        "よくある質問の把握",
        "社員の利用状況確認",
        "新しいメンバーの招待"
      ]
    },
    {
      title: "情報ソース表示",
      icon: <InfoIcon sx={{ color: '#7b1fa2', fontSize: '2rem' }} />,
      description: "回答の根拠となった文書を明示",
      details: [
        "どの文書から情報を取得したかを表示",
        "ページ番号や章の情報も含む",
        "回答の信頼性を確認可能",
        "元文書へのリンク機能"
      ]
    }
  ];

  const usageSteps = [
    {
      title: "ログインする",
      description: "管理者から送られた招待メールのリンクをクリックし、パスワードを設定してログインします。"
    },
    {
      title: "質問を入力する",
      description: "画面下部の入力欄に、知りたいことを自然な言葉で入力します。例：「有給休暇の申請方法を教えて」"
    },
    {
      title: "回答を確認する",
      description: "AIが会社の文書から関連情報を見つけて回答します。情報源も一緒に表示されます。"
    },
    {
      title: "詳細情報を確認する",
      description: "回答の下に表示される情報源をクリックすると、元の文書や詳細情報を確認できます。"
    }
  ];

  const commonQuestions = [
    {
      question: "どんな質問ができますか？",
      answer: "社内規定、業務手順、製品情報、会社の歴史、組織図など、アップロードされた文書に関することなら何でも質問できます。"
    },
    {
      question: "質問回数に制限はありますか？",
      answer: "はい。プランによって1日あたりの質問回数が決まっています。制限に達した場合は翌日まで待つか、管理者にプラン変更を相談してください。"
    },
    {
      question: "回答が間違っている場合はどうすればいいですか？",
      answer: "情報源を確認し、元の文書に問題がないか確認してください。文書が古い場合は管理者に更新を依頼してください。"
    },
    {
      question: "管理者になるにはどうすればいいですか？",
      answer: "上位の権限を持つユーザー（社長や運営者）に権限変更を依頼してください。権限は運営者→社長→管理者→社員の順になっています。"
    },
    {
      question: "スマートフォンでも使えますか？",
      answer: "はい。スマートフォンやタブレットでも快適に利用できるよう設計されています。"
    }
  ];

  const tips = [
    "具体的で明確な質問をすると、より正確な回答が得られます",
    "複数の質問がある場合は、一つずつ分けて質問してください",
    "文書名や部署名を含めると、より関連性の高い情報が見つかります",
    "定期的に新しい文書をアップロードして、情報を最新に保ちましょう",
    "チャット履歴は管理者が分析して、よくある質問をFAQとして整理できます"
  ];

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      {/* ヘッダー */}
      <AppBar position="static" color="inherit" elevation={0} sx={{ borderBottom: '1px solid rgba(0, 0, 0, 0.08)' }}>
        <Toolbar>
          <IconButton edge="start" color="primary" onClick={handleBackToChat} sx={{ mr: 2 }}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ fontWeight: 600, color: 'primary.main' }}>
            <HelpOutlineIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            ワークメイトAI 使用書
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* 概要セクション */}
        <Paper elevation={0} sx={{ p: 4, mb: 4, borderRadius: 2, border: '1px solid rgba(37, 99, 235, 0.1)' }}>
          <Box textAlign="center" mb={3}>
            <Avatar sx={{ width: 80, height: 80, mx: 'auto', mb: 2, bgcolor: 'primary.main' }}>
              <ChatIcon sx={{ fontSize: '2.5rem' }} />
            </Avatar>
            <Typography variant="h4" gutterBottom fontWeight="bold" color="primary.main">
              ワークメイトAI
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
              社内の情報を瞬時に検索・回答する次世代AIアシスタント
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ textAlign: 'center', maxWidth: 800, mx: 'auto', lineHeight: 1.8 }}>
            ワークメイトAIは、あなたの会社の文書や情報をAIが学習し、社員の質問に自動で回答するシステムです。
            社内規定、マニュアル、報告書などの情報を自然な対話で検索でき、業務効率を大幅に向上させます。
          </Typography>
        </Paper>

        {/* ユーザー権限について */}
        <Paper elevation={0} sx={{ p: 4, mb: 4, borderRadius: 2 }}>
          <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <GroupIcon sx={{ mr: 1, color: 'primary.main' }} />
            ユーザー権限について
          </Typography>
          <Grid container spacing={3}>
            {userRoles.map((role, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Card sx={{ height: '100%', border: '1px solid rgba(0, 0, 0, 0.08)' }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      {role.icon}
                      <Typography variant="h6" fontWeight="bold" sx={{ ml: 1 }}>
                        {role.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" mb={2}>
                      {role.description}
                    </Typography>
                    <List dense>
                      {role.permissions.map((permission, idx) => (
                        <ListItem key={idx} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 30 }}>
                            <CheckCircleIcon sx={{ fontSize: '1rem', color: 'success.main' }} />
                          </ListItemIcon>
                          <ListItemText primary={permission} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>

        {/* 主要機能 */}
        <Paper elevation={0} sx={{ p: 4, mb: 4, borderRadius: 2 }}>
          <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <SettingsIcon sx={{ mr: 1, color: 'primary.main' }} />
            主要機能
          </Typography>
          <Grid container spacing={3}>
            {mainFeatures.map((feature, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Card sx={{ height: '100%', border: '1px solid rgba(0, 0, 0, 0.08)' }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      {feature.icon}
                      <Typography variant="h6" fontWeight="bold" sx={{ ml: 1 }}>
                        {feature.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" mb={2}>
                      {feature.description}
                    </Typography>
                    <List dense>
                      {feature.details.map((detail, idx) => (
                        <ListItem key={idx} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 30 }}>
                            <CheckCircleIcon sx={{ fontSize: '1rem', color: 'primary.main' }} />
                          </ListItemIcon>
                          <ListItemText primary={detail} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>

        {/* 使い方の手順 */}
        <Paper elevation={0} sx={{ p: 4, mb: 4, borderRadius: 2 }}>
          <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <SearchIcon sx={{ mr: 1, color: 'primary.main' }} />
            基本的な使い方
          </Typography>
          <Stepper orientation="vertical">
            {usageSteps.map((step, index) => (
              <Step key={index} active={true}>
                <StepLabel>
                  <Typography variant="h6" fontWeight="bold">
                    {step.title}
                  </Typography>
                </StepLabel>
                <StepContent>
                  <Typography variant="body1" sx={{ pb: 2 }}>
                    {step.description}
                  </Typography>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </Paper>

        {/* よくある質問 */}
        <Paper elevation={0} sx={{ p: 4, mb: 4, borderRadius: 2 }}>
          <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <QuestionAnswerIcon sx={{ mr: 1, color: 'primary.main' }} />
            よくある質問
          </Typography>
          {commonQuestions.map((faq, index) => (
            <Accordion key={index} sx={{ mb: 1, '&:before': { display: 'none' } }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {faq.question}
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                  {faq.answer}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </Paper>

        {/* 使用のコツ */}
        <Paper elevation={0} sx={{ p: 4, mb: 4, borderRadius: 2 }}>
          <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <LightbulbIcon sx={{ mr: 1, color: 'primary.main' }} />
            効果的な使用のコツ
          </Typography>
          <List>
            {tips.map((tip, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <CheckCircleIcon sx={{ color: 'success.main' }} />
                </ListItemIcon>
                <ListItemText primary={tip} />
              </ListItem>
            ))}
          </List>
        </Paper>

        {/* 管理者向け情報 */}
        <Paper elevation={0} sx={{ p: 4, mb: 4, borderRadius: 2, bgcolor: 'primary.50' }}>
          <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <AdminPanelSettingsIcon sx={{ mr: 1, color: 'primary.main' }} />
            管理者の方へ
          </Typography>
          <Typography variant="body1" sx={{ mb: 3, lineHeight: 1.8 }}>
            管理者権限をお持ちの方は、管理画面から以下の操作が可能です：
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon sx={{ color: 'primary.main' }} />
              </ListItemIcon>
              <ListItemText 
                primary="文書のアップロード" 
                secondary="PDF、Excel、Word、PowerPointファイルをアップロードして、AIに学習させることができます" 
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon sx={{ color: 'primary.main' }} />
              </ListItemIcon>
              <ListItemText 
                primary="Google Drive連携" 
                secondary="Google Driveのファイルを直接取り込んで、常に最新の情報を維持できます" 
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon sx={{ color: 'primary.main' }} />
              </ListItemIcon>
              <ListItemText 
                primary="チャット履歴の分析" 
                secondary="社員の質問傾向を分析し、よくある質問をFAQとして整理できます" 
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon sx={{ color: 'primary.main' }} />
              </ListItemIcon>
              <ListItemText 
                primary="ユーザー管理" 
                secondary="新しいメンバーの招待、権限の変更、利用状況の確認ができます" 
              />
            </ListItem>
          </List>
        </Paper>

        {/* フッター */}
        <Box textAlign="center" sx={{ mt: 4, py: 3, borderTop: '1px solid rgba(0, 0, 0, 0.08)' }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleBackToChat}
            sx={{ 
              borderRadius: 3,
              px: 4,
              py: 1.5,
              fontWeight: 'bold',
              boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)'
            }}
          >
            チャットを開始する
          </Button>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            ご不明な点がございましたら、管理者にお問い合わせください
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default UserGuide; 