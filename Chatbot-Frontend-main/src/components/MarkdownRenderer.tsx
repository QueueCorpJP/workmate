import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Divider } from '@mui/material';
import { styled } from '@mui/material/styles';

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
    
    // テーブル
    table: ({ children }: any) => (
      <TableContainer component={Paper} sx={{ my: 2, maxWidth: '100%', overflow: 'auto' }}>
        <Table size="small">
          {children}
        </Table>
      </TableContainer>
    ),
    thead: ({ children }: any) => <TableHead>{children}</TableHead>,
    tbody: ({ children }: any) => <TableBody>{children}</TableBody>,
    tr: ({ children }: any) => <TableRow>{children}</TableRow>,
    th: ({ children }: any) => (
      <TableCell sx={{ fontWeight: 'bold', backgroundColor: 'action.hover' }}>
        {children}
      </TableCell>
    ),
    td: ({ children }: any) => <TableCell>{children}</TableCell>,
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