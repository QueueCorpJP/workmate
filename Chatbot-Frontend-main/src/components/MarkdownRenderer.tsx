import React, { useRef, useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Divider, Chip } from '@mui/material';
import { styled } from '@mui/material/styles';
import { KeyboardArrowRight, SwipeLeft } from '@mui/icons-material';

// スタイル付きコンポーネント
const StyledPre = styled('pre')(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f5f5f5',
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(2),
  overflow: 'auto',
  fontFamily: '"Fira Code", "Monaco", "Consolas", monospace',
  fontSize: '0.875rem',
  lineHeight: 1.5,
  margin: theme.spacing(1, 0),
}));

const StyledCode = styled('code')(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark' ? '#2d2d2d' : '#f0f0f0',
  padding: theme.spacing(0.25, 0.5),
  borderRadius: theme.shape.borderRadius / 2,
  fontFamily: '"Fira Code", "Monaco", "Consolas", monospace',
  fontSize: '0.875rem',
}));

const StyledBlockquote = styled('blockquote')(({ theme }) => ({
  borderLeft: `4px solid ${theme.palette.primary.main}`,
  paddingLeft: theme.spacing(2),
  margin: theme.spacing(1, 0),
  fontStyle: 'italic',
  color: theme.palette.text.secondary,
}));

// スマートテーブルコンテナ（横スクロール可能を視覚的に示す）
const SmartTableContainer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isScrollable, setIsScrollable] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const [canScrollLeft, setCanScrollLeft] = useState(false);

  const checkScrollability = () => {
    if (containerRef.current) {
      const { scrollWidth, clientWidth, scrollLeft } = containerRef.current;
      setIsScrollable(scrollWidth > clientWidth);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 1);
      setCanScrollLeft(scrollLeft > 1);
    }
  };

  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      checkScrollability();
      const resizeObserver = new ResizeObserver(checkScrollability);
      resizeObserver.observe(container);
      
      return () => resizeObserver.disconnect();
    }
  }, []);

  const handleScroll = () => {
    checkScrollability();
  };

  return (
    <Box sx={{ position: 'relative', my: 2 }}>
      {/* ヒントメッセージ */}
      {isScrollable && (
        <Box sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            icon={<SwipeLeft />}
            label="横にスクロールして全ての列を確認できます"
            size="small"
            color="info"
            variant="outlined"
            sx={{ 
              fontSize: '0.75rem',
              height: 24,
              '& .MuiChip-icon': { fontSize: 16 },
              // モバイルでより目立つスタイル
              '@media (max-width: 768px)': {
                backgroundColor: 'info.light',
                color: 'info.contrastText',
                border: 'none',
                animation: 'fadeInOut 3s infinite',
                '@keyframes fadeInOut': {
                  '0%, 100%': { opacity: 0.8 },
                  '50%': { opacity: 1 },
                }
              }
            }}
          />
        </Box>
      )}
      
      {/* テーブルコンテナ */}
      <TableContainer 
        component={Paper} 
        ref={containerRef}
        onScroll={handleScroll}
        sx={{ 
          maxWidth: '100%',
          overflow: 'auto',
          position: 'relative',
          // テーブル専用のスタイリング
          borderRadius: 2,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
          border: '1px solid rgba(0, 0, 0, 0.12)',
          // タッチデバイス向けのスクロール改善
          WebkitOverflowScrolling: 'touch',
          scrollBehavior: 'smooth',
          // スクロールバーのスタイリング
          '&::-webkit-scrollbar': {
            height: { xs: 6, sm: 8 }, // モバイルでより薄く
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: 'rgba(0,0,0,0.05)',
            borderRadius: 4,
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0,0,0,0.3)',
            borderRadius: 4,
            '&:hover': {
              backgroundColor: 'rgba(0,0,0,0.4)',
            },
          },
          // モバイルでのタッチ体験向上
          '@media (max-width: 768px)': {
            '&::-webkit-scrollbar': {
              height: 4,
            },
          },
        }}
      >
        {children}
        
        {/* 右側のフェードアウト効果（スクロール可能時） */}
        {isScrollable && canScrollRight && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              right: 0,
              height: '100%',
              width: { xs: 50, sm: 40 }, // モバイルでより幅広く
              background: {
                xs: 'linear-gradient(to left, rgba(255,255,255,0.95), transparent)', // モバイルでより濃く
                sm: 'linear-gradient(to left, rgba(255,255,255,0.9), transparent)'
              },
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1,
            }}
          >
            <KeyboardArrowRight 
              sx={{ 
                color: 'text.secondary',
                fontSize: { xs: 24, sm: 20 }, // モバイルでより大きく
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 0.5 },
                  '50%': { opacity: 1 },
                },
                // モバイルでより目立つ効果
                '@media (max-width: 768px)': {
                  backgroundColor: 'rgba(33, 150, 243, 0.1)',
                  borderRadius: '50%',
                  padding: '4px',
                  boxShadow: '0 2px 8px rgba(33, 150, 243, 0.3)',
                }
              }} 
            />
          </Box>
        )}
      </TableContainer>
    </Box>
  );
};

interface MarkdownRendererProps {
  content: string;
  isUser?: boolean;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, isUser = false }) => {
  const components: any = {
    // 見出し
    h1: ({ children }: any) => (
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', mt: 2, mb: 1 }}>
        {children}
      </Typography>
    ),
    h2: ({ children }: any) => (
      <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 'bold', mt: 2, mb: 1 }}>
        {children}
      </Typography>
    ),
    h3: ({ children }: any) => (
      <Typography variant="h6" component="h3" gutterBottom sx={{ fontWeight: 'bold', mt: 1.5, mb: 1 }}>
        {children}
      </Typography>
    ),
    h4: ({ children }: any) => (
      <Typography variant="subtitle1" component="h4" gutterBottom sx={{ fontWeight: 'bold', mt: 1.5, mb: 0.5 }}>
        {children}
      </Typography>
    ),
    h5: ({ children }: any) => (
      <Typography variant="subtitle2" component="h5" gutterBottom sx={{ fontWeight: 'bold', mt: 1, mb: 0.5 }}>
        {children}
      </Typography>
    ),
    h6: ({ children }: any) => (
      <Typography variant="body1" component="h6" gutterBottom sx={{ fontWeight: 'bold', mt: 1, mb: 0.5 }}>
        {children}
      </Typography>
    ),
    
    // 段落
    p: ({ children }: any) => (
      <Typography variant="body1" component="p" sx={{ mb: 1, lineHeight: 1.6 }}>
        {children}
      </Typography>
    ),
    
    // リスト
    ul: ({ children }: any) => (
      <Box component="ul" sx={{ pl: 3, my: 1 }}>
        {children}
      </Box>
    ),
    ol: ({ children }: any) => (
      <Box component="ol" sx={{ pl: 3, my: 1 }}>
        {children}
      </Box>
    ),
    li: ({ children }: any) => (
      <Typography component="li" variant="body1" sx={{ mb: 0.5, lineHeight: 1.6 }}>
        {children}
      </Typography>
    ),
    
    // コードブロック
    pre: ({ children }: any) => (
      <StyledPre>
        {children}
      </StyledPre>
    ),
    code: ({ inline, children }: any) => {
      if (inline) {
        return <StyledCode>{children}</StyledCode>;
      }
      return <code>{children}</code>;
    },
    
    // 引用
    blockquote: ({ children }: any) => (
      <StyledBlockquote>
        {children}
      </StyledBlockquote>
    ),
    
    // 水平線
    hr: () => <Divider sx={{ my: 2 }} />,
    
    // 強調
    strong: ({ children }: any) => (
      <Typography component="strong" sx={{ fontWeight: 'bold' }}>
        {children}
      </Typography>
    ),
    em: ({ children }: any) => (
      <Typography component="em" sx={{ fontStyle: 'italic' }}>
        {children}
      </Typography>
    ),
    
    // リンク
    a: ({ href, children }: any) => (
      <Typography
        component="a"
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        sx={{
          color: 'primary.main',
          textDecoration: 'underline',
          '&:hover': {
            textDecoration: 'none',
          },
        }}
      >
        {children}
      </Typography>
    ),
    
    // テーブル - 横スクロール可能を視覚的に示すスマートテーブル
    table: ({ children }: any) => (
      <SmartTableContainer>
        <Table size="small" sx={{ 
          minWidth: 500,  // 最小幅を設定
          tableLayout: 'auto', // 自動レイアウト
        }}>
          {children}
        </Table>
      </SmartTableContainer>
    ),
    thead: ({ children }: any) => <TableHead>{children}</TableHead>,
    tbody: ({ children }: any) => <TableBody>{children}</TableBody>,
    tr: ({ children }: any) => <TableRow>{children}</TableRow>,
    th: ({ children }: any) => (
      <TableCell sx={{ 
        fontWeight: 'bold', 
        backgroundColor: 'action.hover',
        // ヘッダーセルのスタイリング
        minWidth: '100px',
        maxWidth: '200px',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        padding: '8px 12px',
        fontSize: '0.875rem',
        // ヘッダー固定（スクロール中も見える）
        position: 'sticky',
        top: 0,
        zIndex: 2,
        borderBottom: '2px solid',
        borderBottomColor: 'divider',
        // スクロール時の視覚的強調
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
      }}>
        {children}
      </TableCell>
    ),
    td: ({ children }: any) => (
      <TableCell sx={{
        // セル内容の折り返しとスタイリング
        maxWidth: '250px',
        wordWrap: 'break-word',
        wordBreak: 'break-word',
        whiteSpace: 'pre-wrap',
        lineHeight: 1.4,
        padding: '8px 12px',
        fontSize: '0.875rem',
        // 長いテキストの処理
        '& *': {
          maxWidth: '100% !important',
          wordWrap: 'break-word !important',
          wordBreak: 'break-word !important',
        }
      }}>
        {children}
      </TableCell>
    ),
  };

  return (
    <Box
      sx={{
        '& .hljs': {
          background: 'transparent !important',
        },
        color: isUser ? 'inherit' : 'text.primary',
        wordBreak: 'break-word',
        overflowWrap: 'break-word',
        // テーブル表示の改善
        '& table': {
          fontSize: '0.85rem',
        },
        // テーブルコンテナがメッセージボックスの制約を受けないように
        '& .MuiTableContainer-root': {
          marginLeft: 'calc(-1 * var(--message-padding, 0px))',
          marginRight: 'calc(-1 * var(--message-padding, 0px))',
          width: 'calc(100% + 2 * var(--message-padding, 0px))',
        },
      }}
    >
      <ReactMarkdown
        components={components}
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
      >
        {content}
      </ReactMarkdown>
    </Box>
  );
};

export default MarkdownRenderer; 