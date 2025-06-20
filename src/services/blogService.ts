import { microCMSClient } from '@/integrations/microcms/client';
import { BlogPost } from '@/types/blog';

export const getBlogPosts = async (limit = 10, offset = 0) => {
  try {
    console.log('Fetching blog posts with params:', { limit, offset });
    const response = await microCMSClient.getList<BlogPost>({
      endpoint: 'blogs',
      queries: {
        limit,
        offset,
        orders: '-publishedAt',
      },
    });
    console.log('ブログ記事一覧:', {
      totalCount: response.totalCount,
      offset: response.offset,
      limit: response.limit,
      contents: response.contents.map(post => ({
        id: post.id,
        title: post.title,
        publishedAt: post.publishedAt,
        picture: post.picture,
      })),
    });
    return response;
  } catch (error) {
    console.error('ブログ記事の取得に失敗しました:', error);
    console.error('Error details:', {
      message: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      endpoint: 'blogs',
      params: { limit, offset },
    });
    return {
      contents: [],
      totalCount: 0,
      offset: 0,
      limit,
    };
  }
};

export const getBlogPost = async (id: string) => {
  try {
    console.log('Fetching blog post with ID:', id);
    const response = await microCMSClient.getListDetail<BlogPost>({
      endpoint: 'blogs',
      contentId: id,
    });
    console.log('ブログ記事詳細:', {
      id: response.id,
      title: response.title,
      publishedAt: response.publishedAt,
      picture: response.picture,
      body: response.body.substring(0, 100) + '...', // 内容の一部を表示
    });
    return response;
  } catch (error) {
    console.error('ブログ記事の取得に失敗しました:', error);
    console.error('Error details:', {
      message: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      endpoint: 'blogs',
      contentId: id,
    });
    return null;
  }
}; 