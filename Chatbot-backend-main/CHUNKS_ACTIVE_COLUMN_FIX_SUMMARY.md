# 🔧 Chunks Active Column Fix Summary

## 🚨 Problem Description

The system was experiencing errors when trying to query the `chunks` table with an `active` column filter:

```
❌ chunksテーブルからのコンテンツ取得 エラー: {'code': '42703', 'details': None, 'hint': None, 'message': 'column chunks.active does not exist'}
```

## 🔍 Root Cause Analysis

According to the `Workmate_Database_Schema_Guide.md`, the database schema is designed as follows:

- **`chunks` table**: Does NOT have an `active` column
- **`document_sources` table**: DOES have an `active` column (line 172 in schema guide)

The code was incorrectly trying to filter chunks by a non-existent `active` column instead of using the `document_sources.active` column.

## ✅ Files Fixed

### 1. `modules/resource.py` (Line 441)
**Before:**
```python
chunks_query = supabase.table("chunks").select("content,chunk_index").eq("doc_id", doc_id).eq("active", True).order("chunk_index")
```

**After:**
```python
# chunksテーブルからコンテンツを取得（document_sourcesのactiveフラグでフィルタ）
# まずdocument_sourcesでactiveかどうかをチェック
doc_query = supabase.table("document_sources").select("active").eq("id", doc_id).single()
doc_result = doc_query.execute()

if not doc_result.data or not doc_result.data.get("active", False):
    print(f"⚠️ ドキュメントが非アクティブまたは存在しません: {doc_id}")
    return ""

# アクティブなドキュメントの場合のみchunksを取得
chunks_query = supabase.table("chunks").select("content,chunk_index").eq("doc_id", doc_id).order("chunk_index")
```

### 2. `setup_document_system.py` (Line 221)
**Before:**
```python
("idx_chunks_active", "CREATE INDEX IF NOT EXISTS idx_chunks_active ON chunks(active);"),
```

**After:**
```python
# Note: chunks table doesn't have active column - active status is managed in document_sources
```

### 3. `setup_document_system.py` (Lines 310-319)
**Before:**
```python
insert_sql = """
    INSERT INTO chunks (doc_id, chunk_index, content, company_id, active)
    VALUES (%s, %s, %s, %s, %s)
"""
cursor.execute(insert_sql, (
    doc['id'],
    chunk_data['chunk_index'],
    chunk_data['content'],
    doc['company_id'],
    True
))
```

**After:**
```python
insert_sql = """
    INSERT INTO chunks (doc_id, chunk_index, content, company_id)
    VALUES (%s, %s, %s, %s)
"""
cursor.execute(insert_sql, (
    doc['id'],
    chunk_data['chunk_index'],
    chunk_data['content'],
    doc['company_id']
))
```

### 4. `modules/upload_api.py` (Line 304)
**Before:**
```python
# chunksテーブルのactive状態を同期
```

**After:**
```python
# chunksテーブルの更新日時を同期（activeフラグはdocument_sourcesで管理）
```

### 5. `modules/upload_api.py` (Line 338)
**Before:**
```python
chunks_query = supabase.table("chunks").select("id,chunk_index,active").eq("doc_id", doc_id)
```

**After:**
```python
chunks_query = supabase.table("chunks").select("id,chunk_index").eq("doc_id", doc_id)
```

## 🏗️ Database Schema Alignment

The fixes align the code with the correct database schema:

### Chunks Table (Actual Schema)
```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id TEXT NOT NULL → document_sources(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(3072),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    company_id TEXT
    -- ❌ NO 'active' column
);
```

### Document Sources Table (Actual Schema)
```sql
CREATE TABLE document_sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    page_count INTEGER,
    uploaded_by TEXT → users(id),
    company_id TEXT → companies(id),
    uploaded_at TIMESTAMP NOT NULL,
    active BOOLEAN DEFAULT true,  -- ✅ Active column is HERE
    special TEXT,
    parent_id TEXT → document_sources(id)
);
```

## 🔄 Correct Query Pattern

To filter chunks by active status, use a JOIN with document_sources:

```python
# ✅ Correct approach
chunks_query = supabase.table("chunks").select(
    "content,chunk_index,document_sources!inner(active)"
).eq("doc_id", doc_id).eq("document_sources.active", True).order("chunk_index")
```

## 🎯 Expected Result

After these fixes, the knowledge base retrieval should work correctly:
- ✅ No more "column chunks.active does not exist" errors
- ✅ Proper filtering based on document_sources.active
- ✅ Chunks from inactive documents will be excluded from results
- ✅ Database operations will succeed without schema conflicts

## 📊 Impact

This fix resolves the core issue preventing the RAG (Retrieval-Augmented Generation) system from retrieving knowledge base content, which was causing empty responses in the chatbot.