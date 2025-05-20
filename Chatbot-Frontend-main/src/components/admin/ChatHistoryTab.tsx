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

interface ChatHistoryTabProps {
  chatHistory: ChatHistoryItem[];
  isLoading: boolean;
  onRefresh: () => void;
}

const ChatHistoryTab: React.FC<ChatHistoryTabProps> = ({
  chatHistory,
  isLoading,
  onRefresh,
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
          label: "中立",
          bgColor: theme.palette.warning.light + "30", // Using alpha on hex
        };
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
        }}
      >
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          チャット履歴
        </Typography>
        <Button
          variant="outlined"
          onClick={() => onRefresh()}
          disabled={isLoading}
        >
          更新
        </Button>
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
                <TableCell>ユーザーの質問</TableCell>
                <TableCell>ボットの回答</TableCell>
                <TableCell>カテゴリ</TableCell>
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
                      textOverflow: "ellipsis",
                    }}
                  >
                    {chat.bot_response}
                  </TableCell>
                  <TableCell>{chat.category || "未分類"}</TableCell>
                  <TableCell>{chat.sentiment || "neutral"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </>
  );
};

export default ChatHistoryTab;
