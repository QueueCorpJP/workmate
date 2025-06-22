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

  if (!source || !source.trim()) return null;

  // 不要なソース情報を除外
  const trimmedSource = source.trim();
  const invalidSources = [
    'なし',
    'デバッグ',
    'debug',
    'Debug',
    'DEBUG',
    'Source: "なし"',
    'デバッグ - Source: "なし"',
    '情報なし',
    '該当なし',
    '不明',
    'unknown',
    'Unknown',
    'UNKNOWN',
    'null',
    'undefined',
    ''
  ];
  
  // 無効なソース情報の場合は表示しない
  if (invalidSources.some(invalid => 
    trimmedSource === invalid || 
    trimmedSource.toLowerCase() === invalid.toLowerCase() ||
    trimmedSource.includes('デバッグ') ||
    trimmedSource.includes('debug')
  )) {
    return null;
  }

  console.log("SourceCitation受信ソース:", source);

  // 複数のソースを処理する（ [file1.pdf], [file2.pdf] 形式に対応）
  const parseMultipleSources = (sourceText: string) => {
    console.log("ソース解析開始:", sourceText);
    
    // [filename] 形式で囲まれたファイル名を抽出
    const bracketMatches = sourceText.match(/\[([^\]]+)\]/g);
    if (bracketMatches) {
      const result = bracketMatches.map(match => match.slice(1, -1)); // [] を除去
      console.log("ブラケット形式で解析:", result);
      return result;
    }
    
    // カンマ区切りのソースを処理
    if (sourceText.includes(',')) {
      const result = sourceText.split(',').map(s => s.trim());
      console.log("カンマ区切りで解析:", result);
      return result;
    }
    
    // 単一のソース
    console.log("単一ソースとして解析:", [sourceText]);
    return [sourceText];
  };

  const sources = parseMultipleSources(source);
  
  // 最初のソースを基準にファイル情報を取得（表示用）
  const firstSource = sources[0];
  const isUrl = firstSource.startsWith('http://') || firstSource.startsWith('https://');
  
  // ページ番号の抽出 - 複数のフォーマットに対応
  // 例: (P.14) または (P.14-15) または (緊急時対応、5)
  const pageMatch = firstSource.match(/\((?:P\.)?(\d+(?:-\d+)?|[^)]+)\)$/);
  const pageInfo = pageMatch ? pageMatch[1] : null;
  
  // ページ番号を除いたソース名
  const sourceName = pageMatch
    ? firstSource.replace(/\s*\([^)]+\)$/, '')
    : firstSource;
  


  return (
    <Fade in={animate} timeout={800}>
      <Box sx={{ mt: 2, mb: 1 }}>
        {/* 情報ソースヘッダー */}
        <Typography
          variant="body2"
          sx={{
            color: 'text.secondary',
            mb: 1,
            fontSize: '0.875rem'
          }}
        >
          情報ソース：{sources.length > 1 ? sources.join('、') : sourceName}{pageInfo && `（${pageInfo.includes('ページ') ? pageInfo : `ページ${pageInfo}`}）`}
        </Typography>
        
        {/* ファイルカード */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {sources.map((currentSource, index) => {
            // 各ソースのファイル情報を個別に取得
            const sourceIsUrl = currentSource.startsWith('http://') || currentSource.startsWith('https://');
            const sourcePageMatch = currentSource.match(/\((?:P\.)?(\d+(?:-\d+)?|[^)]+)\)$/);
            const sourcePageInfo = sourcePageMatch ? sourcePageMatch[1] : null;
            const cleanSourceName = sourcePageMatch
              ? currentSource.replace(/\s*\([^)]+\)$/, '')
              : currentSource;
            
            // 各ソースのファイルタイプ情報を取得
            const getSourceFileTypeInfo = (sourceName: string) => {
              if (sourceName.includes('緊急') || sourceName.includes('災害') || sourceName.includes('防災')) {
                return {
                  icon: <VerifiedIcon fontSize="small" sx={{ color: '#d32f2f' }} />,
                  colors: { light: '#ffebee', main: '#d32f2f' }
                };
              }
              
              if (sourceName.includes('マニュアル') || sourceName.includes('ハンドブック') || sourceName.includes('ガイド')) {
                return {
                  icon: <BookmarkIcon fontSize="small" sx={{ color: '#7b1fa2' }} />,
                  colors: { light: '#f3e5f5', main: '#7b1fa2' }
                };
              }
              
              if (sourceIsUrl) {
                return {
                  icon: <LinkIcon fontSize="small" sx={{ color: '#1976d2' }} />,
                  colors: { light: '#e3f2fd', main: '#1976d2' }
                };
              }
              
              if (sourceName.endsWith('.pdf')) {
                return {
                  icon: <PictureAsPdfIcon fontSize="small" sx={{ color: '#f44336' }} />,
                  colors: { light: '#ffebee', main: '#f44336' }
                };
              }
              
              if (sourceName.endsWith('.xlsx') || sourceName.endsWith('.xls')) {
                return {
                  icon: <TableChartIcon fontSize="small" sx={{ color: '#2e7d32' }} />,
                  colors: { light: '#e8f5e9', main: '#2e7d32' }
                };
              }
              
              if (sourceName.endsWith('.txt')) {
                return {
                  icon: <TextSnippetIcon fontSize="small" sx={{ color: '#0288d1' }} />,
                  colors: { light: '#e1f5fe', main: '#0288d1' }
                };
              }
              
              return {
                icon: <ArticleIcon fontSize="small" sx={{ color: '#ed6c02' }} />,
                colors: { light: '#fff3e0', main: '#ed6c02' }
              };
            };

            const sourceFileInfo = getSourceFileTypeInfo(cleanSourceName);
            
            return (
              <Paper
                key={index}
                elevation={1}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  p: 1.5,
                  borderRadius: '8px',
                  backgroundColor: sourceFileInfo.colors.light,
                  border: `1px solid ${sourceFileInfo.colors.main}20`,
                  transition: 'all 0.2s ease',
                  cursor: sourceIsUrl ? 'pointer' : 'default',
                  '&:hover': {
                    backgroundColor: sourceFileInfo.colors.light,
                    transform: sourceIsUrl ? 'translateY(-1px)' : 'none',
                    boxShadow: sourceIsUrl ? '0 2px 8px rgba(0,0,0,0.1)' : '0 1px 3px rgba(0,0,0,0.1)'
                  }
                }}
                onClick={sourceIsUrl ? () => window.open(cleanSourceName, '_blank') : undefined}
              >
                {/* ファイルアイコン */}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 32,
                    height: 32,
                    borderRadius: '6px',
                    backgroundColor: 'white',
                    mr: 1.5,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                  }}
                >
                  {sourceFileInfo.icon}
                </Box>
                
                {/* ファイル情報 */}
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 500,
                      color: 'text.primary',
                      fontSize: '0.875rem',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                    title={cleanSourceName}
                  >
                    {cleanSourceName}
                  </Typography>
                  
                  {sourcePageInfo && (
                    <Typography
                      variant="caption"
                      sx={{
                        color: 'text.secondary',
                        fontSize: '0.75rem',
                        display: 'block',
                        mt: 0.25
                      }}
                    >
                      {sourcePageInfo.includes('ページ') ? sourcePageInfo : `${sourcePageInfo}ページ目`}
                    </Typography>
                  )}
                </Box>
                
                {sourceIsUrl && (
                  <Box sx={{ ml: 1 }}>
                    <OpenInNewIcon 
                      sx={{ 
                        fontSize: '1rem', 
                        color: 'text.secondary',
                        opacity: 0.7
                      }} 
                    />
                  </Box>
                )}
              </Paper>
            );
          })}
        </Box>
      </Box>
    </Fade>
  );
};

export default SourceCitation;