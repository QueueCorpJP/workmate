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
  Alert,
  Snackbar,
  Menu,
  MenuItem,
  Tooltip,
  Chip,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import LogoutIcon from "@mui/icons-material/Logout";
import SettingsIcon from "@mui/icons-material/Settings";
import BusinessIcon from "@mui/icons-material/Business";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import ChatIcon from "@mui/icons-material/Chat";
import DeleteIcon from "@mui/icons-material/Delete";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import DescriptionIcon from "@mui/icons-material/Description";
import CloseIcon from "@mui/icons-material/Close";
import LinkIcon from "@mui/icons-material/Link";
import ArticleIcon from "@mui/icons-material/Article";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import TableChartIcon from "@mui/icons-material/TableChart";
import api from "./api";
import { cache } from "./utils/cache";
import DemoLimits from "./components/DemoLimits";
import SourceCitation from "./components/SourceCitation";
import ApplicationForm from "./components/ApplicationForm";
import MarkdownRenderer from "./components/MarkdownRenderer";
import { useTheme } from "@mui/material/styles";
import { useMediaQuery } from "@mui/material";

interface Message {
  text: string;
  isUser: boolean;
  source?: string;
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

  const [showLimitReachedAlert, setShowLimitReachedAlert] =
    useState<boolean>(false);

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
  
  // チャット履歴の表示制御用の状態
  const [displayedMessageCount, setDisplayedMessageCount] = useState(10); // 最初は5ペア（10件）表示
  const [showLoadMoreButton, setShowLoadMoreButton] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  
  // フローティング参照パネルの状態
  const [showSourcePanel, setShowSourcePanel] = useState(false);
  const [sourceTooltipOpen, setSourceTooltipOpen] = useState(false);

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

  // 参照部分まで含めたスマートスクロール
  const scrollToIncludeSource = useCallback(() => {
    if (chatContainerRef.current) {
      const container = chatContainerRef.current;
      const lastMessage = container.querySelector('.message-with-source:last-child');
      if (lastMessage) {
        const sourceElement = lastMessage.querySelector('[data-source-citation]');
        if (sourceElement) {
          // 参照部分まで含めてスクロール
          sourceElement.scrollIntoView({ 
            behavior: "smooth", 
            block: "end",
            inline: "nearest"
          });
        } else {
          // 参照がない場合は通常のスクロール
          scrollToBottom();
        }
      } else {
        scrollToBottom();
      }
    }
  }, []);

  // メッセージ送信後の自動スクロールを改善
  const smartScrollAfterMessage = useCallback(() => {
    // 少し遅延を入れて、レンダリング完了後にスクロール
    setTimeout(() => {
      scrollToIncludeSource();
    }, 300);
  }, [scrollToIncludeSource]);

  // メッセージが更新されたらローカルストレージに保存
  useEffect(() => {
    if (user?.id) {
      localStorage.setItem(`chatMessages_${user.id}`, JSON.stringify(messages));
    }
    // 新しいメッセージにソースがある場合はスマートスクロール
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.source) {
      smartScrollAfterMessage();
    } else {
    scrollToBottom();
    }
  }, [messages, user?.id, smartScrollAfterMessage]);

  // ユーザーが変わったらメッセージをクリア
  useEffect(() => {
    if (user?.id) {
      const savedMessages = localStorage.getItem(`chatMessages_${user.id}`);
      const loadedMessages = savedMessages ? JSON.parse(savedMessages) : [];
      setMessages(loadedMessages);
      // 保存されたメッセージ数に応じて表示数を設定
      setDisplayedMessageCount(Math.min(10, loadedMessages.length));
    } else {
      setMessages([]);
      setDisplayedMessageCount(10);
    }
  }, [user?.id]);



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
      console.log("バックエンドからのソース情報:", response.data.source);
      console.log("レスポンス全体:", response.data);
      
      // レスポンステキストから情報ソース部分を分離
      let responseText = response.data.response;
      let sourceInfo = response.data.source || "";
      
      // レスポンステキストに「情報ソース:」が含まれている場合は分離
      const sourcePattern = /(?:\n|^)\s*情報ソース[:：]\s*(.+?)(?:\n|$)/s;
      const sourceMatch = responseText.match(sourcePattern);
      if (sourceMatch) {
        // レスポンステキストから抽出した情報ソースを優先使用
        sourceInfo = sourceMatch[1].trim();
        console.log("テキストから抽出した情報ソース:", sourceInfo);
        // 情報ソース部分をレスポンステキストから完全に除去
        responseText = responseText.replace(/(?:\n|^)\s*情報ソース[:：][^\n]*(?:\n|$)*/g, '').trim();
        console.log("情報ソース除去後のテキスト:", responseText);
      } else if (!sourceInfo && response.data.source) {
        // バックエンドからのsourceプロパティを使用
        sourceInfo = response.data.source;
        console.log("バックエンドからのソース情報を使用:", sourceInfo);
      }
      
      console.log("分離後のレスポンステキスト:", responseText);
      console.log("分離後のソース情報:", sourceInfo);
      
      setMessages((prev) => [
        ...prev,
        {
          text: responseText,
          isUser: false,
          source: sourceInfo,
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
    setDisplayedMessageCount(10); // 表示数をリセット
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

  // 「もっと見る」ボタンの処理
  const handleLoadMoreMessages = () => {
    const prevScrollHeight = chatContainerRef.current?.scrollHeight || 0;
    setDisplayedMessageCount(prev => prev + 10); // さらに5ペア（10件）表示
    
    // スクロール位置を保持
    setTimeout(() => {
      if (chatContainerRef.current) {
        const newScrollHeight = chatContainerRef.current.scrollHeight;
        const scrollDiff = newScrollHeight - prevScrollHeight;
        chatContainerRef.current.scrollTop = scrollDiff;
      }
    }, 100);
  };

  // メッセージ数が変更されたら「もっと見る」ボタンの表示を判定
  useEffect(() => {
    setShowLoadMoreButton(messages.length > displayedMessageCount);
  }, [messages.length, displayedMessageCount]);

  // 新しいメッセージが追加されたら下にスクロール＆表示数を調整
  useEffect(() => {
    if (messages.length > 0) {
      // 新しいメッセージが追加された場合、表示数を調整
      if (displayedMessageCount < messages.length) {
        // 現在の表示数が総メッセージ数より少ない場合、最新のメッセージが見えるように調整
        const needToShow = messages.length - displayedMessageCount;
        if (needToShow <= 2) { // 新しいメッセージが1-2件の場合は表示数を増やす
          setDisplayedMessageCount(messages.length);
        }
      }
      
      // 最新メッセージが表示範囲内の場合のみスクロール
      const isLatestMessageVisible = displayedMessageCount >= messages.length;
      if (isLatestMessageVisible) {
        setTimeout(() => scrollToBottom(), 100);
      }
    }
  }, [messages.length, displayedMessageCount]);

  // 表示するメッセージを取得
  const getDisplayedMessages = () => {
    return messages.slice(-displayedMessageCount);
  };

  // 現在の会話から参照ソース情報を抽出
  const getSourceInfos = useCallback(() => {
    const sourceMap = new Map();
    
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

        const key = `${cleanSourceName}${pageInfo ? `-${pageInfo}` : ''}`;
        
        if (sourceMap.has(key)) {
          sourceMap.get(key).count += 1;
        } else {
          sourceMap.set(key, {
            name: cleanSourceName,
            page: pageInfo,
            isUrl: source.startsWith('http://') || source.startsWith('https://'),
            count: 1,
          });
        }
      });
    });

    return Array.from(sourceMap.values())
      .sort((a, b) => b.count - a.count);
  }, [messages]);

  const currentSources = getSourceInfos();

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
          {/* 参照ソースクイックアクセスボタン */}
          {currentSources.length > 0 && (
            <Tooltip title={`${currentSources.length}件の参照ソース`} placement="bottom">
              <IconButton
                color="inherit"
                onClick={() => setShowSourcePanel(!showSourcePanel)}
                sx={{
                  ml: { xs: 0.5, sm: 0.75 },
                  bgcolor: showSourcePanel 
                    ? "rgba(255, 255, 255, 0.3)" 
                    : "rgba(255, 255, 255, 0.15)",
                  backdropFilter: "blur(4px)",
                  p: { xs: 1.2, sm: 1.5 },
                  width: { xs: 40, sm: 46 },
                  height: { xs: 40, sm: 46 },
                  position: 'relative',
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
                <DescriptionIcon sx={{ fontSize: { xs: "1.3rem", sm: "1.5rem" } }} />
                <Typography
                  variant="caption"
                  sx={{
                    position: 'absolute',
                    top: -4,
                    right: -4,
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    color: 'primary.main',
                    borderRadius: '50%',
                    width: 18,
                    height: 18,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    border: '1.5px solid rgba(255, 255, 255, 0.9)',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
                  }}
                >
                  {currentSources.length}
                </Typography>
              </IconButton>
            </Tooltip>
          )}
          
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
            {(isAdmin || (user && (user.role === "user" || user.role === "admin_user"))) && (
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
  // ローディングアニメーションコンポーネント
  // 「もっと見る」ボタンコンポーネント
  const LoadMoreButton = () => (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        py: 2,
        px: 3,
        position: 'sticky',
        top: 0,
        zIndex: 10,
        backgroundColor: 'rgba(248, 250, 252, 0.95)',
        backdropFilter: 'blur(8px)',
        borderBottom: '1px solid rgba(37, 99, 235, 0.1)',
        mb: 2,
      }}
    >
      <Button
        variant="outlined"
        onClick={handleLoadMoreMessages}
        sx={{
          borderRadius: '20px',
          textTransform: 'none',
          fontWeight: 600,
          px: 3,
          py: 1,
          background: 'rgba(255, 255, 255, 0.9)',
          border: '1px solid rgba(37, 99, 235, 0.2)',
          color: 'primary.main',
          boxShadow: '0 2px 8px rgba(37, 99, 235, 0.1)',
          '&:hover': {
            background: 'rgba(37, 99, 235, 0.05)',
            border: '1px solid rgba(37, 99, 235, 0.3)',
            boxShadow: '0 4px 16px rgba(37, 99, 235, 0.15)',
            transform: 'translateY(-1px)',
          },
          transition: 'all 0.2s ease',
        }}
      >
        ↑ 過去のメッセージを読み込む ({messages.length - displayedMessageCount}件)
      </Button>
    </Box>
  );

  const TypingAnimation = () => (
    <Box
      sx={{
        ...botMessageStyles,
        display: 'flex',
        alignItems: 'center',
        minHeight: '60px',
        animation: 'fadeIn 0.3s ease-out',
        background: 'linear-gradient(135deg, #FFFFFF, #F8FAFC)',
        border: '1px solid rgba(37, 99, 235, 0.12)',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: '-100%',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(90deg, transparent, rgba(37, 99, 235, 0.05), transparent)',
          animation: 'shimmer 3s infinite',
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, position: 'relative', zIndex: 1 }}>
        <Box
          sx={{
            width: 24,
            height: 24,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            animation: 'pulse 2s infinite',
          }}
        >
          <ChatIcon sx={{ color: 'white', fontSize: '0.8rem' }} />
        </Box>
        <Typography 
          variant="body2" 
          sx={{ 
            color: 'text.secondary', 
            fontWeight: 500,
            fontSize: { xs: '0.8rem', sm: '0.85rem' },
          }}
        >
          AIが回答を考えています
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.4, ml: 0.5 }}>
          {[0, 1, 2].map((index) => (
            <Box
              key={index}
              sx={{
                width: { xs: 6, sm: 8 },
                height: { xs: 6, sm: 8 },
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
                animation: `typingDot 1.4s infinite ease-in-out`,
                animationDelay: `${index * 0.16}s`,
                boxShadow: '0 1px 3px rgba(37, 99, 235, 0.3)',
                '@keyframes typingDot': {
                  '0%, 80%, 100%': {
                    transform: 'scale(0.6)',
                    opacity: 0.4,
                  },
                  '40%': {
                    transform: 'scale(1.1)',
                    opacity: 1,
                  },
                },
              }}
            />
          ))}
        </Box>
      </Box>
    </Box>
  );

  const renderChatMessages = () => (
    <Box 
      ref={chatContainerRef}
      sx={{
        ...messageContainerStyles,
        pt: showLoadMoreButton ? 0 : { xs: 2, sm: 2.5, md: 3 }, // 「もっと見る」ボタンがある場合は上部パディングを削除
        height: '100%', // 高さを100%に設定
        WebkitOverflowScrolling: 'touch', // iOSのスムーススクロール対応
        overscrollBehavior: 'contain', // スクロールの慣性を制御
      }}
    >
      {messages.length === 0 && !isLoading ? (
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
        <>
          {/* 「もっと見る」ボタンを最上部に表示 */}
          {showLoadMoreButton && <LoadMoreButton />}
          
          {/* 制限されたメッセージ数のみ表示 */}
          {getDisplayedMessages().map((message, index) => {
            // 元のインデックスを計算（キーとして使用）
            const originalIndex = messages.length - displayedMessageCount + index;
            const isLastMessage = index === getDisplayedMessages().length - 1;
            return (
              <Box
                key={originalIndex}
                className={message.source ? 'message-with-source' : 'message-normal'}
                sx={message.isUser ? userMessageStyles : botMessageStyles}
              >
                <MarkdownRenderer 
                  content={message.text} 
                  isUser={message.isUser}
                />
                {message.source && (
                  <Box data-source-citation>
                    <SourceCitation source={message.source} />
                  </Box>
                )}
              </Box>
            );
          })}
          {isLoading && <TypingAnimation />}
        </>
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
            placeholder={isLoading ? "AIが回答を準備中..." : "質問を入力してください..."}
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
                backgroundColor: isLoading 
                  ? "rgba(37, 99, 235, 0.02)" 
                  : "rgba(255, 255, 255, 0.95)",
                boxShadow: isLoading 
                  ? "0 2px 6px rgba(37, 99, 235, 0.08)" 
                  : "0 2px 6px rgba(37, 99, 235, 0.04)",
                pr: { xs: 3.2, sm: 3.5 },
                transition: "all 0.3s ease",
                maxHeight: { xs: "42px", sm: "44px", md: "46px" },
                overflowY: "hidden",
                border: isLoading 
                  ? "1px solid rgba(37, 99, 235, 0.15)" 
                  : "1px solid rgba(37, 99, 235, 0.08)",
                position: "relative",
                overflow: "hidden",
                "&::before": isLoading ? {
                  content: '""',
                  position: "absolute",
                  top: 0,
                  left: "-100%",
                  width: "100%",
                  height: "100%",
                  background: "linear-gradient(90deg, transparent, rgba(37, 99, 235, 0.1), transparent)",
                  animation: "shimmer 2s infinite",
                } : {},
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
                  backgroundColor: isLoading ? "rgba(37, 99, 235, 0.02)" : "white",
                },
                "&.Mui-disabled": {
                  backgroundColor: "rgba(37, 99, 235, 0.02)",
                  "& .MuiOutlinedInput-notchedOutline": {
                    borderColor: "rgba(37, 99, 235, 0.1)",
                  },
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
                "&.Mui-disabled": {
                  color: "rgba(0, 0, 0, 0.4)",
                  WebkitTextFillColor: "rgba(0, 0, 0, 0.4)",
                },
                "&::placeholder": {
                  opacity: isLoading ? 0.7 : 1,
                  transition: "opacity 0.3s ease",
                },
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

      {/* フローティング参照ソースパネル */}
      {showSourcePanel && currentSources.length > 0 && (
        <Paper
          elevation={8}
          sx={{
            position: 'fixed',
            bottom: isMobile ? 80 : 100,
            right: isMobile ? 16 : 24,
            width: isMobile ? 280 : 350,
            maxHeight: isMobile ? 350 : 450,
            zIndex: 1000,
            borderRadius: 3,
            overflow: 'hidden',
            background: 'rgba(255, 255, 255, 0.98)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(37, 99, 235, 0.1)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
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
                label={currentSources.length}
                size="small"
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  fontSize: '0.7rem',
                  height: 20,
                }}
              />
            </Box>
            <IconButton
              size="small"
              onClick={() => setShowSourcePanel(false)}
              sx={{ color: 'white' }}
            >
              <CloseIcon />
            </IconButton>
          </Box>

          {/* ソース一覧 */}
          <Box sx={{ maxHeight: 350, overflow: 'auto' }}>
            {currentSources.map((sourceInfo, index) => (
              <Box
                key={index}
                onClick={() => {
                  if (sourceInfo.isUrl) {
                    window.open(sourceInfo.name, '_blank');
                  }
                }}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  p: 2,
                  borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                  cursor: sourceInfo.isUrl ? 'pointer' : 'default',
                  transition: 'all 0.2s ease',
                  '&:hover': sourceInfo.isUrl ? {
                    backgroundColor: 'rgba(37, 99, 235, 0.04)',
                  } : {},
                }}
              >
                {/* ファイルアイコン */}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 36,
                    height: 36,
                    borderRadius: 2,
                    backgroundColor: sourceInfo.isUrl ? '#e3f2fd' : '#fff3e0',
                    mr: 2,
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  }}
                >
                  {sourceInfo.isUrl ? (
                    <LinkIcon sx={{ color: '#1976d2', fontSize: '1.2rem' }} />
                  ) : sourceInfo.name.endsWith('.pdf') ? (
                    <PictureAsPdfIcon sx={{ color: '#f44336', fontSize: '1.2rem' }} />
                  ) : sourceInfo.name.endsWith('.xlsx') || sourceInfo.name.endsWith('.xls') ? (
                    <TableChartIcon sx={{ color: '#2e7d32', fontSize: '1.2rem' }} />
                  ) : (
                    <ArticleIcon sx={{ color: '#ed6c02', fontSize: '1.2rem' }} />
                  )}
                </Box>
                
                {/* ファイル情報 */}
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 600,
                      color: 'text.primary',
                      fontSize: '0.9rem',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      mb: 0.5,
                    }}
                    title={sourceInfo.name}
                  >
                    {sourceInfo.name.length > 25 
                      ? `${sourceInfo.name.substring(0, 25)}...`
                      : sourceInfo.name
                    }
                  </Typography>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography
                      variant="caption"
                      sx={{ 
                        color: 'text.secondary', 
                        fontSize: '0.75rem',
                        backgroundColor: 'rgba(37, 99, 235, 0.08)',
                        px: 1,
                        py: 0.25,
                        borderRadius: 1,
                      }}
                    >
                      {sourceInfo.isUrl ? 'ウェブサイト' : 
                       sourceInfo.name.endsWith('.pdf') ? 'PDF文書' :
                       sourceInfo.name.endsWith('.xlsx') || sourceInfo.name.endsWith('.xls') ? 'Excel文書' :
                       '文書'}
                    </Typography>
                    
                    {sourceInfo.page && (
                      <Typography
                        variant="caption"
                        sx={{ 
                          color: 'text.secondary', 
                          fontSize: '0.75rem',
                          backgroundColor: 'rgba(67, 56, 202, 0.08)',
                          px: 1,
                          py: 0.25,
                          borderRadius: 1,
                        }}
                      >
                        P.{sourceInfo.page}
                      </Typography>
                    )}
                    
                    {sourceInfo.count > 1 && (
                      <Typography
                        variant="caption"
                        sx={{
                          color: 'white',
                          fontSize: '0.7rem',
                          backgroundColor: '#2563eb',
                          px: 1,
                          py: 0.25,
                          borderRadius: 1,
                          fontWeight: 600,
                        }}
                      >
                        {sourceInfo.count}回参照
                      </Typography>
                    )}
                  </Box>
                </Box>
              </Box>
            ))}
          </Box>

          {/* フッター */}
          <Box
            sx={{
              p: 2,
              backgroundColor: 'rgba(248, 250, 252, 0.8)',
              borderTop: '1px solid rgba(0, 0, 0, 0.05)',
            }}
          >
            <Typography
              variant="caption"
              sx={{ color: 'text.secondary', fontSize: '0.75rem', textAlign: 'center', display: 'block' }}
            >
              ソースをクリックして詳細を確認 • {currentSources.reduce((sum, s) => sum + s.count, 0)}回の参照
            </Typography>
          </Box>
        </Paper>
      )}
    </Box>
  );
}

export default ChatInterface;
