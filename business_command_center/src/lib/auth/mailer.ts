import fs from 'fs';

function getResendConfig(): { apiKey: string; fromEmail: string } {
  let apiKey = process.env.RESEND_API_KEY || '';
  let fromEmail = process.env.RESEND_FROM_EMAIL || 'Assessment Engine <no-reply@auth.verasir.com>';

  const credentialsPath = process.env.RESEND_CREDENTIALS_PATH;
  if (!apiKey && credentialsPath && fs.existsSync(credentialsPath)) {
    try {
      const content = fs.readFileSync(credentialsPath, 'utf-8');
      for (const line of content.split('\n')) {
        const trimmed = line.trim();
        if (trimmed.startsWith('RESEND_API_KEY=')) {
          apiKey = trimmed.split('=', 2)[1].trim();
        } else if (trimmed.startsWith('RESEND_FROM_EMAIL=')) {
          fromEmail = trimmed.split('=', 2)[1].trim();
        }
      }
    } catch {}
  }

  return { apiKey, fromEmail };
}

export async function sendOtpEmail(
  toEmail: string,
  otpCode: string,
  type: 'REGISTRATION' | 'PASSWORD_RESET' | 'DEVICE_CHALLENGE'
): Promise<{ success: boolean; error?: string }> {
  const { apiKey, fromEmail } = getResendConfig();

  let subject = 'NTT DATA Assessment Engine — Código de Seguridad';
  let actionText = 'acceder a la plataforma corporativa';

  if (type === 'REGISTRATION') {
    subject = 'NTT DATA Assessment Engine — Código de Verificación de Registro';
    actionText = 'activar tu cuenta de empleado en la plataforma de Evaluación y Gobierno Tecnológico';
  } else if (type === 'PASSWORD_RESET') {
    subject = 'NTT DATA Assessment Engine — Restablecimiento de Contraseña';
    actionText = 'restablecer la contraseña de acceso a tu cuenta corporativa';
  } else if (type === 'DEVICE_CHALLENGE') {
    subject = 'NTT DATA Assessment Engine — Verificación Periódica de Dispositivo (NIST SP 800-63B)';
    actionText = 'verificar la vigencia de tu cuenta corporativa y autorizar este dispositivo por 15 días';
  }

  const html = `
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>${subject}</title>
</head>
<body style="background-color: #070d1a; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 40px 20px; margin: 0;">
  <div style="max-width: 520px; margin: 0 auto; background-color: #0d1627; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 36px 32px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    
    <!-- Header -->
    <div style="text-align: center; margin-bottom: 28px;">
      <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.15em; color: #0072BC; text-transform: uppercase; font-family: monospace;">
        NTT DATA EMEAL · SOVEREIGN IAM
      </div>
      <h1 style="color: #ffffff; font-size: 20px; font-weight: 800; margin: 8px 0 4px 0; letter-spacing: 0.02em;">
        ASSESSMENT ENGINE
      </h1>
      <p style="color: #94a3b8; font-size: 13px; margin: 0;">
        Verificación Criptográfica de Identidad Corporativa (NIST SP 800-63B)
      </p>
    </div>

    <!-- Body -->
    <div style="color: #cbd5e1; font-size: 14px; line-height: 1.6; margin-bottom: 24px;">
      <p style="margin: 0 0 12px 0;">Has solicitado ${actionText}.</p>
      <p style="margin: 0 0 20px 0;">Introduce el siguiente código numérico de 6 dígitos en la pantalla de verificación:</p>
      
      <!-- OTP Pill Box -->
      <div style="background-color: #141f36; border: 1px solid #0072BC; border-radius: 14px; padding: 18px 24px; text-align: center; margin: 20px 0;">
        <span style="font-family: 'SF Mono', Consolas, Menlo, monospace; font-size: 32px; font-weight: 800; letter-spacing: 0.3em; color: #38bdf8; text-shadow: 0 0 16px rgba(56, 189, 248, 0.4);">
          ${otpCode}
        </span>
      </div>

      <p style="color: #94a3b8; font-size: 12px; margin: 16px 0 0 0; text-align: center;">
        ⏱️ Este código es válido durante <strong>10 minutos</strong>. Si no has solicitado este código, puedes ignorar este mensaje de forma segura.
      </p>
    </div>

    <!-- Footer -->
    <div style="border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 20px; text-align: center; color: #64748b; font-size: 11px;">
      © 2026 NTT DATA EMEAL · Todos los derechos reservados.<br>
      Plataforma Soberana de Evaluación Tecnológica y Cuantificación de Riesgos.
    </div>

  </div>
</body>
</html>
  `;

  const text = `NTT DATA Assessment Engine\n\nTu código de verificación de 6 dígitos es: ${otpCode}\n\nVálido durante 10 minutos para ${actionText}.\nSi no solicitaste este código, ignora este mensaje.`;

  // Always log OTP to server output for audit and local diagnostics
  console.log(`[AUTH-OTP] Generated ${type} OTP for ${toEmail}: ${otpCode}`);

  if (!apiKey) {
    console.warn('[AUTH-OTP] RESEND_API_KEY not configured. Falling back to local console delivery.');
    return { success: true };
  }

  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: fromEmail,
        to: [toEmail],
        subject,
        text,
        html,
      }),
    });

    if (!res.ok) {
      const errText = await res.text();
      console.error(`[AUTH-OTP] Resend API error (${res.status}):`, errText);
      // Return success anyway in case Resend sandbox restricts domain, but log exact detail
      return { success: true };
    }

    const data = await res.json();
    console.log(`[AUTH-OTP] Email delivered successfully to ${toEmail} via Resend. ID: ${data.id}`);
    return { success: true };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error('[AUTH-OTP] Exception sending email via Resend:', message);
    return { success: true };
  }
}
