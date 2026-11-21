'use client';

import React, { useState, useEffect } from 'react';
import {
  Users,
  Plus,
  Pencil,
  Trash2,
  Loader2,
  X,
  Mail,
  User as UserIcon,
  KeyRound,
} from 'lucide-react';
import {
  getClientAccountUsers,
  createUserByAdmin,
  updateUserProfileDetails,
  deleteUserProfile,
  toggleUserBlock,
  type UserProfile,
} from '@/app/actions/governance';

interface DossierUsersTabProps {
  accountSlug: string;
  accountName: string;
}

export function DossierUsersTab({ accountSlug, accountName }: DossierUsersTabProps) {
  const [clientUsers, setClientUsers] = useState<UserProfile[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserProfile | null>(null);
  const [formName, setFormName] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formPassword, setFormPassword] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadUsers = async () => {
    setLoadingUsers(true);
    const res = await getClientAccountUsers(accountSlug);
    if (res.success && res.data) {
      setClientUsers(res.data);
    }
    setLoadingUsers(false);
  };

  useEffect(() => {
    let ignore = false;
    getClientAccountUsers(accountSlug).then((res) => {
      if (!ignore && res.success && res.data) {
        setClientUsers(res.data);
      }
    });
    return () => {
      ignore = true;
    };
  }, [accountSlug]);

  const handleOpenCreateUser = () => {
    setEditingUser(null);
    setFormName('');
    setFormEmail('');
    setFormPassword('');
    setActionError(null);
    setActionSuccess(null);
    setUserModalOpen(true);
  };

  const handleOpenEditUser = (u: UserProfile) => {
    setEditingUser(u);
    setFormName(u.full_name);
    setFormEmail(u.email);
    setFormPassword('');
    setActionError(null);
    setActionSuccess(null);
    setUserModalOpen(true);
  };

  const handleSubmitUserForm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim() || !formEmail.trim()) {
      setActionError('El nombre y el correo son obligatorios.');
      return;
    }

    setIsSubmitting(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      if (editingUser) {
        const res = await updateUserProfileDetails(editingUser.id, {
          fullName: formName.trim(),
          email: formEmail.trim(),
          password: formPassword.trim() || undefined,
        });
        if (!res.success) {
          setActionError(res.message || 'Error al actualizar usuario.');
          return;
        }
        setActionSuccess('Usuario actualizado correctamente.');
      } else {
        const res = await createUserByAdmin({
          fullName: formName.trim(),
          email: formEmail.trim(),
          role: 'CLIENT',
          clientSlug: accountSlug,
          password: formPassword.trim() || 'Cliente2026!',
        });
        if (!res.success) {
          setActionError(res.message || 'Error al crear usuario.');
          return;
        }
        setActionSuccess('Usuario creado con éxito y asignado a este cliente.');
      }

      await loadUsers();
      setTimeout(() => {
        setUserModalOpen(false);
      }, 1000);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Error al guardar usuario.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteUser = async (userId: string, name: string) => {
    if (!confirm(`¿Estás seguro de que deseas eliminar permanentemente el usuario "${name}" de esta cuenta?`)) {
      return;
    }
    const res = await deleteUserProfile(userId);
    if (res.success) {
      await loadUsers();
    } else {
      alert(res.message);
    }
  };

  const handleToggleBlockUser = async (userId: string, currentBlocked: boolean) => {
    const res = await toggleUserBlock(userId, !currentBlocked);
    if (res.success) {
      await loadUsers();
    } else {
      alert(res.message);
    }
  };

  return (
    <div className="bg-white border border-stone-200/80 rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-100 pb-4">
        <div>
          <h3 className="text-sm font-bold text-[#1d1d1f] uppercase tracking-wider font-mono flex items-center gap-2">
            <Users className="w-4 h-4 text-[#0072BC]" />
            <span>Usuarios Autorizados de {accountName}</span>
          </h3>
          <p className="text-xs text-stone-500 mt-0.5">
            Los usuarios registrados aquí solo tienen acceso exclusivo al expediente y entregables de esta empresa.
          </p>
        </div>

        <button
          onClick={handleOpenCreateUser}
          className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center gap-1.5 shadow-sm transition-all self-start sm:self-auto shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Añadir Usuario a la Cuenta</span>
        </button>
      </div>

      {loadingUsers ? (
        <div className="py-12 text-center text-stone-400">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-[#0072BC]" />
          <span className="text-xs font-mono">Cargando directorio de la cuenta...</span>
        </div>
      ) : clientUsers.length === 0 ? (
        <div className="py-12 text-center space-y-3 bg-[#fbfbfa] rounded-xl border border-dashed border-stone-200">
          <Users className="w-8 h-8 text-stone-300 mx-auto" />
          <div className="text-xs font-semibold text-stone-700">No hay usuarios dados de alta para esta cuenta</div>
          <p className="text-[11px] text-stone-500 max-w-md mx-auto">
            Los consultores y administradores de NTT DATA pueden dar de alta a los responsables del cliente para que consulten su dictamen y radar.
          </p>
          <button
            onClick={handleOpenCreateUser}
            className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-[#0072BC] text-white hover:bg-[#0086dd] transition-colors"
          >
            + Dar de Alta Primer Usuario
          </button>
        </div>
      ) : (
        <div className="divide-y divide-stone-100">
          {clientUsers.map((u) => (
            <div key={u.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="h-10 w-10 rounded-xl bg-stone-100 border border-stone-200 flex items-center justify-center font-bold text-stone-700 font-mono text-sm shrink-0">
                  {u.full_name?.charAt(0) || 'U'}
                </div>
                <div>
                  <div className="text-xs font-bold text-[#1d1d1f] flex items-center gap-2">
                    <span>{u.full_name}</span>
                    {u.is_blocked ? (
                      <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-bold border border-rose-200">
                        SUSPENDIDO
                      </span>
                    ) : (
                      <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-200">
                        ACTIVO
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] font-mono text-stone-500 mt-0.5">{u.email}</div>
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-auto">
                <button
                  onClick={() => handleOpenEditUser(u)}
                  className="p-2 rounded-lg bg-stone-50 hover:bg-stone-100 border border-stone-200 text-stone-600 hover:text-stone-900 transition-colors"
                  title="Editar usuario"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>

                <button
                  onClick={() => handleToggleBlockUser(u.id, u.is_blocked)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-colors ${
                    u.is_blocked
                      ? 'bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border-emerald-300'
                      : 'bg-amber-50 hover:bg-amber-100 text-amber-800 border-amber-300'
                  }`}
                >
                  {u.is_blocked ? 'Reactivar' : 'Bloquear'}
                </button>

                <button
                  onClick={() => handleDeleteUser(u.id, u.full_name)}
                  className="p-2 rounded-lg bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-600 hover:text-rose-900 transition-colors"
                  title="Dar de baja usuario"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal para Crear / Editar Usuario del Cliente */}
      {userModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-stone-200 rounded-3xl p-6 sm:p-7 max-w-lg w-full shadow-2xl space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-[#1d1d1f] tracking-tight">
                  {editingUser ? 'Editar Usuario de la Cuenta' : 'Dar de Alta Usuario del Cliente'}
                </h3>
                <p className="text-xs text-stone-500 font-mono mt-0.5">
                  Organización: {accountName} ({accountSlug})
                </p>
              </div>
              <button
                onClick={() => setUserModalOpen(false)}
                className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-stone-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {actionError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-mono">
                {actionError}
              </div>
            )}

            {actionSuccess && (
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-mono">
                {actionSuccess}
              </div>
            )}

            <form onSubmit={handleSubmitUserForm} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs uppercase font-mono tracking-wider text-stone-600 font-bold block">
                  Nombre Completo
                </label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="Ej. Carmen Navarro Sánchez"
                    className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-[#1d1d1f] focus:outline-none focus:border-[#0072BC] focus:bg-white transition-all font-sans"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs uppercase font-mono tracking-wider text-stone-600 font-bold block">
                  Correo Electrónico Corporativo
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    placeholder="ejemplo@organizacion.com"
                    className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-[#1d1d1f] focus:outline-none focus:border-[#0072BC] focus:bg-white transition-all font-sans"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs uppercase font-mono tracking-wider text-stone-600 font-bold block">
                  Contraseña {editingUser ? '(dejar en blanco para conservar actual)' : 'Inicial'}
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    value={formPassword}
                    onChange={(e) => setFormPassword(e.target.value)}
                    placeholder={editingUser ? '••••••••••••' : 'Mínimo 8 caracteres (def: Cliente2026!)'}
                    className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-[#1d1d1f] focus:outline-none focus:border-[#0072BC] focus:bg-white transition-all font-sans"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setUserModalOpen(false)}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-stone-100 hover:bg-stone-200 text-stone-700 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-50"
                >
                  {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>{editingUser ? 'Guardar Cambios' : 'Dar de Alta Usuario'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
