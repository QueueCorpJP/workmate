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
import PaymentIcon from '@mui/icons-material/Payment';
import SecurityIcon from '@mui/icons-material/Security';
import TouchAppIcon from '@mui/icons-material/TouchApp';
import HistoryIcon from '@mui/icons-material/History';

const GuideBook = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('forAll'); // 'forAll', 'forAdmin'

  const renderSection = (title, icon, children) => (
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

  const renderFeatureCard = (title, description, icon) => (
    <Grid item xs={12} sm={6} md={4}>
      <Card elevation={0} sx={{ 
        height: '100%', 
        borderRadius: 4,
        border: '1px solid rgba(37, 99, 235, 0.1)',
        bgcolor: 'rgba(37, 99, 235, 0.02)',
        p: 1,
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-5px)',
          boxShadow: '0 10px 30px rgba(37, 99, 235, 0.08)'
        }
      }}>
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
      <Container maxWidth="lg" sx={{ py: { xs: 4, md: 6 } }}>
        {/* Tabs Section */}
        <Box sx={{ mb: 4, borderBottom: 1, borderColor: 'divider', bgcolor: 'white', borderRadius: 2, p: 1 }}>
            <Tabs
              value={activeTab}
              onChange={(event, newValue) => setActiveTab(newValue)}
              centered
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab value="forAll" label="全従業員向け" icon={<GroupIcon />} iconPosition="start" />
            <Tab value="forAdmin" label="管理者向け" icon={<AdminPanelSettingsIcon />} iconPosition="start" />
            </Tabs>
        </Box>

        {/* Content based on tab */}
        {activeTab === 'forAll' && (
          <Box>
            {renderSection("はじめに", <TipsAndUpdatesIcon color="primary" />, 
              <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.8 }}>
                ワークメイトAIは、社内に蓄積されたナレッジ（ドキュメント、規定、マニュアルなど）を学習し、従業員からの質問にチャット形式で自動回答するAIアシスタントです。
                このガイドでは、ワークメイトAIを効果的に活用し、日々の業務効率を向上させるための基本的な操作方法や便利な機能について解説します。
              </Typography>
            )}

            {renderSection("権限について", <SecurityIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2, lineHeight: 1.8 }}>
                  ワークメイトAIでは、セキュリティと情報管理のため、4段階の権限が設定されています。自身の権限で何ができるかを把握しておきましょう。
                </Typography>
                <List>
                  <ListItem>
                    <ListItemIcon><AdminPanelSettingsIcon color="error" /></ListItemIcon>
                    <ListItemText primary="運営者" secondary="システム全体の最高管理者。会社の追加や管理、全機能へのアクセスが可能です。" />
                </ListItem>
                  <ListItem>
                    <ListItemIcon><AdminPanelSettingsIcon color="warning" /></ListItemIcon>
                    <ListItemText primary="社長" secondary="自社の管理者を追加・管理できます。会社のすべての情報にアクセス可能です。" />
                </ListItem>
                  <ListItem>
                    <ListItemIcon><AdminPanelSettingsIcon color="primary" /></ListItemIcon>
                    <ListItemText primary="管理者" secondary="管理画面にアクセスし、資料のアップロードや従業員の招待、利用状況の分析ができます。" />
                </ListItem>
                  <ListItem>
                    <ListItemIcon><GroupIcon color="action" /></ListItemIcon>
                    <ListItemText primary="従業員" secondary="チャット機能を利用して、AIに質問することができます。" />
                </ListItem>
              </List>
              </>
          )}
          
            {renderSection("基本操作：チャット画面", <TouchAppIcon color="primary" />,
              <Box>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  全ての従業員の基本となるのが、このチャット画面です。各機能の配置は以下の通りです。
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2, borderColor: 'primary.light' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>画面中央：チャット履歴</Typography>
                  <Typography variant="body2" color="text.secondary">AIとの会話が時系列で表示されます。過去のやり取りをスクロールして確認できます。AIの回答の下には、根拠となった資料名やページ番号が「引用元」として表示されます。クリックすると情報の正確性を確認できます。</Typography>
            </Paper>
                <Paper variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2, borderColor: 'primary.light' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>画面下部：メッセージ入力欄</Typography>
                  <Typography variant="body2" color="text.secondary">質問を入力し、右側の送信ボタン（紙飛行機アイコン）を押してAIに質問を送信します。</Typography>
            </Paper>
                <Paper variant="outlined" sx={{ p: 2, borderRadius: 2, borderColor: 'primary.light' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>画面右上：メニューボタン（三点リーダー）</Typography>
                  <Typography variant="body2" color="text.secondary">クリックするとメニューが開き、「チャット履歴のクリア」「使い方ガイド」「設定」「ログアウト」が選択できます。管理者権限を持つ従業員には、ここに「管理画面」へのリンクが表示されます。</Typography>
          </Paper>
          </Box>
        )}

            {renderSection("効果的な質問のコツ", <SearchIcon color="primary" />,
              <List>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" /></ListItemIcon>
                  <ListItemText primary="具体的かつ明確に" secondary="「福利厚生」のような曖昧な質問より、「住宅手当の申請方法について教えて」のように具体的に質問すると、精度の高い回答が得られます。" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" /></ListItemIcon>
                  <ListItemText primary="一度に一つの質問" secondary="複数の質問を一度に投げかけると、AIが混乱する可能性があります。一つずつ順番に質問しましょう。" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircleIcon color="success" /></ListItemIcon>
                  <ListItemText primary="背景情報を加える" secondary="「新入社員向けの研修資料を要約して」のように、誰が・何のために情報を必要としているかの背景を伝えると、より適切な回答を生成しやすくなります。" />
                </ListItem>
              </List>
            )}

            {renderSection("よくある質問", <HelpOutlineIcon color="primary" />,
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography fontWeight="bold">AIの回答が期待と違う場合は？</Typography></AccordionSummary>
                <AccordionDetails>
                  <Typography>
                    質問の仕方を少し変えてみてください。より具体的なキーワードを入れたり、違う角度から質問したりすると、的確な回答が得られることがあります。また、AIは学習データに基づいて回答するため、情報が古い・不足している可能性も考えられます。その場合は管理者に資料の更新を依頼してください。
                  </Typography>
                </AccordionDetails>
              </Accordion>
            )}
          </Box>
        )}

        {activeTab === 'forAdmin' && (
        <Box>
            {renderSection("管理画面の歩き方", <AdminPanelSettingsIcon color="primary" />,
              <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.8, mb: 2 }}>
                管理者権限を持つ従業員は、チャット画面右上のメニューから「管理画面」にアクセスできます。管理画面は、画面上部に並んだタブで各機能ページに切り替えて使用します。各タブの機能は以下の通りです。
              </Typography>
            )}

            {renderSection("タブ別機能解説：チャット履歴", <HistoryIcon color="primary" />,
              <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.8 }}>
                このタブ（上部メニュー左から1番目）では、自社内の従業員とAIの全ての対話履歴を時系列で確認できます。誰が、いつ、どのような質問をしたか、そしてAIがどう回答したかを閲覧できるため、従業員の利用状況の把握や問題発生時の原因調査に役立ちます。
              </Typography>
            )}

            {renderSection("タブ別機能解説：分析", <InsightsIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2, lineHeight: 1.8 }}>
                  このタブ（上部メニュー左から2番目）では、従業員の利用動向を様々な角度から可視化し、分析できます。
              </Typography>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography fontWeight="bold">カテゴリ・感情分析</Typography></AccordionSummary>
                  <AccordionDetails>
                    <Typography>全チャット履歴をAIが自動で分析し、「質問カテゴリの分布」「ポジティブ/ネガティブな感情の割合」などをグラフで表示します。従業員が何に興味を持ち、何に不満を感じているかの傾向を掴むのに役立ちます。</Typography>
                  </AccordionDetails>
                </Accordion>
                 <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography fontWeight="bold">AIによる洞察（強化分析）</Typography></AccordionSummary>
                  <AccordionDetails>
                    <Typography>「AI洞察を生成」ボタンをクリックすると、蓄積されたデータからAIがより一歩踏み込んだ分析レポートを自動生成します。「よくある質問トップ5」から見えてくる課題や、社内ナレッジの改善提案など、具体的なアクションに繋がるインサイトを得られます。</Typography>
                  </AccordionDetails>
                </Accordion>
              </>
            )}

            {renderSection("タブ別機能解説：社員管理", <GroupIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2, lineHeight: 1.8 }}>
                  会社のメンバーを招待し、利用状況を確認します。このタブは管理画面の**上部メニュー、左から3番目**にあります。
              </Typography>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography fontWeight="bold">新しい従業員を追加・招待する方法</Typography></AccordionSummary>
                  <AccordionDetails>
                    <List component="ol" sx={{ listStyleType: 'decimal', pl: 4 }}>
                      <ListItem sx={{ display: 'list-item' }}>
                        <ListItemText primary="「社員を招待」ボタンをクリック" secondary="「社員管理」タブの画面右上に配置されている青色のボタンです。" />
                      </ListItem>
                      <ListItem sx={{ display: 'list-item' }}>
                        <ListItemText primary="ポップアップ画面で情報を入力" secondary="画面中央に表示されるウィンドウで、招待したい従業員の「メールアドレス」と「初期パスワード」を入力します。" />
                      </ListItem>
                      <ListItem sx={{ display: 'list-item' }}>
                        <ListItemText primary="招待を実行" secondary="「作成」ボタンを押すと、アカウントが作成され、従業員一覧に追加されます。ログイン情報を本人に伝えてください。" />
                      </ListItem>
                    </List>
                  </AccordionDetails>
                </Accordion>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography fontWeight="bold">従業員の利用状況確認・削除</Typography></AccordionSummary>
                  <AccordionDetails>
                    <Typography>従業員一覧では、各メンバーの最終ログイン日時や質問数を確認できます。また、各行の右端にあるゴミ箱アイコンをクリックすることで、従業員のアカウントを削除できます。</Typography>
                  </AccordionDetails>
                </Accordion>
              </>
            )}
            
            {renderSection("タブ別機能解説：リソース", <CloudUploadIcon color="primary" />,
              <>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2, lineHeight: 1.8 }}>
                  AIの知識源となる資料（リソース）を管理します。このタブは管理画面の**上部メニュー、左から4番目**にあります。
              </Typography>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography fontWeight="bold">資料をアップロードする方法</Typography></AccordionSummary>
                  <AccordionDetails>
                    <Typography sx={{ mb: 1 }}>画面右上の「新規アップロード」ボタンから、ポップアップ画面を開いて操作します。</Typography>
                    <Paper variant="outlined" sx={{ p: 2, my: 1, borderRadius: 2, bgcolor: 'grey.50', borderColor: 'grey.300' }}>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>【ポップアップ画面のイメージ】</Typography>
                        <Tabs value={0} sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}><Tab label="ファイルアップロード" disabled sx={{textTransform: 'none'}} /><Tab label="URLから追加" disabled sx={{textTransform: 'none'}} /></Tabs>
                        <Box sx={{textAlign: 'center', p: 2, border: '2px dashed', borderColor: 'grey.400', borderRadius: 2}}><Typography>ファイルをここにドラッグ＆ドロップ</Typography></Box>
                    </Paper>
                  </AccordionDetails>
                </Accordion>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography fontWeight="bold">カスタムプロンプト（管理者指令）の設定</Typography></AccordionSummary>
                  <AccordionDetails>
                    <Typography>リソース一覧の各行にある「カスタムプロンプト」列のテキストエリアに、AIへの特別な指示を入力できます。入力後、右側の「更新」ボタンを押すと保存されます。</Typography>
                    <List>
                      <ListItem><ListItemText primary="例1：回答のトーンを指示" secondary="「この行動規範マニュアルから回答する際は、常に丁寧で、断定的な表現は避けてください。」" /></ListItem>
                      <ListItem><ListItemText primary="例2：情報の要約方法を指示" secondary="「この議事録を要約する際は、『決定事項』『ToDoリスト』の2項目でまとめてください。」" /></ListItem>
                    </List>
                  </AccordionDetails>
                </Accordion>
              </>
            )}

            {renderSection("その他のタブ", <PaymentIcon color="primary" />,
               <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.8 }}>
                「プラン履歴」や「料金管理」のタブでは、現在の契約プランの詳細、利用料金、支払い履歴などを確認することができます。
              </Typography>
            )}
            </Box>
        )}
      </Container>
      
      {/* Footer */}
      <Box component="footer" sx={{ py: 4, borderTop: '1px solid #e0e0e0', backgroundColor: 'white' }}>
        <Container>
          <Typography variant="body2" color="text.secondary" align="center">
              © 2025 ワークメイトAI. All rights reserved.
            </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default GuideBook; 