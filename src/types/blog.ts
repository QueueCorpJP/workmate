export interface BlogPost {
  id: string;
  createdAt: string;
  updatedAt: string;
  publishedAt: string;
  revisedAt: string;
  title: string;
  picture: {
    url: string;
    height: number;
    width: number;
  };
  body: string;
  category?: {
    id: string;
    name: string;
  };
}

export interface BlogCategory {
  id: string;
  createdAt: string;
  updatedAt: string;
  publishedAt: string;
  revisedAt: string;
  name: string;
}

export interface BlogTag {
  id: string;
  createdAt: string;
  updatedAt: string;
  publishedAt: string;
  revisedAt: string;
  name: string;
} 