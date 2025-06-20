import { supabase } from "@/integrations/supabase/client";
import { Article as ArticleType, ArticleFormData } from "@/types/article";

// Article service functions
export const getArticles = async (published = true): Promise<ArticleType[]> => {
  try {
    let query = supabase
      .from('articles')
      .select('*')
      .order('created_at', { ascending: false });
    
    if (published) {
      query = query.eq('is_published', true);
    }
    
    const { data, error } = await query;

    if (error) {
      console.error("Error fetching articles:", error);
      return [];
    }
    return data as ArticleType[];
  } catch (error) {
    console.error("Exception when fetching articles:", error);
    return [];
  }
};

export const getArticleById = async (id: string): Promise<ArticleType | null> => {
  try {
    const { data, error } = await supabase
      .from('articles')
      .select('*')
      .eq('id', id)
      .single();

    if (error) {
      console.error("Error fetching article by ID:", error);
      return null;
    }
    return data as ArticleType;
  } catch (error) {
    console.error("Exception when fetching article by ID:", error);
    return null;
  }
};

export const getArticleBySlug = async (slug: string): Promise<ArticleType | null> => {
  try {
    const { data, error } = await supabase
      .from('articles')
      .select('*')
      .eq('slug', slug)
      .single();

    if (error) {
      console.error("Error fetching article by slug:", error);
      return null;
    }
    return data as ArticleType;
  } catch (error) {
    console.error("Exception when fetching article by slug:", error);
    return null;
  }
};

export const createArticle = async (article: ArticleFormData): Promise<ArticleType | null> => {
  try {
    const { data, error } = await supabase
      .from('articles')
      .insert([
        { 
          ...article, 
          views: 0,
          published_at: article.is_published ? new Date().toISOString() : null
        }
      ])
      .select('*')
      .single();

    if (error) {
      console.error("Error creating article:", error);
      return null;
    }
    return data as ArticleType;
  } catch (error) {
    console.error("Exception when creating article:", error);
    return null;
  }
};

export const updateArticle = async (id: string, updates: Partial<ArticleType>): Promise<ArticleType | null> => {
  try {
    const { data, error } = await supabase
      .from('articles')
      .update(updates)
      .eq('id', id)
      .select('*')
      .single();

    if (error) {
      console.error("Error updating article:", error);
      return null;
    }
    return data as ArticleType;
  } catch (error) {
    console.error("Exception when updating article:", error);
    return null;
  }
};

export const deleteArticle = async (id: string): Promise<boolean> => {
  try {
    const { error } = await supabase
      .from('articles')
      .delete()
      .eq('id', id);

    if (error) {
      console.error("Error deleting article:", error);
      return false;
    }
    return true;
  } catch (error) {
    console.error("Exception when deleting article:", error);
    return false;
  }
};

// Article status functions
export const publishArticle = async (id: string): Promise<boolean> => {
  try {
    const { error } = await supabase
      .from('articles')
      .update({ 
        is_published: true, 
        published_at: new Date().toISOString() 
      })
      .eq('id', id);

    if (error) {
      console.error("Error publishing article:", error);
      return false;
    }
    return true;
  } catch (error) {
    console.error("Exception when publishing article:", error);
    return false;
  }
};

export const archiveArticle = async (id: string): Promise<boolean> => {
  try {
    const { error } = await supabase
      .from('articles')
      .update({ 
        is_published: false 
      })
      .eq('id', id);

    if (error) {
      console.error("Error archiving article:", error);
      return false;
    }
    return true;
  } catch (error) {
    console.error("Exception when archiving article:", error);
    return false;
  }
};

// Article analytics functions
export const incrementArticleViews = async (articleId: string): Promise<boolean> => {
  try {
    const { data: article, error: fetchError } = await supabase
      .from('articles')
      .select('views')
      .eq('id', articleId)
      .single();
    
    if (fetchError) {
      console.error('Error fetching article for view increment:', fetchError);
      return false;
    }
    
    const currentViews = article.views || 0;
    
    const { error: updateError } = await supabase
      .from('articles')
      .update({ views: currentViews + 1 })
      .eq('id', articleId);
    
    if (updateError) {
      console.error('Error incrementing article views:', updateError);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Exception when incrementing article views:', error);
    return false;
  }
};

// Article search and filter functions
export const searchArticles = async (query: string): Promise<ArticleType[]> => {
  try {
    const { data, error } = await supabase
      .from('articles')
      .select('*')
      .ilike('title', `%${query}%`)
      .order('created_at', { ascending: false });

    if (error) {
      console.error("Error searching articles:", error);
      return [];
    }
    return data as ArticleType[];
  } catch (error) {
    console.error("Exception when searching articles:", error);
    return [];
  }
};

export const filterArticlesByCategory = async (category: string): Promise<ArticleType[]> => {
  try {
    const { data, error } = await supabase
      .from('articles')
      .select('*')
      .eq('category', category)
      .order('created_at', { ascending: false });

    if (error) {
      console.error("Error filtering articles by category:", error);
      return [];
    }
    return data as ArticleType[];
  } catch (error) {
    console.error("Exception when filtering articles by category:", error);
    return [];
  }
};

// For compatibility with the old names
export const addArticle = createArticle;
