-- Add metadata JSONB column to store additional document metadata (columns list, date_types, etc.)
ALTER TABLE public.document_sources
ADD COLUMN IF NOT EXISTS metadata JSONB; 