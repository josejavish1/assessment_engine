'use client';

import React from 'react';
import { Refine, type AuthProvider, type HttpError } from '@refinedev/core';
import { dataProvider } from '@refinedev/supabase';
import routerProvider from '@refinedev/nextjs-router/app';
import { createClient } from '@/lib/supabase/client';

export function RefineProvider({ children }: { children: React.ReactNode }) {
  const supabase = createClient();

  const authProvider: AuthProvider = {
    login: async ({ email, password }) => {
      const { error } = await supabase.auth.signInWithPassword({
        email: email as string,
        password: password as string,
      });

      if (error) {
        return {
          success: false,
          error: {
            name: 'LoginError',
            message: error.message,
          },
        };
      }

      return {
        success: true,
        redirectTo: '/',
      };
    },
    logout: async () => {
      const { error } = await supabase.auth.signOut();
      if (error) {
        return {
          success: false,
          error: {
            name: 'LogoutError',
            message: error.message,
          },
        };
      }
      return {
        success: true,
        redirectTo: '/login',
      };
    },
    check: async () => {
      const { data } = await supabase.auth.getSession();
      const { session } = data;

      if (!session) {
        return {
          authenticated: false,
          redirectTo: '/login',
        };
      }

      return {
        authenticated: true,
      };
    },
    getPermissions: async () => {
      const { data: userRes } = await supabase.auth.getUser();
      if (!userRes?.user) return null;

      const { data: profile } = await supabase
        .from('profiles')
        .select('role, organization_id')
        .eq('id', userRes.user.id)
        .single();

      return profile?.role ?? 'member';
    },
    getIdentity: async () => {
      const { data: userRes } = await supabase.auth.getUser();
      if (!userRes?.user) return null;

      const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userRes.user.id)
        .single();

      return {
        id: userRes.user.id,
        email: userRes.user.email,
        name: profile?.full_name ?? userRes.user.email,
        role: profile?.role ?? 'member',
        organizationId: profile?.organization_id,
      };
    },
    onError: async (error: HttpError | Error | unknown) => {
      const status = (error as { status?: number; statusCode?: number })?.statusCode ??
        (error as { status?: number })?.status;

      if (status === 401 || status === 403) {
        return {
          logout: true,
          redirectTo: '/login',
          error: error instanceof Error ? error : new Error(String(error)),
        };
      }
      return {
        error: error instanceof Error ? error : new Error(String(error)),
      };
    },
  };

  return (
    <Refine
      routerProvider={routerProvider}
      dataProvider={dataProvider(supabase)}
      authProvider={authProvider}
      resources={[
        {
          name: 'organizations',
          list: '/admin/organizations',
          show: '/admin/organizations/:id',
          meta: { label: 'Empresas' },
        },
        {
          name: 'profiles',
          list: '/admin/users',
          show: '/admin/users/:id',
          meta: { label: 'Usuarios' },
        },
      ]}
      options={{
        syncWithLocation: true,
        warnWhenUnsavedChanges: true,
      }}
    >
      {children}
    </Refine>
  );
}
