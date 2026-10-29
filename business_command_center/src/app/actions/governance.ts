'use server';

import { createClient } from '@/lib/supabase/server';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'CONSULTANT' | 'CLIENT';
  client_slug?: string | null;
  is_blocked: boolean;
  created_at: string;
  last_login?: string;
}

export async function getUserProfiles(): Promise<{ success: boolean; data?: UserProfile[]; error?: string }> {
  try {
    const supabase = await createClient();
    const { data, error } = await supabase
      .from('user_profiles')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      return { success: false, error: error.message };
    }

    return { success: true, data: data || [] };
  } catch (err: any) {
    return { success: false, error: err.message || 'Database connection error' };
  }
}

export async function toggleUserBlock(
  userId: string,
  isBlocked: boolean
): Promise<{ success: boolean; message: string; error?: string }> {
  try {
    const supabase = await createClient();
    const { error } = await supabase
      .from('user_profiles')
      .update({ is_blocked: isBlocked })
      .eq('id', userId);

    if (error) {
      return { success: false, message: 'Fallo al actualizar estado', error: error.message };
    }

    return {
      success: true,
      message: isBlocked ? 'User suspended and blocked successfully.' : 'User reactivated successfully.',
    };
  } catch (err: any) {
    return { success: false, message: 'Error de base de datos', error: err.message };
  }
}

export async function updateUserRole(
  userId: string,
  newRole: 'ADMIN' | 'CONSULTANT' | 'CLIENT'
): Promise<{ success: boolean; message: string; error?: string }> {
  try {
    const supabase = await createClient();
    const { error } = await supabase
      .from('user_profiles')
      .update({ role: newRole })
      .eq('id', userId);

    if (error) {
      return { success: false, message: 'Fallo al actualizar rol', error: error.message };
    }

    return {
      success: true,
      message: `Role updated to ${newRole} successfully.`,
    };
  } catch (err: any) {
    return { success: false, message: 'Error de base de datos', error: err.message };
  }
}

export async function authenticateUserProfile(
  email: string
): Promise<{ success: boolean; profile?: UserProfile; error?: string }> {
  try {
    const supabase = await createClient();
    const { data, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('email', email.trim().toLowerCase())
      .single();

    if (error || !data) {
      return { success: false, error: 'Corporate credentials not found in system.' };
    }

    if (data.is_blocked) {
      return {
        success: false,
        error: 'This corporate account has been suspended by the NTT DATA Administrator.',
      };
    }

    return { success: true, profile: data };
  } catch (err: any) {
    return { success: false, error: err.message || 'Authentication error' };
  }
}
