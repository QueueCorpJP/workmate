-- template_categoriesテーブルにcompany_idとcategory_typeカラムを追加

-- 1. company_idカラムを追加（NULLを許可）
ALTER TABLE template_categories 
ADD COLUMN IF NOT EXISTS company_id TEXT;

-- 2. category_typeカラムを追加（systemまたはcompany）
ALTER TABLE template_categories 
ADD COLUMN IF NOT EXISTS category_type TEXT DEFAULT 'system';

-- 3. category_typeの制約を追加
ALTER TABLE template_categories 
ADD CONSTRAINT check_category_type 
CHECK (category_type IN ('system', 'company'));

-- 4. 既存のカテゴリをすべてsystemタイプに設定
UPDATE template_categories 
SET category_type = 'system', company_id = NULL 
WHERE category_type IS NULL OR category_type = '';

-- 5. systemタイプのカテゴリはcompany_idをNULLに設定
UPDATE template_categories 
SET company_id = NULL 
WHERE category_type = 'system';

-- 6. インデックスを追加してパフォーマンスを向上
CREATE INDEX IF NOT EXISTS idx_template_categories_company_id 
ON template_categories(company_id);

CREATE INDEX IF NOT EXISTS idx_template_categories_type 
ON template_categories(category_type);

-- 7. 外部キー制約を追加（company_idがNULLでない場合はcompaniesテーブルを参照）
-- Note: PostgreSQLでは条件付き外部キー制約は直接作成できないため、トリガーまたはアプリケーションレベルで制御

-- 8. 確認用クエリ
SELECT id, name, category_type, company_id, is_active 
FROM template_categories 
ORDER BY category_type, display_order; 