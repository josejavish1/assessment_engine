---
status: Verified
owner: docs-governance
source_of_truth:
- README.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
notes: Canonical security policy and operational guide for cryptographic commit signing and author verification.
---
# Cryptographic Commit Signing Policy

Canonical operational specification establishing the cryptographic signing standards, author verification protocols, and key management procedures across `assessment-engine`.

---

## 1. Security Mandate & Policy Invariant

**All commits integrated into protected repository branches (`main`, `develop`) MUST be cryptographically signed.**

Unsigned commits or commits with unverified signatures fail branch protection quality gates. Every commit signature must link directly to a registered public key associated with the author's GitHub identity.

---

## 2. Supported Signing Key Standards

The repository supports two cryptographic signing protocols:

1. **SSH Signatures (Ed25519 - Recommended Standard):** Lightweight, hardware-accelerated elliptic curve cryptography integrated with existing SSH keyrings.
2. **GPG Signatures (RSA 4096 / Ed25519):** Traditional OpenPGP web of trust standard.
3. **Automated Machine Bots:** Autonomous agent commits created via GitHub Actions workflows sign automatically using the repository's pinned GitHub App or ephemeral GITHUB_TOKEN keys.

---

## 3. Deterministic SSH Signing Configuration

Operators and autonomous environments configuring local commit signing MUST execute the following sequence:

### Step 1: Generate a Dedicated Signing Key
```bash
ssh-keygen -t ed25519 -C "engineer@domain.com" -f ~/.ssh/id_ed25519_signing
```

### Step 2: Register Public Key on GitHub
1. Upload `~/.ssh/id_ed25519_signing.pub` to GitHub via `Settings > SSH and GPG keys`.
2. Select Key Type: **Signing Key**.

### Step 3: Configure Local Git Environment
```bash
# Configure SSH as the signing backend
git config --global gpg.format ssh

# Point Git to the dedicated public signing key
git config --global user.signingkey ~/.ssh/id_ed25519_signing.pub

# Enable automatic signing for all commits
git config --global commit.gpgsign true

# Register allowed signers file for local verification
git config --global gpg.ssh.allowedSignersFile ~/.ssh/allowed_signers
echo "$(git config --get user.email) $(cat ~/.ssh/id_ed25519_signing.pub)" >> ~/.ssh/allowed_signers
```

### Step 4: Verify Local Commit Signature
```bash
git commit -m "chore: test signature"
git log --show-signature -n 1
```

---

## 4. Threat Mitigation Analysis

| Threat Vector | Unsigned Vulnerability | Cryptographic Mitigation |
|---|---|---|
| **Author Spoofing** | Malicious actor commits malicious payloads using a trusted engineer's name and email (`git config user.name`). | GitHub rejects unverified authors lacking the author's private key. |
| **Supply Chain Tampering** | Transit manipulation or proxy alterations modify code between local machine and remote origin. | Cryptographic hash digest guarantees non-tampered data payload integrity. |
| **Action Repudiation** | Contributor denies authoring defective or vulnerable code changes. | Provides non-repudiation audit trails required for SOC 2 Type II and ISO 27001 compliance. |
