-- 高精度ファジー検索クエリ（直接SQL実行用）
-- PostgreSQLで直接実行可能な形式

-- 使用方法：
-- 1. '$QUERY$' を検索したいテキストに置き換え
-- 2. '$COMPANY_ID$' を対象の会社IDに置き換え（全体検索の場合は WHERE句を削除）
-- 3. 必要に応じてパラメータを調整

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
    normalize_text('$QUERY$') AS norm_query  -- ここに検索クエリを入力
  FROM chunks c
  LEFT JOIN document_sources ds ON c.doc_id = ds.id
  WHERE c.content IS NOT NULL
    AND length(c.content) > 10
    AND c.company_id = '$COMPANY_ID$'  -- ここに会社IDを入力（全体検索の場合は行を削除）
)
SELECT 
  chunk_id,
  doc_id,
  content,
  chunk_index,
  company_id,
  document_name,
  document_type,
  norm_content as normalized_content,
  norm_query as normalized_query,
  similarity(norm_content, norm_query) AS sim,
  abs(length(norm_content) - length(norm_query)) AS len_diff,
  (
    similarity(norm_content, norm_query)
    - 0.012 * abs(length(norm_content) - length(norm_query))  -- 減点弱めに修正
    + CASE
        WHEN norm_content = norm_query THEN 0.4               -- 完全一致ブースト控えめに
        WHEN norm_content LIKE norm_query || '%' THEN 0.2     -- 前方一致も調整
        ELSE 0
      END
  ) AS final_score
FROM normalized
WHERE similarity(norm_content, norm_query) > 0.45  -- 類似度閾値（調整可能）
ORDER BY final_score DESC
LIMIT 50;  -- 結果数制限（調整可能）

-- パラメータ調整ガイド：
-- 
-- 1. 類似度閾値 (WHERE similarity > X):
--    0.3-0.4: より多くの結果を含む（緩い検索）
--    0.45-0.5: バランス良い検索
--    0.6-0.7: より厳密な検索
--
-- 2. 長さペナルティ係数 (0.012):
--    0.005-0.010: 文字数差のペナルティを軽く
--    0.012-0.015: バランス良いペナルティ
--    0.020-0.030: 文字数差を重視
--
-- 3. ブーストボーナス:
--    完全一致: 0.4（通常推奨）
--    前方一致: 0.2（通常推奨）
--
-- 4. 結果数制限:
--    20-50: 通常推奨
--    100以上: 大量データ分析時 