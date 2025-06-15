import React, { useState, useRef, useEffect, useCallback, startTransition } from "react";
import { useNavigate } from "react-router-dom";
import { useCompany } from "./contexts/CompanyContext";
import { useAuth } from "./contexts/AuthContext";
import {
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Avatar,
  AppBar,
  Toolbar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  OutlinedInput,
  FormHelperText,
  Tabs,
  Tab,
  Alert,
  Snackbar,
  Menu,
  MenuItem,
  Tooltip,
} from "@mui/material";
import { useDropzone } from "react-dropzone";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { Cloud } from "@mui/icons-material";
import SendIcon from "@mui/icons-material/Send";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import LinkIcon from "@mui/icons-material/Link";
import LogoutIcon from "@mui/icons-material/Logout";
import SettingsIcon from "@mui/icons-material/Settings";
import BusinessIcon from "@mui/icons-material/Business";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import ChatIcon from "@mui/icons-material/Chat";
import DeleteIcon from "@mui/icons-material/Delete";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import api from "./api";
import DemoLimits from "./components/DemoLimits";
import SourceCitation from "./components/SourceCitation";
import ApplicationForm from "./components/ApplicationForm";
import { useTheme } from "@mui/material/styles";
import { useMediaQuery } from "@mui/material";
import { isValidURL } from './components/admin/utils';
import { GoogleDriveAuth } from './components/GoogleDriveAuth';
import { GoogleDriveFilePicker } from './components/GoogleDriveFilePicker';
import { GoogleAuthStorage } from './utils/googleAuthStorage';

interface Message {
  text: string;
  isUser: boolean;
  source?: string;
}

interface SourceInfo {
  name: string;
  type: string;
  timestamp: string;
  active: boolean;
}

interface KnowledgeBaseData {
  columns: string[];
  preview: Record<string, any>[];
  total_rows?: number;
  sources?: (string | SourceInfo)[];
}

function ChatInterface() {
  const {
    user,
    logout,
    isAdmin,
    isEmployee,
    remainingQuestions,
    isUnlimited,
    updateRemainingQuestions,
    updateRemainingUploads,
    refreshUserData,
  } = useAuth();
  const { companyName, setCompanyName } = useCompany();
  const [messages, setMessages] = useState<Message[]>(() => {
    // ユーザー固有のキーでローカルストレージからチャット履歴を読み込む
    const userId = user?.id || "";
    const savedMessages = localStorage.getItem(`chatMessages_${userId}`);
    return savedMessages && userId ? JSON.parse(savedMessages) : [];
  });
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>("");
  const [isSubmittingUrl, setIsSubmittingUrl] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [uploadTab, setUploadTab] = useState(-1);
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBaseData | null>(
    null
  );
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [showLimitReachedAlert, setShowLimitReachedAlert] =
    useState<boolean>(false);
  // 従来の社員情報関連の状態（後方互換性のため）
  const [employeeId, setEmployeeId] = useState<string>(() => {
    return user?.id || localStorage.getItem("employeeId") || "";
  });
  const [employeeName, setEmployeeName] = useState<string>(() => {
    return user?.name || localStorage.getItem("employeeName") || "";
  });
  const [showEmployeeModal, setShowEmployeeModal] = useState<boolean>(false);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isTablet = useMediaQuery(theme.breakpoints.between("sm", "md"));
  const [confirmClearOpen, setConfirmClearOpen] = useState<boolean>(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedTab, setSelectedTab] = useState(0);
  const [url, setUrl] = useState("");
  const [applicationOpen, setApplicationOpen] = useState(false);
  const [upgradeSuccess, setUpgradeSuccess] = useState(false);
  
  // Google Drive関連のstate
  const [driveAccessToken, setDriveAccessToken] = useState<string>(() => {
    // 初期化時に保存された認証状態を復元
    return GoogleAuthStorage.getAccessToken() || '';
  });
  const [drivePickerOpen, setDrivePickerOpen] = useState(false);
  const [driveAuthError, setDriveAuthError] = useState<string>('');

  // メッセージエリアのスタイルを改善 - モバイル対応を強化
  const messageContainerStyles = {
    display: "flex",
    flexDirection: "column",
    flexGrow: 1,
    overflow: "auto",
    p: { xs: 1, sm: 2, md: 3 },
    pb: { xs: 16, sm: 14, md: 14 }, // モバイルでの余白をさらに増加
    background: "rgba(248, 250, 252, 0.9)",
    backgroundImage:
      "radial-gradient(rgba(37, 99, 235, 0.04) 1px, transparent 0)",
    backgroundSize: "20px 20px",
    backdropFilter: "blur(8px)",
    position: "relative", // 位置決め用に追加
    msOverflowStyle: 'none', // IE and Edge
    scrollbarWidth: 'none', // Firefox
    '&::-webkit-scrollbar': {
      display: 'none' // Chrome, Safari, Opera
    },
  };

  // メッセージバブルのスタイルを改善 - モバイル対応を強化
  const userMessageStyles = {
    bgcolor: "primary.main",
    color: "white",
    p: { xs: 1.2, sm: 1.5, md: 2 },
    px: { xs: 1.5, sm: 2 },
    borderRadius: { xs: "12px 12px 4px 12px", sm: "16px 16px 6px 16px" }, // モバイルで少し小さく
    maxWidth: { xs: "85%", sm: "75%", md: "65%" }, // モバイルでより幅を広く
    wordBreak: "break-word",
    boxShadow: "0 2px 8px rgba(37, 99, 235, 0.2)",
    alignSelf: "flex-end",
    mb: { xs: 1, sm: 2 }, // モバイルで上下の余白をさらに小さく
    animation: "fadeIn 0.3s ease-out",
    fontSize: { xs: "0.85rem", sm: "0.95rem" }, // モバイルでフォントサイズを小さく
    lineHeight: 1.5,
    transition: "all 0.2s ease",
    "&:hover": {
      boxShadow: "0 4px 16px rgba(37, 99, 235, 0.3)",
      transform: "translateY(-1px)",
    },
    position: "relative",
    "&::after": {
      content: '""',
      position: "absolute",
      right: "-6px", // 吹き出しの三角形を少し小さく
      bottom: "0",
      width: "12px", // 吹き出しの三角形を少し小さく
      height: "12px", // 吹き出しの三角形を少し小さく
      background: "primary.main",
      clipPath: "polygon(0 0, 100% 100%, 0 100%)",
    },
    backgroundImage: "linear-gradient(135deg, #2563eb, #3b82f6)",
    backdropFilter: "blur(4px)",
    border: "1px solid rgba(255, 255, 255, 0.2)",
  };

  const botMessageStyles = {
    bgcolor: "#FFFFFF",
    p: { xs: 1.2, sm: 1.5, md: 2 },
    px: { xs: 1.5, sm: 2 },
    borderRadius: { xs: "12px 12px 12px 4px", sm: "16px 16px 16px 6px" }, // モバイルで少し小さく
    maxWidth: { xs: "85%", sm: "75%", md: "65%" }, // モバイルでより幅を広く
    wordBreak: "break-word",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.06)",
    alignSelf: "flex-start",
    mb: { xs: 1, sm: 2 }, // モバイルで上下の余白をさらに小さく
    animation: "fadeIn 0.3s ease-out",
    fontSize: { xs: "0.85rem", sm: "0.95rem" }, // モバイルでフォントサイズを小さく
    lineHeight: 1.5,
    transition: "all 0.2s ease",
    "&:hover": {
      boxShadow: "0 4px 14px rgba(0, 0, 0, 0.1)",
      transform: "translateY(-1px)",
    },
    position: "relative",
    "&::before": {
      content: '""',
      position: "absolute",
      left: "-6px", // 吹き出しの三角形を少し小さく
      bottom: "0",
      width: "12px", // 吹き出しの三角形を少し小さく
      height: "12px", // 吹き出しの三角形を少し小さく
      background: "linear-gradient(135deg, #FFFFFF, #F8FAFC)",
      clipPath: "polygon(100% 0, 100% 100%, 0 100%)",
      borderRadius: "0 0 0 4px",
      boxShadow: "-1px 1px 2px rgba(0, 0, 0, 0.05)",
    },
    backgroundImage: "linear-gradient(135deg, #FFFFFF, #F8FAFC)",
    border: "1px solid rgba(37, 99, 235, 0.08)",
    backdropFilter: "blur(4px)",
  };

  // メッセージ段落用のスタイル
  const paragraphStyles = {
    mb: 1.5,
    lineHeight: 1.6,
    fontSize: { xs: "0.85rem", sm: "0.95rem" },
  };

  // ユーザーメッセージ段落用のスタイル
  const userParagraphStyles = {
    ...paragraphStyles,
    color: "white",
  };

  // ボットメッセージ段落用のスタイル
  const botParagraphStyles = {
    ...paragraphStyles,
    color: "text.primary",
  };

  // チャット入力エリアのスタイルを改善 - モバイル対応を強化
  const chatInputContainerStyles = {
    position: "fixed",
    bottom: 0,
    left: 0,
    right: 0,
    boxShadow: "0 -4px 20px rgba(0, 0, 0, 0.08)",
    backdropFilter: "blur(16px)",
    background: "rgba(255, 255, 255, 0.95)",
    borderTop: "1px solid rgba(37, 99, 235, 0.1)",
    p: { xs: 1.5, sm: 2, md: 2.5 },
    zIndex: 99, // ヘッダーより下だが他の要素より上に表示
    borderTopLeftRadius: { xs: "20px", sm: "24px" },
    borderTopRightRadius: { xs: "20px", sm: "24px" },
    transition: "all 0.3s ease",
    WebkitTransform: 'translate3d(0,0,0)', // iOSでの表示問題を修正
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // メッセージが更新されたらローカルストレージに保存
  useEffect(() => {
    if (user?.id) {
      localStorage.setItem(`chatMessages_${user.id}`, JSON.stringify(messages));
    }
    scrollToBottom();
  }, [messages, user?.id]);

  // ユーザーが変わったらメッセージをクリア
  useEffect(() => {
    if (user?.id) {
      const savedMessages = localStorage.getItem(`chatMessages_${user.id}`);
      setMessages(savedMessages ? JSON.parse(savedMessages) : []);
    } else {
      setMessages([]);
    }
  }, [user?.id]);

  useEffect(() => {
    // 初期ロード時に知識ベースの状態を確認
    fetchKnowledgeBase();
  }, []);

  const fetchKnowledgeBase = async () => {
    try {
      const response = await api.get(`/knowledge-base`);
      if (response.data.columns) {
        setKnowledgeBase({
          ...response.data,
          preview: response.data.preview || [],
          columns: response.data.columns || [],
        });
      }
    } catch (error) {
      console.error("知識ベースの取得に失敗しました:", error);
    }
  };

  const { getRootProps, getInputProps } = useDropzone({
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
      "application/vnd.ms-excel": [".xls"],
      "application/pdf": [".pdf"],
      "video/x-msvideo": [".avi"], // AVI
      "video/mp4": [".mp4"], // MP4
      "video/webm": [".webm"], // WebM
    },
    maxFiles: 1,
    disabled: isEmployee, // employeeアカウントではドラッグ&ドロップを無効化
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setIsUploading(true);
        setUploadProgress("ファイルを準備中...");
        const formData = new FormData();
        const file = acceptedFiles[0];
        // Ensure the file is properly appended with the correct field name expected by FastAPI
        formData.append("file", file, file.name);

        try {
          console.log("ファイルアップロード開始:", file.name);

          // ファイル拡張子を取得
          const fileExt = acceptedFiles[0].name.split(".").pop()?.toLowerCase();

          // PDFファイルの場合はOCR処理の可能性があることをユーザーに通知
          if (fileExt === "pdf") {
            const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
            const file = acceptedFiles[0];
            if (file.size > MAX_FILE_SIZE) {
              setMessages((prev) => [
                ...prev,
                {
                  text: `エラー: ファイル「${file.name}」はサイズ制限（10MB）を超えています。別のファイルを選択してください。`,
                  isUser: false,
                },
              ]);
              return; // Stop processing
            }

            setUploadProgress(
              "PDFファイルを処理中... OCR処理が必要な場合は時間がかかることがあります"
            );

            // 既存のエラーメッセージを削除して処理中メッセージを追加
            setMessages((prev) => {
              const filteredMessages = prev.filter(
                (msg) =>
                  !msg.text.startsWith("エラー:") &&
                  !msg.text.includes("処理中")
              );
              return [
                ...filteredMessages,
                {
                  text: `PDFファイル「${acceptedFiles[0].name}」を処理中です。OCR処理が必要な場合は完了までに時間がかかることがあります。図形やグラフなども認識して処理します。しばらくお待ちください...`,
                  isUser: false,
                },
              ];
            });
          } else {
            setUploadProgress(
              `${fileExt?.toUpperCase() || ""}ファイルを処理中...`
            );
          }

          // アップロードリクエストを送信
          const response = await api.post(`/upload-knowledge`, formData);
          console.log("アップロード成功:", response.data);
          setKnowledgeBase({
            ...response.data,
            preview: response.data.preview || [],
            columns: response.data.columns || [],
          });

          // 残りアップロード回数を更新
          if (!isUnlimited && response.data.remaining_uploads !== undefined) {
            updateRemainingUploads(response.data.remaining_uploads);
          }

          // 既存のエラーメッセージと処理中メッセージを削除
          setMessages((prev) =>
            prev.filter(
              (msg) =>
                !msg.text.startsWith("エラー:") && !msg.text.includes("処理中")
            )
          );

          setMessages((prev) => [
            ...prev,
            {
              text: `${companyName}の情報が正常に更新されました。`,
              isUser: false,
            },
          ]);
        } catch (error: any) {
          console.error("アップロードエラー:", error.response || error);

          // エラーメッセージの取得
          let errorMessage = "ファイルのアップロードに失敗しました。";
          if (error.response?.data?.detail) {
            errorMessage = error.response.data.detail;
            
            // 特定のエラーメッセージの場合はユーザーフレンドリーなメッセージに変更
            if (errorMessage.includes("データ型エラー")) {
              errorMessage = "ファイルの処理中にエラーが発生しました。別のファイルを試すか、管理者にお問い合わせください。";
            } else if (errorMessage.includes("'int' object has no attribute 'strip'")) {
              errorMessage = "ファイルの処理中にエラーが発生しました。別のファイルを試すか、管理者にお問い合わせください。";
            }
          } else if (error.message) {
            errorMessage = error.message;
          }

          // タイムアウトエラーの場合は特別なメッセージを表示
          if (error.code === "ECONNABORTED") {
            errorMessage =
              "リクエストがタイムアウトしました。PDFまたは動画ファイルが大きすぎるか、処理に時間がかかっている可能性があります。ファイルを分割・圧縮するか、テキスト抽出済みのPDFや短く編集した動画をご利用ください。";
            // "リクエストがタイムアウトしました。PDFファイルが大きすぎるか、OCR処理に時間がかかっています。ファイルを分割するか、テキスト抽出済みのPDFを使用してください。";
          } else if (error.response?.status === 502) {
            return setMessages((prev) => {
              const filteredMessages = prev.filter(
                (msg) =>
                  !msg.text.startsWith("エラー:") &&
                  !msg.text.includes("処理中")
              );
              return [
                ...filteredMessages,
                {
                  text: `${companyName}の情報が正常に更新されました。`,
                  isUser: false,
                },
              ];
            });
          } else if (error.response?.status === 408) {
            errorMessage =
              "処理がタイムアウトしました。ファイルが大きすぎるか、複雑すぎる可能性があります。ファイルを分割するか、より小さなファイルを使用してください。";
          } else if (
            error.response?.status === 400 &&
            error.response?.data?.detail?.includes("大きすぎます")
          ) {
            errorMessage = error.response.data.detail;
            // ファイルサイズが大きすぎる場合のガイダンスを追加
            errorMessage +=
              " 大きなPDFファイルは、Adobe Acrobatなどのツールでページごとに分割してから、個別にアップロードしてください。";
          }

          // 既存のエラーメッセージと処理中メッセージを削除して新しいメッセージを追加
          setMessages((prev) => {
            const filteredMessages = prev.filter(
              (msg) =>
                !msg.text.startsWith("エラー:") && !msg.text.includes("処理中")
            );
            return [
              ...filteredMessages,
              {
                text: `エラー: ${errorMessage}`,
                isUser: false,
              },
            ];
          });
        } finally {
          setIsUploading(false);
          setUploadProgress("");
          setUploadTab(-1);
        }
      }
    },
  });

  // 社員情報を保存
  const saveEmployeeInfo = useCallback((id: string, name: string) => {
    setEmployeeId(id);
    setEmployeeName(name);
    localStorage.setItem("employeeId", id);
    localStorage.setItem("employeeName", name);
    setShowEmployeeModal(false);
  }, []);

  // URLを送信する関数
  const handleSubmitUrl = async () => {
    if (!urlInput.trim()) return;

    setIsSubmittingUrl(true);
    try {
      const response = await api.post(`/submit-url`, {
        url: urlInput.trim(),
      });

      console.log("URL送信成功:", response.data);
      setKnowledgeBase({
        ...response.data,
        preview: response.data.preview || [],
        columns: response.data.columns || [],
      });

      // 残りアップロード回数を更新
      if (!isUnlimited && response.data.remaining_uploads !== undefined) {
        updateRemainingUploads(response.data.remaining_uploads);
      }

      // 既存のエラーメッセージを削除
      setMessages((prev) =>
        prev.filter((msg) => !msg.text.startsWith("エラー:"))
      );

      setMessages((prev) => [
        ...prev,
        {
          text: `${urlInput} からの情報が正常に取得されました。`,
          isUser: false,
        },
      ]);

    } catch (error: any) {
      console.error("URL送信エラー:", error.response || error);

      // エラーメッセージの取得
      let errorMessage = "URLの処理に失敗しました。";
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
        
        // 特定のエラーメッセージの場合はユーザーフレンドリーなメッセージに変更
        if (errorMessage.includes("データ型エラー")) {
          errorMessage = "URLの処理中にエラーが発生しました。別のURLを試すか、管理者にお問い合わせください。";
        } else if (errorMessage.includes("'int' object has no attribute 'strip'")) {
          errorMessage = "URLの処理中にエラーが発生しました。別のURLを試すか、管理者にお問い合わせください。";
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      // 既存のエラーメッセージを削除して新しいメッセージを追加
      setMessages((prev) => {
        const filteredMessages = prev.filter(
          (msg) => !msg.text.startsWith("エラー:")
        );
        return [
          ...filteredMessages,
          {
            text: `エラー: ${errorMessage}`,
            isUser: false,
          },
        ];
      });
    } finally {
      setIsSubmittingUrl(false);
      startTransition(() => {
        // 入力をクリア
        setUrlInput("");
        setUploadTab(-1);
      })
    }
  };

  // タブ変更ハンドラ
  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setUploadTab(newValue);
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    // 利用制限チェック（無制限アカウントでない場合）
    if (
      !isUnlimited &&
      remainingQuestions !== null &&
      remainingQuestions <= 0
    ) {
      setShowLimitReachedAlert(true);
      return;
    }

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { text: userMessage, isUser: true }]);
    setIsLoading(true);

    try {
      const response = await api.post(`/chat`, {
        text: userMessage,
        employee_id: user?.id,
        employee_name: user?.name,
      });

      // ボットの応答を追加（ソース情報付き）
      setMessages((prev) => [
        ...prev,
        {
          text: response.data.response,
          isUser: false,
          source: response.data.source || "",
        },
      ]);

      // 利用制限の表示を更新（無制限アカウントでない場合）
      if (!isUnlimited && response.data.remaining_questions !== undefined) {
        console.log("バックエンドからの応答:", {
          remaining_questions: response.data.remaining_questions,
          limit_reached: response.data.limit_reached,
          response_data: response.data
        });
        
        // AuthContextの状態を更新
        updateRemainingQuestions(response.data.remaining_questions);

        // 制限に達した場合はアラートを表示
        if (response.data.limit_reached) {
          console.log("質問制限に達しました");
          setShowLimitReachedAlert(true);
        }
      } else {
        console.log("利用制限の更新をスキップ:", {
          isUnlimited,
          remaining_questions: response.data.remaining_questions,
          response_data: response.data
        });
      }
    } catch (error: any) {
      console.error("チャットエラー:", error.response || error);

      // エラーメッセージの取得
      let errorMessage =
        "すみません、エラーが発生しました。もう一度お試しください。";
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }

      // 利用制限エラーの場合は特別な処理
      if (
        error.response?.status === 403 &&
        error.response?.data?.detail?.includes("質問回数制限")
      ) {
        // 利用制限に達した場合はアラートを表示
        setShowLimitReachedAlert(true);
        updateRemainingQuestions(0);
        errorMessage = error.response.data.detail;
      }

      setMessages((prev) => [
        ...prev,
        {
          text: errorMessage,
          isUser: false,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoToAdmin = () => {
    navigate("/admin");
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleClearChat = () => {
    setConfirmClearOpen(true);
    handleMenuClose();
  };

  const confirmClearChat = () => {
    if (user?.id) {
      localStorage.removeItem(`chatMessages_${user.id}`);
    }
    setMessages([]);
    setConfirmClearOpen(false);
  };

  const cancelClearChat = () => {
    setConfirmClearOpen(false);
  };

  const handleCloseAlert = () => {
    setShowLimitReachedAlert(false);
  };

  const handleOpenApplication = () => {
    setApplicationOpen(true);
  };

  const handleCloseApplication = () => {
    setApplicationOpen(false);
  };

  // Google Drive関連のハンドラー
  const handleDriveAuthSuccess = (accessToken: string) => {
    setDriveAccessToken(accessToken);
    setDriveAuthError('');
    console.log('Google Drive認証成功');
  };

  const handleDriveAuthError = (error: string) => {
    setDriveAuthError(error);
    console.error('Google Drive認証エラー:', error);
  };

  // トークンの有効期限をチェックするeffect
  useEffect(() => {
    if (!driveAccessToken) return;

    const checkTokenExpiry = () => {
      if (GoogleAuthStorage.willExpireSoon(5)) { // 5分前に警告
        console.log('Google Driveトークンの有効期限が近づいています');
        setDriveAuthError('認証の有効期限が近づいています。再度認証してください。');
        // トークンを無効化してユーザーに再認証を促す
        setDriveAccessToken('');
        GoogleAuthStorage.clearAuthData();
      }
    };

    // 1分ごとにチェック
    const interval = setInterval(checkTokenExpiry, 60000);
    
    // 初回チェック
    checkTokenExpiry();

    return () => clearInterval(interval);
  }, [driveAccessToken]);

  const handleDriveFileSelect = async (file: any) => {
    try {
      setIsUploading(true);
      setUploadProgress("Google Driveからファイルを取得中...");

      console.log('選択されたファイル:', file);

      // Google Driveファイルをサーバーに送信
      const formData = new FormData();
      formData.append('file_id', file.id);
      formData.append('access_token', driveAccessToken);
      formData.append('file_name', file.name);
      formData.append('mime_type', file.mimeType);

      setUploadProgress("ファイルを処理中...");

      const response = await api.post('/upload-from-drive', formData);
      
      console.log("Google Driveアップロード成功:", response.data);
      setKnowledgeBase({
        ...response.data,
        preview: response.data.preview || [],
        columns: response.data.columns || [],
      });

      // 残りアップロード回数を更新
      if (!isUnlimited && response.data.remaining_uploads !== undefined) {
        updateRemainingUploads(response.data.remaining_uploads);
      }

      setMessages((prev) => [
        ...prev,
        {
          text: `Google Driveから「${file.name}」が正常に読み込まれました。`,
          isUser: false,
        },
      ]);

      setDrivePickerOpen(false);
    } catch (error: any) {
      console.error("Google Driveアップロードエラー:", error);
      
      let errorMessage = "Google Driveからのファイル読み込みに失敗しました。";
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }

      setMessages((prev) => [
        ...prev,
        {
          text: `エラー: ${errorMessage}`,
          isUser: false,
        },
      ]);
    } finally {
      setIsUploading(false);
      setUploadProgress("");
    }
  };

  // AppBarコンポーネントのスタイル修正 - メニューボタン追加
  const renderAppBar = () => (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        boxShadow: "0 4px 20px rgba(37, 99, 235, 0.15)",
        background: "linear-gradient(135deg, #2563eb, #3b82f6)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.15)",
        borderRadius: "0 0 20px 20px",
        mb: 1,
        width: "100%",
        zIndex: 100,
        top: 0,
      }}
    >
      <Toolbar
        sx={{
          minHeight: { xs: "56px", sm: "64px" },
          px: { xs: 2, sm: 3 },
          justifyContent: "space-between",
        }}
      >
        <Box display="flex" alignItems="center">
          <Avatar
            sx={{
              background: "rgba(255, 255, 255, 0.2)",
              mr: 1.5,
              width: { xs: 34, sm: 40 },
              height: { xs: 34, sm: 40 },
              backdropFilter: "blur(4px)",
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.12)",
              border: "2px solid rgba(255, 255, 255, 0.4)",
            }}
          >
            <ChatIcon
              sx={{
                color: "white",
                fontSize: { xs: "1.3rem", sm: "1.5rem" },
              }}
            />
          </Avatar>
          <Typography
            variant={isMobile ? "subtitle1" : "h6"}
            component="div"
            sx={{
              fontWeight: 700,
              fontSize: { xs: "1.1rem", sm: "1.25rem" },
              color: "white",
              textShadow: "0 1px 3px rgba(0, 0, 0, 0.15)",
              letterSpacing: "0.01em",
            }}
          >
            {companyName || "ワークメイトAI"}
          </Typography>
        </Box>
        <Box display="flex" alignItems="center">
          {messages.length > 0 && (
            <Tooltip title="チャット履歴をクリア" placement="bottom">
              <IconButton
                color="inherit"
                onClick={handleClearChat}
                sx={{
                  ml: { xs: 0.5, sm: 0.75 },
                  bgcolor: "rgba(255, 255, 255, 0.15)",
                  backdropFilter: "blur(4px)",
                  p: { xs: 1.2, sm: 1.5 },
                  width: { xs: 40, sm: 46 },
                  height: { xs: 40, sm: 46 },
                  "&:hover": {
                    bgcolor: "rgba(255, 255, 255, 0.25)",
                    transform: "translateY(-2px)",
                    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
                  },
                  transition: "all 0.2s ease",
                  boxShadow: "0 2px 6px rgba(0, 0, 0, 0.12)",
                  borderRadius: "14px",
                  border: "1px solid rgba(255, 255, 255, 0.3)",
                }}
              >
                <DeleteIcon sx={{ fontSize: { xs: "1.3rem", sm: "1.5rem" } }} />
              </IconButton>
            </Tooltip>
          )}
          <IconButton
            color="inherit"
            onClick={handleMenuOpen}
            sx={{
              ml: { xs: 0.5, sm: 0.75 },
              bgcolor: "rgba(255, 255, 255, 0.15)",
              backdropFilter: "blur(4px)",
              p: { xs: 1.2, sm: 1.5 },
              width: { xs: 40, sm: 46 },
              height: { xs: 40, sm: 46 },
              "&:hover": {
                bgcolor: "rgba(255, 255, 255, 0.25)",
                transform: "translateY(-2px)",
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
              },
              transition: "all 0.2s ease",
              boxShadow: "0 2px 6px rgba(0, 0, 0, 0.12)",
              borderRadius: "14px",
              border: "1px solid rgba(255, 255, 255, 0.3)",
            }}
          >
            <MoreVertIcon sx={{ fontSize: { xs: "1.3rem", sm: "1.5rem" } }} />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            PaperProps={{
              elevation: 3,
              sx: {
                mt: 1.5,
                borderRadius: "12px",
                boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
                overflow: "visible",
                filter: "drop-shadow(0px 2px 8px rgba(0,0,0,0.12))",
                "&:before": {
                  content: '""',
                  display: "block",
                  position: "absolute",
                  top: 0,
                  right: 14,
                  width: 10,
                  height: 10,
                  bgcolor: "background.paper",
                  transform: "translateY(-50%) rotate(45deg)",
                  zIndex: 0,
                },
              },
            }}
            transformOrigin={{ horizontal: "right", vertical: "top" }}
            anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
          >
            {messages.length > 0 && (
              <MenuItem onClick={handleClearChat} sx={{ gap: 1 }}>
                <DeleteIcon fontSize="small" color="error" />
                <Typography>チャット履歴をクリア</Typography>
              </MenuItem>
            )}
            <MenuItem onClick={() => navigate("/guide")} sx={{ gap: 1 }}>
              <HelpOutlineIcon fontSize="small" color="primary" />
              <Typography>使い方ガイド</Typography>
            </MenuItem>
            {(isAdmin || (user && user.role === "user")) && (
              <MenuItem onClick={handleGoToAdmin} sx={{ gap: 1 }}>
                <AdminPanelSettingsIcon fontSize="small" color="primary" />
                <Typography>管理画面</Typography>
              </MenuItem>
            )}
            <MenuItem onClick={() => navigate("/settings?referrer=index")} sx={{ gap: 1 }}>
              <SettingsIcon fontSize="small" color="primary" />
              <Typography>設定</Typography>
            </MenuItem>
            <MenuItem onClick={logout} sx={{ gap: 1 }}>
              <LogoutIcon fontSize="small" color="primary" />
              <Typography>ログアウト</Typography>
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );

  // メッセージエリアのレンダリング部分
  const renderChatMessages = () => (
    <Box sx={{
      ...messageContainerStyles,
      pt: { xs: 2, sm: 2.5, md: 3 }, // スクロール領域の上部パディングを追加
      height: '100%', // 高さを100%に設定
      WebkitOverflowScrolling: 'touch', // iOSのスムーススクロール対応
      overscrollBehavior: 'contain', // スクロールの慣性を制御
    }}>
      {messages.length === 0 ? (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            height: "100%",
            textAlign: "center",
            px: 3,
            opacity: 0.8,
          }}
        >
          <ChatIcon
            sx={{
              fontSize: { xs: "3rem", sm: "4rem", md: "5rem" },
              color: "primary.main",
              opacity: 0.2,
              mb: 2,
            }}
          />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: "text.secondary",
              fontSize: { xs: "1rem", sm: "1.25rem" },
              mb: 1,
            }}
          >
            ワークメイトAIへようこそ
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: "text.secondary",
              maxWidth: "500px",
              fontSize: { xs: "0.8rem", sm: "0.9rem" },
            }}
          >
            質問やお手伝いが必要なことがあれば、お気軽にメッセージをお送りください。
          </Typography>
        </Box>
      ) : (
        messages.map((message, index) => (
          <Box
            key={index}
            sx={message.isUser ? userMessageStyles : botMessageStyles}
          >
            <Typography component="div">
              {message.text.split("\n\n").map((paragraph, pIndex) => {
                const isLastParagraph =
                  pIndex === message.text.split("\n\n").length - 1;
                return (
                  <Typography
                    key={pIndex}
                    component="p"
                    sx={{
                      ...(message.isUser
                        ? userParagraphStyles
                        : botParagraphStyles),
                      mb: isLastParagraph ? 0 : 1.5,
                    }}
                  >
                    {paragraph.split("\n").map((line, lIndex) => {
                      const isLastLine =
                        lIndex === paragraph.split("\n").length - 1;
                      return (
                        <React.Fragment key={lIndex}>
                          {line}
                          {!isLastLine && <br />}
                        </React.Fragment>
                      );
                    })}
                  </Typography>
                );
              })}
            </Typography>
            {message.source && <SourceCitation source={message.source} />}
          </Box>
        ))
      )}
      <div ref={messagesEndRef} />
    </Box>
  );

  // 入力エリアのレンダリング部分
  const renderChatInputField = () => (
    <Box sx={chatInputContainerStyles}>
      <Box
        sx={{
          maxWidth: { xs: "95%", sm: "90%", md: "85%", lg: "900px" },
          mx: "auto",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* アップロードボタン部分 - employeeアカウントでは非表示 */}
        {!isEmployee && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              gap: { xs: 1, sm: 1.5 },
              mb: { xs: 0.7, sm: 0.8 },
              mx: "auto",
            }}
          >
            <Button
              variant="outlined"
              color="primary"
              onClick={() => setUploadTab(0)}
              startIcon={
                <CloudUploadIcon
                  sx={{ fontSize: { xs: "0.65rem", sm: "0.7rem" } }}
                />
              }
              size="small"
              sx={{
                py: { xs: 0.2, sm: 0.2 },
                px: { xs: 0.7, sm: 0.8 },
                minHeight: 0,
                minWidth: 0,
                height: { xs: "22px", sm: "24px" },
                borderRadius: "12px",
                fontWeight: 500,
                fontSize: { xs: "0.6rem", sm: "0.65rem" },
                textTransform: "none",
                backgroundColor: "rgba(255, 255, 255, 0.9)",
                backdropFilter: "blur(8px)",
                borderColor: "rgba(37, 99, 235, 0.15)",
                color: "#3b82f6",
                boxShadow: "0 1px 2px rgba(37, 99, 235, 0.03)",
                "&:hover": {
                  borderColor: "rgba(37, 99, 235, 0.3)",
                  backgroundColor: "rgba(237, 242, 255, 0.8)",
                  transform: "translateY(-1px)",
                  boxShadow: "0 2px 4px rgba(37, 99, 235, 0.08)",
                },
                transition: "all 0.2s ease",
              }}
            >
              ファイル
            </Button>
            <Button
              variant="outlined"
              color="primary"
              onClick={() => setUploadTab(1)}
              startIcon={
                <LinkIcon sx={{ fontSize: { xs: "0.65rem", sm: "0.7rem" } }} />
              }
              size="small"
              sx={{
                py: { xs: 0.2, sm: 0.2 },
                px: { xs: 0.7, sm: 0.8 },
                minHeight: 0,
                minWidth: 0,
                height: { xs: "22px", sm: "24px" },
                borderRadius: "12px",
                fontWeight: 500,
                fontSize: { xs: "0.6rem", sm: "0.65rem" },
                textTransform: "none",
                backgroundColor: "rgba(255, 255, 255, 0.9)",
                backdropFilter: "blur(8px)",
                borderColor: "rgba(37, 99, 235, 0.15)",
                color: "#3b82f6",
                boxShadow: "0 1px 2px rgba(37, 99, 235, 0.03)",
                "&:hover": {
                  borderColor: "rgba(37, 99, 235, 0.3)",
                  backgroundColor: "rgba(237, 242, 255, 0.8)",
                  transform: "translateY(-1px)",
                  boxShadow: "0 2px 4px rgba(37, 99, 235, 0.08)",
                },
                transition: "all 0.2s ease",
              }}
            >
              URL
            </Button>
            <Button
              variant="outlined"
              color="primary"
              onClick={() => setUploadTab(2)}
              startIcon={
                <Cloud sx={{ fontSize: { xs: "0.65rem", sm: "0.7rem" } }} />
              }
              size="small"
              sx={{
                py: { xs: 0.2, sm: 0.2 },
                px: { xs: 0.7, sm: 0.8 },
                minHeight: 0,
                minWidth: 0,
                height: { xs: "22px", sm: "24px" },
                borderRadius: "12px",
                fontWeight: 500,
                fontSize: { xs: "0.6rem", sm: "0.65rem" },
                textTransform: "none",
                backgroundColor: "rgba(255, 255, 255, 0.9)",
                backdropFilter: "blur(8px)",
                borderColor: "rgba(37, 99, 235, 0.15)",
                color: "#3b82f6",
                boxShadow: "0 1px 2px rgba(37, 99, 235, 0.03)",
                "&:hover": {
                  borderColor: "rgba(37, 99, 235, 0.3)",
                  backgroundColor: "rgba(237, 242, 255, 0.8)",
                  transform: "translateY(-1px)",
                  boxShadow: "0 2px 4px rgba(37, 99, 235, 0.08)",
                },
                transition: "all 0.2s ease",
              }}
            >
              Drive
            </Button>
          </Box>
        )}

        {/* employeeアカウント向けのメッセージ */}
        {isEmployee && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              mb: { xs: 0.7, sm: 0.8 },
              mx: "auto",
            }}
          >
            <Alert
              severity="info"
              sx={{
                fontSize: { xs: "0.7rem", sm: "0.8rem" },
                py: 0.5,
                px: 1.5,
                borderRadius: "12px",
                backgroundColor: "rgba(33, 150, 243, 0.08)",
                border: "1px solid rgba(33, 150, 243, 0.15)",
                "& .MuiAlert-icon": {
                  fontSize: { xs: "0.8rem", sm: "1rem" },
                },
              }}
            >
              ファイルアップロードは管理者のみ利用できます
            </Alert>
          </Box>
        )}

        {/* アップロード・URL送信モーダル */}
        <Dialog
          open={uploadTab !== -1}
          onClose={() => setUploadTab(-1)}
          PaperProps={{
            sx: {
              borderRadius: 3,
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
              maxWidth: "500px",
              width: "100%",
            },
          }}
        >
          <DialogTitle
            sx={{
              pb: 1,
              pt: 2.5,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <Typography
              component="div"
              variant="h6"
              sx={{ fontWeight: 700, color: "primary.main" }}
            >
              {uploadTab === 0 ? "ファイルをアップロード" : uploadTab === 1 ? "URLを送信" : "Google Drive"}
            </Typography>
            <IconButton
              onClick={() => setUploadTab(-1)}
              sx={{
                color: "text.secondary",
                "&:hover": { color: "primary.main" },
              }}
            >
              <span aria-hidden="true" style={{ fontSize: "1.2rem" }}>
                &times;
              </span>
            </IconButton>
          </DialogTitle>
          <DialogContent sx={{ py: 2 }}>
            {uploadTab === 0 && (
              <Box>
                <Box
                  {...getRootProps()}
                  sx={{
                    border: "2px dashed rgba(37, 99, 235, 0.3)",
                    borderRadius: "16px",
                    p: { xs: 2, sm: 3.5 }, // モバイルでパディングを小さく
                    mb: 2,
                    textAlign: "center",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    backgroundColor: "rgba(237, 242, 255, 0.5)",
                    "&:hover": {
                      borderColor: "primary.main",
                      backgroundColor: "rgba(237, 242, 255, 0.8)",
                      transform: "translateY(-2px)",
                      boxShadow: "0 4px 12px rgba(37, 99, 235, 0.15)",
                    },
                  }}
                >
                  <input {...getInputProps()} />
                  <CloudUploadIcon
                    color="primary"
                    sx={{
                      fontSize: { xs: "2.5rem", sm: "3.5rem" },
                      mb: 2,
                      opacity: 0.9,
                    }} // モバイルでアイコンを小さく
                  />
                  <Typography
                    variant="body1"
                    sx={{ fontWeight: 600, mb: 1, color: "primary.main" }}
                  >
                    ファイルをドロップまたはクリックして選択
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Excel(.xlsx, .xls) または PDF(.pdf) ファイル
                  </Typography>
                </Box>
                {(isUploading || uploadProgress) && (
                  <Box sx={{ textAlign: "center", my: 2 }}>
                    {isUploading ? (
                      <CircularProgress size={32} sx={{ mb: 1.5 }} />
                    ) : null}
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ fontWeight: 500 }}
                    >
                      {uploadProgress}
                    </Typography>
                  </Box>
                )}
              </Box>
            )}

            {uploadTab === 1 && (
              <Box>
                <TextField
                  fullWidth
                  placeholder="https://example.com/document.pdf"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  variant="outlined"
                  sx={{
                    mb: 3,
                    mt: 1,
                    "& .MuiOutlinedInput-root": {
                      borderRadius: "12px",
                      "& fieldset": {
                        borderColor: "rgba(37, 99, 235, 0.2)",
                        borderWidth: "1.5px",
                      },
                      "&:hover fieldset": {
                        borderColor: "rgba(37, 99, 235, 0.4)",
                      },
                      "&.Mui-focused fieldset": {
                        borderColor: "primary.main",
                        borderWidth: "2px",
                      },
                    },
                  }}
                  InputProps={{
                    startAdornment: (
                      <LinkIcon color="primary" sx={{ mr: 1, opacity: 0.7 }} />
                    ),
                  }}
                />
                <Button
                  variant="contained"
                  color="primary"
                  disabled={!isValidURL(urlInput.trim()) || isSubmittingUrl}
                  onClick={handleSubmitUrl}
                  fullWidth
                  sx={{
                    py: 1.2,
                    borderRadius: "12px",
                    fontWeight: 600,
                    textTransform: "none",
                    boxShadow: "0 2px 10px rgba(37, 99, 235, 0.2)",
                    background:
                      "linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)",
                    "&:hover": {
                      boxShadow: "0 4px 14px rgba(37, 99, 235, 0.3)",
                      background:
                        "linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)",
                    },
                    transition: "all 0.2s ease",
                  }}
                >
                  {isSubmittingUrl ? (
                    <CircularProgress size={24} color="inherit" />
                  ) : (
                    "URLを送信"
                  )}
                </Button>
              </Box>
            )}

            {uploadTab === 2 && (
              <Box>
                <GoogleDriveAuth
                  onAuthSuccess={handleDriveAuthSuccess}
                  onAuthError={handleDriveAuthError}
                />
                
                {driveAuthError && (
                  <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                    {driveAuthError}
                  </Alert>
                )}

                {driveAccessToken && (
                  <Box>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={() => setDrivePickerOpen(true)}
                      fullWidth
                      sx={{
                        py: 1.5,
                        borderRadius: "12px",
                        fontWeight: 600,
                        textTransform: "none",
                        boxShadow: "0 2px 10px rgba(37, 99, 235, 0.2)",
                        background:
                          "linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)",
                        "&:hover": {
                          boxShadow: "0 4px 14px rgba(37, 99, 235, 0.3)",
                          background:
                            "linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)",
                        },
                        transition: "all 0.2s ease",
                      }}
                    >
                      Google Driveからファイルを選択
                    </Button>
                  </Box>
                )}

                {(isUploading || uploadProgress) && (
                  <Box sx={{ textAlign: "center", my: 2 }}>
                    {isUploading ? (
                      <CircularProgress size={32} sx={{ mb: 1.5 }} />
                    ) : null}
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ fontWeight: 500 }}
                    >
                      {uploadProgress}
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </DialogContent>
        </Dialog>

        {/* 入力フィールド */}
        <Box
          sx={{
            position: "relative",
            borderRadius: { xs: "24px", sm: "28px" },
            boxShadow: "0 2px 8px rgba(37, 99, 235, 0.04)",
            backgroundColor: "rgba(255, 255, 255, 0.9)",
            transition: "all 0.3s ease",
            width: "100%",
            mb: { xs: 0.5, sm: 0.8 }, // 下部に少し余白を追加
            "&:hover": {
              boxShadow: "0 3px 10px rgba(37, 99, 235, 0.06)",
            },
          }}
        >
          <TextField
            fullWidth
            placeholder="質問を入力してください..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter" && !e.shiftKey && input.trim()) {
                e.preventDefault();
                handleSend();
              }
            }}
            multiline
            maxRows={1}
            variant="outlined"
            disabled={isLoading}
            sx={{
              "& .MuiOutlinedInput-root": {
                borderRadius: { xs: "20px", sm: "24px" },
                backgroundColor: "rgba(255, 255, 255, 0.95)",
                boxShadow: "0 2px 6px rgba(37, 99, 235, 0.04)",
                pr: { xs: 3.2, sm: 3.5 },
                transition: "all 0.3s ease",
                maxHeight: { xs: "42px", sm: "44px", md: "46px" },
                overflowY: "hidden",
                border: "1px solid rgba(37, 99, 235, 0.08)",
                "&.Mui-focused": {
                  boxShadow: "0 3px 10px rgba(37, 99, 235, 0.08)",
                  backgroundColor: "white",
                  transform: "translateY(-1px)",
                  "& .MuiOutlinedInput-notchedOutline": {
                    borderColor: "rgba(59, 130, 246, 0.5)",
                    borderWidth: "1px",
                  },
                },
                "&:hover": {
                  boxShadow: "0 3px 8px rgba(37, 99, 235, 0.06)",
                  backgroundColor: "white",
                },
              },
              "& .MuiOutlinedInput-input": {
                padding: { xs: "8px 12px", sm: "10px 14px", md: "10px 16px" },
                fontSize: { xs: "0.85rem", sm: "0.9rem", md: "0.92rem" },
                lineHeight: 1.4,
                height: "auto",
                minHeight: { xs: "18px", sm: "20px", md: "22px" },
                maxHeight: { xs: "18px", sm: "20px", md: "22px" },
                overflowY: "hidden",
              },
              "& .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(37, 99, 235, 0.06)",
                borderWidth: "1px",
              },
            }}
          />

          <IconButton
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            size="small"
            sx={{
              position: "absolute",
              right: { xs: "6px", sm: "8px" },
              top: "50%",
              transform: "translateY(-50%)",
              background: isLoading
                ? "rgba(0, 0, 0, 0.06)"
                : input.trim()
                  ? "linear-gradient(135deg, #2563eb, #3b82f6)"
                  : "rgba(0, 0, 0, 0.04)",
              color:
                isLoading || !input.trim() ? "rgba(0, 0, 0, 0.3)" : "white",
              width: { xs: "28px", sm: "30px", md: "32px" },
              height: { xs: "28px", sm: "30px", md: "32px" },
              minWidth: 0,
              transition: "all 0.2s ease",
              borderRadius: "50%",
              boxShadow:
                input.trim() && !isLoading
                  ? "0 2px 6px rgba(37, 99, 235, 0.15)"
                  : "none",
              "&:hover": {
                background:
                  input.trim() && !isLoading
                    ? "linear-gradient(135deg, #1d4ed8, #2563eb)"
                    : "rgba(0, 0, 0, 0.04)",
                transform:
                  input.trim() && !isLoading
                    ? "translateY(-50%) scale(1.05)"
                    : "translateY(-50%)",
                boxShadow:
                  input.trim() && !isLoading
                    ? "0 3px 8px rgba(37, 99, 235, 0.2)"
                    : "none",
              },
            }}
          >
            {isLoading ? (
              <CircularProgress size={16} color="inherit" />
            ) : (
              <SendIcon
                sx={{
                  fontSize: { xs: "0.9rem", sm: "1rem", md: "1.1rem" },
                  transform: "rotate(320deg) translateX(1px)",
                }}
              />
            )}
          </IconButton>
        </Box>
      </Box>

      {/* 装飾要素を追加 */}
      <Box
        sx={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: "4px",
          background:
            "linear-gradient(90deg, #2563eb, #3b82f6, #60a5fa, #93c5fd)",
          opacity: 0.7,
          zIndex: 11,
        }}
      />
    </Box>
  );

  // メインのレンダリング関数内を調整
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
        WebkitOverflowScrolling: 'touch', // iOSのスムーススクロール対応
        overscrollBehavior: 'none', // バウンス効果を防止
      }}
    >
      {renderAppBar()}
      <Box
        sx={{
          display: "flex",
          flexGrow: 1,
          overflow: "hidden",
          position: "relative",
          mt: { xs: '56px', sm: '64px' },
          height: { xs: 'calc(100vh - 56px)', sm: 'calc(100vh - 64px)' }, // 画面高さからヘッダーの高さを引いた値
          WebkitOverflowScrolling: 'touch', // iOSのスムーススクロール対応
          overscrollBehavior: 'contain', // スクロールの慣性を制御
        }}
      >
        <Container
          maxWidth="lg"
          sx={{ display: "flex", flexDirection: "column", flexGrow: 1, py: 0 }}
        >
          {/* DemoLimitsを絶対配置にして、メッセージエリアを圧迫しないようにする */}
          {!isUnlimited && (
            <DemoLimits
              remainingQuestions={remainingQuestions}
              showAlert={showLimitReachedAlert}
              onCloseAlert={handleCloseAlert}
            />
          )}
          {renderChatMessages()}
          {renderChatInputField()}
        </Container>
      </Box>

      {/* 全体の背景グラデーションを追加 */}
      <Box
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: -1,
          background:
            "linear-gradient(160deg, rgba(219, 234, 254, 0.3), rgba(255, 255, 255, 0.7))",
          pointerEvents: "none",
        }}
      />

      {/* チャット履歴クリア確認ダイアログ */}
      <Dialog
        open={confirmClearOpen}
        onClose={cancelClearChat}
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
            maxWidth: "400px",
            width: "90%",
          },
        }}
      >
        <DialogTitle sx={{ fontWeight: 700, color: "error.main", pt: 3 }}>
          チャット履歴のクリア
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            すべてのチャット履歴が消去されます。この操作は元に戻せません。
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 2, pt: 1 }}>
          <Button
            onClick={cancelClearChat}
            variant="outlined"
            sx={{
              borderRadius: "10px",
              textTransform: "none",
              fontWeight: 600,
            }}
          >
            キャンセル
          </Button>
          <Button
            onClick={confirmClearChat}
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            sx={{
              borderRadius: "10px",
              textTransform: "none",
              fontWeight: 600,
              boxShadow: "0 4px 12px rgba(239, 68, 68, 0.2)",
            }}
          >
            クリア
          </Button>
        </DialogActions>
      </Dialog>

      {/* 制限に達した際のアラート */}
      {showLimitReachedAlert && (
        <Snackbar
          open={showLimitReachedAlert}
          autoHideDuration={null}
          onClose={handleCloseAlert}
          anchorOrigin={{ vertical: "top", horizontal: "center" }}
        >
          <Alert
            onClose={handleCloseAlert}
            severity="warning"
            variant="filled"
            sx={{
              width: "100%",
              boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
              borderRadius: 2,
            }}
            action={
              <Button
                color="inherit"
                size="small"
                onClick={handleOpenApplication}
                sx={{
                  fontWeight: 600,
                  textTransform: "none",
                }}
              >
                本番版に移行
              </Button>
            }
          >
            デモ版の質問回数制限に達しました。続けるには本番版に移行してください。
          </Alert>
        </Snackbar>
      )}

      {/* アップグレード成功メッセージ */}
      {upgradeSuccess && (
        <Snackbar
          open={upgradeSuccess}
          autoHideDuration={5000}
          onClose={() => setUpgradeSuccess(false)}
          anchorOrigin={{ vertical: "top", horizontal: "center" }}
        >
          <Alert
            onClose={() => setUpgradeSuccess(false)}
            severity="success"
            variant="filled"
            sx={{
              width: "100%",
              boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
              borderRadius: 2,
            }}
          >
            🎉 本番版への移行が完了しました！無制限にご利用いただけます。
          </Alert>
        </Snackbar>
      )}

      {/* 申請フォームダイアログ */}
      <ApplicationForm
        open={applicationOpen}
        onClose={handleCloseApplication}
      />

      {/* Google DriveファイルピッカーDialog */}
      <GoogleDriveFilePicker
        open={drivePickerOpen}
        onClose={() => setDrivePickerOpen(false)}
        onFileSelect={handleDriveFileSelect}
        accessToken={driveAccessToken}
      />
    </Box>
  );
}

export default ChatInterface;
