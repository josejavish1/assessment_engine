---
status: "Verified"
owner: "engineering-governance"
last_verified_against: "2026-05-03"
applies_to:
  - humans
source_of_truth:
  - https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification
doc_type: "canonical"
---

# Política de Firma de Commits

Esta política establece el requisito de firmar criptográficamente los commits para garantizar la autenticidad e integridad del historial de cambios del repositorio.

## 1. Política

**Todos los commits fusionados en la rama `main` deben estar firmados.**

La firma debe estar asociada a la identidad del autor del commit en GitHub. Se utilizará GPG o SSH para la firma, gestionado preferiblemente a través de la integración con `gh` (GitHub CLI).

## 2. Configuración

La forma más robusta y recomendada de configurar la firma de commits es utilizando una clave SSH.

### Pasos para configurar la firma con SSH:

1.  **Generar una nueva clave SSH para firma:**
    ```bash
    ssh-keygen -t ed25519 -C "your_email@example.com"
    ```
    *Es recomendable usar una clave dedicada para la firma.*

2.  **Añadir la clave SSH a tu cuenta de GitHub:**
    -   Ve a `Settings > SSH and GPG keys` en tu perfil de GitHub.
    -   Haz clic en `New SSH key`.
    -   Añade tu clave pública (`.pub`) y márcala como "Signing Key".

3.  **Configurar Git para usar tu clave de firma:**
    ```bash
    # Ruta a tu clave pública
    git config --global gpg.ssh.allowedSignersFile "~/.ssh/allowed_signers"

    # Email asociado a la clave
    echo "$(git config --get user.email) $(cat ~/.ssh/id_ed25519_signing.pub)" >> ~/.ssh/allowed_signers

    # Configurar Git para que use SSH para firmar
    git config --global gpg.format ssh

    # Indicar a Git la clave a usar
    git config --global user.signingkey ~/.ssh/id_ed25519_signing.pub
    ```

4.  **Firmar un commit:**
    -   Usa el flag `-S` para firmar un commit individual: `git commit -S -m "Your commit message"`
    -   Para firmar todos los commits por defecto: `git config --global commit.gpgsign true`

## 3. Racional: ¿Por qué es esta política crítica?

La firma de commits no es una simple formalidad; es una capa de seguridad fundamental que protege la integridad de nuestro código y la confianza en nuestro proceso de desarrollo.

### Riesgos que Mitiga

1.  **Suplantación de Identidad (Spoofing):** Sin firmas, un actor malicioso podría configurar localmente el nombre y correo de otro desarrollador (`git config user.name "Fulano"`) e introducir código malicioso bajo su identidad. La firma criptográfica hace esto imposible, ya que el atacante no posee la clave privada del desarrollador.

2.  **Alteración de Código (Tampering):** Una firma garantiza que el código no ha sido modificado después de que el autor lo firmó. Esto protege contra ataques "man-in-the-middle" en la cadena de suministro de software.

3.  **Repudio de Acciones:** La firma proporciona una prueba irrefutable (no repudio) de que un desarrollador específico es el autor de un cambio. Esto es vital para la rendición de cuentas y la auditoría.

### Valor Estratégico

*   **Confianza y Trazabilidad:** Construye un historial de cambios auditable y de alta integridad, esencial para el cumplimiento de normativas como SOC 2 o ISO 27001.

*   **Automatización Segura:** Permite construir workflows de CI/CD y GitOps que confían en el origen del código. Las reglas de protección de ramas en GitHub pueden hacer cumplir esta política, bloqueando código de origen no verificado antes de que llegue a producción.

*   **Cultura de Seguridad:** Fomenta una mentalidad de seguridad en todo el equipo, reforzando la importancia de la autoría y la responsabilidad.
