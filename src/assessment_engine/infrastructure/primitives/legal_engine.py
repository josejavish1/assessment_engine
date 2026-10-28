"""
Provide automated compliance for GDPR/LOPDGDD (EU 2016/679 & LO 3/2018) and LSSI-CE (Spain Law 34/2002). Generate statutory legal documents adhering to official AEPD and INCIBE guidelines:
1. Legal Notice and General Terms of Use (Art. 10 LSSI-CE).
2. Privacy Policy and Personal Data Processing with ARCO-POL rights (Art. 13 GDPR).
3. Technical Cookie Policy with exhaustive specification table per official AEPD guidelines.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.legal_engine")


@dataclass
class LegalCompanyIdentity:
    legal_name: str
    trade_name: str
    tax_id: str
    registered_address: str
    contact_email: str
    registry_details: str = "Registro Mercantil y Notarial Oficial / Official Commercial Register"
    dpo_email: str = "dpo@autonomuos.app"


class LegalEnginePrimitive:
    """
    Provide statutory legal document generation compliant with Spanish and European regulations.
    """

    def generate_legal_notice_html(self, idt: LegalCompanyIdentity) -> str:
        """Generate the complete Legal Notice compliant with Art. 10 of Law 34/2002 (LSSI-CE)."""
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Aviso Legal y Condiciones de Uso — {idt.trade_name}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1e293b; max-width: 860px; margin: 40px auto; padding: 0 20px; }}
    h1 {{ font-size: 28px; color: #0f172a; border-bottom: 2px solid #0d9488; padding-bottom: 12px; }}
    h2 {{ font-size: 20px; color: #0f172a; margin-top: 30px; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 6px; }}
    .box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 20px 0; }}
    .header-nav {{ border-bottom: 1px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
    .back-btn {{ font-size: 13px; font-weight: 600; color: #0d9488; text-decoration: none; padding: 8px 14px; background: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 8px; }}
    .back-btn:hover {{ background: #ccfbf1; }}
  </style>
</head>
<body>
  <div class="header-nav">
    <div style="font-weight: 800; font-size: 18px; color: #0f172a;">{idt.trade_name}</div>
    <a href="/#view=landing" class="back-btn">← Volver al Portal</a>
  </div>
  <h1>Aviso Legal y Términos de Uso</h1>
  <p>En cumplimiento de lo dispuesto en el artículo 10 de la Ley 34/2002, de 11 de julio, de Servicios de la Sociedad de la Información y de Comercio Electrónico (LSSI-CE), se pone a disposición de los usuarios y autoridades competentes la siguiente información relativa a la entidad titular del sitio web:</p>

  <div class="box">
    <ul>
      <li><strong>Razón Social:</strong> {idt.legal_name}</li>
      <li><strong>Nombre Comercial:</strong> {idt.trade_name}</li>
      <li><strong>Número de Identificación Fiscal (NIF/CIF):</strong> {idt.tax_id}</li>
      <li><strong>Domicilio Social:</strong> {idt.registered_address}</li>
      <li><strong>Datos Registrales:</strong> {idt.registry_details}</li>
      <li><strong>Correo Electrónico de Contacto:</strong> {idt.contact_email}</li>
      <li><strong>Actividad Principal:</strong> Prestación de servicios de gestión digital y software en la nube.</li>
    </ul>
  </div>

  <h2>1. Objeto y Ámbito de Aplicación</h2>
  <p>Las presentes Condiciones Generales de Uso regulan el acceso, navegación y uso del presente sitio web y sus plataformas asociadas. El acceso al sitio web atribuye la condición de usuario e implica la aceptación plena y sin reservas de todas y cada una de las disposiciones incluidas en este Aviso Legal.</p>

  <h2>2. Condiciones de Acceso y Uso del Sitio Web</h2>
  <p>El usuario se compromete a hacer un uso diligente, correcto y lícito de los contenidos y servicios de la plataforma, absteniéndose expresamente de:</p>
  <ul>
    <li>Difundir contenidos ilícitos, violentos, pornográficos, degradantes o contrarios a la ley y al orden público.</li>
    <li>Introducir virus informáticos, malware o realizar acciones susceptibles de alterar, interrumpir o generar errores en los sistemas telemáticos del titular o de terceros.</li>
    <li>Intentar acceder a cuentas restringidas, paneles administrativos, bases de datos no públicas o vulnerar medidas de autenticación y seguridad.</li>
    <li>Vulnerar los derechos de propiedad intelectual o industrial del titular o de legítimos terceros.</li>
  </ul>

  <h2>3. Propiedad Intelectual e Industrial</h2>
  <p>Todos los elementos que forman parte de este sitio web, incluyendo de forma enunciativa pero no limitativa: códigos fuente, arquitecturas de software, textos, diseños gráficos, logotipos, iconos, botones, combinaciones de colores, estructura y ordenación de contenidos, se encuentran protegidos por la legislación española e internacional sobre propiedad intelectual e industrial, ostentando {idt.legal_name} la titularidad exclusiva de los mismos o las correspondientes licencias de uso. Queda expresamente prohibida la reproducción, distribución, transformación o comunicación pública, total o parcial, con fines comerciales sin la autorización previa y por escrito del titular.</p>

  <h2>4. Exclusión de Garantías y Limitación de Responsabilidad</h2>
  <p>{idt.legal_name} aplica los máximos estándares de calidad técnica y seguridad cibernética; no obstante, dentro de los límites legalmente permitidos, no se hace responsable de los daños y perjuicios de cualquier naturaleza que pudieran derivarse de interferencias, omisiones, interrupciones, virus informáticos, averías telefónicas o desconexiones en el funcionamiento operativo de la red de internet motivadas por causas ajenas a su control.</p>

  <h2>5. Enlaces de Terceros (Links)</h2>
  <p>En el caso de que en el sitio web se dispusiesen enlaces o hipervínculos hacia otros sitios de internet, {idt.legal_name} no ejercerá ningún tipo de control sobre dichos sitios y contenidos, no asumiendo responsabilidad alguna por la exactitud o licitud de los mismos.</p>

  <h2>6. Legislación Aplicable y Jurisdicción Competente</h2>
  <p>Para la resolución de todas las controversias o cuestiones relacionadas con el presente sitio web o de las actividades en él desarrolladas, será de aplicación la legislación española vigente, a la que se someten expresamente las partes, siendo competentes para la resolución de todos los conflictos derivados los Juzgados y Tribunales de Madrid capital, salvo que la normativa en materia de consumidores y usuarios establezca imperativamente otro fuero.</p>
</body>
</html>"""

    def generate_privacy_policy_html(self, idt: LegalCompanyIdentity) -> str:
        """Generate the Privacy Policy compliant with Art. 13 of the GDPR and LO 3/2018 (LOPDGDD)."""
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Política de Privacidad y Protección de Datos — {idt.trade_name}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1e293b; max-width: 860px; margin: 40px auto; padding: 0 20px; }}
    h1 {{ font-size: 28px; color: #0f172a; border-bottom: 2px solid #0d9488; padding-bottom: 12px; }}
    h2 {{ font-size: 20px; color: #0f172a; margin-top: 30px; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 6px; }}
    .box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 20px 0; }}
    .header-nav {{ border-bottom: 1px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
    .back-btn {{ font-size: 13px; font-weight: 600; color: #0d9488; text-decoration: none; padding: 8px 14px; background: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 8px; }}
    .back-btn:hover {{ background: #ccfbf1; }}
  </style>
</head>
<body>
  <div class="header-nav">
    <div style="font-weight: 800; font-size: 18px; color: #0f172a;">{idt.trade_name}</div>
    <a href="/#view=landing" class="back-btn">← Volver al Portal</a>
  </div>
  <h1>Política de Privacidad y Protección de Datos Personales</h1>
  <p>La presente Política de Privacidad establece los términos en que <strong>{idt.legal_name}</strong> trata y protege la información facilitada por sus usuarios, dando estricto cumplimiento al Reglamento (UE) 2016/679 del Parlamento Europeo y del Consejo (Reglamento General de Protección de Datos - RGPD) y a la Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y garantía de los derechos digitales (LOPDGDD).</p>

  <div class="box">
    <h2>1. Responsable del Tratamiento de los Datos</h2>
    <ul>
      <li><strong>Identidad:</strong> {idt.legal_name} ({idt.trade_name})</li>
      <li><strong>NIF:</strong> {idt.tax_id}</li>
      <li><strong>Domicilio Postal:</strong> {idt.registered_address}</li>
      <li><strong>Correo Electrónico de Contacto:</strong> {idt.contact_email}</li>
      <li><strong>Delegado de Protección de Datos (DPO):</strong> {idt.dpo_email}</li>
    </ul>
  </div>

  <h2>2. Finalidades del Tratamiento de Datos</h2>
  <p>En función de los servicios y funcionalidades utilizados en la plataforma, tratamos sus datos personales para las siguientes finalidades:</p>
  <ul>
    <li><strong>Gestión de Usuarios y Prestación de Servicios:</strong> Creación y mantenimiento de cuentas de acceso, prestación de los servicios operativos contratados, gestión de reservas, citas médicas/profesionales y facturación oficial.</li>
    <li><strong>Comunicaciones y Avisos de Servicio:</strong> Envío de confirmaciones transaccionales, recordatorios de citas por mensajería o correo electrónico, y notificaciones operativas obligatorias.</li>
    <li><strong>Comunicaciones Comerciales de la Red (LSSI-CE Art. 21):</strong> Siempre que el usuario haya otorgado su consentimiento expreso mediante la casilla correspondiente en el registro, {idt.legal_name} y la plataforma tecnológica asociada <strong>Soverik Platform (soverik.com)</strong> podrán remitirle novedades, promociones y ofertas comerciales electrónicas relacionadas con servicios y funcionalidades de la plataforma. El usuario puede revocar este consentimiento en cualquier momento con un solo clic.</li>
    <li><strong>Cumplimiento de Obligaciones Legales:</strong> Emisión de facturas y conservación de libros contables de conformidad con la Ley General Tributaria y el Código de Comercio.</li>
    <li><strong>Seguridad de la Plataforma:</strong> Detección de accesos no autorizados, prevención del fraude y salvaguarda de la integridad de los sistemas de información.</li>
  </ul>

  <h2>3. Base Jurídica y Legitimación del Tratamiento</h2>
  <p>El tratamiento de sus datos se fundamenta en las siguientes bases jurídicas establecidas en el artículo 6 del RGPD:</p>
  <ul>
    <li><strong>Ejecución de una relación contractual (Art. 6.1.b RGPD):</strong> Necesaria para la prestación de los servicios de la plataforma solicitados por el usuario.</li>
    <li><strong>Cumplimiento de obligaciones legales aplicables (Art. 6.1.c RGPD):</strong> Especialmente en materia fiscal, tributaria, contable y sanitaria.</li>
    <li><strong>Consentimiento expreso e informado (Art. 6.1.a RGPD y Art. 21 LSSI-CE):</strong> Solicitado expresamente para el envío de comunicaciones comerciales y promociones de la red tecnológica Soverik Platform (soverik.com), así como para la activación de cookies no esenciales.</li>
    <li><strong>Interés legítimo del responsable (Art. 6.1.f RGPD):</strong> Para garantizar la seguridad de las redes y la prevención del fraude tecnológico.</li>
  </ul>

  <h2>4. Plazos de Conservación de los Datos</h2>
  <p>Los datos personales se conservarán durante el tiempo estrictamente necesario para cumplir con las finalidades para las que fueron recabados:</p>
  <ul>
    <li>Los datos vinculados a cuentas de usuario se conservarán mientras el usuario mantenga su condición de usuario registrado.</li>
    <li>Tras la baja o supresión de la cuenta, los datos económicos, transaccionales y facturas se mantendrán debidamente bloqueados durante un plazo de <strong>cinco (5) años</strong> en cumplimiento de las obligaciones de prescripción legal del Código Civil y la Ley General Tributaria de España.</li>
  </ul>

  <h2>5. Destinatarios y Cesiones de Datos</h2>
  <p>{idt.legal_name} no cederá datos personales a terceros, salvo imperativo legal expreso (ej. Administración Tributaria, Cuerpos y Fuerzas de Seguridad del Estado, Juzgados y Tribunales). Tendrán acceso a los datos aquellos proveedores tecnológicos que actúen en calidad de <strong>Encargados del Tratamiento</strong> bajo contrato vinculante conforme al artículo 28 del RGPD (servicios de hosting seguro, pasarelas de pago certificadas PCI-DSS y servicios de correo).</p>
  <p><strong>Plataforma Tecnológica de Red (Soverik Platform - soverik.com):</strong> La infraestructura de autenticación soberana, seguridad de accesos y despacho transaccional opera sobre la tecnología de Soverik Platform (soverik.com). Los datos de cuenta necesarios para el control de acceso y el despacho de comunicaciones consentidas son tratados de forma coordinada con la plataforma tecnológica bajo estrictos acuerdos de confidencialidad y estándares europeos de cifrado.</p>

  <h2>6. Derechos del Usuario (ARCO-POL)</h2>
  <p>El usuario puede ejercer en cualquier momento sus derechos reconocidos en los artículos 15 a 22 del RGPD:</p>
  <ul>
    <li><strong>Derecho de Acceso:</strong> Consultar qué datos personales están siendo tratados.</li>
    <li><strong>Derecho de Rectificación:</strong> Modificar datos inexactos o incompletos.</li>
    <li><strong>Derecho de Supresión (Derecho al Olvido):</strong> Solicitar la eliminación de sus datos cuando ya no sean necesarios para los fines recabados.</li>
    <li><strong>Derecho a la Limitación del Tratamiento:</strong> Solicitar la paralización cautelar del tratamiento en los supuestos legalmente previstos.</li>
    <li><strong>Derecho a la Portabilidad:</strong> Recibir sus datos en formato estructurado, de uso común y lectura mecánica (JSON/CSV).</li>
    <li><strong>Derecho de Oposición:</strong> Oponerse al tratamiento de sus datos fundamentado en el interés legítimo.</li>
  </ul>
  <p>Para ejercer estos derechos, el usuario puede remitir comunicación escrita acreditando su identidad a la dirección postal del responsable o mediante correo electrónico a <strong>{idt.contact_email}</strong> o <strong>{idt.dpo_email}</strong> con la referencia "Protección de Datos".</p>
  <p>Asimismo, el usuario tiene derecho a presentar una reclamación ante la autoridad de control competente, la <strong>Agencia Española de Protección de Datos (AEPD)</strong>, a través de su sede electrónica en <a href="https://www.aepd.es" target="_blank">www.aepd.es</a>.</p>
</body>
</html>"""

    def generate_cookie_policy_html(self, idt: LegalCompanyIdentity) -> str:
        """Generate the technical Cookie Policy compliant with official AEPD guidelines."""
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Política de Cookies — {idt.trade_name}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1e293b; max-width: 860px; margin: 40px auto; padding: 0 20px; }}
    h1 {{ font-size: 28px; color: #0f172a; border-bottom: 2px solid #0d9488; padding-bottom: 12px; }}
    h2 {{ font-size: 20px; color: #0f172a; margin-top: 30px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: left; }}
    th {{ background: #f1f5f9; color: #0f172a; font-weight: 700; }}
    .header-nav {{ border-bottom: 1px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
    .back-btn {{ font-size: 13px; font-weight: 600; color: #0d9488; text-decoration: none; padding: 8px 14px; background: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 8px; }}
    .back-btn:hover {{ background: #ccfbf1; }}
  </style>
</head>
<body>
  <div class="header-nav">
    <div style="font-weight: 800; font-size: 18px; color: #0f172a;">{idt.trade_name}</div>
    <a href="/#view=landing" class="back-btn">← Volver al Portal</a>
  </div>
  <h1>Política de Cookies</h1>
  <p>En cumplimiento de lo dispuesto en el artículo 22.2 de la Ley 34/2002, de 11 de julio, de Servicios de la Sociedad de la Información y de Comercio Electrónico (LSSI-CE), y de conformidad con la Guía sobre el uso de las cookies aprobada por la Agencia Española de Protección de Datos (AEPD), el presente sitio web informa a los usuarios acerca del uso de dispositivos de almacenamiento y recuperación de datos en equipos terminales (cookies).</p>

  <h2>1. ¿Qué son las Cookies?</h2>
  <p>Una cookie es un fichero que se descarga en el ordenador, smartphone o dispositivo del usuario al acceder a determinadas páginas web. Las cookies permiten a una página web, entre otras cosas, almacenar y recuperar información sobre los hábitos de navegación de un usuario o de su equipo y, dependiendo de la información que contengan y de la forma en que utilice su equipo, pueden utilizarse para reconocer al usuario.</p>

  <h2>2. Tipología y Clasificación de Cookies Utilizadas</h2>
  <p>Este sitio web utiliza cookies técnicas estrictamente necesarias para el funcionamiento y la seguridad de la plataforma, así como cookies de personalización de interfaz exentas de la obligación de recabar consentimiento expreso por tratarse de cookies de sesión técnica y preferencias del usuario:</p>

  <table>
    <thead>
      <tr>
        <th>Nombre de Cookie</th>
        <th>Titular / Proveedor</th>
        <th>Finalidad Técnica</th>
        <th>Durabilidad</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>access_token</code></td>
        <td>Propia ({idt.trade_name})</td>
        <td>Autenticación de sesión de usuario mediante JWT cifrado con prefijo __Host- y flag HttpOnly para prevención de ataques XSS y secuestro de sesión.</td>
        <td>7 días / Sesión</td>
      </tr>
      <tr>
        <td><code>theme</code></td>
        <td>Propia ({idt.trade_name})</td>
        <td>Almacenamiento local de la preferencia visual del usuario (modo claro o modo oscuro) para evitar el parpadeo en recarga (Zero-FOUC).</td>
        <td>Persistente (1 año)</td>
      </tr>
      <tr>
        <td><code>app_cache_v1</code></td>
        <td>Propia (Service Worker)</td>
        <td>Caché local del navegador para permitir el funcionamiento de la aplicación en modo progresivo sin conexión a internet (PWA W3C).</td>
        <td>Persistente</td>
      </tr>
      <tr>
        <td><code>cc_cookie</code></td>
        <td>Propia (vanilla-cookieconsent)</td>
        <td>Registro del consentimiento o rechazo granular del usuario respecto a las políticas de privacidad y cookies.</td>
        <td>180 días</td>
      </tr>
    </tbody>
  </table>

  <h2>3. Ausencia de Cookies Publicitarias de Terceros y Rastreo Invasivo</h2>
  <p>Este sitio web <strong>NO utiliza cookies publicitarias, cookies de seguimiento conductual ni transfiere datos de navegación a redes de publicidad programática de terceros</strong>. Todas las métricas de visita se procesan de forma agregada y anónima localmente en el servidor, de conformidad con los criterios de exención de consentimiento dictados por el Comité Europeo de Protección de Datos (CEPD).</p>

  <h2>4. Cómo Gestionar y Desactivar las Cookies en el Navegador</h2>
  <p>El usuario puede permitir, bloquear o eliminar las cookies instaladas en su equipo mediante la configuración de las opciones del navegador instalado en su ordenador o dispositivo móvil:</p>
  <ul>
    <li><strong>Google Chrome:</strong> Configuración &gt; Privacidad y seguridad &gt; Cookies y otros datos de sitios.</li>
    <li><strong>Mozilla Firefox:</strong> Ajustes &gt; Privacidad &amp; Seguridad &gt; Cookies y datos del sitio.</li>
    <li><strong>Apple Safari:</strong> Preferencias &gt; Privacidad &gt; Bloquear todas las cookies.</li>
    <li><strong>Microsoft Edge:</strong> Configuración &gt; Permisos del sitio &gt; Cookies y datos almacenados.</li>
  </ul>
</body>
</html>"""

    def apply_to_workspace(self, ws_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
        """Generate and save the complete statutory legal bundle to web/public/legal/."""
        app_name = contract.get("app_name", "Plataforma Profesional")
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", app_name.lower())
        legal_company = contract.get("legal_name") or f"{app_name} Global Corp."
        legal_tax = contract.get("tax_id") or "TAX-ID-PENDING"
        legal_addr = contract.get("registered_address") or contract.get("billing_address") or "Headquarters / Corporate Address"
        legal_reg = contract.get("commercial_registry") or "Inscripción Oficial en el Registro / Commercial Register"

        identity = LegalCompanyIdentity(
            legal_name=legal_company,
            trade_name=app_name,
            tax_id=legal_tax,
            registered_address=legal_addr,
            contact_email=contract.get("contact_email") or f"legal@{clean_name}.com",
            dpo_email=contract.get("dpo_email") or f"dpo@{clean_name}.com",
            registry_details=legal_reg
        )

        legal_dir = ws_dir / "web" / "public" / "legal"
        legal_dir.mkdir(parents=True, exist_ok=True)

        aviso_html = self.generate_legal_notice_html(identity)
        privacidad_html = self.generate_privacy_policy_html(identity)
        cookies_html = self.generate_cookie_policy_html(identity)

        (legal_dir / "aviso-legal.html").write_text(aviso_html, encoding="utf-8")
        (legal_dir / "privacidad.html").write_text(privacidad_html, encoding="utf-8")
        (legal_dir / "cookies.html").write_text(cookies_html, encoding="utf-8")

        total_chars = len(aviso_html) + len(privacidad_html) + len(cookies_html)
        logger.info(f"[{ws_dir.name}] Documentación LegalTech AEPD/LSSI generada: {total_chars} caracteres certificados.")
        return {
            "applied": True,
            "legal_dir": str(legal_dir),
            "total_chars": total_chars
        }


legal_engine = LegalEnginePrimitive()
