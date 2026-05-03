# Política de Firma de Commits

**status: Verified | **Propietario:** `docs-governance` | **Fecha de Efectividad:** `2026-05-02`

## 1. Resumen Ejecutivo

Para mejorar la seguridad y la integridad del repositorio, todos los commits fusionados en la rama `main` **deben estar firmados criptográficamente**. Esta política garantiza que cada cambio proviene de una fuente auténtica y verificada, protegiendo el proyecto contra contribuciones no autorizadas o maliciosas.

La firma de commits se puede realizar utilizando una clave GPG o una clave SSH.

## 2. Principios Clave de la Firma de Commits

-   **Verificación de Identidad:** Un commit firmado prueba que fue creado por el titular de la clave privada, quien se asume que es el autor del commit.
-   **Integridad del Código:** La firma protege contra la manipulación del código después de que el commit ha sido creado y firmado.
-   **Trazabilidad y Confianza:** Refuerza la cadena de confianza en el historial del proyecto, algo crucial para auditorías y para mantener un alto estándar de seguridad.

## 3. Racional de la Política

La firma de commits no es una medida meramente ceremonial; es un control de seguridad fundamental con implicaciones directas en la integridad del proyecto y la confianza del cliente. Esta política existe para mitigar riesgos específicos en un entorno de desarrollo moderno que combina contribuciones humanas y de agentes de IA.

1.  **Garantía de Autoría (No Repudio):** En un proyecto donde se generan artefactos para clientes B2B, es imperativo poder demostrar que cada línea de código y cada cambio provienen de una fuente autorizada. La firma criptográfica proporciona una prueba irrefutable de que un commit fue realizado por un desarrollador específico (o un agente autorizado), impidiendo que alguien pueda atribuir cambios a otra persona o negar la autoría de los suyos.

2.  **Protección contra Adulteración del Repositorio:** Un repositorio de código es un activo crítico. Si un actor malicioso obtuviera acceso a la cuenta de GitHub de un desarrollador, podría inyectar código malicioso (backdoors, filtrado de datos) en el historial del proyecto. La firma de commits, especialmente cuando se combina con la protección de ramas (`branch protection`), exige que cualquier cambio provenga de una clave privada que el atacante no posee, añadiendo una capa robusta de defensa.

3.  **Habilitación de la Automatización Segura (GitOps y Agentes de IA):** A medida que el proyecto depende más de workflows automatizados y contribuciones de agentes de IA, la firma de commits se vuelve aún más crítica. Permite distinguir claramente entre los cambios realizados por un humano verificado y los realizados por un sistema automatizado. Cada agente puede (y debe) tener su propia identidad de firma, garantizando una trazabilidad completa y segura en un entorno de GitOps.

4.  **Cumplimiento de Estándares Profesionales:** La firma de commits es una práctica estándar en proyectos de software de alta seguridad y en el mundo del código abierto. Adoptarla no solo mejora nuestra seguridad, sino que también alinea el proyecto con las mejores prácticas de la industria, transmitiendo madurez y profesionalismo tanto al equipo de desarrollo como a los auditores externos o clientes.

En resumen, esta política es un pilar para mantener una **cadena de custodia digital** sobre nuestro código, asegurando que el historial del repositorio sea fiable, seguro y auditable en todo momento.

## 4. Configuración de la Firma de Commits con GPG

Esta es la opción recomendada y más robusta para la firma de commits.

### Paso 1: Generar una nueva clave GPG

Si no tienes una clave GPG, puedes generar una con el siguiente comando:

```bash
gpg --full-generate-key
```

Sigue las instrucciones en pantalla. Se recomienda usar los siguientes valores:

-   **Tipo de clave:** RSA y RSA (opción por defecto)
-   **Tamaño de la clave:** 4096 bits
-   **Expiración:** Elige un período de expiración razonable (e.g., 1 año).
-   **Nombre real y correo electrónico:** Usa el mismo nombre y correo electrónico asociados a tu cuenta de GitHub.

### Paso 2: Listar tu clave GPG y obtener su ID

Una vez creada la clave, lístala para obtener su ID:

```bash
gpg --list-secret-keys --keyid-format=long
```

La salida será similar a esta:

```
/Users/hubot/.gnupg/secring.gpg
------------------------------------
sec   4096R/3AA5C34371567BD2 2016-03-10 [expira: 2027-03-10]
uid                          Hubot <hubot@example.com>
ssb   4096R/4BB6D45482678BE3 2016-03-10
```

En este ejemplo, el ID de la clave GPG es `3AA5C34371567BD2`.

### Paso 3: Exportar la clave pública GPG

Exporta tu clave pública usando el ID que obtuviste en el paso anterior:

```bash
gpg --armor --export 3AA5C34371567BD2
```

Copia la salida completa, incluyendo `-----BEGIN PGP PUBLIC KEY BLOCK-----` y `-----END PGP PUBLIC KEY BLOCK-----`.

### Paso 4: Añadir la clave GPG a tu cuenta de GitHub

1.  Ve a la configuración de tu cuenta de GitHub.
2.  Navega a la sección "SSH and GPG keys".
3.  Haz clic en "New GPG key".
4.  Pega tu clave pública exportada en el campo de texto y haz clic en "Add GPG key".

### Paso 5: Configurar Git para usar tu clave GPG

Configura Git globalmente para que use tu clave GPG para firmar todos los commits por defecto:

```bash
# Reemplaza 3AA5C34371567BD2 con el ID de tu clave
git config --global user.signingkey 3AA5C34371567BD2

# Configura Git para firmar todos los commits por defecto
git config --global commit.gpgsign true
```

## 5. Configuración de la Firma de Commits con SSH

Como alternativa a GPG, puedes usar tu clave SSH existente para firmar commits, siempre que la hayas subido a tu cuenta de GitHub para autenticación.

### Paso 1: Configurar Git para usar SSH para la firma

```bash
git config --global gpg.format ssh
```

### Paso 2: Especificar la clave SSH a usar

Encuentra tu clave pública SSH y configura Git para que la use:

```bash
# Reemplaza con la ruta a tu clave pública SSH
git config --global user.signingkey ~/.ssh/id_ed25519.pub
```

### Paso 3: Habilitar la firma de commits por defecto

```bash
git config --global commit.gpgsign true
```

## 6. Cómo Firmar Commits

Si has configurado `commit.gpgsign` como `true`, Git firmará tus commits automáticamente.

Si prefieres firmar commits de forma manual, puedes omitir la configuración `commit.gpgsign` y usar el flag `-S` al hacer commit:

```bash
git commit -S -m "Mi mensaje de commit"
```

Al hacer `git log --show-signature`, podrás ver la verificación de la firma en los commits.

## 7. Verificación

Una vez que hayas pusheado tus commits firmados a GitHub, verás una insignia "Verified" junto al hash del commit en la interfaz de usuario de GitHub, confirmando que la política se está cumpliendo correctamente.
