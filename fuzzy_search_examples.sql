-- 高精度ファジー検索の実際の使用例
-- 以下の例をコピーして、値を置き換えて実行してください

-- ======================================
-- 例1: 特定の会社での検索
-- ======================================
WITH normalized AS (
  SELECT
    c.id as chunk_id,
    c.doc_id,
    c.content,
    c.chunk_index,
    c.company_id,
    COALESCE(ds.name, 'Unknown') as document_name,
    COALESCE(ds.type, 'unknown') as document_type,
    normalize_text(c.content) AS norm_content,
    normalize_text('営業戦略') AS norm_query  -- 検索クエリ例
  FROM chunks c
  LEFT JOIN document_sources ds ON c.doc_id = ds.id
  WHERE c.content IS NOT NULL
    AND length(c.content) > 10
    AND c.company_id = 'your-company-id-here'  -- 実際の会社IDに置き換え
)
SELECT 
  chunk_id,
  doc_id,
  document_name,
  document_type,
  similarity(norm_content, norm_query) AS sim,
  abs(length(norm_content) - length(norm_query)) AS len_diff,
  (
    similarity(norm_content, norm_query)
    - 0.012 * abs(length(norm_content) - length(norm_query))
    + CASE
        WHEN norm_content = norm_query THEN 0.4
        WHEN norm_content LIKE norm_query || '%' THEN 0.2
        ELSE 0
      END
  ) AS final_score,
  LEFT(content, 200) || '...' as content_preview  -- 内容のプレビュー
FROM normalized
WHERE similarity(norm_content, norm_query) > 0.45
ORDER BY final_score DESC
LIMIT 50;

-- ======================================
-- 例2: 全社横断検索（会社IDフィルターなし）
-- ======================================
WITH normalized AS (
  SELECT
    c.id as chunk_id,
    c.doc_id,
    c.content,
    c.chunk_index,
    c.company_id,
    COALESCE(ds.name, 'Unknown') as document_name,
    COALESCE(ds.type, 'unknown') as document_type,
    normalize_text(c.content) AS norm_content,
    normalize_text('マーケティング') AS norm_query  -- 検索クエリ例
  FROM chunks c
  LEFT JOIN document_sources ds ON c.doc_id = ds.id
  WHERE c.content IS NOT NULL
    AND length(c.content) > 10
)
SELECT 
  chunk_id,
  company_id,
  document_name,
  document_type,
  similarity(norm_content, norm_query) AS sim,
  abs(length(norm_content) - length(norm_query)) AS len_diff,
  (
    similarity(norm_content, norm_query)
    - 0.012 * abs(length(norm_content) - length(norm_query))
    + CASE
        WHEN norm_content = norm_query THEN 0.4
        WHEN norm_content LIKE norm_query || '%' THEN 0.2
        ELSE 0
      END
  ) AS final_score,
  LEFT(content, 150) || '...' as content_preview
FROM normalized
WHERE similarity(norm_content, norm_query) > 0.45
ORDER BY final_score DESC
LIMIT 30;

-- ======================================
-- 例3: 厳密検索（高い閾値）
-- ======================================
WITH normalized AS (
  SELECT
    c.id as chunk_id,
    c.doc_id,
    c.content,
    c.chunk_index,
    c.company_id,
    COALESCE(ds.name, 'Unknown') as document_name,
    COALESCE(ds.type, 'unknown') as document_type,
    normalize_text(c.content) AS norm_content,
    normalize_text('売上計画') AS norm_query  -- 検索クエリ例
  FROM chunks c
  LEFT JOIN document_sources ds ON c.doc_id = ds.id
  WHERE c.content IS NOT NULL
    AND length(c.content) > 10
    AND c.company_id = 'your-company-id-here'  -- 実際の会社IDに置き換え
)
SELECT 
  chunk_id,
  document_name,
  document_type,
  similarity(norm_content, norm_query) AS sim,
  abs(length(norm_content) - length(norm_query)) AS len_diff,
  (
    similarity(norm_content, norm_query)
    - 0.008 * abs(length(norm_content) - length(norm_query))  -- ペナルティ軽減
    + CASE
        WHEN norm_content = norm_query THEN 0.5  -- ブースト強化
        WHEN norm_content LIKE norm_query || '%' THEN 0.3
        ELSE 0
      END
  ) AS final_score,
  content  -- 完全な内容を表示
FROM normalized
WHERE similarity(norm_content, norm_query) > 0.6  -- 高い閾値
ORDER BY final_score DESC
LIMIT 20;

-- ======================================
-- 例4: 緩い検索（多くの結果を取得）
-- ======================================
WITH normalized AS (
  SELECT
    c.id as chunk_id,
    c.doc_id,
    c.content,
    c.chunk_index,
    c.company_id,
    COALESCE(ds.name, 'Unknown') as document_name,
    COALESCE(ds.type, 'unknown') as document_type,
    normalize_text(c.content) AS norm_content,
    normalize_text('プロジェクト') AS norm_query  -- 検索クエリ例
  FROM chunks c
  LEFT JOIN document_sources ds ON c.doc_id = ds.id
  WHERE c.content IS NOT NULL
    AND length(c.content) > 10
    AND c.company_id = 'your-company-id-here'  -- 実際の会社IDに置き換え
)
SELECT 
  chunk_id,
  document_name,
  document_type,
  similarity(norm_content, norm_query) AS sim,
  abs(length(norm_content) - length(norm_query)) AS len_diff,
  (
    similarity(norm_content, norm_query)
    - 0.015 * abs(length(norm_content) - length(norm_query))  -- ペナルティ強化
    + CASE
        WHEN norm_content = norm_query THEN 0.3  -- ブースト軽減
        WHEN norm_content LIKE norm_query || '%' THEN 0.15
        ELSE 0
      END
  ) AS final_score,
  LEFT(content, 100) || '...' as content_preview
FROM normalized
WHERE similarity(norm_content, norm_query) > 0.35  -- 低い閾値
ORDER BY final_score DESC
LIMIT 100;

-- ======================================
-- normalize_text関数のテスト用クエリ
-- ======================================
SELECT 
  '株式会社テスト' as original,
  normalize_text('株式会社テスト') as normalized
UNION ALL
SELECT 
  'ＴＥＳＴカンパニー' as original,
  normalize_text('ＴＥＳＴカンパニー') as normalized
UNION ALL
SELECT 
  '有限会社　サンプル' as original,
  normalize_text('有限会社　サンプル') as normalized; 