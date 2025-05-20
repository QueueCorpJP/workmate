import React from 'react';
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
  IconButton
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
                    資料アップロード
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  PDFやWordなどの資料をアップロードすると、AIがその内容を理解し、質問に回答できるようになります。複数の資料を組み合わせた質問も可能です。
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
            使い方ガイド
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
                  bgcolor: theme.palette.primary.main,
                  color: 'white',
                  fontWeight: 'bold'
                }}
              >
                1
              </Box>
              <Typography variant="h6" fontWeight={600}>
                資料のアップロード
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ mb: 2, ml: 7 }}>
              ホーム画面の「資料をアップロード」ボタンをクリックし、分析したい資料を選択します。PDFやWord、Excelなど様々な形式に対応しています。
            </Typography>
            <List sx={{ ml: 7 }}>
              <ListItem sx={{ p: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <CheckCircleIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText primary="ファイルをドラッグ＆ドロップするか、「ファイルを選択」でアップロード" />
              </ListItem>
              <ListItem sx={{ p: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <CheckCircleIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText primary="アップロードが完了すると、AIが自動的に内容を分析" />
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
                  bgcolor: theme.palette.primary.main,
                  color: 'white',
                  fontWeight: 'bold'
                }}
              >
                2
              </Box>
              <Typography variant="h6" fontWeight={600}>
                質問をする
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ mb: 2, ml: 7 }}>
              チャットインターフェースに質問を入力します。資料の内容に関する質問や、要約、分析の依頼など、自然な言葉で問いかけてください。
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
        </Box>
        
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
                A: PDF、Word（.docx）、Excel（.xlsx）、PowerPoint（.pptx）、テキストファイル（.txt）などの一般的な形式に対応しています。画像が含まれる資料も処理可能ですが、テキスト抽出の精度は画像の品質によって異なる場合があります。
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
            
            <Box>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
                Q: デモ版の制限を超えて利用するにはどうすればよいですか？
              </Typography>
              <Typography variant="body1">
                A: 完全版へのアップグレードをご検討ください。完全版では資料のアップロード回数や質問回数の制限がなく、追加機能もご利用いただけます。詳細については、お問い合わせフォームからご連絡ください。
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
              さっそく始めましょう
            </Typography>
            <Typography
              variant="body1"
              sx={{
                mb: 4,
                color: 'text.secondary',
                fontSize: '1.1rem'
              }}
            >
              ワークメイトAIを使って、資料の分析と理解を次のレベルへ。
              AIパワードアシスタントがあなたの業務をサポートします。
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
                href="https://queue-lp.vercel.app/"
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