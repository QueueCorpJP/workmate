import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Fade, Tooltip, IconButton, Divider, useTheme, useMediaQuery } from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import LinkIcon from '@mui/icons-material/Link';
import InfoIcon from '@mui/icons-material/Info';
import ArticleIcon from '@mui/icons-material/Article';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import TableChartIcon from '@mui/icons-material/TableChart';
import TextSnippetIcon from '@mui/icons-material/TextSnippet';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import VerifiedIcon from '@mui/icons-material/Verified';
import BookmarkIcon from '@mui/icons-material/Bookmark';

interface SourceCitationProps {
  source: string;
}

const SourceCitation: React.FC<SourceCitationProps> = ({ source }) => {
  const [animate, setAnimate] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  
  useEffect(() => {
    // マウント時にアニメーションを開始
    setAnimate(true);
  }, []);

  if (!source) return null;

  // ソースがURLかファイルかを判定
  const isUrl = source.startsWith('http://') || source.startsWith('https://');
  
  // ページ番号の抽出 - 複数のフォーマットに対応
  // 例: (P.14) または (P.14-15) または (緊急時対応、5)
  const pageMatch = source.match(/\((?:P\.)?(\d+(?:-\d+)?|[^)]+)\)$/);
  const pageInfo = pageMatch ? pageMatch[1] : null;
  
  // ページ番号を除いたソース名
  const sourceName = pageMatch
    ? source.replace(/\s*\([^)]+\)$/, '')
    : source;
  
  // ソース名が長すぎる場合は省略 (デバイスサイズに応じて調整)
  const getDisplayNameMaxLength = () => {
    if (isMobile) return 20;
    if (isTablet) return 25;
    return 30;
  };
  
  const maxLength = getDisplayNameMaxLength();
  const displayName = sourceName.length > maxLength
    ? sourceName.substring(0, maxLength - 3) + '...'
    : sourceName;

  // ファイルタイプを判定
  const getFileTypeInfo = () => {
    // 緊急時対応マニュアルなどの特別なドキュメントを検出
    if (sourceName.includes('緊急') || sourceName.includes('災害') || sourceName.includes('防災')) {
      return {
        icon: <VerifiedIcon fontSize="small" sx={{ color: '#d32f2f' }} />,
        label: '緊急マニュアル',
        badge: '重要',
        colors: {
          light: '#ffebee',
          main: '#d32f2f',
          dark: '#b71c1c',
          gradient: 'linear-gradient(135deg, #ffcdd2 0%, #ef5350 100%)',
          glow: '0 0 8px rgba(211, 47, 47, 0.4)'
        }
      };
    }
    
    // 社内マニュアルやハンドブックを検出
    if (sourceName.includes('マニュアル') || sourceName.includes('ハンドブック') || sourceName.includes('ガイド')) {
      return {
        icon: <BookmarkIcon fontSize="small" sx={{ color: '#7b1fa2' }} />,
        label: '社内マニュアル',
        badge: '公式',
        colors: {
          light: '#f3e5f5',
          main: '#7b1fa2',
          dark: '#4a148c',
          gradient: 'linear-gradient(135deg, #e1bee7 0%, #ba68c8 100%)',
          glow: '0 0 8px rgba(123, 31, 162, 0.4)'
        }
      };
    }
    
    if (isUrl) {
      return {
        icon: <LinkIcon fontSize="small" sx={{ color: '#1976d2' }} />,
        label: 'ウェブページ',
        colors: {
          light: '#e3f2fd',
          main: '#1976d2',
          dark: '#0d47a1',
          gradient: 'linear-gradient(135deg, #bbdefb 0%, #64b5f6 100%)',
          glow: '0 0 8px rgba(25, 118, 210, 0.4)'
        }
      };
    }
    
    if (sourceName.endsWith('.pdf')) {
      return {
        icon: <PictureAsPdfIcon fontSize="small" sx={{ color: '#f44336' }} />,
        label: 'PDF文書',
        colors: {
          light: '#ffebee',
          main: '#f44336',
          dark: '#c62828',
          gradient: 'linear-gradient(135deg, #ffcdd2 0%, #ef5350 100%)',
          glow: '0 0 8px rgba(244, 67, 54, 0.4)'
        }
      };
    }
    
    if (sourceName.endsWith('.xlsx') || sourceName.endsWith('.xls')) {
      return {
        icon: <TableChartIcon fontSize="small" sx={{ color: '#2e7d32' }} />,
        label: 'Excel表計算',
        colors: {
          light: '#e8f5e9',
          main: '#2e7d32',
          dark: '#1b5e20',
          gradient: 'linear-gradient(135deg, #c8e6c9 0%, #81c784 100%)',
          glow: '0 0 8px rgba(46, 125, 50, 0.4)'
        }
      };
    }
    
    if (sourceName.endsWith('.txt')) {
      return {
        icon: <TextSnippetIcon fontSize="small" sx={{ color: '#0288d1' }} />,
        label: 'テキスト文書',
        colors: {
          light: '#e1f5fe',
          main: '#0288d1',
          dark: '#01579b',
          gradient: 'linear-gradient(135deg, #b3e5fc 0%, #4fc3f7 100%)',
          glow: '0 0 8px rgba(2, 136, 209, 0.4)'
        }
      };
    }
    
    return {
      icon: <ArticleIcon fontSize="small" sx={{ color: '#ed6c02' }} />,
      label: '文書',
      colors: {
        light: '#fff3e0',
        main: '#ed6c02',
        dark: '#e65100',
        gradient: 'linear-gradient(135deg, #ffe0b2 0%, #ffb74d 100%)',
        glow: '0 0 8px rgba(237, 108, 2, 0.4)'
      }
    };
  };

  const fileInfo = getFileTypeInfo();

  const handleOpenSource = () => {
    if (isUrl) {
      window.open(sourceName, '_blank');
    }
  };

  return (
    <Fade in={animate} timeout={800}>
      <Paper
        elevation={2}
        sx={{
          mt: 2,
          mb: 1,
          display: 'flex',
          alignItems: 'stretch',
          borderRadius: { xs: '10px', sm: '12px' },
          overflow: 'hidden',
          maxWidth: '100%',
          boxShadow: `0 3px 10px rgba(0,0,0,0.08), ${fileInfo.colors.glow || '0 0 0 transparent'}`,
          border: `1px solid ${fileInfo.colors.light}`,
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative',
          '&:hover': {
            boxShadow: `0 4px 15px rgba(0,0,0,0.12), ${fileInfo.colors.glow || '0 0 0 transparent'}`,
            transform: 'translateY(-2px)'
          },
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '1px',
            background: `linear-gradient(90deg, transparent, ${fileInfo.colors.main}40, transparent)`,
            opacity: 0.7
          }
        }}
      >
        {/* ソースタイプを示すサイドバー */}
        <Box
          sx={{
            width: { xs: '4px', sm: '6px' },
            background: fileInfo.colors.gradient,
            boxShadow: 'inset -1px 0 2px rgba(0,0,0,0.05)'
          }}
        />
        
        {/* ソースタイプアイコンエリア */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: { xs: 1, sm: 1.5 },
            background: `linear-gradient(135deg, ${fileInfo.colors.light} 0%, ${fileInfo.colors.light}80 100%)`,
            position: 'relative',
            '&::after': {
              content: '""',
              position: 'absolute',
              top: 0,
              right: 0,
              bottom: 0,
              width: '8px',
              background: `linear-gradient(to right, transparent, ${fileInfo.colors.light}80)`,
              zIndex: 1
            }
          }}
        >
          <Tooltip title={fileInfo.label}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: { xs: 32, sm: 38 },
                height: { xs: 32, sm: 38 },
                borderRadius: '50%',
                bgcolor: 'white',
                boxShadow: `0 0 0 1px ${fileInfo.colors.main}30, 0 2px 4px rgba(0,0,0,0.1)`,
                transition: 'all 0.2s ease',
                position: 'relative',
                '&:hover': {
                  transform: 'scale(1.05) rotate(5deg)',
                  boxShadow: `0 0 0 2px ${fileInfo.colors.main}40, 0 3px 6px rgba(0,0,0,0.15)`
                },
                '&::after': fileInfo.badge ? {
                  content: '""',
                  position: 'absolute',
                  top: -2,
                  right: -2,
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: fileInfo.colors.main,
                  border: '2px solid white',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.2)'
                } : {}
              }}
            >
              {fileInfo.icon}
            </Box>
          </Tooltip>
        </Box>
        
        {/* ソース名と詳細情報 */}
        <Box
          sx={{
            display: 'flex',
            flex: 1,
            flexDirection: { xs: 'column', sm: 'row' },
            justifyContent: 'space-between',
            alignItems: { xs: 'flex-start', sm: 'center' },
            p: { xs: 1.2, sm: 1.5 },
            overflow: 'hidden'
          }}
        >
          <Box sx={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', flex: 1 }}>
            <Typography
              variant="body2"
              component="div"
              sx={{
                fontWeight: 500,
                color: 'text.primary',
                fontSize: { xs: '0.85rem', sm: '0.9rem' },
                whiteSpace: 'nowrap',
                textOverflow: 'ellipsis',
                overflow: 'hidden',
                maxWidth: '100%'
              }}
              title={sourceName}
            >
              {displayName}
            </Typography>
            
            {pageInfo && (
              <Typography
                variant="caption"
                component="div"
                sx={{
                  color: 'text.secondary',
                  mt: 0.3,
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <InfoIcon sx={{ fontSize: '0.9rem', mr: 0.5, opacity: 0.7 }} />
                {pageInfo.includes('-') ? `${pageInfo}ページ` : `${pageInfo}ページ目`}
              </Typography>
            )}
            
            {/* タブレット以上のサイズでラベル表示 */}
            {!isMobile && (
              <Box
                sx={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  mt: 0.5,
                  px: 0.8,
                  py: 0.2,
                  borderRadius: '4px',
                  backgroundColor: `${fileInfo.colors.light}`,
                  border: `1px solid ${fileInfo.colors.light}`,
                  maxWidth: 'fit-content'
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    color: fileInfo.colors.main,
                    textTransform: 'uppercase',
                    letterSpacing: '0.03em'
                  }}
                >
                  {fileInfo.badge || fileInfo.label}
                </Typography>
              </Box>
            )}
          </Box>
          
          {isUrl && (
            <Tooltip title="ソースを開く">
              <IconButton
                size="small"
                onClick={handleOpenSource}
                sx={{
                  ml: { xs: 0, sm: 1 },
                  mt: { xs: 1, sm: 0 },
                  color: fileInfo.colors.main,
                  backgroundColor: 'white',
                  border: `1px solid ${fileInfo.colors.light}`,
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  '&:hover': {
                    backgroundColor: fileInfo.colors.light,
                  },
                  alignSelf: { xs: 'flex-start', sm: 'center' }
                }}
              >
                <OpenInNewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Paper>
    </Fade>
  );
};

export default SourceCitation;