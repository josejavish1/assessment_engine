'use client';

import React, { useState } from 'react';
import {
  Lock,
  Mail,
  User,
  AlertCircle,
  Loader2,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  KeyRound,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import {
  authenticateUserProfile,
  verifyDeviceChallengeOtp,
  requestNttDataRegistrationOtp,
  verifyNttDataRegistrationOtp,
  requestPasswordResetOtp,
  verifyAndResetPasswordOtp,
} from '@/app/actions/governance';
import Image from 'next/image';

export interface AuthUser {
  id: string;
  email: string;
  fullName: string;
  role: 'ADMIN' | 'CONSULTANT' | 'CLIENT';
  clientSlug?: string;
}

interface NttDataAuthGateProps {
  onSuccess?: (user: AuthUser) => void;
  isModal?: boolean;
}

export function NttDataAuthGate({ onSuccess, isModal }: NttDataAuthGateProps) {
  const completeAuth = (user: AuthUser) => {
    if (onSuccess) {
      onSuccess(user);
    } else {
      window.location.reload();
    }
  };
  const [mode, setMode] = useState<'login' | 'register' | 'register_otp' | 'forgot' | 'forgot_otp' | 'device_challenge'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // 1. Iniciar Sesión con Credenciales
  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setErrorMsg('Por favor introduzca su correo corporativo.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await authenticateUserProfile(email.trim(), password.trim());
      if (res.requireDeviceChallenge) {
        setMode('device_challenge');
        setOtpCode('');
        setSuccessMsg(res.message || 'Código de seguridad enviado a su correo.');
        return;
      }

      if (res.success && res.profile) {
        const user: AuthUser = {
          id: res.profile.id,
          email: res.profile.email,
          fullName: res.profile.full_name,
          role: res.profile.role,
          clientSlug: res.profile.client_slug || undefined,
        };
        sessionStorage.setItem('assessment_auth_user', JSON.stringify(user));
        try { localStorage.removeItem('assessment_auth_user'); } catch {}
        completeAuth(user);
      } else {
        setErrorMsg(res.error || 'Credenciales no autorizadas en el sistema.');
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error de conexión con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  // 1B. Validar Desafío Periódico de Dispositivo (15 Días)
  const handleVerifyDeviceOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCode.trim() || otpCode.trim().length !== 6) {
      setErrorMsg('Por favor introduzca el código de 6 dígitos.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await verifyDeviceChallengeOtp({
        email: email.trim(),
        otpCode: otpCode.trim(),
      });

      if (!res.success || !res.profile) {
        setErrorMsg(res.error || 'Código incorrecto o caducado.');
        return;
      }

      setSuccessMsg('Dispositivo verificado y autorizado por 15 días. Iniciando sesión...');
      const user: AuthUser = {
        id: res.profile.id,
        email: res.profile.email,
        fullName: res.profile.full_name,
        role: res.profile.role,
        clientSlug: res.profile.client_slug || undefined,
      };
      sessionStorage.setItem('assessment_auth_user', JSON.stringify(user));
      try { localStorage.removeItem('assessment_auth_user'); } catch {}
      setTimeout(() => completeAuth(user), 1000);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error al validar dispositivo.');
    } finally {
      setLoading(false);
    }
  };

  // 2. Paso 1 de Registro: Solicitar OTP a correo NTT DATA
  const handleRequestRegisterOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await requestNttDataRegistrationOtp({
        fullName: fullName.trim(),
        email: email.trim(),
        password: password.trim(),
      });

      if (!res.success) {
        setErrorMsg(res.error || 'Error al procesar la solicitud de registro.');
        return;
      }

      setSuccessMsg(res.message || 'Código de 6 dígitos enviado a su correo.');
      setMode('register_otp');
      setOtpCode('');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error de conexión al solicitar verificación.');
    } finally {
      setLoading(false);
    }
  };

  // 3. Paso 2 de Registro: Validar OTP de 6 dígitos y Activar Cuenta
  const handleVerifyRegisterOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCode.trim() || otpCode.trim().length !== 6) {
      setErrorMsg('Por favor introduzca el código de verificación de 6 dígitos.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await verifyNttDataRegistrationOtp({
        email: email.trim(),
        otpCode: otpCode.trim(),
      });

      if (!res.success || !res.profile) {
        setErrorMsg(res.error || 'Código incorrecto o caducado.');
        return;
      }

      setSuccessMsg('¡Correo corporativo verificado! Activando sesión...');
      const user: AuthUser = {
        id: res.profile.id,
        email: res.profile.email,
        fullName: res.profile.full_name,
        role: res.profile.role,
        clientSlug: res.profile.client_slug || undefined,
      };
      sessionStorage.setItem('assessment_auth_user', JSON.stringify(user));
      try { localStorage.removeItem('assessment_auth_user'); } catch {}
      setTimeout(() => completeAuth(user), 1000);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error al verificar código.');
    } finally {
      setLoading(false);
    }
  };

  // 4. Paso 1 de Recuperación: Solicitar OTP a correo NTT DATA
  const handleRequestResetOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await requestPasswordResetOtp({
        email: email.trim(),
      });

      if (!res.success) {
        setErrorMsg(res.error || 'Error al solicitar restablecimiento.');
        return;
      }

      setSuccessMsg(res.message || 'Código de 6 dígitos enviado.');
      setMode('forgot_otp');
      setOtpCode('');
      setNewPassword('');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error al procesar solicitud.');
    } finally {
      setLoading(false);
    }
  };

  // 5. Paso 2 de Recuperación: Validar OTP y Asignar Nueva Clave
  const handleVerifyResetOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCode.trim() || otpCode.trim().length !== 6) {
      setErrorMsg('Por favor introduzca el código de 6 dígitos.');
      return;
    }

    if (!newPassword.trim() || newPassword.trim().length < 8) {
      setErrorMsg('La nueva contraseña debe tener al menos 8 caracteres.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await verifyAndResetPasswordOtp({
        email: email.trim(),
        otpCode: otpCode.trim(),
        newPassword: newPassword.trim(),
      });

      if (!res.success) {
        setErrorMsg(res.error || 'Fallo al restablecer contraseña.');
        return;
      }

      setSuccessMsg('Contraseña restablecida con éxito. Redirigiendo a inicio de sesión...');
      setTimeout(() => {
        setMode('login');
        setPassword('');
        setNewPassword('');
        setOtpCode('');
        setSuccessMsg(null);
      }, 2000);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error al procesar actualización.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        background: isModal
          ? undefined
          : 'radial-gradient(ellipse at top, #0f2142 0%, #070d1a 55%, #03060d 100%)',
      }}
      className={`${
        isModal
          ? 'p-2'
          : 'min-h-screen bg-[#070d1a] text-slate-100 flex items-center justify-center p-4 sm:p-6'
      } font-sans select-none`}
    >
      <div className="w-full max-w-xl space-y-6">
        {/* Brand & Clean Identity Header */}
        <div className="text-center space-y-2.5">
          <div className="inline-flex p-3 rounded-2xl bg-[#0a1120] border border-[#1e3052] shadow-xl">
            <Image src="/ntt_data_brand.svg" alt="NTT DATA" width={140} height={32} priority className="h-8 w-auto object-contain" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-wide">
              ASSESSMENT ENGINE
            </h1>
            <p className="text-sm sm:text-base text-slate-300 font-normal mt-0.5">
              Plataforma de Evaluación y Gobierno Tecnológico
            </p>
          </div>
        </div>

        {/* Card Principal */}
        <div className="p-6 sm:p-8 rounded-3xl bg-[#0d1627]/90 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.5)] space-y-5">
          {/* Encabezado dinámico según modo */}
          <div className="space-y-1.5 border-b border-white/10 pb-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base sm:text-lg font-bold text-white uppercase tracking-wider">
                {mode === 'login' && 'Acceso Corporativo'}
                {mode === 'register' && 'Registro Empleados NTT DATA'}
                {mode === 'register_otp' && 'Verificación de Correo (Paso 2/2)'}
                {mode === 'forgot' && 'Restablecer Contraseña'}
                {mode === 'forgot_otp' && 'Confirmar Código y Nueva Clave'}
                {mode === 'device_challenge' && 'Verificación de Dispositivo (NIST SP 800-63B)'}
              </h2>
              {mode !== 'login' && (
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setErrorMsg(null);
                    setSuccessMsg(null);
                  }}
                  className="text-xs text-blue-400 hover:text-white flex items-center gap-1 transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Volver al Login</span>
                </button>
              )}
            </div>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
              {mode === 'login' &&
                'Inicie sesión con su cuenta corporativa para acceder al cuadro de mando.'}
              {mode === 'register' &&
                'Autoregistro exclusivo para empleados con correo @nttdata.com. Se enviará un código de verificación de 6 dígitos.'}
              {mode === 'register_otp' &&
                `Hemos enviado un código numérico de 6 dígitos a ${email}. Introdúzcalo para verificar la posesión del correo.`}
              {mode === 'forgot' &&
                'Introduzca su correo corporativo @nttdata.com para recibir un código de seguridad.'}
              {mode === 'forgot_otp' &&
                `Introduzca el código de 6 dígitos enviado a ${email} y su nueva contraseña.`}
              {mode === 'device_challenge' &&
                `Por política de seguridad corporativa (verificación periódica cada 15 días o nuevo navegador), hemos enviado un código a ${email}.`}
            </p>
          </div>

          {/* Mensajes de error o éxito */}
          {errorMsg && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs sm:text-sm flex items-start gap-2.5">
              <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
              <span className="leading-snug">{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs sm:text-sm flex items-start gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <span className="leading-snug">{successMsg}</span>
            </div>
          )}

          {/* MODO 1: LOGIN MANUAL */}
          {mode === 'login' && (
            <form onSubmit={handleManualLogin} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs sm:text-sm uppercase tracking-wider text-slate-300 font-medium block">
                  Email Corporativo
                </label>
                <div className="relative">
                  <Mail className="h-4 w-4 absolute left-3.5 top-3.5 text-slate-400" />
                  <input
                    type="email"
                    aria-label="Corporate Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="usuario@nttdata.com"
                    className="w-full bg-[#141f36] border border-[#233557] rounded-xl pl-10 pr-3.5 py-3 text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/20 transition-all font-sans"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs sm:text-sm uppercase tracking-wider text-slate-300 font-medium block">
                    Contraseña
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setMode('forgot');
                      setErrorMsg(null);
                      setSuccessMsg(null);
                    }}
                    className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    ¿Olvidaste tu contraseña?
                  </button>
                </div>
                <div className="relative">
                  <Lock className="h-4 w-4 absolute left-3.5 top-3.5 text-slate-400" />
                  <input
                    type="password"
                    aria-label="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-[#141f36] border border-[#233557] rounded-xl pl-10 pr-3.5 py-3 text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/20 transition-all"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm sm:text-base font-semibold bg-[#0072BC] hover:bg-[#0086dd] active:bg-[#00609e] text-white transition-all shadow-lg shadow-[#0072BC]/30 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <span>Iniciar Sesión</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setMode('register');
                    setErrorMsg(null);
                    setSuccessMsg(null);
                  }}
                  className="text-xs sm:text-sm text-slate-300 hover:text-white transition-colors"
                >
                  ¿Eres empleado de NTT DATA?{' '}
                  <span className="text-blue-400 font-semibold underline underline-offset-4">
                    Regístrate aquí
                  </span>
                </button>
              </div>
            </form>
          )}

          {/* MODO 2: SOLICITAR REGISTRO (PASO 1) */}
          {mode === 'register' && (
            <form onSubmit={handleRequestRegisterOtp} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs sm:text-sm uppercase tracking-wider text-slate-300 font-medium block">
                  Nombre y Apellidos
                </label>
                <div className="relative">
                  <User className="h-4 w-4 absolute left-3.5 top-3.5 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Ej. Carlos Mendoza"
                    className="w-full bg-[#141f36] border border-[#233557] rounded-xl pl-10 pr-3.5 py-3 text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/20 transition-all font-sans"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs sm:text-sm uppercase tracking-wider text-slate-300 font-medium block">
                  Email Corporativo NTT DATA
                </label>
                <div className="relative">
                  <Mail className="h-4 w-4 absolute left-3.5 top-3.5 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="nombre.apellido@nttdata.com"
                    className="w-full bg-[#141f36] border border-[#233557] rounded-xl pl-10 pr-3.5 py-3 text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/20 transition-all font-sans"
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  Dominio autorizado: @nttdata.com, @emeal.nttdata.com, @global.ntt
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs sm:text-sm uppercase tracking-wider text-slate-300 font-medium block">
                  Contraseña de Acceso (mínimo 8 caracteres)
                </label>
                <div className="relative">
                  <Lock className="h-4 w-4 absolute left-3.5 top-3.5 text-slate-400" />
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-[#141f36] border border-[#233557] rounded-xl pl-10 pr-3.5 py-3 text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/20 transition-all"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm sm:text-base font-semibold bg-[#0072BC] hover:bg-[#0086dd] active:bg-[#00609e] text-white transition-all shadow-lg shadow-[#0072BC]/30 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <span>Enviar Código de Verificación</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setErrorMsg(null);
                    setSuccessMsg(null);
                  }}
                  className="text-xs sm:text-sm text-slate-400 hover:text-white"
                >
                  ¿Ya tienes cuenta?{' '}
                  <span className="text-blue-400 font-semibold underline underline-offset-4">
                    Inicia sesión
                  </span>
                </button>
              </div>
            </form>
          )}

          {/* MODO 2B: VERIFICAR OTP DE REGISTRO (PASO 2) */}
          {mode === 'register_otp' && (
            <form onSubmit={handleVerifyRegisterOtp} className="space-y-5">
              <div className="p-4 rounded-2xl bg-blue-950/30 border border-blue-500/30 space-y-1.5 text-center">
                <div className="inline-flex p-2 rounded-full bg-blue-500/20 text-blue-400 mb-1">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div className="text-xs sm:text-sm font-semibold text-white">
                  Código de 6 dígitos enviado a:
                </div>
                <div className="text-sm font-mono text-blue-300 font-bold">{email}</div>
              </div>

              <div className="space-y-2">
                <label className="text-xs sm:text-sm uppercase tracking-wider text-slate-300 font-medium block text-center">
                  Introduce el Código de 6 Dígitos
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    maxLength={6}
                    autoFocus
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="••••••"
                    className="w-full bg-[#141f36] border border-[#233557] rounded-xl py-3.5 text-center text-2xl font-mono tracking-[0.4em] font-extrabold text-white placeholder-slate-600 focus:outline-none focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/20 transition-all"
                  />
                </div>
                <p className="text-xs text-slate-400 text-center">
                  Válido durante 10 minutos. Revisa tu carpeta de correo o spam de NTT DATA.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || otpCode.length !== 6}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm sm:text-base font-semibold bg-[#0072BC] hover:bg-[#0086dd] active:bg-[#00609e] text-white transition-all shadow-lg shadow-[#0072BC]/30 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <span>Verificar y Activar Cuenta</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>

              <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                <button
                  type="button"
                  onClick={() => setMode('register')}
                  className="hover:text-white transition-colors"
                >
                  ← Modificar datos
                </button>
                <button
                  type="button"
                  onClick={handleRequestRegisterOtp}
                  disabled={loading}
                  className="text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" /> Reenviar código
                </button>
              </div>
            </form>
          )}

          {/* MODO 3: SOLICITAR RESTABLECER CONTRASEÑA (PASO 1) */}
          {mode === 'forgot' && (
            <form onSubmit={handleRequestResetOtp} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs sm:text-sm uppercase tracking-wider text-slate-300 font-medium block">
                  Email Corporativo NTT DATA
                </label>
                <div className="relative">
                  <Mail className="h-4 w-4 absolute left-3.5 top-3.5 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="tu.correo@nttdata.com"
                    className="w-full bg-[#141f36] border border-[#233557] rounded-xl pl-10 pr-3.5 py-3 text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/20 transition-all font-sans"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm sm:text-base font-semibold bg-[#0072BC] hover:bg-[#0086dd] active:bg-[#00609e] text-white transition-all shadow-lg shadow-[#0072BC]/30 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <span>Enviar Código de Recuperación</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setErrorMsg(null);
                    setSuccessMsg(null);
                  }}
                  className="text-xs sm:text-sm text-slate-400 hover:text-white"
                >
                  Cancelar y volver a{' '}
                  <span className="text-blue-400 font-semibold underline underline-offset-4">
                    Iniciar Sesión
                  </span>
                </button>
              </div>
            </form>
          )}

          {/* MODO 3B: VALIDAR OTP Y ASIGNAR NUEVA CONTRASEÑA (PASO 2) */}
          {mode === 'forgot_otp' && (
            <form onSubmit={handleVerifyResetOtp} className="space-y-4">
              <div className="p-3.5 rounded-2xl bg-blue-950/30 border border-blue-500/30 text-center">
                <div className="text-xs text-slate-300">
                  Código de recuperación enviado a: <strong className="text-blue-300">{email}</strong>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs sm:text-sm uppercase tracking-wider text-slate-300 font-medium block">
                  Código de 6 Dígitos
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    maxLength={6}
                    autoFocus
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="••••••"
                    className="w-full bg-[#141f36] border border-[#233557] rounded-xl py-3 text-center text-xl font-mono tracking-[0.3em] font-extrabold text-white placeholder-slate-600 focus:outline-none focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/20 transition-all"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs sm:text-sm uppercase tracking-wider text-slate-300 font-medium block">
                  Nueva Contraseña (mínimo 8 caracteres)
                </label>
                <div className="relative">
                  <KeyRound className="h-4 w-4 absolute left-3.5 top-3.5 text-slate-400" />
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-[#141f36] border border-[#233557] rounded-xl pl-10 pr-3.5 py-3 text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/20 transition-all"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || otpCode.length !== 6}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm sm:text-base font-semibold bg-[#0072BC] hover:bg-[#0086dd] active:bg-[#00609e] text-white transition-all shadow-lg shadow-[#0072BC]/30 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <span>Confirmar y Restablecer Contraseña</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setErrorMsg(null);
                    setSuccessMsg(null);
                  }}
                  className="text-xs sm:text-sm text-slate-400 hover:text-white"
                >
                  Cancelar y volver a{' '}
                  <span className="text-blue-400 font-semibold underline underline-offset-4">
                    Iniciar Sesión
                  </span>
                </button>
              </div>
            </form>
          )}

          {/* MODO 4: DESAFÍO DE DISPOSITIVO (NIST SP 800-63B / OWASP 15 DÍAS) */}
          {mode === 'device_challenge' && (
            <form onSubmit={handleVerifyDeviceOtp} className="space-y-5">
              <div className="p-4 rounded-2xl bg-blue-950/30 border border-blue-500/30 space-y-1.5 text-center">
                <div className="inline-flex p-2 rounded-full bg-blue-500/20 text-blue-400 mb-1">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div className="text-xs sm:text-sm font-semibold text-white">
                  Verificación periódica de dispositivo para:
                </div>
                <div className="text-sm font-mono text-blue-300 font-bold">{email}</div>
              </div>

              <div className="space-y-2">
                <label className="text-xs sm:text-sm uppercase tracking-wider text-slate-300 font-medium block text-center">
                  Introduce el Código de 6 Dígitos
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    maxLength={6}
                    autoFocus
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="••••••"
                    className="w-full bg-[#141f36] border border-[#233557] rounded-xl py-3.5 text-center text-2xl font-mono tracking-[0.4em] font-extrabold text-white placeholder-slate-600 focus:outline-none focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/20 transition-all"
                  />
                </div>
                <p className="text-xs text-slate-400 text-center">
                  Al verificar, este navegador quedará autorizado durante <strong>15 días</strong> sin volver a solicitar código.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || otpCode.length !== 6}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm sm:text-base font-semibold bg-[#0072BC] hover:bg-[#0086dd] active:bg-[#00609e] text-white transition-all shadow-lg shadow-[#0072BC]/30 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <span>Verificar y Autorizar Dispositivo (15 Días)</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>

              <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setErrorMsg(null);
                    setSuccessMsg(null);
                  }}
                  className="hover:text-white transition-colors"
                >
                  ← Volver al Login
                </button>
                <button
                  type="button"
                  onClick={handleManualLogin}
                  disabled={loading}
                  className="text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" /> Reenviar código
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Clean Corporate Footer */}
        <div className="text-center text-xs sm:text-sm text-slate-400">
          © 2026 NTT DATA EMEAL · Todos los derechos reservados
        </div>
      </div>
    </div>
  );
}
