
// This file is kept for backward compatibility
// All functions are now implemented in articleService.ts and articleAnalytics.ts
// using Supabase database instead of localStorage

import { Article } from '@/types/article';
import { getArticles as fetchArticles } from './articleService';

// Initial sample data - no longer used directly, now stored in Supabase
export const articles: Article[] = [];

// Local storage key - no longer used as we're now using Supabase
export const ARTICLES_STORAGE_KEY = 'workmate_articles';

// These functions are kept for backward compatibility but now use Supabase
// Implementations are in articleService.ts and articleAnalytics.ts
export const getArticles = async (): Promise<Article[]> => {
  return fetchArticles();
};

export const saveArticles = async (updatedArticles: Article[]): Promise<void> => {
  console.warn('saveArticles is deprecated. Use individual CRUD operations instead.');
  // This function is now a no-op as we're using Supabase
};
