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
  Chip,
} from "@mui/material";
import { Resource } from "./types";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";
import api from "../../api";

interface ResourcesTabProps {
  resources: Resource[];
  isLoading: boolean;
  onRefresh: () => void;
}

const ResourcesTab: React.FC<ResourcesTabProps> = ({
  resources,
  isLoading,
  onRefresh,
}) => {
  const handleToggleResourceStatus = async (sourceId: string) => {
    try {
      const response = await api.post(
        `${import.meta.env.VITE_API_URL}/admin/resources/${encodeURIComponent(sourceId)}/toggle`
      );
      console.log("リソース状態切り替え結果:", response.data);
      // リソース情報を再取得
      onRefresh();
    } catch (error) {
      console.error("リソース状態の切り替えに失敗しました:", error);
      alert("リソース状態の切り替えに失敗しました。");
    }
  };

  const handleDeleteResource = async (sourceId: string, name: string) => {
    // 確認ダイアログを表示
    if (
      !confirm(
        `リソース「${name}」を削除してもよろしいですか？この操作は元に戻せません。`
      )
    ) {
      return;
    }

    try {
      console.log(`リソース ${sourceId} を削除中...`);
      const response = await api.delete(
        `${import.meta.env.VITE_API_URL}/admin/resources/${encodeURIComponent(sourceId)}`
      );
      console.log("リソース削除結果:", response.data);
      // リソース情報を再取得
      onRefresh();
    } catch (error) {
      console.error("リソースの削除に失敗しました:", error);
      alert("リソースの削除に失敗しました。");
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
          アップロードリソース
        </Typography>
        <Button variant="outlined" onClick={onRefresh} disabled={isLoading}>
          更新
        </Button>
      </Box>

      {isLoading ? (
        <LoadingIndicator />
      ) : resources.length === 0 ? (
        <EmptyState message="アップロードされたリソースがありません" />
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
                <TableCell>名前</TableCell>
                <TableCell>タイプ</TableCell>
                <TableCell>ページ数</TableCell>
                <TableCell>アップロード者</TableCell>
                <TableCell>アップロード日時</TableCell>
                <TableCell>使用回数</TableCell>
                <TableCell>最終使用日時</TableCell>
                <TableCell>状態</TableCell>
                <TableCell>操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {resources.map((resource, index) => (
                <TableRow
                  key={index}
                  hover
                  sx={{
                    opacity: resource.active ? 1 : 0.5,
                  }}
                >
                  <TableCell>{resource.name}</TableCell>
                  <TableCell>
                    <Chip
                      label={resource.type}
                      size="small"
                      sx={{
                        bgcolor:
                          resource.type === "URL"
                            ? "rgba(54, 162, 235, 0.6)"
                            : resource.type === "PDF"
                              ? "rgba(255, 99, 132, 0.6)"
                              : resource.type === "TXT"
                                ? "rgba(75, 192, 192, 0.6)"
                                : "rgba(255, 206, 86, 0.6)",
                        color: "white",
                        fontWeight: 500,
                      }}
                    />
                  </TableCell>
                  <TableCell>{resource.page_count || "-"}</TableCell>
                  <TableCell>{resource.uploader_name || "不明"}</TableCell>
                  <TableCell>
                    {resource.timestamp
                      ? new Date(resource.timestamp).toLocaleString("ja-JP", {
                        year: "numeric",
                        month: "2-digit",
                        day: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })
                      : "情報なし"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={resource.usage_count || 0}
                      size="small"
                      color={resource.usage_count ? "primary" : "default"}
                    />
                  </TableCell>
                  <TableCell>
                    {resource.last_used
                      ? new Date(resource.last_used).toLocaleString("ja-JP", {
                        year: "numeric",
                        month: "2-digit",
                        day: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                      : "未使用"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={resource.active ? "有効" : "無効"}
                      size="small"
                      color={resource.active ? "success" : "default"}
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="outlined"
                      size="small"
                      sx={{ marginRight: "5px" }}
                      color={resource.active ? "error" : "success"}
                      onClick={() => handleToggleResourceStatus(resource.id)}
                    >
                      {resource.active ? "無効にする" : "有効にする"}
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      color="error"
                      onClick={() =>
                        handleDeleteResource(resource.id, resource.name)
                      }
                    >
                      削除
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </>
  );
};

export default ResourcesTab;
