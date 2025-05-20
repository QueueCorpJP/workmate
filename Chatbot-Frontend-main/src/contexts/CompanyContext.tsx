import React, {
  createContext,
  useState,
  useContext,
  useEffect,
  ReactNode,
} from "react";
import api from "../api";

// デフォルト値（空文字列）
const DEFAULT_COMPANY_NAME = "";

// コンテキストの型定義
interface CompanyContextType {
  companyName: string;
  setCompanyName: (name: string) => void;
  companyNameLoading: boolean;
}

// コンテキストの作成
const CompanyContext = createContext<CompanyContextType | undefined>(undefined);

// プロバイダーコンポーネントの型定義
interface CompanyProviderProps {
  children: ReactNode;
}

// プロバイダーコンポーネント
export const CompanyProvider: React.FC<CompanyProviderProps> = ({
  children,
}) => {
  // ローカルストレージから社名を取得、なければデフォルト値を使用
  const [companyName, setCompanyName] = useState<string>(() => {
    const savedName = localStorage.getItem("companyName");
    return savedName || DEFAULT_COMPANY_NAME;
  });

  const [companyNameLoading, setCompanyNameLoading] = useState<boolean>(true);

  // 初期ロード時にバックエンドから会社名を取得
  useEffect(() => {
    const storedCompanyName = localStorage.getItem("companyName");
    if (storedCompanyName) {
      setCompanyName(storedCompanyName);
    }
    setCompanyNameLoading(false);
  }, []);

  // 社名が変更されたらローカルストレージに保存
  useEffect(() => {
    localStorage.setItem("companyName", companyName);
  }, [companyName]);

  return (
    <CompanyContext.Provider
      value={{ companyName, setCompanyName, companyNameLoading }}
    >
      {children}
    </CompanyContext.Provider>
  );
};

// カスタムフック
export const useCompany = (): CompanyContextType => {
  const context = useContext(CompanyContext);
  if (context === undefined) {
    throw new Error("useCompany must be used within a CompanyProvider");
  }
  return context;
};
