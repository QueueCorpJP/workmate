import api from '../api';
import { withSharedCache, cache } from '../utils/cache';

// 共通で使用されるデータタイプ
export interface PlanHistoryItem {
  id: string;
  user_id: string;
  user_name?: string;
  user_email?: string;
  from_plan: string;
  to_plan: string;
  changed_at: string;
  duration_days: number | null;
}

export interface PlanHistoryResponse {
  history: PlanHistoryItem[];
  analytics: any;
}

export interface TokenUsageData {
  total_tokens_used: number;
  basic_plan_limit: number;
  current_month_cost: number;
  usage_percentage: number;
  remaining_tokens: number;
  warning_level: 'safe' | 'warning' | 'critical';
  company_users_count: number;
  company_name: string;
}

/**
 * 共有データサービス - 重複API呼び出しを防ぐ
 */
export class SharedDataService {
  
  /**
   * プラン履歴データを取得（共有キャッシュ使用）
   */
  static async getPlanHistory(): Promise<PlanHistoryResponse> {
    return withSharedCache(
      'plan-history-shared',
      async () => {
        console.log('🔄 プラン履歴を取得中（共有）...');
        const response = await api.get('/plan-history');
        return response.data;
      },
      2 * 60 * 1000 // 2分キャッシュ
    );
  }

  /**
   * 特定ユーザーのプラン履歴を取得
   */
  static async getUserPlanHistory(userId: string): Promise<PlanHistoryItem[]> {
    const data = await this.getPlanHistory();
    return data.history.filter(item => item.user_id === userId);
  }

  /**
   * トークン使用量データを取得（共有キャッシュ使用）
   */
  static async getTokenUsage(): Promise<TokenUsageData> {
    return withSharedCache(
      'token-usage-shared',
      async () => {
        console.log('🔄 トークン使用量を取得中（共有）...');
        try {
          const response = await api.get('/company-token-usage-with-prompts');
          return response.data;
        } catch (error) {
          console.warn('プロンプト付きトークン使用量取得に失敗、フォールバック中...');
          const fallbackResponse = await api.get('/company-token-usage');
          return fallbackResponse.data;
        }
      },
      1 * 60 * 1000 // 1分キャッシュ（リアルタイム性重要）
    );
  }

  /**
   * 会社の従業員データを取得（共有キャッシュ使用）
   */
  static async getCompanyEmployees(): Promise<any[]> {
    return withSharedCache(
      'company-employees-shared',
      async () => {
        console.log('🔄 会社従業員データを取得中（共有）...');
        const response = await api.get('/admin/company-employees');
        return response.data;
      },
      5 * 60 * 1000 // 5分キャッシュ
    );
  }

  /**
   * 従業員利用状況を取得（共有キャッシュ使用）
   */
  static async getEmployeeUsage(): Promise<any[]> {
    return withSharedCache(
      'employee-usage-shared',
      async () => {
        console.log('🔄 従業員利用状況を取得中（共有）...');
        const response = await api.get('/admin/employee-usage');
        return response.data;
      },
      3 * 60 * 1000 // 3分キャッシュ
    );
  }

  /**
   * チャット履歴を取得（共有キャッシュ使用）
   */
  static async getChatHistory(params: {
    limit?: number;
    offset?: number;
    user_id?: string;
  } = {}): Promise<any> {
    const cacheKey = `chat-history-${JSON.stringify(params)}`;
    
    return withSharedCache(
      cacheKey,
      async () => {
        console.log('🔄 チャット履歴を取得中（共有）...');
        const searchParams = new URLSearchParams();
        
        if (params.limit) searchParams.append('limit', params.limit.toString());
        if (params.offset) searchParams.append('offset', params.offset.toString());
        if (params.user_id) searchParams.append('user_id', params.user_id);
        
        const url = `/admin/chat-history${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
        const response = await api.get(url);
        return response.data;
      },
      2 * 60 * 1000 // 2分キャッシュ
    );
  }

  /**
   * 分析データを取得（共有キャッシュ使用）
   */
  static async getAnalysis(): Promise<any> {
    return withSharedCache(
      'analysis-shared',
      async () => {
        console.log('🔄 分析データを取得中（共有）...');
        const response = await api.get('/admin/analyze-chats');
        return response.data;
      },
      10 * 60 * 1000 // 10分キャッシュ（計算コストが高い）
    );
  }

  /**
   * 強化分析データを取得（共有キャッシュ使用）
   */
  static async getEnhancedAnalysis(): Promise<any> {
    return withSharedCache(
      'enhanced-analysis-shared',
      async () => {
        console.log('🔄 強化分析データを取得中（共有）...');
        const response = await api.get('/admin/enhanced-analysis');
        return response.data;
      },
      10 * 60 * 1000 // 10分キャッシュ
    );
  }

  /**
   * リソースデータを取得（共有キャッシュ使用）
   */
  static async getResources(): Promise<any[]> {
    return withSharedCache(
      'resources-shared',
      async () => {
        console.log('🔄 リソースデータを取得中（共有）...');
        const response = await api.get('/admin/resources');
        return response.data;
      },
      5 * 60 * 1000 // 5分キャッシュ
    );
  }

  /**
   * デモ統計を取得（共有キャッシュ使用）
   */
  static async getDemoStats(): Promise<any> {
    return withSharedCache(
      'demo-stats-shared',
      async () => {
        console.log('🔄 デモ統計を取得中（共有）...');
        const response = await api.get('/admin/demo-stats');
        return response.data;
      },
      5 * 60 * 1000 // 5分キャッシュ
    );
  }

  /**
   * 会社一覧を取得（共有キャッシュ使用）
   */
  static async getCompanies(): Promise<any[]> {
    return withSharedCache(
      'companies-shared',
      async () => {
        console.log('🔄 会社一覧を取得中（共有）...');
        const response = await api.get('/admin/companies');
        return response.data;
      },
      15 * 60 * 1000 // 15分キャッシュ（変更頻度が低い）
    );
  }

  /**
   * ユーザーデータを取得（ユーザー固有）
   */
  static async getUserData(): Promise<any> {
    return withSharedCache(
      'user-data-current',
      async () => {
        console.log('🔄 ユーザーデータを取得中...');
        const response = await api.get('/auth/user');
        return response.data;
      },
      5 * 60 * 1000 // 5分キャッシュ
    );
  }

  /**
   * キャッシュを強制クリア
   */
  static clearCache(key?: string): void {
    if (key) {
      cache.clear(key);
      console.log(`🗑️ キャッシュクリア: ${key}`);
    } else {
      cache.clear();
      console.log('🗑️ 全キャッシュクリア');
    }
  }

  /**
   * 特定データタイプのキャッシュを更新
   */
  static async refreshData(dataType: string): Promise<void> {
    switch (dataType) {
      case 'plan-history':
        this.clearCache('plan-history-shared');
        await this.getPlanHistory();
        break;
      case 'token-usage':
        this.clearCache('token-usage-shared');
        await this.getTokenUsage();
        break;
      case 'employee-usage':
        this.clearCache('employee-usage-shared');
        await this.getEmployeeUsage();
        break;
      case 'analysis':
        this.clearCache('analysis-shared');
        this.clearCache('enhanced-analysis-shared');
        await this.getAnalysis();
        await this.getEnhancedAnalysis();
        break;
      default:
        console.warn(`未知のデータタイプ: ${dataType}`);
    }
  }
} 