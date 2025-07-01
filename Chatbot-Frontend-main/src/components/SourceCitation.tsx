import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Fade, useTheme, useMediaQuery } from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import LinkIcon from '@mui/icons-material/Link';
import ArticleIcon from '@mui/icons-material/Article';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import TableChartIcon from '@mui/icons-material/TableChart';
import TextSnippetIcon from '@mui/icons-material/TextSnippet';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

interface SourceCitationProps {
  source: string;
}

const SourceCitation: React.FC<SourceCitationProps> = ({ source }) => {
  const [animate, setAnimate] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  useEffect(() => {
    // マウント時にアニメーションを開始
    setAnimate(true);
  }, []);

  // 強化されたデバッグログ
  console.log("=== SourceCitation コンポーネント (強化版) ===");
  console.log("受信したsource:", source);
  console.log("sourceの型:", typeof source);
  console.log("sourceの長さ:", source ? source.length : 'null/undefined');
  console.log("source の詳細内容:", JSON.stringify(source));

  // 大幅に緩和された条件チェック - 空文字列、null、undefinedのみを除外
  if (!source || source === "" || source === "null" || source === "undefined") {
    console.log("❌ 完全に空のソース情報のため表示をスキップ");
    return null;
  }

  // 文字列でない場合は文字列に変換
  const sourceString = String(source).trim();
  
  // より緩い無効判定 - 本当に不要なもののみ除外
  const strictInvalidSources = [
    '',
    'null',
    'undefined',
    'なし',
    'none',
    'None',
    'NONE'
  ];
  
  if (strictInvalidSources.includes(sourceString.toLowerCase())) {
    console.log("❌ 厳格な無効判定により表示をスキップ:", sourceString);
    return null;
  }

  console.log("✅ SourceCitation表示を実行します:", sourceString);

  // ソース解析（シンプル化）
  const parseSourceInfo = (sourceText: string) => {
    console.log("ソース解析開始:", sourceText);
    
    // 単純にカンマ区切りで分割
    if (sourceText.includes(',')) {
      const sources = sourceText.split(',').map(s => s.trim()).filter(s => s.length > 0);
      console.log("カンマ区切りで解析:", sources);
      return sources;
    }
    
    // 単一のソース
    console.log("単一ソースとして解析:", [sourceText]);
    return [sourceText];
  };

  const sources = parseSourceInfo(sourceString);
  console.log("最終的に表示するソース:", sources);
  
  // ファイルタイプのアイコンを取得する関数（緑色統一）
  const getFileIcon = (filename: string) => {
    const lowerName = filename.toLowerCase();
    const iconColor = '#4CAF50'; // 緑色に統一
    
    if (lowerName.startsWith('http://') || lowerName.startsWith('https://')) {
      return <LinkIcon fontSize="small" sx={{ color: iconColor }} />;
    }
    if (lowerName.endsWith('.pdf')) {
      return <PictureAsPdfIcon fontSize="small" sx={{ color: iconColor }} />;
    }
    if (lowerName.endsWith('.xlsx') || lowerName.endsWith('.xls')) {
      return <TableChartIcon fontSize="small" sx={{ color: iconColor }} />;
    }
    if (lowerName.endsWith('.txt')) {
      return <TextSnippetIcon fontSize="small" sx={{ color: iconColor }} />;
    }
    return <DescriptionIcon fontSize="small" sx={{ color: iconColor }} />;
  };

  return (
    <Fade in={animate} timeout={600}>
      <Box sx={{ mt: 1.5, mb: 0.5 }}>
        {/* 情報ソースヘッダー（写真と同じスタイル） */}
        <Typography
          variant="body2"
          sx={{
            color: '#666',
            fontSize: '0.875rem',
            mb: 1,
            fontWeight: 400,
          }}
        >
          情報ソース：
        </Typography>
        
        {/* ファイルカード（写真と同じデザイン） */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          {sources.slice(0, 3).map((currentSource, index) => {
            // ページ番号を抽出（存在する場合）
            const pageMatch = currentSource.match(/\((?:P\.)?(\d+(?:-\d+)?|[^)]+)\)$/);
            const cleanName = pageMatch 
              ? currentSource.replace(/\s*\([^)]+\)$/, '') 
              : currentSource;
            const pageInfo = pageMatch ? pageMatch[1] : null;
            
            const isUrl = cleanName.startsWith('http://') || cleanName.startsWith('https://');
            
            return (
              <Paper
                key={index}
                elevation={0}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  p: 1.5,
                  borderRadius: '8px',
                  backgroundColor: '#E8F5E8', // 薄い緑色の背景（写真と同じ）
                  border: '1px solid #C8E6C9', // 緑色のボーダー（写真と同じ）
                  cursor: isUrl ? 'pointer' : 'default',
                  transition: 'all 0.2s ease',
                  '&:hover': isUrl ? {
                    backgroundColor: '#DDF4DD',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 2px 8px rgba(76, 175, 80, 0.15)'
                  } : {}
                }}
                onClick={isUrl ? () => window.open(cleanName, '_blank') : undefined}
              >
                {/* ファイルアイコン（写真と同じスタイル） */}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 24,
                    height: 24,
                    mr: 1.5,
                  }}
                >
                  {getFileIcon(cleanName)}
                </Box>
                
                {/* ファイル情報 */}
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 500,
                      color: '#2E7D32', // 濃い緑色（写真と同じ）
                      fontSize: '0.875rem',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                    title={cleanName}
                  >
                    {cleanName}
                  </Typography>
                  
                  {pageInfo && (
                    <Typography
                      variant="caption"
                      sx={{
                        color: '#4CAF50', // 緑色（写真と同じ）
                        fontSize: '0.75rem',
                        display: 'block',
                        mt: 0.25
                      }}
                    >
                      {pageInfo.includes('ページ') ? pageInfo : `${pageInfo}ページ目`}
                    </Typography>
                  )}
                </Box>
                
                {isUrl && (
                  <Box sx={{ ml: 1 }}>
                    <OpenInNewIcon 
                      sx={{ 
                        fontSize: '1rem', 
                        color: '#4CAF50',
                        opacity: 0.7
                      }} 
                    />
                  </Box>
                )}
              </Paper>
            );
          })}
          
          {/* 3個以上のソースがある場合は省略表示 */}
          {sources.length > 3 && (
            <Typography
              variant="caption"
              sx={{
                color: '#666',
                fontSize: '0.8rem',
                fontStyle: 'italic',
                textAlign: 'center',
                mt: 0.5
              }}
            >
              他{sources.length - 3}件の資料
            </Typography>
          )}
        </Box>
      </Box>
    </Fade>
  );
};

export default SourceCitation;