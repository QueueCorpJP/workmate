import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Fab,
  Paper,
  Typography,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  useTheme,
  useMediaQuery,
  Tooltip,
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CloseIcon from '@mui/icons-material/Close';
import LinkIcon from '@mui/icons-material/Link';
import ArticleIcon from '@mui/icons-material/Article';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import TableChartIcon from '@mui/icons-material/TableChart';
import TextSnippetIcon from '@mui/icons-material/TextSnippet';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import VerifiedIcon from '@mui/icons-material/Verified';

interface Message {
  text: string;
  isUser: boolean;
  source?: string;
}

interface FloatingSourcePanelProps {
  messages: Message[];
  isVisible: boolean;
  onToggle: () => void;
  onClose: () => void;
}

interface SourceInfo {
  name: string;
  page?: string;
  isUrl: boolean;
  type: string;
  icon: React.ReactNode;
  color: string;
  count: number;
}

const FloatingSourcePanel: React.FC<FloatingSourcePanelProps> = ({
  messages,
  isVisible,
  onToggle,
  onClose,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // メッセージから参照ソース情報を抽出
  const sourceInfos = useMemo(() => {
    const sourceMap = new Map<string, SourceInfo>();

    messages.forEach((message) => {
      if (!message.source || message.isUser) return;

      // 複数ソースを解析
      const parseMultipleSources = (sourceText: string) => {
        const bracketMatches = sourceText.match(/\[([^\]]+)\]/g);
        if (bracketMatches) {
          return bracketMatches.map(match => match.slice(1, -1));
        }
        if (sourceText.includes(',')) {
          return sourceText.split(',').map(s => s.trim());
        }
        return [sourceText];
      };

      const sources = parseMultipleSources(message.source);

      sources.forEach((source) => {
        const pageMatch = source.match(/\((?:P\.)?(\d+(?:-\d+)?|[^)]+)\)$/);
        const pageInfo = pageMatch ? pageMatch[1] : undefined;
        const cleanSourceName = pageMatch
          ? source.replace(/\s*\([^)]+\)$/, '')
          : source;

        const isUrl = source.startsWith('http://') || source.startsWith('https://');
        
        // ファイルタイプとアイコンを決定
        let icon: React.ReactNode;
        let color: string;
        let type: string;

        if (cleanSourceName.includes('緊急') || cleanSourceName.includes('災害') || cleanSourceName.includes('防災')) {
          icon = <VerifiedIcon fontSize="small" />;
          color = '#d32f2f';
          type = '緊急文書';
        } else if (cleanSourceName.includes('マニュアル') || cleanSourceName.includes('ハンドブック') || cleanSourceName.includes('ガイド')) {
          icon = <BookmarkIcon fontSize="small" />;
          color = '#7b1fa2';
          type = 'マニュアル';
        } else if (isUrl) {
          icon = <LinkIcon fontSize="small" />;
          color = '#1976d2';
          type = 'ウェブサイト';
        } else if (cleanSourceName.endsWith('.pdf')) {
          icon = <PictureAsPdfIcon fontSize="small" />;
          color = '#f44336';
          type = 'PDF文書';
        } else if (cleanSourceName.endsWith('.xlsx') || cleanSourceName.endsWith('.xls')) {
          icon = <TableChartIcon fontSize="small" />;
          color = '#2e7d32';
          type = 'Excel文書';
        } else if (cleanSourceName.endsWith('.txt')) {
          icon = <TextSnippetIcon fontSize="small" />;
          color = '#0288d1';
          type = 'テキスト文書';
        } else {
          icon = <ArticleIcon fontSize="small" />;
          color = '#ed6c02';
          type = '文書';
        }

        const key = `${cleanSourceName}${pageInfo ? `-${pageInfo}` : ''}`;
        
        if (sourceMap.has(key)) {
          sourceMap.get(key)!.count += 1;
        } else {
          sourceMap.set(key, {
            name: cleanSourceName,
            page: pageInfo,
            isUrl,
            type,
            icon,
            color,
            count: 1,
          });
        }
      });
    });

    return Array.from(sourceMap.values())
      .sort((a, b) => b.count - a.count); // 参照回数順にソート
  }, [messages]);

  // 参照ソースがない場合は非表示
  if (sourceInfos.length === 0) {
    return null;
  }

  const handleSourceClick = (sourceInfo: SourceInfo) => {
    if (sourceInfo.isUrl) {
      window.open(sourceInfo.name, '_blank');
    }
  };

  return (
    <>
      {/* フローティングボタン */}
      {!isVisible && (
        <Tooltip title="参照ソース一覧を表示" arrow>
          <Fab
            size={isMobile ? "small" : "medium"}
            color="primary"
            onClick={onToggle}
            sx={{
              position: 'fixed',
              bottom: isMobile ? 80 : 100,
              right: isMobile ? 16 : 24,
              zIndex: 1000,
              background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
              boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
              '&:hover': {
                background: 'linear-gradient(135deg, #1d4ed8, #2563eb)',
                transform: 'scale(1.05)',
              },
            }}
          >
            <DescriptionIcon />
          </Fab>
        </Tooltip>
      )}

      {/* フローティングパネル */}
      {isVisible && (
        <Paper
          elevation={8}
          sx={{
            position: 'fixed',
            bottom: isMobile ? 80 : 100,
            right: isMobile ? 16 : 24,
            width: isMobile ? 280 : 320,
            maxHeight: isMobile ? 300 : 400,
            zIndex: 1000,
            borderRadius: 3,
            overflow: 'hidden',
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(37, 99, 235, 0.1)',
          }}
        >
          {/* ヘッダー */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              p: 2,
              background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
              color: 'white',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <DescriptionIcon fontSize="small" />
              <Typography variant="subtitle2" fontWeight={600}>
                参照ソース
              </Typography>
              <Chip
                label={sourceInfos.length}
                size="small"
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  fontSize: '0.7rem',
                  height: 20,
                }}
              />
            </Box>
            <Box>
              <IconButton
                size="small"
                onClick={() => setIsExpanded(!isExpanded)}
                sx={{ color: 'white', mr: 0.5 }}
              >
                {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
              <IconButton
                size="small"
                onClick={onClose}
                sx={{ color: 'white' }}
              >
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>

          {/* ソース一覧 */}
          <Collapse in={isExpanded}>
            <List dense sx={{ maxHeight: 280, overflow: 'auto', p: 0 }}>
              {sourceInfos.map((sourceInfo, index) => (
                <ListItem
                  key={index}
                  button={sourceInfo.isUrl}
                  onClick={() => handleSourceClick(sourceInfo)}
                  sx={{
                    borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                    '&:hover': sourceInfo.isUrl ? {
                      backgroundColor: 'rgba(37, 99, 235, 0.04)',
                    } : {},
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <Box
                      sx={{
                        color: sourceInfo.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: 24,
                        height: 24,
                        borderRadius: 1,
                        backgroundColor: `${sourceInfo.color}10`,
                      }}
                    >
                      {sourceInfo.icon}
                    </Box>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 500,
                          fontSize: '0.8rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {sourceInfo.name.length > 20 
                          ? `${sourceInfo.name.substring(0, 20)}...`
                          : sourceInfo.name
                        }
                      </Typography>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        <Typography
                          variant="caption"
                          sx={{ color: 'text.secondary', fontSize: '0.7rem' }}
                        >
                          {sourceInfo.type}
                        </Typography>
                        {sourceInfo.page && (
                          <Typography
                            variant="caption"
                            sx={{ color: 'text.secondary', fontSize: '0.7rem' }}
                          >
                            • P.{sourceInfo.page}
                          </Typography>
                        )}
                        {sourceInfo.count > 1 && (
                          <Chip
                            label={`${sourceInfo.count}回参照`}
                            size="small"
                            sx={{
                              fontSize: '0.6rem',
                              height: 16,
                              backgroundColor: sourceInfo.color,
                              color: 'white',
                            }}
                          />
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Collapse>

          {/* コンパクト表示（折りたたみ時） */}
          {!isExpanded && (
            <Box sx={{ p: 2, pt: 1 }}>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                {sourceInfos.length}件の情報ソースが参照されています
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                {sourceInfos.slice(0, 3).map((sourceInfo, index) => (
                  <Chip
                    key={index}
                    label={sourceInfo.name.length > 15 
                      ? `${sourceInfo.name.substring(0, 15)}...`
                      : sourceInfo.name
                    }
                    size="small"
                    sx={{
                      fontSize: '0.7rem',
                      height: 20,
                      backgroundColor: `${sourceInfo.color}15`,
                      color: sourceInfo.color,
                      border: `1px solid ${sourceInfo.color}30`,
                    }}
                  />
                ))}
                {sourceInfos.length > 3 && (
                  <Typography variant="caption" sx={{ color: 'text.secondary', alignSelf: 'center' }}>
                    他{sourceInfos.length - 3}件
                  </Typography>
                )}
              </Box>
            </Box>
          )}
        </Paper>
      )}
    </>
  );
};

export default FloatingSourcePanel; 