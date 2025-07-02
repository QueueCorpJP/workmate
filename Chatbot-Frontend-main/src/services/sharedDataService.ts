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
      0 // キャッシュを無効化 (以前は 2 * 60 * 1000)
    );
  }

  /**
   * 分析データを取得（共有キャッシュ使用）
   */
  static async getAnalysis(): Promise<any> {
    console.log('📊 [SharedDataService] getAnalysis 開始');
    
    return withSharedCache(
      'analysis-shared',
      async () => {
        console.log('📊 [SharedDataService] 分析データAPI呼び出し開始: /admin/analyze-chats');
        try {
          const response = await api.get('/admin/analyze-chats');
          console.log('📊 [SharedDataService] 分析データAPI呼び出し成功');
          console.log('📊 [SharedDataService] response.status:', response.status);
          console.log('📊 [SharedDataService] response.data:', response.data);
          console.log('📊 [SharedDataService] response.data type:', typeof response.data);
          console.log('📊 [SharedDataService] response.data keys:', response.data ? Object.keys(response.data) : 'no data');
          return response.data;
        } catch (error: any) {
          console.error('📊 [SharedDataService] 分析データAPI呼び出し失敗:', error);
          console.error('📊 [SharedDataService] error.message:', error.message);
          console.error('📊 [SharedDataService] error.response:', error.response);
          throw error;
        }
      },
      10 * 60 * 1000 // 10分キャッシュ（計算コストが高い）
    );
  }

  /**
   * 強化分析データを取得（データベース分析のみ・高速）
   */
  static async getEnhancedAnalysisDatabase(): Promise<any> {
    console.log('🔬 [SharedDataService] getEnhancedAnalysisDatabase 開始');
    
    return withSharedCache(
      'enhanced-analysis-database-shared',
      async () => {
        console.log('🔬 [SharedDataService] 強化分析データAPI呼び出し開始: /admin/enhanced-analysis?include_ai_insights=false');
        try {
          const response = await api.get('/admin/enhanced-analysis?include_ai_insights=false');
          console.log('🔬 [SharedDataService] 強化分析データAPI呼び出し成功');
          console.log('🔬 [SharedDataService] response.status:', response.status);
          console.log('🔬 [SharedDataService] response.data:', response.data);
          console.log('🔬 [SharedDataService] response.data type:', typeof response.data);
          console.log('🔬 [SharedDataService] response.data keys:', response.data ? Object.keys(response.data) : 'no data');
          return response.data;
        } catch (error: any) {
          console.error('🔬 [SharedDataService] 強化分析データAPI呼び出し失敗:', error);
          console.error('🔬 [SharedDataService] error.message:', error.message);
          console.error('🔬 [SharedDataService] error.response:', error.response);
          throw error;
        }
      },
      10 * 60 * 1000 // 10分キャッシュ
    );
  }

  /**
   * AI洞察データを取得（Gemini分析・20秒程度）
   */
  static async getAIInsights(): Promise<any> {
    return withSharedCache(
      'ai-insights-shared',
      async () => {
        console.log('🤖 AI洞察を生成中（Gemini分析・共有）...');
        const response = await api.get('/admin/ai-insights');
        return response.data;
      },
      30 * 60 * 1000 // 30分キャッシュ（Gemini処理が重いため長期保持）
    );
  }

  /**
   * 強化分析データを取得（AI洞察も含む・従来互換）
   */
  static async getEnhancedAnalysis(): Promise<any> {
    return withSharedCache(
      'enhanced-analysis-full-shared',
      async () => {
        console.log('🔄 強化分析データを取得中（AI洞察含む・共有）...');
        const response = await api.get('/admin/enhanced-analysis?include_ai_insights=true');
        return response.data;
      },
      15 * 60 * 1000 // 15分キャッシュ
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
        this.clearCache('enhanced-analysis-database-shared');
        this.clearCache('enhanced-analysis-full-shared');
        this.clearCache('ai-insights-shared');
        await this.getAnalysis();
        await this.getEnhancedAnalysisDatabase();
        break;
      case 'ai-insights':
        this.clearCache('ai-insights-shared');
        await this.getAIInsights();
        break;
      default:
        console.warn(`未知のデータタイプ: ${dataType}`);
    }
  }
} 