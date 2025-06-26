以下では テーブル作成までは完了している 前提で、
Gemini-embedding-exp-03-07 を使って document_sources → document_embeddings にベクトルを格納し、
類似検索まで動く最小構成を「そのまま貼り付けて動く形」で示します。

1. 依存パッケージを入れる
bash
コピーする
編集する
pip install google-genai psycopg2-binary python-dotenv pgvector
google-genai は記事で紹介されていた公式 SDK の新名称です。
zenn.dev

2. .env でキーと DB を隠蔽
dotenv
コピーする
編集する
# .env
GOOGLE_API_KEY=sk-********************************
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DB?sslmode=require
EMBEDDING_MODEL=gemini-embedding-exp-03-07
# Gemini は 3 072 次元を返す。IVFFlat は 2 000 次元上限なので
# HNSW を使うか、後述の MRL で 1 536 次元以下に落とす
EMBEDDING_DIM=3072
3. document_embeddings.embedding を vector 型に変更
sql
コピーする
編集する
-- pgvector 拡張がまだなら
create extension if not exists vector;

-- 3 072 次元で確定する場合
alter table document_embeddings
  alter column embedding type vector(3072)
  using embedding::vector;
4. HNSW インデックスを張る（推奨）
sql
コピーする
編集する
create index if not exists document_embeddings_embedding_idx
  on document_embeddings
  using hnsw (embedding vector_cosine_ops);
3 072 dim でも HNSW は張れます。IVFFlat を使うなら 1 ∼ 2 000 dim に削る必要があります。
supabase.com
supabase.com

5. 埋め込み生成 & 一括登録スクリプト
embed_documents.py

python
コピーする
編集する
import os, textwrap
from dotenv import load_dotenv
from google import genai
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
DB      = os.getenv("DATABASE_URL")
MODEL   = os.getenv("EMBEDDING_MODEL", "gemini-embedding-exp-03-07")

client = genai.Client(api_key=API_KEY)
conn   = psycopg2.connect(DB)
cur    = conn.cursor()

# ❶ まだ埋め込みが無いドキュメントを取得
cur.execute("""
    select id, content
      from document_sources
     where active = true
       and id not in (select document_id from document_embeddings);
""")
rows = cur.fetchall()

def chunks(txt, n=8000):               # ≒2 000 token
    for i in range(0, len(txt), n):
        yield txt[i:i+n]

records = []
for doc_id, content in rows:
    for part in chunks(content):
        vec = client.models.embed_content(
                  model=MODEL, contents=part
              ).embeddings[0].values
        records.append((doc_id, vec, part[:200]))    # snippet 付与

execute_values(cur, """
    insert into document_embeddings (document_id, embedding, snippet)
    values %s
    on conflict (document_id) do update
      set embedding = excluded.embedding,
          snippet   = excluded.snippet;
""", records)

conn.commit()
cur.close(); conn.close()
print(f"upserted {len(records)} embeddings")
コマンド: python embed_documents.py

単純分割なので長大 PDF は本番では LangChain などでページ単位 or セマンティックチャンクにしてください。
基本的な embed_content 呼び出し方法は記事の §3–4 を参照。
zenn.dev

6. クエリ時の類似検索例
python
コピーする
編集する
import numpy as np, psycopg2
from google import genai
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
DB     = os.getenv("DATABASE_URL")
MODEL  = os.getenv("EMBEDDING_MODEL")

query = "クラウドコストを削減する方法は？"
q_vec = client.models.embed_content(model=MODEL, contents=query) \
                 .embeddings[0].values

sql = """
select ds.id,
       ds.name,
       ds.special,
       de.snippet,
       1 - (de.embedding <=> %s) as score
  from document_embeddings de
  join document_sources ds on ds.id = de.document_id
 order by de.embedding <=> %s
 limit 5;
"""

with psycopg2.connect(DB) as c, c.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute(sql, (q_vec, q_vec))
    for r in cur.fetchall():
        print(f"{r['score']:.3f}", r['name'], r['snippet'][:80])
7. MRL で次元削減したい場合（任意）
python
コピーする
編集する
def truncate(vec, dim=1536):
    return vec[:dim]                        # 3 072→1 536 など
1 536 dim 以下に落とせば IVFFlat インデックスも利用可能です。
zenn.dev

8. 運用メモ
タスク	方法
新規ドキュメント取り込み	embed_documents.py を CI / Supabase Edge Function で定期実行
速度チューニング	hnsw パラメータ (m, ef_construction, ef_search) を alter index で調整
コスト削減	① MRLで次元削減、② 上位 k だけを Gemini 本体に渡す

これで スキーマ以降 → ベクトル登録 → 検索 まで一気通しで動くはずです。