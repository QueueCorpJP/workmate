import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import {
  ThemeProvider,
  createTheme,
  responsiveFontSizes,
} from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { useState, useEffect } from "react";
import ChatInterface from "./ChatInterface";
import AdminPanel from "./AdminPanel";
import CompanySettings from "./CompanySettings";
import CompanyNameModal from "./CompanyNameModal";
import LoginPage from "./LoginPage";
import UserGuide from "./UserGuide";
import GuideBook from "./GuideBook";
import { CompanyProvider, useCompany } from "./contexts/CompanyContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { jaJP } from "@mui/material/locale";
import LoadingIndicator from "./components/admin/LoadingIndicator";

// レスポンシブ対応のためのテーマを作成
let theme = createTheme(
  {
    palette: {
      primary: {
        main: "#2563eb", // Modern blue
        light: "#3b82f6",
        dark: "#1d4ed8",
        contrastText: "#ffffff",
      },
      secondary: {
        main: "#60a5fa", // Lighter blue for secondary actions
        light: "#93c5fd",
        dark: "#3b82f6",
        contrastText: "#ffffff",
      },
      background: {
        default: "#f8fafc",
        paper: "#ffffff",
      },
      text: {
        primary: "#1e293b",
        secondary: "#64748b",
      },
      divider: "rgba(0, 0, 0, 0.06)",
      action: {
        active: "#2563eb",
        hover: "rgba(37, 99, 235, 0.08)",
        selected: "rgba(37, 99, 235, 0.12)",
        disabled: "rgba(0, 0, 0, 0.26)",
        disabledBackground: "rgba(0, 0, 0, 0.04)",
      },
    },
    typography: {
      fontFamily:
        '"Noto Sans JP", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      h1: {
        fontSize: "2.5rem",
        fontWeight: 700,
        lineHeight: 1.3,
      },
      h2: {
        fontSize: "2rem",
        fontWeight: 700,
        lineHeight: 1.35,
      },
      h3: {
        fontSize: "1.75rem",
        fontWeight: 600,
        lineHeight: 1.4,
      },
      h4: {
        fontSize: "1.5rem",
        fontWeight: 600,
        lineHeight: 1.4,
      },
      h5: {
        fontSize: "1.25rem",
        fontWeight: 500,
        lineHeight: 1.5,
      },
      h6: {
        fontSize: "1rem",
        fontWeight: 500,
        lineHeight: 1.5,
      },
      button: {
        textTransform: "none",
        fontWeight: 500,
      },
      body1: {
        lineHeight: 1.6,
      },
      body2: {
        lineHeight: 1.6,
      },
    },
    shape: {
      borderRadius: 10,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            padding: "8px 20px",
            transition: "all 0.2s ease",
            fontWeight: 500,
          },
          containedPrimary: {
            boxShadow: "0 4px 14px rgba(37, 99, 235, 0.25)",
            "&:hover": {
              boxShadow: "0 6px 20px rgba(37, 99, 235, 0.35)",
              transform: "translateY(-1px)",
            },
          },
          outlined: {
            borderWidth: 1.5,
            "&:hover": {
              borderWidth: 1.5,
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.05)",
          },
          elevation1: {
            boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08)",
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            "& .MuiOutlinedInput-root": {
              borderRadius: 10,
              transition: "all 0.2s",
              "&.Mui-focused": {
                boxShadow: "0 0 0 3px rgba(37, 99, 235, 0.15)",
              },
            },
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow: "0 2px 10px rgba(0, 0, 0, 0.06)",
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
            overflow: "hidden",
            transition: "all 0.3s ease",
            "&:hover": {
              boxShadow: "0 6px 16px rgba(0, 0, 0, 0.1)",
              transform: "translateY(-2px)",
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            fontWeight: 500,
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: 10,
          },
        },
      },
      MuiDivider: {
        styleOverrides: {
          root: {
            borderColor: "rgba(0, 0, 0, 0.06)",
          },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: "none",
            fontWeight: 500,
            fontSize: "0.9rem",
          },
        },
      },
    },
    breakpoints: {
      values: {
        xs: 0,
        sm: 600,
        md: 960,
        lg: 1280,
        xl: 1920,
      },
    },
  },
  jaJP
);

// テーマをレスポンシブに
theme = responsiveFontSizes(theme);

// 認証が必要なルートのラッパー
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// 管理者専用ルートのラッパー
const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isAdmin, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!isAdmin && !(user && user.role === "user")) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

// AppContent コンポーネント - CompanyProvider と AuthProvider の中で使用するため
function AppContent() {
  const { isAuthenticated, isEmployee, loading, isAdmin } = useAuth();
  const { companyName, companyNameLoading } = useCompany();
  const [showCompanyModal, setShowCompanyModal] = useState(false);

  // 会社名が設定されているかチェック
  useEffect(() => {
    if (isAuthenticated && !(isEmployee || isAdmin) && !companyName) {
      setShowCompanyModal(true);
    } else {
      setShowCompanyModal(false);
    }
  }, [companyName, isAuthenticated, isEmployee]);

  if (loading || companyNameLoading) {
    return <LoadingIndicator />;
  }

  return (
    <>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/guide" element={<GuideBook />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <ChatInterface />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminPanel />
              </AdminRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <CompanySettings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/user-guide"
            element={
              <ProtectedRoute>
                <UserGuide />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>

      {/* 会社名設定モーダル */}
      {showCompanyModal && (
        <CompanyNameModal
          open={showCompanyModal}
          onClose={() => setShowCompanyModal(false)}
        />
      )}
    </>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <CompanyProvider>
          <AppContent />
        </CompanyProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
