
import { Article } from '@/types/article';
import { supabase } from '@/integrations/supabase/client';

// Increment view count for an article
export const incrementArticleViews = async (id: string): Promise<Article | null> => {
  try {
    // First, get the current article to get its view count
    const { data: article, error: fetchError } = await supabase
      .from('articles')
      .select('views')
      .eq('id', id)
      .maybeSingle();
    
    if (fetchError || !article) {
      console.error('Error fetching article for view increment:', fetchError);
      return null;
    }
    
    // Increment the view count
    const { data, error } = await supabase
      .from('articles')
      .update({ views: article.views + 1 })
      .eq('id', id)
      .select()
      .maybeSingle();
    
    if (error) {
      console.error('Error incrementing article views:', error);
      return null;
    }
    
    return data as Article;
  } catch (err) {
    console.error('Failed to increment article views:', err);
    return null;
  }
};

// Get most viewed articles
export const getMostViewedArticles = async (limit: number = 5): Promise<Article[]> => {
  try {
    const { data, error } = await supabase
      .from('articles')
      .select('*')
      .eq('is_published', true)
      .order('views', { ascending: false })
      .limit(limit);
    
    if (error) {
      console.error('Error fetching most viewed articles:', error);
      return [];
    }
    
    return data as Article[];
  } catch (err) {
    console.error('Failed to fetch most viewed articles:', err);
    return [];
  }
};
