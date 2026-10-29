-- Migration 003: Hierarchical RBAC (HRBAC) User Profiles and Governance

CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('CLIENT', 'CONSULTANT', 'ADMIN')),
    client_slug TEXT,
    is_blocked BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON public.user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON public.user_profiles(role);

-- Enable Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Allow all for internal server queries
DROP POLICY IF EXISTS "Public Profile Access" ON public.user_profiles;
CREATE POLICY "Public Profile Access"
    ON public.user_profiles FOR ALL
    USING (true);

-- Seed Initial Enterprise Profiles for Demo
INSERT INTO public.user_profiles (email, full_name, role, client_slug, is_blocked)
VALUES
    ('director@nttdata.com', 'Director de Práctica Cloud & Soberanía', 'ADMIN', NULL, false),
    ('consultor@nttdata.com', 'Consultor Senior de Evaluación', 'CONSULTANT', NULL, false),
    ('ciso@nordicgrid.de', 'CISO · Nordic Grid Power GmbH', 'CLIENT', 'nordic_grid_power_gmbh', false),
    ('seguridad@repsol.com', 'Responsable Ciberseguridad · Repsol Global', 'CLIENT', 'repsol_energia_global', false),
    ('auditor@bancosantander.es', 'Auditor de Riesgo · Banco Santander', 'CLIENT', 'banco_santander_corporacion', false)
ON CONFLICT (email) DO NOTHING;

-- Notify PostgREST to reload schema
NOTIFY pgrst, 'reload schema';
