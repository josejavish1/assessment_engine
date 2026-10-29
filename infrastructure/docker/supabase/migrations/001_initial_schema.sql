-- Migration 001: Initial Multi-Tenant Schema for Assessment Engine Portal

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Role Enum
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('superadmin', 'company_admin', 'member');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Organizations (Tenants / Empresas)
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- User Profiles (Linked to auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    role user_role NOT NULL DEFAULT 'member',
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Helper function to check if user is superadmin
CREATE OR REPLACE FUNCTION public.is_superadmin(user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = user_id AND role = 'superadmin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Profiles Policies
DROP POLICY IF EXISTS "Users can read own profile" ON public.profiles;
CREATE POLICY "Users can read own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id OR public.is_superadmin(auth.uid()));

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Superadmin full access on profiles" ON public.profiles;
CREATE POLICY "Superadmin full access on profiles"
    ON public.profiles FOR ALL
    USING (public.is_superadmin(auth.uid()));

-- Organizations Policies
DROP POLICY IF EXISTS "Members can view own organization" ON public.organizations;
CREATE POLICY "Members can view own organization"
    ON public.organizations FOR SELECT
    USING (
        id IN (SELECT organization_id FROM public.profiles WHERE id = auth.uid())
        OR public.is_superadmin(auth.uid())
    );

DROP POLICY IF EXISTS "Superadmin full access on organizations" ON public.organizations;
CREATE POLICY "Superadmin full access on organizations"
    ON public.organizations FOR ALL
    USING (public.is_superadmin(auth.uid()));

-- Auto-create profile trigger on auth.users sign-up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, role)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        CASE
            WHEN NOT EXISTS (SELECT 1 FROM public.profiles) THEN 'superadmin'::user_role
            ELSE 'member'::user_role
        END
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
