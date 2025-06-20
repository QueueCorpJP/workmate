export interface Article {
  id: number;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  category: string;
  author: string;
  created_at: string;
  updated_at: string;
  is_published: boolean;
  views: number;
  tags: string[];
}

export type ArticleFormData = {
  title: string;
  content: string;
  category: string;
  slug: string;
  excerpt: string;
  is_published: boolean;
  published_at?: string;
};
