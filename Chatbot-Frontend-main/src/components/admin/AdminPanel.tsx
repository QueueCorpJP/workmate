import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Container,
  Paper,
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Tabs,
  Tab,
  useTheme,
  useMediaQuery,
  Fade,
  Chip,
  Badge,
  Divider,
  Avatar,
  Dialog,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import HistoryIcon from "@mui/icons-material/History";
import InsightsIcon from "@mui/icons-material/Insights";
import GroupIcon from "@mui/icons-material/Group";
import StorageIcon from "@mui/icons-material/Storage";
import QueryStatsIcon from "@mui/icons-material/QueryStats";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import DashboardIcon from "@mui/icons-material/Dashboard";
import PersonAddIcon from "@mui/icons-material/PersonAdd";
import SettingsApplicationsIcon from "@mui/icons-material/SettingsApplications";
import CloseIcon from "@mui/icons-material/Close";
import CircularProgress from "@mui/material/CircularProgress";
import TimelineIcon from "@mui/icons-material/Timeline";
import MonetizationOnIcon from "@mui/icons-material/MonetizationOn";
import api from "../../api";
import { useAuth } from "../../contexts/AuthContext";

// Import tab components
import ChatHistoryTab from "./ChatHistoryTab";
import AnalysisTab from "./AnalysisTab";
import EmployeeUsageTab from "./EmployeeUsageTab";
import ResourcesTab from "./ResourcesTab";
import DemoStatsTab from "./DemoStatsTab";
import UserManagementTab from "./UserManagementTab";
import PlanHistoryTab from "./PlanHistoryTab";
import CompanyDetailsDialog from "./CompanyDetailsDialog";
import BillingTab from "../BillingTab";

// Import types
import {
  ChatHistoryItem,
  AnalysisResult,
  EmployeeUsageItem,
  CompanyEmployee,
  Resource,
  DemoStats,
} from "./types";

const AdminPanel: React.FC = () => {
  // 認証コンテキストを使用
  const { user } = useAuth();
  const isUserRole = user?.role === "user";

  // Tab state
  const [tabValue, setTabValue] = useState(0);

  // Data states
  const [chatHistory, setChatHistory] = useState<ChatHistoryItem[]>([]);
  const [chatPagination, setChatPagination] = useState({
    total_count: 0,
    limit: 30,
    offset: 0,
    has_more: false
  });
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [employeeUsage, setEmployeeUsage] = useState<EmployeeUsageItem[]>([]);
  const [companyEmployees, setCompanyEmployees] = useState<CompanyEmployee[]>(
    []
  );
  const [resources, setResources] = useState<Resource[]>([]);
  const [demoStats, setDemoStats] = useState<DemoStats | null>(null);

  // Loading states
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);
  const [isEmployeeUsageLoading, setIsEmployeeUsageLoading] = useState(false);
  const [isEmployeeDetailsLoading, setIsEmployeeDetailsLoading] =
    useState(false);
  const [isResourcesLoading, setIsResourcesLoading] = useState(false);
  const [isCompanyEmployeesLoading, setIsCompanyEmployeesLoading] =
    useState(false);
  const [isDemoStatsLoading, setIsDemoStatsLoading] = useState(false);

  // Employee details states
  const [selectedEmployee, setSelectedEmployee] =
    useState<EmployeeUsageItem | null>(null);
  const [employeeDetails, setEmployeeDetails] = useState<ChatHistoryItem[]>([]);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);

  // Admin state
  const [isSpecialAdmin, setIsSpecialAdmin] = useState(false);

  // User creation states
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [isUserCreating, setIsUserCreating] = useState(false);
  const [userCreateError, setUserCreateError] = useState<string | null>(null);
  const [userCreateSuccess, setUserCreateSuccess] = useState<string | null>(
    null
  );

  // Company details states
  const [companyDetailsOpen, setCompanyDetailsOpen] = useState(false);
  const [companyDetails, setCompanyDetails] = useState<any[]>([]);
  const [isCompanyDetailsLoading, setIsCompanyDetailsLoading] = useState(false);
  const [isUserDeleting, setIsUserDeleting] = useState(false);
  const [userDeleteError, setUserDeleteError] = useState<string | null>(null);
  const [userDeleteSuccess, setUserDeleteSuccess] = useState<string | null>(
    null
  );

  // Employee creation states
  const [newEmployeeEmail, setNewEmployeeEmail] = useState("");
  const [newEmployeePassword, setNewEmployeePassword] = useState("");
  const [isEmployeeCreating, setIsEmployeeCreating] = useState(false);
  const [employeeCreateError, setEmployeeCreateError] = useState<string | null>(
    null
  );
  const [employeeCreateSuccess, setEmployeeCreateSuccess] = useState<
    string | null
  >(null);
  const [showEmployeeCreateForm, setShowEmployeeCreateForm] = useState(false);

  // Company selection states (for admin user creation)
  const [companies, setCompanies] = useState<any[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");
  const [isCompaniesLoading, setIsCompaniesLoading] = useState(false);
  const [newCompanyName, setNewCompanyName] = useState<string>("");

  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isTablet = useMediaQuery(theme.breakpoints.between("sm", "md"));

  // チャット履歴の取得とユーザー情報の確認
  useEffect(() => {
    fetchChatHistory();

    // 特別な管理者またはadminロールかどうかを確認
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      const user = JSON.parse(storedUser);
      if (user && (user.email === "queue@queuefood.co.jp" || user.role === "admin")) {
        setIsSpecialAdmin(true);
      }
    }

    // 初期データの読み込み
    fetchCompanyEmployees();
    fetchEmployeeUsage();
  }, []);

  // チャット履歴の取得（ページネーション対応）
  const fetchChatHistory = async (loadMore: boolean = false) => {
    setIsLoading(true);
    try {
      console.log("チャット履歴を取得中...");
      const storedUser = localStorage.getItem("user");
      const userId = storedUser ? JSON.parse(storedUser).id : null;
      
      // ページネーションパラメータ
      const limit = 30;
      const offset = loadMore ? chatHistory.length : 0;
      
      const baseUrl = isSpecialAdmin
        ? `${import.meta.env.VITE_API_URL}/admin/chat-history`
        : `${import.meta.env.VITE_API_URL}/admin/chat-history`;
      
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString()
      });
      
      if (!isSpecialAdmin && userId) {
        params.append('user_id', userId);
      }
      
      const url = `${baseUrl}?${params.toString()}`;
      
      const response = await api.get(url, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'application/json'
        }
      });
      
      console.log("チャット履歴取得結果:", response.data);
      
      // 新しいレスポンス形式に対応
      if (response.data && response.data.data && Array.isArray(response.data.data)) {
        if (loadMore) {
          // 既存のデータに追加
          setChatHistory(prev => [...prev, ...response.data.data]);
        } else {
          // 新しいデータで置き換え
          setChatHistory(response.data.data);
        }
        
        // ページネーション情報を保存
        setChatPagination({
          total_count: response.data.total_count,
          limit: response.data.limit,
          offset: response.data.offset + response.data.data.length,
          has_more: response.data.has_more
        });
        
      } else if (Array.isArray(response.data)) {
        // 後方互換性のため古い形式にも対応
        setChatHistory(response.data);
        setChatPagination({
          total_count: response.data.length,
          limit: response.data.length,
          offset: response.data.length,
          has_more: false
        });
      } else {
        console.error(
          "チャット履歴のレスポンスが想定される形式ではありません:",
          response.data
        );
        setChatHistory([]);
        setChatPagination({
          total_count: 0,
          limit: 30,
          offset: 0,
          has_more: false
        });
      }
    } catch (error) {
      console.error("チャット履歴の取得に失敗しました:", error);
      alert(
        "チャット履歴の取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
    } finally {
      setIsLoading(false);
    }
  };

  // 分析データの取得
  const fetchAnalysis = async () => {
    if (analysis && Object.keys(analysis.category_distribution).length > 0)
      return; // 既に有効なデータがある場合は何もしない

    setIsAnalysisLoading(true);
    try {
      console.log("チャット分析を取得中...");
      // 特別な管理者でない場合は、ユーザーIDをクエリパラメータとして渡す
      const storedUser = localStorage.getItem("user");
      const userId = storedUser ? JSON.parse(storedUser).id : null;
      const url = isSpecialAdmin
        ? `${import.meta.env.VITE_API_URL}/admin/analyze-chats`
        : `${import.meta.env.VITE_API_URL}/admin/analyze-chats?user_id=${userId}`;
      const response = await api.get(url, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'application/json'
        }
      });
      console.log("チャット分析取得結果:", response.data);
      // レスポンスが有効なオブジェクトであることを確認
      if (
        response.data &&
        typeof response.data === "object"
      ) {
        // 必要なプロパティがない場合は初期化
        if (!("category_distribution" in response.data)) {
          response.data.category_distribution = {};
        }
        if (!("sentiment_distribution" in response.data)) {
          response.data.sentiment_distribution = {};
        }
        if (!("common_questions" in response.data)) {
          response.data.common_questions = [];
        } else if (!Array.isArray(response.data.common_questions)) {
          response.data.common_questions = [];
        }
        if (!("daily_usage" in response.data)) {
          response.data.daily_usage = [];
        }
        
        console.log("チャット分析データを設定:", response.data);
        setAnalysis(response.data);
      } else {
        console.error(
          "チャット分析のレスポンスが有効なオブジェクトではありません:",
          response.data
        );
        setAnalysis({
          category_distribution: {},
          sentiment_distribution: {},
          common_questions: [],
          insights: "データの取得に失敗しました。",
        });
      }
    } catch (error) {
      console.error("チャット分析の取得に失敗しました:", error);
      // エラーメッセージを表示
      alert(
        "チャット分析の取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
    } finally {
      setIsAnalysisLoading(false);
    }
  };

  // 会社の管理者用アカウント利用状況の取得
  const fetchEmployeeUsage = async (forceRefresh = false) => {
    if (employeeUsage.length > 0 && !forceRefresh) return; // 既に有効なデータがある場合は何もしない（強制更新フラグがない場合）

    setIsEmployeeUsageLoading(true);
    try {
      console.log("会社の管理者用アカウント利用状況を取得中...");
      // 認証情報はHTTPヘッダーに含まれるため、クエリパラメータは不要
      const response = await api.get(
        `${import.meta.env.VITE_API_URL}/admin/employee-usage`,
        {
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
          }
        }
      );
      console.log("会社の管理者用アカウント利用状況取得結果:", response.data);
      // レスポンスが有効なオブジェクトであることを確認
      if (
        response.data &&
        typeof response.data === "object" &&
        "employee_usage" in response.data &&
        Array.isArray(response.data.employee_usage)
      ) {
        setEmployeeUsage(response.data.employee_usage);
      } else {
        console.error(
          "社員利用状況のレスポンスが有効なオブジェクトではありません:",
          response.data
        );
        setEmployeeUsage([]);
      }
    } catch (error) {
      console.error(
        "会社の管理者用アカウント利用状況の取得に失敗しました:",
        error
      );
      // エラーメッセージを表示
      alert(
        "会社の管理者用アカウント利用状況の取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
    } finally {
      setIsEmployeeUsageLoading(false);
    }
  };

  // 会社の全社員情報を取得
  const fetchCompanyEmployees = async (forceRefresh = false) => {
    if (companyEmployees.length > 0 && !forceRefresh) return; // 既に有効なデータがある場合は何もしない（強制更新フラグがない場合）

    setIsCompanyEmployeesLoading(true);
    try {
      console.log("会社の全社員情報を取得中...");
      // ユーザーIDをクエリパラメータとして渡す
      const storedUser = localStorage.getItem("user");
      const userId = storedUser ? JSON.parse(storedUser).id : null;
      const response = await api.get(
        `${import.meta.env.VITE_API_URL}/admin/company-employees?user_id=${userId}`,
        {
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
          }
        }
      );
      console.log("会社の全社員情報取得結果:", response.data);

      // レスポンスが有効なオブジェクトであることを確認
      if (
        response.data &&
        Array.isArray(response.data)
      ) {
        setCompanyEmployees(response.data);
      } else if (
        response.data &&
        typeof response.data === "object" &&
        "employees" in response.data &&
        Array.isArray(response.data.employees)
      ) {
        // 後方互換性のために残す
        setCompanyEmployees(response.data.employees);
      } else {
        console.error(
          "会社の全社員情報のレスポンスが有効なオブジェクトではありません:",
          response.data
        );
        setCompanyEmployees([]);
      }
    } catch (error) {
      console.error("会社の全社員情報の取得に失敗しました:", error);
      // エラーメッセージを表示
      alert(
        "会社の全社員情報の取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
      setCompanyEmployees([]);
    } finally {
      setIsCompanyEmployeesLoading(false);
    }
  };

  // アップロードされたリソースの取得
  const fetchResources = async () => {
    setIsResourcesLoading(true);
    try {
      console.log("アップロードされたリソースを取得中...");
      const response = await api.get(`${import.meta.env.VITE_API_URL}/admin/resources`);
      console.log("リソース取得結果:", response.data);
      // レスポンスが有効なオブジェクトであることを確認
      if (
        response.data &&
        typeof response.data === "object" &&
        "resources" in response.data &&
        Array.isArray(response.data.resources)
      ) {
        setResources(response.data.resources);
      } else {
        console.error(
          "リソースのレスポンスが有効なオブジェクトではありません:",
          response.data
        );
        setResources([]);
      }
    } catch (error) {
      console.error("リソースの取得に失敗しました:", error);
      // エラーメッセージを表示
      alert(
        "リソースの取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
    } finally {
      setIsResourcesLoading(false);
    }
  };

  // デモ利用状況の取得
  const fetchDemoStats = async () => {
    setIsDemoStatsLoading(true);
    try {
      console.log("デモ利用状況を取得中...");
      const response = await api.get(`${import.meta.env.VITE_API_URL}/admin/demo-stats`);
      console.log("デモ利用状況取得結果:", response.data);
      setDemoStats(response.data);
    } catch (error) {
      console.error("デモ利用状況の取得に失敗しました:", error);
      alert(
        "デモ利用状況の取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
    } finally {
      setIsDemoStatsLoading(false);
    }
  };

  // 新規ユーザー作成
  const handleCreateUser = async (role: string = "employee") => {
    if (!newUserEmail || !newUserPassword) {
      setUserCreateError("メールアドレスとパスワードは必須です");
      return;
    }

    setIsUserCreating(true);
    setUserCreateError(null);
    setUserCreateSuccess(null);

    try {
      const requestData: any = {
        email: newUserEmail,
        password: newUserPassword,
        name: newUserEmail.split("@")[0],
        role: role,
      };

      // 特別管理者で会社名が入力されている場合
      if (isSpecialAdmin && newCompanyName && newCompanyName.trim()) {
        requestData.company_name = newCompanyName.trim();
      }
      // 特別管理者で既存の会社IDが選択されている場合
      else if (isSpecialAdmin && selectedCompanyId) {
        requestData.company_id = selectedCompanyId;
      }

      const response = await api.post("/admin/register-user", requestData);

        setUserCreateSuccess(
        `${role === "user" ? "社長用" : "社員"}アカウントが正常に作成されました`
        );
      setNewUserEmail("");
      setNewUserPassword("");
      setSelectedCompanyId("");
      setNewCompanyName("");
    } catch (error: any) {
      console.error("アカウント作成エラー:", error);
      if (error.response?.data?.detail) {
        setUserCreateError(error.response.data.detail);
      } else {
        setUserCreateError("アカウント作成に失敗しました");
      }
    } finally {
      setIsUserCreating(false);
    }
  };

  // 会社一覧を取得する関数
  const fetchCompanies = async () => {
    if (!isSpecialAdmin) return;

    setIsCompaniesLoading(true);
    try {
      const response = await api.get("/admin/companies");
      setCompanies(response.data);
      console.log("会社一覧取得成功:", response.data);
    } catch (error) {
      console.error("会社一覧取得エラー:", error);
      setCompanies([]);
    } finally {
      setIsCompaniesLoading(false);
    }
  };

  // 管理者の場合は会社一覧を取得
  useEffect(() => {
    if (isSpecialAdmin) {
      fetchCompanies();
    }
  }, [isSpecialAdmin]);

  // 会社詳細情報の取得
  const fetchCompanyDetails = async () => {
    setIsCompanyDetailsLoading(true);
    try {
      console.log("会社詳細情報を取得中...");
      const response = await api.get("/admin/company-employees");
      console.log("会社詳細情報取得結果:", response.data);
      setCompanyDetails(response.data);
    } catch (error) {
      console.error("会社詳細情報の取得に失敗しました:", error);
      alert(
        "会社詳細情報の取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
    } finally {
      setIsCompanyDetailsLoading(false);
    }
  };

  // 会社詳細ダイアログを開く
  const handleOpenCompanyDetails = () => {
    fetchCompanyDetails();
    setCompanyDetailsOpen(true);
  };

  // 会社詳細ダイアログを閉じる
  const handleCloseCompanyDetails = () => {
    setCompanyDetailsOpen(false);
  };

  // ユーザー削除
  const handleDeleteUser = async (userId: string, userEmail: string) => {
    if (!confirm(`管理者 ${userEmail} を削除してもよろしいですか？`)) {
      return;
    }

    setUserDeleteError("");
    setUserDeleteSuccess("");
    
    try {
      console.log(`管理者 ${userId} を削除中...`);
      const response = await api.delete(`/admin/users/${userId}`);
      console.log("管理者削除結果:", response.data);
      setUserDeleteSuccess(`管理者 ${userEmail} を削除しました`);
      
      // 削除後にユーザーリストを更新
      await fetchEmployeeUsage();
    } catch (error: any) {
      console.error("管理者削除に失敗しました:", error);
      setUserDeleteError(
        error.response?.data?.detail || "管理者削除に失敗しました"
      );
    }
  };

  // 社員アカウント作成
  const handleCreateEmployee = async (role: string = "employee") => {
    if (!newEmployeeEmail || !newEmployeePassword) {
      setEmployeeCreateError("メールアドレスとパスワードを入力してください");
      return;
    }

    setIsEmployeeCreating(true);
    setEmployeeCreateError(null);
    setEmployeeCreateSuccess(null);

    try {
      console.log(`新規アカウントを作成中... (ロール: ${role})`);
      const response = await api.post(`${import.meta.env.VITE_API_URL}/admin/register-user`, {
        email: newEmployeeEmail,
        password: newEmployeePassword,
        name: newEmployeeEmail.split("@")[0], // メールアドレスの@前をデフォルト名として使用
        role: role,
      });
      console.log("アカウント作成結果:", response.data);

      // 成功メッセージをロールに応じて変更
      if (role === "user") {
        setEmployeeCreateSuccess(
          `会社の管理者用アカウント ${newEmployeeEmail} を作成しました (管理画面アクセス可)`
        );
      } else {
        setEmployeeCreateSuccess(
          `社員アカウント ${newEmployeeEmail} を作成しました (管理画面アクセス不可)`
        );
      }

      setNewEmployeeEmail("");
      setNewEmployeePassword("");

      // 社員利用状況と会社の全社員情報を再取得
      setEmployeeUsage([]);
      setCompanyEmployees([]);
      fetchEmployeeUsage();
      fetchCompanyEmployees();

      // フォームを閉じる
      setShowEmployeeCreateForm(false);
    } catch (error: any) {
      console.error("アカウント作成に失敗しました:", error);
      setEmployeeCreateError(
        error.response?.data?.detail || "アカウント作成に失敗しました"
      );
    } finally {
      setIsEmployeeCreating(false);
    }
  };

  // 社員詳細情報の取得
  const fetchEmployeeDetails = async (employeeId: string) => {
    setIsEmployeeDetailsLoading(true);
    try {
      console.log(`社員ID: ${employeeId} の詳細情報を取得中...`);
      // 特別な管理者でない場合は、ユーザーIDをクエリパラメータとして渡す
      const storedUser = localStorage.getItem("user");
      const userId = storedUser ? JSON.parse(storedUser).id : null;
      const url = isSpecialAdmin
        ? `${import.meta.env.VITE_API_URL}/admin/employee-details/${employeeId}`
        : `${import.meta.env.VITE_API_URL}/admin/employee-details/${employeeId}?user_id=${userId}`;
      const response = await api.get(url, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'application/json'
        }
      });
      console.log("社員詳細情報取得結果:", response.data);
      // レスポンスが配列であることを確認
      if (Array.isArray(response.data)) {
        setEmployeeDetails(response.data);
      } else {
        console.error(
          "社員詳細情報のレスポンスが配列ではありません:",
          response.data
        );
        setEmployeeDetails([]);
      }
    } catch (error) {
      console.error("社員詳細情報の取得に失敗しました:", error);
      alert(
        "社員詳細情報の取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
      setEmployeeDetails([]);
    } finally {
      setIsEmployeeDetailsLoading(false);
    }
  };

  // 社員カードクリック時の処理
  const handleEmployeeCardClick = (employee: EmployeeUsageItem) => {
    setSelectedEmployee(employee);
    fetchEmployeeDetails(employee.employee_id);
    setDetailsDialogOpen(true);
  };

  // 詳細ダイアログを閉じる
  const handleCloseDetailsDialog = () => {
    setDetailsDialogOpen(false);
  };

  // タブのアイコンとラベルを定義（色分け用のスタイルを追加）
  const tabDefinitions = [
    {
      icon: <HistoryIcon sx={{ color: "#3b82f6" }} />,
      label: "チャット履歴",
      ariaLabel: "チャット履歴タブ",
    },
    {
      icon: <InsightsIcon sx={{ color: "#3b82f6" }} />,
      label: "分析",
      ariaLabel: "分析タブ",
    },
    {
      icon: <GroupIcon sx={{ color: "#3b82f6" }} />,
      label: "社員管理",
      ariaLabel: "社員管理タブ",
    },
    {
      icon: <StorageIcon sx={{ color: "#3b82f6" }} />,
      label: "リソース",
      ariaLabel: "リソースタブ",
    },
    {
      icon: <TimelineIcon sx={{ color: "#3b82f6" }} />,
      label: "プラン履歴",
      ariaLabel: "プラン履歴タブ",
    },
    {
      icon: <MonetizationOnIcon sx={{ color: "#3b82f6" }} />,
      label: "料金管理",
      ariaLabel: "料金管理タブ",
    },
    ...(isUserRole
      ? []
      : [
        {
          icon: <QueryStatsIcon sx={{ color: "#3b82f6" }} />,
          label: "デモ統計",
          ariaLabel: "デモ統計タブ",
        },
      ]),
    {
      icon: <PersonAddIcon sx={{ color: "#3b82f6" }} />,
      label: "ユーザー管理",
      ariaLabel: "ユーザー管理タブ",
    },
  ];

  // タブが変更されたときの実際のインデックスを計算する関数
  const getActualTabIndex = (visibleIndex: number) => {
    if (isUserRole && visibleIndex >= 6) {
      return visibleIndex + 1; // デモ統計タブがスキップされるので+1する
    }
    return visibleIndex;
  };

  // タブが変更されたときのハンドラ
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);

    // タブに応じてデータを取得
    const actualTabIndex = getActualTabIndex(newValue);
    switch (actualTabIndex) {
      case 0: // チャット履歴
        fetchChatHistory();
        break;
      case 1: // 分析
        fetchAnalysis();
        break;
      case 2: // 社員管理
        fetchEmployeeUsage(true);
        fetchCompanyEmployees(true);
        break;
      case 3: // リソース
        fetchResources();
        break;
      case 4: // プラン履歴
        // プラン履歴は内部で自動読み込みするため何もしない
        break;
      case 5: // 料金管理
        // 料金管理は内部で自動読み込みするため何もしない
        break;
      case 6: // デモ統計 (ユーザーロールでない場合のみ)
        if (!isUserRole) {
          fetchDemoStats();
        }
        break;
      case 7: // ユーザー管理
        break;
      default:
        break;
    }
  };

  // チャットページに戻る
  const handleBackToChat = () => {
    navigate("/");
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
        position: "relative",
        bgcolor: "rgba(249, 250, 252, 0.97)",
      }}
    >
      {/* AppBar */}
      <AppBar
        position="static"
        elevation={0}
        sx={{
          boxShadow: "0 2px 12px rgba(37, 99, 235, 0.15)",
          backgroundColor: "white",
          borderBottom: "1px solid rgba(37, 99, 235, 0.08)",
          backdropFilter: "blur(10px)",
          zIndex: 10,
          transition: "all 0.3s ease",
          background:
            "linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(59, 130, 246, 0.97))",
          borderRadius: "0 0 12px 12px",
        }}
      >
        <Toolbar
          sx={{
            minHeight: { xs: "54px", sm: "60px", md: "64px" },
            px: { xs: 1.5, sm: 2, md: 3, lg: 4 },
            display: "flex",
            justifyContent: "space-between",
            flexWrap: "nowrap",
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              flexShrink: 0,
              width: { xs: "auto", sm: "auto" },
              overflow: "hidden",
              paddingY: .25
            }}
          >
            <IconButton
              color="inherit"
              onClick={() => navigate("/")}
              edge="start"
              sx={{
                mr: { xs: 1, sm: 1.5 },
                ml: { xs: 1, sm: 0 },
                backgroundColor: "rgba(255, 255, 255, 0.2)",
                "&:hover": {
                  backgroundColor: "rgba(255, 255, 255, 0.3)",
                  transform: "translateY(-2px)",
                },
                transition: "all 0.2s ease",
                width: { xs: 36, sm: 40 },
                height: { xs: 36, sm: 40 },
                borderRadius: "10px",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                flexShrink: 0,
              }}
            >
              <ArrowBackIcon
                sx={{ fontSize: { xs: "1.2rem", sm: "1.4rem" } }}
              />
            </IconButton>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                minWidth: 0,
                overflow: "hidden",
              }}
            >
              <Avatar
                sx={{
                  bgcolor: "rgba(255, 255, 255, 0.2)",
                  mr: { xs: 1, sm: 1.5 },
                  width: { xs: 36, sm: 40 },
                  height: { xs: 36, sm: 40 },
                  border: "1px solid rgba(255, 255, 255, 0.2)",
                  boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                  flexShrink: 0,
                }}
              >
                <AdminPanelSettingsIcon
                  sx={{ fontSize: { xs: "1.3rem", sm: "1.5rem" } }}
                />
              </Avatar>
              <Typography
                variant={isMobile ? "h6" : "h5"}
                component="div"
                sx={{
                  fontWeight: 700,
                  fontSize: { xs: "1rem", sm: "1.2rem", md: "1.4rem" },
                  color: "white",
                  textShadow: "0 1px 4px rgba(0, 0, 0, 0.1)",
                  letterSpacing: "0.01em",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                管理パネル
              </Typography>
              <Chip
                icon={<PersonAddIcon />}
                label={isUserRole ? "一般管理者" : "管理者"}
                size="small"
                color={isUserRole ? "default" : "primary"}
                sx={{
                  fontWeight: 600,
                  borderRadius: 2
                }}
              />
            </Box>
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          <IconButton
            color="inherit"
            onClick={() => navigate("/settings?referrer=admin")}
            sx={{
              backgroundColor: "rgba(255, 255, 255, 0.15)",
              "&:hover": {
                backgroundColor: "rgba(255, 255, 255, 0.25)",
                transform: "translateY(-2px)",
              },
              transition: "all 0.2s ease",
              width: { xs: 36, sm: 40 },
              height: { xs: 36, sm: 40 },
              borderRadius: "10px",
              border: "1px solid rgba(255, 255, 255, 0.2)",
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
              ml: { xs: 1, sm: 1.5 },
              flexShrink: 0,
            }}
          >
            <SettingsApplicationsIcon
              sx={{ fontSize: { xs: "1.2rem", sm: "1.4rem" } }}
            />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* タブと内容 */}
      <Container
        maxWidth="xl"
        sx={{
          mt: { xs: 1.5, sm: 2, md: 3 },
          mb: { xs: 1.5, sm: 2, md: 3 },
          flexGrow: 1,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          height: {
            xs: "calc(100vh - 90px)",
            sm: "calc(100vh - 100px)",
            md: "calc(100vh - 106px)",
          },
          px: { xs: 1, sm: 2, md: 3, lg: 4 },
        }}
      >
        <Paper
          elevation={0}
          sx={{
            borderRadius: { xs: "12px", sm: "16px" },
            height: "100%",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            bgcolor: "white",
            border: "1px solid rgba(37, 99, 235, 0.08)",
            boxShadow: "0 4px 20px rgba(37, 99, 235, 0.05)",
            position: "relative",
          }}
        >
          {/* タブバー */}
          <Box
            sx={{
              borderBottom: 1,
              borderColor: "rgba(0, 0, 0, 0.08)",
              bgcolor: "rgba(249, 250, 252, 0.9)",
              boxShadow: "0 2px 5px rgba(0, 0, 0, 0.03)",
              borderRadius: "16px 16px 0 0",
              px: { xs: 0, sm: 1.5, md: 2 },
              position: "relative",
              width: "100%",
              height: { xs: "52px", sm: "48px" },
              minHeight: { xs: "52px", sm: "48px" },
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              overflow: isMobile ? "hidden" : "visible",
              flexShrink: 0,
            }}
          >
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              variant={isMobile ? "scrollable" : "fullWidth"}
              scrollButtons={isMobile ? "auto" : false}
              allowScrollButtonsMobile
              sx={{
                height: { xs: "52px", sm: "48px" },
                minHeight: { xs: "52px", sm: "48px" },
                maxHeight: { xs: "52px", sm: "48px" },
                width: "100%",
                maxWidth: "100%",
                "& .MuiTabs-flexContainer": {
                  width: isMobile ? "auto" : "100%",
                  gap: { xs: 0.5, sm: 0 }
                },
                "& .MuiTabs-scroller": {
                  width: "100%",
                  overflow: isMobile ? "auto" : "visible",
                  scrollbarWidth: "none", // Firefox
                  msOverflowStyle: "none", // IE and Edge
                  "&::-webkit-scrollbar": {
                    display: "none", // Webkit browsers
                  },
                },
                "& .MuiTab-root": {
                  minWidth: { xs: 85, sm: 100, md: 120 },
                  minHeight: { xs: "52px", sm: "48px" },
                  fontSize: { xs: "0.65rem", sm: "0.75rem", md: "0.8rem" },
                  fontWeight: 600,
                  color: "text.secondary",
                  textTransform: "none",
                  py: { xs: 1, sm: 1.5 },
                  px: { xs: 0.5, sm: 2 },
                  flexDirection: isMobile ? "column" : "row",
                  alignItems: "center",
                  gap: { xs: 0.25, sm: 1 },
                  transition: "all 0.2s ease",
                  flex: isMobile ? "0 0 auto" : 1,
                  display: "flex",
                  justifyContent: "center",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                },
                "& .MuiTab-root.Mui-selected": {
                  color: "primary.main",
                  fontWeight: 700,
                  backgroundColor: "rgba(59, 130, 246, 0.05)",
                },
                "& .MuiTabs-indicator": {
                  backgroundColor: "primary.main",
                  height: 3,
                  borderRadius: "3px 3px 0 0",
                },
                "& .MuiTabScrollButton-root": {
                  width: { xs: 32, sm: 36 },
                  height: "100%",
                  color: "rgba(59, 130, 246, 0.7)",
                  backgroundColor: "rgba(255, 255, 255, 0.9)",
                  borderRadius: "4px",
                  margin: "4px 2px",
                  "&:hover": {
                    backgroundColor: "rgba(59, 130, 246, 0.1)",
                  },
                  "&.Mui-disabled": {
                    opacity: 0.3,
                  },
                  "& .MuiSvgIcon-root": {
                    fontSize: "1.2rem",
                  },
                },
              }}
            >
              {tabDefinitions.map((tab, index) => (
                <Tab
                  key={index}
                  icon={tab.icon}
                  label={tab.label}
                  aria-label={tab.ariaLabel}
                  iconPosition={isMobile ? "top" : "start"}
                  sx={{
                    "&:hover": {
                      bgcolor: "rgba(59, 130, 246, 0.05)",
                      color: "primary.main",
                    },
                    "& .MuiSvgIcon-root": {
                      fontSize: { xs: "1rem", sm: "1.2rem", md: "1.3rem" },
                      marginRight: isMobile ? 0 : 1,
                      marginBottom: isMobile ? "2px" : "0px",
                    },
                    "& .MuiTab-iconWrapper": {
                      marginBottom: isMobile ? "2px" : 0,
                    },
                  }}
                />
              ))}
            </Tabs>
          </Box>

          {/* タブの内容 */}
          <Box
            sx={{
              flexGrow: 1,
              overflow: "auto",
              p: { xs: 1.5, sm: 2, md: 3 },
              mt: 0, // 上部マージンを明示的に0に設定
              "::-webkit-scrollbar": {
                width: "6px",
              },
              "::-webkit-scrollbar-track": {
                bgcolor: "rgba(0, 0, 0, 0.02)",
              },
              "::-webkit-scrollbar-thumb": {
                bgcolor: "rgba(59, 130, 246, 0.2)",
                borderRadius: "10px",
              },
              display: "flex",
              flexDirection: "column",
              justifyContent: "flex-start",
              alignItems: "stretch",
            }}
          >
            {/* タブコンテンツ内のレスポンシブラッパー */}
            <Box
              sx={{
                maxWidth: "100%",
                width: "100%",
                mx: "auto",
                height: "100%",
                display: "flex",
                flexDirection: "column",
              }}
            >
              {/* チャット履歴タブ */}
              {tabValue === 0 && (
                <ChatHistoryTab
                  chatHistory={chatHistory}
                  isLoading={isLoading}
                  onRefresh={() => fetchChatHistory(false)}
                  onLoadMore={() => fetchChatHistory(true)}
                  hasMore={chatPagination.has_more}
                  totalCount={chatPagination.total_count}
                />
              )}

              {/* 分析タブ */}
              {tabValue === 1 && (
                <AnalysisTab
                  analysis={analysis}
                  isLoading={isAnalysisLoading}
                  onRefresh={fetchAnalysis}
                />
              )}

              {/* 社員管理タブ */}
              {tabValue === 2 && (
                <EmployeeUsageTab
                  employeeUsage={employeeUsage}
                  companyEmployees={companyEmployees}
                  isEmployeeUsageLoading={isEmployeeUsageLoading}
                  isCompanyEmployeesLoading={isCompanyEmployeesLoading}
                  isEmployeeDetailsLoading={isEmployeeDetailsLoading}
                  employeeDetails={employeeDetails}
                  onRefreshEmployeeUsage={() => fetchEmployeeUsage(true)}
                  onRefreshCompanyEmployees={() => fetchCompanyEmployees(true)}
                  onEmployeeCardClick={handleEmployeeCardClick}
                  selectedEmployee={selectedEmployee}
                  detailsDialogOpen={detailsDialogOpen}
                  onCloseDetailsDialog={handleCloseDetailsDialog}
                  showEmployeeCreateForm={showEmployeeCreateForm}
                  onToggleEmployeeCreateForm={() =>
                    setShowEmployeeCreateForm(!showEmployeeCreateForm)
                  }
                  newEmployeeEmail={newEmployeeEmail}
                  onNewEmployeeEmailChange={(email: string) =>
                    setNewEmployeeEmail(email)
                  }
                  newEmployeePassword={newEmployeePassword}
                  onNewEmployeePasswordChange={(password: string) =>
                    setNewEmployeePassword(password)
                  }
                  isEmployeeCreating={isEmployeeCreating}
                  employeeCreateError={employeeCreateError}
                  employeeCreateSuccess={employeeCreateSuccess}
                  onCreateEmployee={handleCreateEmployee}
                />
              )}

              {/* リソースタブ */}
              {tabValue === 3 && (
                <ResourcesTab
                  resources={resources}
                  isLoading={isResourcesLoading}
                  onRefresh={fetchResources}
                />
              )}

              {/* プラン履歴タブ */}
              {tabValue === 4 && (
                <PlanHistoryTab />
              )}

              {/* 料金管理タブ */}
              {tabValue === 5 && (
                <BillingTab />
              )}

              {/* デモ統計タブ - ユーザーロールでない場合のみ表示 */}
              {!isUserRole && getActualTabIndex(tabValue) === 6 && (
                <DemoStatsTab
                  demoStats={demoStats}
                  isLoading={isDemoStatsLoading}
                  onRefresh={fetchDemoStats}
                  onOpenCompanyDetails={handleOpenCompanyDetails}
                  isCompanyDetailsLoading={isCompanyDetailsLoading}
                />
              )}

              {/* ユーザー管理タブ */}
              {tabValue === (isUserRole ? 6 : 7) && (
                <UserManagementTab
                  isSpecialAdmin={isSpecialAdmin}
                  newUserEmail={newUserEmail}
                  onNewUserEmailChange={setNewUserEmail}
                  newUserPassword={newUserPassword}
                  onNewUserPasswordChange={setNewUserPassword}
                  isUserCreating={isUserCreating}
                  userCreateError={userCreateError}
                  userCreateSuccess={userCreateSuccess}
                  onCreateUser={handleCreateUser}
                  onOpenCompanyDetails={() => setSelectedCompanyId("")}
                  companies={companies}
                  selectedCompanyId={selectedCompanyId}
                  onSelectedCompanyIdChange={setSelectedCompanyId}
                  isCompaniesLoading={isCompaniesLoading}
                  user={user}
                  newCompanyName={newCompanyName}
                  onNewCompanyNameChange={setNewCompanyName}
                />
              )}
            </Box>
          </Box>
        </Paper>
      </Container>

      {/* 全体の背景グラデーション */}
      <Box
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: -1,
          backgroundImage:
            "radial-gradient(at 30% 20%, rgba(219, 234, 254, 0.4) 0px, transparent 60%), radial-gradient(at 80% 80%, rgba(191, 219, 254, 0.3) 0px, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      {/* 会社詳細ダイアログ */}
      {companyDetailsOpen && (
        <CompanyDetailsDialog
          open={companyDetailsOpen}
          onClose={handleCloseCompanyDetails}
          companyDetails={companyDetails}
          isLoading={isCompanyDetailsLoading}
          onDeleteUser={handleDeleteUser}
          isDeleting={isUserDeleting}
          deleteError={userDeleteError}
          deleteSuccess={userDeleteSuccess}
          PaperProps={{
            sx: {
              borderRadius: { xs: "16px", sm: "20px" },
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.15)",
              overflow: "hidden",
              backgroundImage:
                "linear-gradient(to bottom, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 1))",
              backdropFilter: "blur(16px)",
              p: { xs: 1.5, sm: 2, md: 3 },
              margin: { xs: 1.5, sm: 2, md: 3 },
              maxHeight: { xs: "calc(100% - 32px)", sm: "calc(100% - 64px)" },
              maxWidth: { xs: "calc(100% - 32px)", sm: 800, md: 1000 },
            },
          }}
        />
      )}
    </Box>
  );
};

export default AdminPanel;
