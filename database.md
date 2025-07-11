-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.applications (
  id text NOT NULL,
  company_name text NOT NULL,
  contact_name text NOT NULL,
  email text NOT NULL,
  phone text,
  expected_users text,
  current_usage text,
  message text,
  application_type text NOT NULL DEFAULT 'production-upgrade'::text,
  status text NOT NULL DEFAULT 'pending'::text,
  submitted_at text NOT NULL,
  processed_at text,
  processed_by text,
  notes text,
  CONSTRAINT applications_pkey PRIMARY KEY (id)
);
CREATE TABLE public.chat_history (
  id text NOT NULL,
  user_message text NOT NULL,
  bot_response text NOT NULL,
  timestamp timestamp without time zone NOT NULL,
  category text,
  sentiment text,
  employee_id text,
  employee_name text,
  source_document text,
  source_page text,
  input_tokens integer DEFAULT 0,
  output_tokens integer DEFAULT 0,
  total_tokens integer DEFAULT 0,
  model_name character varying DEFAULT 'gpt-4o-mini'::character varying,
  cost_usd numeric DEFAULT 0.000000,
  user_id character varying,
  company_id character varying,
  prompt_references integer DEFAULT 0,
  base_cost_usd numeric DEFAULT 0.000000,
  prompt_cost_usd numeric DEFAULT 0.000000,
  CONSTRAINT chat_history_pkey PRIMARY KEY (id)
);
CREATE TABLE public.chunks (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  content text NOT NULL,
  chunk_index integer NOT NULL,
  doc_id text NOT NULL,
  company_id text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  embedding USER-DEFINED,
  CONSTRAINT chunks_pkey PRIMARY KEY (id)
);
CREATE TABLE public.companies (
  id text NOT NULL,
  name text NOT NULL,
  created_at timestamp without time zone NOT NULL,
  CONSTRAINT companies_pkey PRIMARY KEY (id)
);
CREATE TABLE public.company_settings (
  company_id character varying NOT NULL,
  monthly_token_limit integer DEFAULT 25000000,
  warning_threshold_percentage integer DEFAULT 80,
  critical_threshold_percentage integer DEFAULT 95,
  pricing_tier character varying DEFAULT 'basic'::character varying,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT company_settings_pkey PRIMARY KEY (company_id)
);
CREATE TABLE public.document_sources (
  id text NOT NULL,
  name text NOT NULL,
  type text NOT NULL,
  page_count integer,
  uploaded_by text NOT NULL,
  company_id text NOT NULL,
  uploaded_at timestamp with time zone NOT NULL,
  active boolean NOT NULL DEFAULT true,
  special text,
  parent_id text,
  doc_id text UNIQUE,
  CONSTRAINT document_sources_pkey PRIMARY KEY (id),
  CONSTRAINT document_sources_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.document_sources(id),
  CONSTRAINT document_sources_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id),
  CONSTRAINT document_sources_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);
CREATE TABLE public.monthly_token_usage (
  id character varying NOT NULL,
  company_id character varying NOT NULL,
  user_id character varying NOT NULL,
  year_month character varying NOT NULL,
  total_input_tokens integer DEFAULT 0,
  total_output_tokens integer DEFAULT 0,
  total_tokens integer DEFAULT 0,
  total_cost_usd numeric DEFAULT 0.000000,
  conversation_count integer DEFAULT 0,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT monthly_token_usage_pkey PRIMARY KEY (id)
);
CREATE TABLE public.notifications (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  title text NOT NULL,
  content text NOT NULL,
  notification_type text DEFAULT 'general'::text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  created_by text,
  CONSTRAINT notifications_pkey PRIMARY KEY (id)
);
CREATE TABLE public.plan_history (
  id text NOT NULL DEFAULT (gen_random_uuid())::text,
  user_id text NOT NULL,
  from_plan text NOT NULL,
  to_plan text NOT NULL,
  changed_at timestamp without time zone DEFAULT now(),
  duration_days integer,
  CONSTRAINT plan_history_pkey PRIMARY KEY (id),
  CONSTRAINT plan_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.usage_limits (
  user_id text NOT NULL,
  document_uploads_used integer NOT NULL DEFAULT 0,
  document_uploads_limit integer NOT NULL DEFAULT 2,
  questions_used integer NOT NULL DEFAULT 0,
  questions_limit integer NOT NULL DEFAULT 10,
  is_unlimited boolean NOT NULL DEFAULT false,
  CONSTRAINT usage_limits_pkey PRIMARY KEY (user_id),
  CONSTRAINT usage_limits_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.users (
  id text NOT NULL,
  email text NOT NULL UNIQUE,
  password text NOT NULL,
  name text NOT NULL,
  role text NOT NULL DEFAULT 'user'::text,
  company_id text,
  created_at timestamp without time zone NOT NULL,
  created_by text,
  CONSTRAINT users_pkey PRIMARY KEY (id),
  CONSTRAINT users_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id),
  CONSTRAINT users_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);