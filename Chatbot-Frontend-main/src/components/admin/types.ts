// Admin panel type definitions

export interface ChatHistoryItem {
  id: string;
  user_message: string;
  bot_response: string;
  timestamp: string;
  category: string;
  sentiment: string;
  employee_id?: string;
  employee_name?: string;
}

export interface AnalysisResult {
  total_messages?: number;
  average_response_time?: number;
  category_distribution: Record<string, number> | Array<{category: string, count: number}>;
  sentiment_distribution: Record<string, number> | Array<{sentiment: string, count: number}>;
  common_questions?: string[] | Array<{ question: string; count: number }>;
  daily_usage?: Array<{date: string, count: number}>;
  insights?: string;
  detailed_topic_analysis?: string;
  efficiency_opportunities?: string;
  frustration_points?: string;
  improvement_suggestions?: string;
  communication_gaps?: string;
  specific_recommendations?: string;
  business_analysis_completed?: boolean;
  source_data?: any[];
}

export interface EmployeeUsageItem {
  employee_id: string;
  employee_name: string;
  message_count: number;
  last_activity: string;
  top_categories: Array<{ category: string; count: number }>;
  recent_questions: string[];
}

export interface CompanyEmployee {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
  last_activity?: string;
  message_count?: number;
  is_demo?: boolean;
  usage_limits?: {
    is_unlimited: boolean;
    is_demo?: boolean;
    questions_used: number;
    questions_limit: number;
    document_uploads_used: number;
    document_uploads_limit: number;
  };
}

export interface Resource {
  id: string;
  name: string;
  type: string;
  timestamp: string;
  active: boolean;
  page_count?: number;
  uploaded_by?: string;
  uploader_name?: string;
  usage_count?: number;
  last_used?: string;
}

export interface DemoStats {
  total_users: number;
  active_users: number;
  total_documents: number;
  total_questions: number;
  limit_reached_users: number;
  error_rate?: string;
}

// Color configurations
export const categoryColors = [
  "rgba(54, 162, 235, 0.6)",
  "rgba(255, 99, 132, 0.6)",
  "rgba(255, 206, 86, 0.6)",
  "rgba(75, 192, 192, 0.6)",
  "rgba(153, 102, 255, 0.6)",
  "rgba(255, 159, 64, 0.6)",
  "rgba(199, 199, 199, 0.6)",
];

export const sentimentColors: Record<string, string> = {
  ポジティブ: "rgba(75, 192, 192, 0.6)",
  ネガティブ: "rgba(255, 99, 132, 0.6)",
  ニュートラル: "rgba(255, 206, 86, 0.6)",
  neutral: "rgba(255, 206, 86, 0.6)",
};
