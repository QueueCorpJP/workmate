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
import NotificationsIcon from "@mui/icons-material/Notifications";
import DescriptionIcon from "@mui/icons-material/Description";
import api from "../../api";
import { withCache } from "../../utils/cache";
import { useAuth } from "../../contexts/AuthContext";
import usePermissions from "../../utils/usePermissions";

// Import tab components
import ChatHistoryTab from "./ChatHistoryTab";
import AnalysisTab from "./AnalysisTab";
import EmployeeUsageTab from "./EmployeeUsageTab";
import ResourcesTab from "./ResourcesTab";
import DemoStatsTab from "./DemoStatsTab";
import UserManagementTab from "./UserManagementTab";
import PlanHistoryTab from "./PlanHistoryTab";
import NotificationManagementTab from "./NotificationManagementTab";
import TemplateManagementTab from "./TemplateManagementTab";
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
  const permissions = usePermissions(user);
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

  // Employee deletion states
  const [isEmployeeDeleting, setIsEmployeeDeleting] = useState(false);
  const [employeeDeleteError, setEmployeeDeleteError] = useState<string | null>(
    null
  );
  const [employeeDeleteSuccess, setEmployeeDeleteSuccess] = useState<
    string | null
  >(null);

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
    console.log("Admin Panel mounted");

    // 特別な管理者かどうかを確認（admin ロールは存在しないため削除）
    if (permissions.is_special_admin) {
      setIsSpecialAdmin(true);
    }

    // 初期データは最初のタブ（チャット履歴）のみ読み込み
    // 他のタブのデータは必要に応じて遅延読み込み
    fetchChatHistory();
  }, []);

  // チャット履歴の取得（共有サービス使用、ページネーション対応）
  const fetchChatHistory = async (loadMore: boolean = false, forceRefresh = false) => {
    setIsLoading(true);
    try {
      const { SharedDataService } = await import('../../services/sharedDataService');
      
      // ページネーションパラメータ
      const limit = 30;
      const offset = loadMore ? chatHistory.length : 0;
      
      const cacheKey = `chat-history-${limit}-${offset}`;
      
      if (forceRefresh) {
        SharedDataService.clearCache(cacheKey);
      }
      
      const data = await SharedDataService.getChatHistory({
        limit,
        offset,
        user_id: (!isSpecialAdmin && !permissions.can_create) ? JSON.parse(localStorage.getItem("user") || "{}").id : undefined
      });
      
      console.log("チャット履歴取得結果:", data);
      
      // SharedDataServiceから取得したデータを処理
      if (data && data.data && Array.isArray(data.data)) {
        if (loadMore) {
          // 既存のデータに追加
          setChatHistory(prev => [...prev, ...data.data]);
        } else {
          // 新しいデータで置き換え
          setChatHistory(data.data);
        }
        
        // ページネーション情報を保存
        const pagination = data.pagination || {};
        const newOffset = loadMore ? 
          (chatPagination.offset + data.data.length) : 
          (pagination.offset || data.offset || 0) + data.data.length;
        
        setChatPagination({
          total_count: pagination.total_count || data.total_count || 0,
          limit: pagination.limit || data.limit || 30,
          offset: newOffset,
          has_more: pagination.has_more !== undefined ? pagination.has_more : data.has_more || false
        });
        
      } else if (Array.isArray(data)) {
        // 後方互換性のため古い形式にも対応
        setChatHistory(data);
        setChatPagination({
          total_count: data.length,
          limit: data.length,
          offset: data.length,
          has_more: false
        });
      } else {
        console.error(
          "チャット履歴のレスポンスが想定される形式ではありません:",
          data
        );
        setChatHistory([]);
        setChatPagination({
          total_count: 0,
          limit: 30,
          offset: 0,
          has_more: false
        });
      }
    } catch (error: any) {
      console.error("チャット履歴の取得に失敗しました:", error);
      alert(
        "チャット履歴の取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
    } finally {
      setIsLoading(false);
    }
  };

  // 強化分析データの状態
  const [enhancedAnalysis, setEnhancedAnalysis] = useState<any>(null);
  const [isEnhancedAnalysisLoading, setIsEnhancedAnalysisLoading] = useState(false);

  // 分析データの取得（共有サービス使用、強化分析も並行取得）
  const fetchAnalysis = async (forceRefresh = false) => {
    console.log("🔍 [DEBUG] fetchAnalysis 開始");
    console.log("🔍 [DEBUG] 現在の analysis:", analysis);
    console.log("🔍 [DEBUG] forceRefresh:", forceRefresh);
    
    // 既に実行中の場合はスキップ
    if (isAnalysisLoading || isEnhancedAnalysisLoading) {
      console.log("🔍 [DEBUG] 既に分析中のためスキップ");
      return;
    }
    
    // 強制更新でない場合、既存データがあればスキップ
    if (!forceRefresh && analysis && Object.keys(analysis.category_distribution || {}).length > 0 && enhancedAnalysis) {
      console.log("🔍 [DEBUG] 既に有効なデータがあるためスキップ");
      return;
    }

    console.log("🔍 [DEBUG] ローディング状態を開始");
    setIsAnalysisLoading(true);
    setIsEnhancedAnalysisLoading(true);
    
    try {
      console.log("🔍 [DEBUG] SharedDataService をインポート");
      const { SharedDataService } = await import('../../services/sharedDataService');
      
      if (forceRefresh) {
        console.log("🔍 [DEBUG] キャッシュをクリア");
        SharedDataService.clearCache('analysis-shared');
        SharedDataService.clearCache('enhanced-analysis-database-shared');
        SharedDataService.clearCache('ai-insights-shared');
      }
      
      console.log("🔍 [DEBUG] 基本分析とデータベース強化分析を並行取得開始");
      // 基本分析とデータベース強化分析を並行取得（AbortSignal削除）
      const [basicData, enhancedDatabaseData] = await Promise.allSettled([
        SharedDataService.getAnalysis(),
        SharedDataService.getEnhancedAnalysisDatabase()
      ]);
      
      console.log("🔍 [DEBUG] Promise.allSettled 完了");
      console.log("🔍 [DEBUG] basicData.status:", basicData.status);
      console.log("🔍 [DEBUG] enhancedDatabaseData.status:", enhancedDatabaseData.status);
      
      // 基本分析データの処理
      if (basicData.status === 'fulfilled') {
        const data = basicData.value;
        console.log("🔍 [DEBUG] チャット分析取得結果:", data);
        console.log("🔍 [DEBUG] データ型:", typeof data);
        console.log("🔍 [DEBUG] データのキー:", data ? Object.keys(data) : "null/undefined");
        
        if (data && typeof data === "object") {
          const analysisData = data as any;
          
          // 必要なプロパティがない場合は初期化
          if (!("category_distribution" in analysisData)) {
            console.log("🔍 [DEBUG] category_distribution を初期化");
            analysisData.category_distribution = {};
          }
          if (!("sentiment_distribution" in analysisData)) {
            console.log("🔍 [DEBUG] sentiment_distribution を初期化");
            analysisData.sentiment_distribution = {};
          }
          if (!("common_questions" in analysisData)) {
            console.log("🔍 [DEBUG] common_questions を初期化");
            analysisData.common_questions = [];
          } else if (!Array.isArray(analysisData.common_questions)) {
            console.log("🔍 [DEBUG] common_questions を配列に変換");
            analysisData.common_questions = [];
          }
          if (!("daily_usage" in analysisData)) {
            console.log("🔍 [DEBUG] daily_usage を初期化");
            analysisData.daily_usage = [];
          }
          
          console.log("🔍 [DEBUG] 最終的な analysisData:", analysisData);
          console.log("🔍 [DEBUG] setAnalysis を実行");
          setAnalysis(analysisData);
        } else {
          console.error("🔍 [ERROR] チャット分析のレスポンスが有効なオブジェクトではありません:", data);
          const fallbackData = {
            category_distribution: {},
            sentiment_distribution: {},
            common_questions: [],
            insights: "データの取得に失敗しました。",
          };
          console.log("🔍 [DEBUG] フォールバックデータを設定:", fallbackData);
          setAnalysis(fallbackData);
        }
      } else {
        console.error("🔍 [ERROR] 基本分析の取得に失敗:", basicData.reason);
      }
      
      // データベース強化分析データの処理（AI洞察なし）
      if (enhancedDatabaseData.status === 'fulfilled') {
        console.log("🔍 [DEBUG] データベース強化分析取得結果:", enhancedDatabaseData.value);
        const databaseAnalysis = enhancedDatabaseData.value;
        console.log("🔍 [DEBUG] databaseAnalysis 型:", typeof databaseAnalysis);
        console.log("🔍 [DEBUG] databaseAnalysis キー:", databaseAnalysis ? Object.keys(databaseAnalysis) : "null/undefined");
        
        // AI洞察は空文字列で設定（後で追加可能）
        if (databaseAnalysis) {
          databaseAnalysis.ai_insights = databaseAnalysis.ai_insights || "";
          console.log("🔍 [DEBUG] setEnhancedAnalysis を実行");
          setEnhancedAnalysis(databaseAnalysis);
        } else {
          console.log("🔍 [DEBUG] databaseAnalysis が null のため setEnhancedAnalysis(null) を実行");
          setEnhancedAnalysis(null);
        }
      } else {
        console.error("🔍 [ERROR] データベース強化分析の取得に失敗:", enhancedDatabaseData.reason);
        setEnhancedAnalysis(null);
      }
      
    } catch (error: any) {
      console.error("🔍 [ERROR] 分析データの取得に失敗しました:", error);
      console.error("🔍 [ERROR] エラーの詳細:", error.stack);
      // エラーメッセージを表示
      alert(
        "分析データの取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
    } finally {
      console.log("🔍 [DEBUG] ローディング状態を終了");
      setIsAnalysisLoading(false);
      setIsEnhancedAnalysisLoading(false);
      console.log("🔍 [DEBUG] fetchAnalysis 完了");
    }
  };

  // AI洞察のみを取得する関数
  const fetchAIInsights = async () => {
    if (!enhancedAnalysis) {
      console.warn('データベース分析が完了していないため、AI洞察を取得できません');
      return;
    }
    
    // 既にAI洞察がある場合はスキップ
    if (enhancedAnalysis.ai_insights && enhancedAnalysis.ai_insights.trim()) {
      console.log('AI洞察は既に取得済みです');
      return;
    }
    
    setIsEnhancedAnalysisLoading(true);
    
    try {
      console.log("🤖 AI洞察生成開始...");
      const { SharedDataService } = await import('../../services/sharedDataService');
      
      const aiInsightsData = await SharedDataService.getAIInsights();
      
      console.log("🤖 AI洞察取得結果:", aiInsightsData);
      
      // 既存の強化分析データにAI洞察を追加
      if (enhancedAnalysis && aiInsightsData.ai_insights) {
        const updatedAnalysis = {
          ...enhancedAnalysis,
          ai_insights: aiInsightsData.ai_insights
        };
        setEnhancedAnalysis(updatedAnalysis);
        console.log("🤖 AI洞察が正常に統合されました");
      }
      
    } catch (error: any) {
      console.error("AI洞察の生成に失敗しました:", error);
      
      // エラー時は既存のデータにエラーメッセージを設定
      if (enhancedAnalysis) {
        const updatedAnalysis = {
          ...enhancedAnalysis,
          ai_insights: `AI洞察の生成に失敗しました: ${error.message || 'ネットワークエラー'}`
        };
        setEnhancedAnalysis(updatedAnalysis);
      }
    } finally {
      setIsEnhancedAnalysisLoading(false);
    }
  };

  // 会社の管理者用アカウント利用状況の取得（共有サービス使用）
  const fetchEmployeeUsage = async (forceRefresh = false) => {
    if (employeeUsage.length > 0 && !forceRefresh) return;

    setIsEmployeeUsageLoading(true);
    try {
      const { SharedDataService } = await import('../../services/sharedDataService');
      if (forceRefresh) {
        SharedDataService.clearCache('employee-usage-shared');
      }
      const data = await SharedDataService.getEmployeeUsage();
      console.log("従業員利用状況取得結果:", data);
      
      // SharedDataServiceから取得したデータを直接使用
      if (
        data &&
        typeof data === "object" &&
        "employee_usage" in data &&
        Array.isArray(data.employee_usage)
      ) {
        setEmployeeUsage(data.employee_usage);
      } else if (Array.isArray(data)) {
        // 直接配列が返される場合
        setEmployeeUsage(data);
      } else {
        console.error(
          "社員利用状況のレスポンスが有効なオブジェクトではありません:",
          data
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

  // 会社の全社員情報を取得（共有サービス使用）
  const fetchCompanyEmployees = async (forceRefresh = false) => {
    if (companyEmployees.length > 0 && !forceRefresh) return; // 既に有効なデータがある場合は何もしない（強制更新フラグがない場合）

    setIsCompanyEmployeesLoading(true);
    try {
      const { SharedDataService } = await import('../../services/sharedDataService');
      if (forceRefresh) {
        SharedDataService.clearCache('company-employees-shared');
      }
      const data = await SharedDataService.getCompanyEmployees();
      console.log("会社の全社員情報取得結果:", data);

      // SharedDataServiceから取得したデータを直接使用
      if (Array.isArray(data)) {
        setCompanyEmployees(data);
      } else if (
        data &&
        typeof data === "object" &&
        "employees" in data &&
        Array.isArray((data as any).employees)
      ) {
        // 後方互換性のために残す
        setCompanyEmployees((data as any).employees);
      } else {
        console.error(
          "会社の全社員情報のレスポンスが有効なオブジェクトではありません:",
          data
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

  // アップロードされたリソースの取得（共有サービス使用）
  const fetchResources = async (forceRefresh = false) => {
    console.log("🔍 [FRONTEND DEBUG] fetchResources 開始");
    setIsResourcesLoading(true);
    try {
      const { SharedDataService } = await import('../../services/sharedDataService');
      if (forceRefresh) {
        SharedDataService.clearCache('resources-shared');
      }
      const data = await SharedDataService.getResources();
      console.log("リソース取得結果:", data);
      
      // SharedDataServiceから取得したデータを直接使用
      if (Array.isArray(data)) {
        console.log("🔍 [FRONTEND DEBUG] リソース配列の長さ:", data.length);
        setResources(data);
        console.log("🔍 [FRONTEND DEBUG] setResources 完了");
      } else if (
        data &&
        typeof data === "object" &&
        "resources" in data &&
        Array.isArray((data as any).resources)
      ) {
        console.log("🔍 [FRONTEND DEBUG] リソース配列の長さ:", (data as any).resources.length);
        setResources((data as any).resources);
        console.log("🔍 [FRONTEND DEBUG] setResources 完了");
      } else {
        console.error("🔍 [FRONTEND DEBUG] レスポンス検証失敗");
        console.error("  - dataタイプ:", typeof data);
        console.error("  - 'resources'プロパティ存在:", data && "resources" in data);
        console.error(
          "リソースのレスポンスが有効なオブジェクトではありません:",
          data
        );
        setResources([]);
      }
    } catch (error: any) {
      console.error("🔍 [FRONTEND DEBUG] fetchResourcesエラー:", error);
      console.error("🔍 [FRONTEND DEBUG] エラー詳細:", {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        response: error && typeof error === 'object' && 'response' in error ? (error as any).response : undefined,
        request: error && typeof error === 'object' && 'request' in error ? (error as any).request : undefined
      });
      console.error("リソースの取得に失敗しました:", error);
      // エラーメッセージを表示
      alert(
        "リソースの取得に失敗しました。バックエンドサーバーが起動しているか確認してください。"
      );
    } finally {
      setIsResourcesLoading(false);
      console.log("🔍 [FRONTEND DEBUG] fetchResources 完了 (isResourcesLoading = false)");
    }
  };

  // デモ利用状況の取得（共有サービス使用）
  const fetchDemoStats = async (forceRefresh = false) => {
    setIsDemoStatsLoading(true);
    try {
      const { SharedDataService } = await import('../../services/sharedDataService');
      if (forceRefresh) {
        SharedDataService.clearCache('demo-stats-shared');
      }
      const data = await SharedDataService.getDemoStats();
      console.log("デモ利用状況取得結果:", data);
      setDemoStats(data);
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

      // ユーザー作成成功後、関連データのキャッシュをクリアして再読み込み
      console.log("ユーザー作成成功 - キャッシュクリアと再読み込み開始");
      const { SharedDataService } = await import('../../services/sharedDataService');
      
      // 社員関連のキャッシュをクリア
      SharedDataService.clearCache('company-employees-shared');
      SharedDataService.clearCache('employee-usage-shared');
      
      // 社員データを強制再読み込み
      await fetchCompanyEmployees(true);
      await fetchEmployeeUsage(true);
      
      console.log("ユーザー作成後のデータ更新完了");
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

  // コンポーネントがアンマウントされる際のクリーンアップ
  useEffect(() => {
    return () => {
      console.log('🧹 AdminPanel: コンポーネントアンマウント');
    };
  }, []);

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
      const response = await api.post("/admin/register-user", {
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
        ? `/admin/employee-details/${employeeId}`
        : `/admin/employee-details/${employeeId}?user_id=${userId}`;
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

  // 社員削除ハンドラー
  const handleDeleteEmployee = async (userId: string, userEmail: string) => {
    setIsEmployeeDeleting(true);
    setEmployeeDeleteError(null);
    setEmployeeDeleteSuccess(null);

    try {
      console.log(`社員 ${userId} を削除中...`);
      const response = await api.delete(`/admin/delete-user/${userId}`);
      console.log("社員削除結果:", response.data);
      setEmployeeDeleteSuccess(`社員 ${userEmail} を削除しました`);
      
      // 削除後に社員リストを更新
      await fetchCompanyEmployees(true);
      await fetchEmployeeUsage(true);
    } catch (error: any) {
      console.error("社員削除に失敗しました:", error);
      setEmployeeDeleteError(
        error.response?.data?.detail || "社員削除に失敗しました"
      );
    } finally {
      setIsEmployeeDeleting(false);
    }
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
    {
      icon: <DescriptionIcon sx={{ color: "#3b82f6" }} />,
      label: "テンプレート",
      ariaLabel: "テンプレート管理タブ",
    },
    ...(permissions.is_special_admin
      ? [
        {
          icon: <QueryStatsIcon sx={{ color: "#3b82f6" }} />,
          label: "デモ統計",
          ariaLabel: "デモ統計タブ",
        },
      ]
      : []),
    ...(permissions.is_special_admin
      ? [
        {
          icon: <NotificationsIcon sx={{ color: "#3b82f6" }} />,
          label: "通知管理",
          ariaLabel: "通知管理タブ",
        },
      ]
      : []),
    {
      icon: <PersonAddIcon sx={{ color: "#3b82f6" }} />,
      label: "ユーザー管理",
      ariaLabel: "ユーザー管理タブ",
    },
  ];

  // タブが変更されたときの実際のインデックスを計算する関数
  const getActualTabIndex = (visibleIndex: number) => {
    let adjustment = 0;
    
    // デモ統計タブがスキップされる場合
    if (!permissions.is_special_admin && visibleIndex >= 7) {
      adjustment += 1;
    }
    
    // 通知管理タブは管理者なら表示されるので調整不要
    
    return visibleIndex + adjustment;
  };

  // タブが変更されたときのハンドラ（キャッシュ活用で高速化）
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);

    // タブに応じてデータを取得（キャッシュがあれば即座に表示）
    const actualTabIndex = getActualTabIndex(newValue);
    switch (actualTabIndex) {
      case 0: // チャット履歴
        if (chatHistory.length === 0) {
          fetchChatHistory();
        }
        break;
      case 1: // 分析
        console.log("📋 [TAB_CHANGE] 分析タブに切り替え");
        console.log("📋 [TAB_CHANGE] 現在の analysis:", analysis);
        console.log("📋 [TAB_CHANGE] 現在の enhancedAnalysis:", enhancedAnalysis);
        
        // データがない場合のみ自動で取得（重複取得を防止）
        if (!analysis || Object.keys(analysis?.category_distribution || {}).length === 0 || !enhancedAnalysis) {
          console.log("📋 [TAB_CHANGE] 分析データが不足しているため fetchAnalysis() を実行");
          fetchAnalysis();
        } else {
          console.log("📋 [TAB_CHANGE] 分析データが既に存在するためスキップ");
        }
        break;
      case 2: // 社員管理
        if (employeeUsage.length === 0) {
          fetchEmployeeUsage(); // forceRefresh削除でキャッシュ活用
        }
        if (companyEmployees.length === 0) {
          fetchCompanyEmployees(); // forceRefresh削除でキャッシュ活用
        }
        break;
      case 3: // リソース
        if (resources.length === 0) {
          fetchResources();
        }
        break;
      case 4: // プラン履歴
        // プラン履歴は内部で自動読み込みするため何もしない
        break;
      case 5: // 料金管理
        // 料金管理は内部で自動読み込みするため何もしない
        break;
      case 6: // テンプレート管理
        // テンプレート管理は内部で自動読み込みするため何もしない
        break;
      case 7: // デモ統計 (queue@queueu-tech.jpのみ)
        if (permissions.is_special_admin && (!demoStats || Object.keys(demoStats).length === 0)) {
          fetchDemoStats();
        }
        break;
      case 8: // 通知管理 (管理者のみ)
        // 通知管理は内部で自動読み込みするため何もしない
        break;
      default: // ユーザー管理タブ（最後のタブ）
        if (actualTabIndex === tabDefinitions.length - 1) {
          // ユーザー管理タブの場合、必要に応じてデータを取得
          if (isSpecialAdmin && companies.length === 0) {
            fetchCompanies();
          }
        }
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
                  onRefresh={() => fetchChatHistory(false, true)} // 強制更新
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
                  enhancedAnalysis={enhancedAnalysis}
                  isEnhancedLoading={isEnhancedAnalysisLoading}
                  onRefresh={() => fetchAnalysis(true)} // 強制更新
                  onStartAnalysis={() => fetchAnalysis(true)} // 手動分析開始
                  onStartAIInsights={fetchAIInsights} // AI洞察開始
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
                  onDeleteEmployee={handleDeleteEmployee}
                  isEmployeeDeleting={isEmployeeDeleting}
                  employeeDeleteError={employeeDeleteError}
                  employeeDeleteSuccess={employeeDeleteSuccess}
                />
              )}

              {/* リソースタブ */}
              {tabValue === 3 && (
                <ResourcesTab
                  resources={resources}
                  isLoading={isResourcesLoading}
                  onRefresh={() => fetchResources(true)} // 強制更新
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

              {/* テンプレート管理タブ */}
              {tabValue === 6 && (
                <TemplateManagementTab user={user} />
              )}

              {/* デモ統計タブ - queue@queueu-tech.jpのみ表示 */}
              {permissions.is_special_admin && getActualTabIndex(tabValue) === 7 && (
                <DemoStatsTab
                  demoStats={demoStats}
                  isLoading={isDemoStatsLoading}
                  onRefresh={fetchDemoStats}
                  onOpenCompanyDetails={handleOpenCompanyDetails}
                  isCompanyDetailsLoading={isCompanyDetailsLoading}
                />
              )}

              {/* 通知管理タブ - 最高権限管理者のみ表示 */}
              {permissions.is_special_admin && getActualTabIndex(tabValue) === 8 && (
                <NotificationManagementTab />
              )}

              {/* ユーザー管理タブ */}
              {tabValue === (tabDefinitions.length - 1) && (
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
