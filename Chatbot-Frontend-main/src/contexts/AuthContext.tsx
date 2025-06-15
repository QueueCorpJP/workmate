import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import api from "../api";

// ユーザー情報の型定義
interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  created_at: string;
  usage_limits: {
    document_uploads_used: number;
    document_uploads_limit: number;
    questions_used: number;
    questions_limit: number;
    is_unlimited: boolean;
  };
}

// 認証コンテキストの型定義
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isEmployee: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string, name: string) => Promise<void>;
  remainingQuestions: number | null;
  remainingUploads: number | null;
  isUnlimited: boolean;
  updateRemainingQuestions: (remaining: number | null) => void;
  updateRemainingUploads: (remaining: number | null) => void;
  refreshUserData: () => Promise<void>;
  loading: boolean;
}

// 認証コンテキストの作成
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 認証プロバイダーの型定義
interface AuthProviderProps {
  children: ReactNode;
}

// 認証プロバイダーコンポーネント
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [isEmployee, setIsEmployee] = useState<boolean>(false);
  const [remainingQuestions, setRemainingQuestions] = useState<number | null>(
    null
  );
  const [remainingUploads, setRemainingUploads] = useState<number | null>(null);
  const [isUnlimited, setIsUnlimited] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  // ローカルストレージからユーザー情報を読み込む
  useEffect(() => {
    const storedUser = localStorage.getItem("user");

    if (storedUser) {
      const parsedUser = JSON.parse(storedUser);
      setUser(parsedUser);
      setIsAuthenticated(true);
      setIsAdmin(parsedUser.role === "admin" || 
        (parsedUser.email && ["queue@queuefood.co.jp", "queue@queueu-tech.jp"].includes(parsedUser.email)));
      setIsEmployee(parsedUser.role === "employee");

      // 利用制限情報を設定
      if (parsedUser.usage_limits) {
        const {
          document_uploads_used,
          document_uploads_limit,
          questions_used,
          questions_limit,
          is_unlimited,
        } = parsedUser.usage_limits;
        setRemainingQuestions(
          is_unlimited ? null : questions_limit - questions_used
        );
        setRemainingUploads(
          is_unlimited ? null : document_uploads_limit - document_uploads_used
        );
        setIsUnlimited(is_unlimited);
      }
    }
    setLoading(false);
  }, []);

  // ログイン処理
  const login = async (email: string, password: string) => {
    try {
      // POSTリクエストでログイン情報を送信
      const response = await api.post(`/auth/login`, { email, password });

      const userData = response.data;
      setUser(userData);
      setIsAuthenticated(true);
      setIsAdmin(userData.role === "admin" || 
        (userData.email && ["queue@queuefood.co.jp", "queue@queueu-tech.jp"].includes(userData.email)));
      setIsEmployee(userData.role === "employee");

      // 利用制限情報を設定
      if (userData.usage_limits) {
        const {
          document_uploads_used,
          document_uploads_limit,
          questions_used,
          questions_limit,
          is_unlimited,
        } = userData.usage_limits;
        setRemainingQuestions(
          is_unlimited ? null : questions_limit - questions_used
        );
        setRemainingUploads(
          is_unlimited ? null : document_uploads_limit - document_uploads_used
        );
        setIsUnlimited(is_unlimited);
      }

      // ローカルストレージに保存
      localStorage.setItem("user", JSON.stringify(userData));
      // 認証のためにパスワードも保存（セキュリティ上の理由から実際のアプリではこの方法は推奨されません）
      localStorage.setItem("password", password);
      localStorage.setItem("companyName", userData.company_name);
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    }
  };

  // ログアウト処理
  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    setIsAdmin(false);
    setRemainingQuestions(null);
    setRemainingUploads(null);
    setIsUnlimited(false);
    localStorage.removeItem("user");
    localStorage.removeItem("password");
    localStorage.removeItem("companyName");
  };

  // ユーザー登録処理
  const register = async (email: string, password: string, name: string) => {
    try {
      const response = await api.post(`/auth/register`, {
        email,
        password,
        name,
      });
      // 登録後に自動ログイン
      await login(email, password);
    } catch (error) {
      console.error("Registration failed:", error);
      throw error;
    }
  };

  // 質問利用後に残り回数を更新
  const updateRemainingQuestions = (remaining: number | null) => {
    console.log(`updateRemainingQuestions呼び出し - 残り質問数: ${remaining}`);
    console.log(`現在の状態 - isUnlimited: ${isUnlimited}, user:`, user);
    
    if (user && !isUnlimited && remaining !== null) {
      console.log(`質問回数を${remainingQuestions}から${remaining}に更新`);
      setRemainingQuestions(remaining);

      // ユーザー情報も更新
      const updatedUser = {
        ...user,
        usage_limits: {
          ...user.usage_limits,
          questions_used: user.usage_limits.questions_limit - remaining,
        },
      };
      console.log("更新されたユーザー情報:", updatedUser);
      setUser(updatedUser);
      localStorage.setItem("user", JSON.stringify(updatedUser));
    } else {
      console.log("質問回数の更新をスキップ:", { 
        hasUser: !!user, 
        isUnlimited, 
        remaining 
      });
    }
  };

  // アップロード利用後に残り回数を更新
  const updateRemainingUploads = (remaining: number | null) => {
    if (user && !isUnlimited && remaining !== null) {
      setRemainingUploads(remaining);

      // ユーザー情報も更新
      const updatedUser = {
        ...user,
        usage_limits: {
          ...user.usage_limits,
          document_uploads_used:
            user.usage_limits.document_uploads_limit - remaining,
        },
      };
      setUser(updatedUser);
      localStorage.setItem("user", JSON.stringify(updatedUser));
    }
  };

  // ユーザー情報を更新
  const refreshUserData = async () => {
    try {
      const response = await api.get(`/auth/user`);
      const userData = response.data;
      setUser(userData);
      setIsAuthenticated(true);
      setIsAdmin(userData.role === "admin" || 
        (userData.email && ["queue@queuefood.co.jp", "queue@queueu-tech.jp"].includes(userData.email)));
      setIsEmployee(userData.role === "employee");

      // 利用制限情報を設定
      if (userData.usage_limits) {
        const {
          document_uploads_used,
          document_uploads_limit,
          questions_used,
          questions_limit,
          is_unlimited,
        } = userData.usage_limits;
        setRemainingQuestions(
          is_unlimited ? null : questions_limit - questions_used
        );
        setRemainingUploads(
          is_unlimited ? null : document_uploads_limit - document_uploads_used
        );
        setIsUnlimited(is_unlimited);
      }

      // ローカルストレージに保存
      localStorage.setItem("user", JSON.stringify(userData));
    } catch (error) {
      console.error("Failed to refresh user data:", error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isAdmin,
        isEmployee,
        login,
        logout,
        register,
        remainingQuestions,
        remainingUploads,
        isUnlimited,
        updateRemainingQuestions,
        updateRemainingUploads,
        refreshUserData,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// 認証コンテキストを使用するためのフック
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
