import React from "react";
import {
  Box,
  Typography,
  Button,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
} from "@mui/material";
import { ChatHistoryItem } from "./types";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";
import { formatDate } from "./utils";
import { useTheme } from "@mui/material/styles";
import SentimentSatisfiedAltIcon from "@mui/icons-material/SentimentSatisfiedAlt";
import SentimentVeryDissatisfiedIcon from "@mui/icons-material/SentimentVeryDissatisfied";
import SentimentNeutralIcon from "@mui/icons-material/SentimentNeutral";
import DownloadIcon from "@mui/icons-material/Download";
import MarkdownRenderer from "../MarkdownRenderer";
import api from "../../api";

interface ChatHistoryTabProps {
  chatHistory: ChatHistoryItem[];
  isLoading: boolean;
  onRefresh: () => void;
  onLoadMore?: () => void;
  hasMore?: boolean;
  totalCount?: number;
}

const ChatHistoryTab: React.FC<ChatHistoryTabProps> = ({
  chatHistory,
  isLoading,
  onRefresh,
  onLoadMore,
  hasMore = false,
  totalCount = 0,
}) => {
  const theme = useTheme();

  // 感情に基づいたアイコンと色を取得
  const getSentimentInfo = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case "positive":
        return {
          icon: <SentimentSatisfiedAltIcon fontSize="small" />,
          color: theme.palette.primary.main,
          label: "ポジティブ",
          bgColor: theme.palette.action.selected,
        };
      case "negative":
        return {
          icon: <SentimentVeryDissatisfiedIcon fontSize="small" />,
          color: theme.palette.error.main,
          label: "ネガティブ",
          bgColor: theme.palette.error.light + "30", // Using alpha on hex
        };
      case "neutral":
      default:
        return {
          icon: <SentimentNeutralIcon fontSize="small" />,
          color: theme.palette.warning.main,
          label: "通常",
          bgColor: theme.palette.warning.light + "30", // Using alpha on hex
        };
    }
  };

  // CSVダウンロード機能
  const handleDownloadCSV = async () => {
    try {
      console.log('CSVダウンロード開始...');
      console.log('API URL:', `${api.defaults.baseURL}/admin/chat-history/csv`);
      
      const response = await api.get('/admin/chat-history/csv', {
        responseType: 'blob',
        timeout: 60000, // 60秒のタイムアウト
      });
      
      console.log('CSVレスポンス受信:', response.status, response.data);
      
      // Blobからダウンロードリンクを作成
      const blob = new Blob([response.data], { type: 'text/csv; charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // ファイル名を設定（現在の日時を含む）
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
      link.download = `chat_history_${timestamp}.csv`;
      
      // ダウンロードを実行
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log('チャット履歴のCSVダウンロードが完了しました');
    } catch (error: any) {
      console.error('CSVダウンロードエラー:', error);
      
      if (error.response) {
        console.error('エラーレスポンス:', error.response.status, error.response.data);
        alert(`CSVファイルのダウンロードに失敗しました。ステータス: ${error.response.status}`);
      } else if (error.request) {
        console.error('リクエストエラー:', error.request);
        alert('サーバーに接続できませんでした。ネットワーク接続を確認してください。');
      } else {
        console.error('設定エラー:', error.message);
        alert('CSVファイルのダウンロード中にエラーが発生しました。');
      }
    }
  };

  return (
    <>
      <Box
        sx={{
          mb: 3,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 1,
        }}
      >
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          チャット履歴 {totalCount > 0 && `(${chatHistory.length}/${totalCount}件)`}
        </Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
        <Button
          variant="outlined"
          onClick={() => onRefresh()}
          disabled={isLoading}
        >
          更新
        </Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadCSV}
            disabled={isLoading || chatHistory.length === 0}
            sx={{
              backgroundColor: theme.palette.success.main,
              '&:hover': {
                backgroundColor: theme.palette.success.dark,
              },
            }}
          >
            CSV出力
          </Button>
        </Box>
      </Box>

      {isLoading ? (
        <LoadingIndicator />
      ) : chatHistory.length === 0 ? (
        <EmptyState message="チャット履歴がありません" />
      ) : (
        <TableContainer
          component={Paper}
          sx={{
            boxShadow: "none",
            border: "1px solid",
            borderColor: "divider",
          }}
        >
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: "background.default" }}>
                <TableCell>日時</TableCell>
                <TableCell>管理者の質問</TableCell>
                <TableCell>ボットの回答</TableCell>
                <TableCell>感情</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {chatHistory.map((chat) => (
                <TableRow key={chat.id} hover>
                  <TableCell sx={{ whiteSpace: "nowrap" }}>
                    {formatDate(chat.timestamp)}
                  </TableCell>
                  <TableCell
                    sx={{
                      maxWidth: "200px",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {chat.user_message}
                  </TableCell>
                  <TableCell
                    sx={{
                      maxWidth: "300px",
                      overflow: "hidden",
                    }}
                  >
                    <MarkdownRenderer content={chat.bot_response} />
                  </TableCell>
                  <TableCell>{getSentimentInfo(chat.sentiment).label}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      
      {/* もっと読み込むボタン */}
      {chatHistory.length > 0 && hasMore && onLoadMore && (
        <Box sx={{ mt: 2, display: "flex", justifyContent: "center" }}>
          <Button
            variant="outlined"
            onClick={onLoadMore}
            disabled={isLoading}
            sx={{ minWidth: 200 }}
          >
            {isLoading ? "読み込み中..." : "もっと読み込む"}
          </Button>
        </Box>
      )}
    </>
  );
};

export default ChatHistoryTab;
