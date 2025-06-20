import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Session, User, AuthError } from '@supabase/supabase-js';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

type AuthContextType = {
  user: User | null;
  session: Session | null;
  userRole: string | null;
  signIn: (email: string, password: string) => Promise<{
    user: User | null;
    session: Session | null;
  }>;
  signOut: () => Promise<void>;
  loading: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Helper function to check if email matches admin emails
  const isAdminEmail = (email: string | undefined): boolean => {
    if (!email) return false;
    return email === 'queue@queuefood.co.jp' || email === 'taichi.tanigusan@gmail.com';
  };

  // Helper function to handle role setting
  const setRoleBasedOnEmail = (email: string | undefined): string => {
    const role = isAdminEmail(email) ? 'admin' : 'user';
    setUserRole(role);
    localStorage.setItem('userRole', role);
    return role;
  };

  // Helper function to handle navigation after auth state change
  const navigateBasedOnRole = (event: string, role: string) => {
    // ログアウト時のみ自動遷移
    if (event === 'SIGNED_OUT') {
      navigate('/login');
    }
  };

  useEffect(() => {
    console.log('Setting up auth state listener');
    
    // Set up auth state listener FIRST
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event);
        setSession(session);
        setUser(session?.user || null);
        
        if (session?.user) {
          const role = setRoleBasedOnEmail(session.user.email);
          navigateBasedOnRole(event, role);
        } else {
          setUserRole(null);
          localStorage.removeItem('userRole');
          
          // If signed out, redirect to login
          if (event === 'SIGNED_OUT') {
            navigate('/login');
          }
        }
        
        setLoading(false);
      }
    );

    // THEN check for existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      console.log('Initial session check:', session ? 'Found session' : 'No session');
      setSession(session);
      setUser(session?.user || null);
      
      if (session?.user) {
        setRoleBasedOnEmail(session.user.email);
      } else {
        setUserRole(null);
        localStorage.removeItem('userRole');
      }
      
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [navigate]);

  const signIn = async (email: string, password: string) => {
    setLoading(true);
    try {
      console.log(`Attempting to sign in with email: ${email}`);
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      
      if (error) {
        console.error("Sign in error:", error);
        throw error;
      }
      
      console.log("Sign in successful:", data.user?.email);
      // ログイン成功後はダッシュボードに遷移
      if (isAdminEmail(data.user?.email)) {
        navigate('/admin');
      } else {
        navigate('/dashboard');
      }
      return data;
    } catch (error: any) {
      console.error("Sign in error:", error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    setLoading(true);
    try {
      const { error } = await supabase.auth.signOut();
      if (error) {
        console.error("Sign out error:", error);
        throw error;
      }
      navigate('/login');
    } catch (error) {
      console.error("Sign out error:", error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    session,
    userRole,
    signIn,
    signOut,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
