# AWS Secrets Manager vs HashiCorp Vault — Comparison for SSH Key and Secrets Management in SaltStack

## 🔁 Now You Can Compare

| Feature                | AWS Secrets Manager + SSM         | HashiCorp Vault                      |
|------------------------|------------------------------------|--------------------------------------|
| Integration with Salt  | `ext_pillar` + Boto3              | `ext_pillar` + hvac                  |
| Rotation Support       | ✅ (auto via AWS)                  | ✅ (via dynamic secrets / leases)    |
| Access Control         | IAM Policies                      | Vault Policies / AppRole             |
| Deployment Flexibility | AWS-native only                   | Can run anywhere (self-hosted or HCP Vault) |
| Complexity             | Medium                            | Higher                               |
| Best for               | AWS environments                  | Multi-cloud or advanced workflows    |

---

## ✅ 1. AWS Secrets Manager / SSM Parameter Store

### Can You Store SSH Keys?
✅ Yes, both support:
- SSH private keys (`.pem`, `.key`)
- Public keys
- TLS certs (`.crt`, `.key`)
- JWT secrets, symmetric keys
- API tokens

### 🔐 Format & Limitations

| Feature               | Secrets Manager         | SSM Parameter Store       |
|----------------------|--------------------------|---------------------------|
| Max size per secret  | 64 KB                    | 4 KB                      |
| Binary support       | ✅ Base64-encoded         | ❌ Text only              |
| Ideal for SSH keys?  | ✅ Yes                    | ⚠️ If < 4KB               |

### Example Secret (JSON)

```json
{
  "ssh_private_key": "-----BEGIN RSA PRIVATE KEY-----\n...",
  "ssh_public_key": "ssh-rsa AAAAB3... user@example"
}
```

---

## ✅ 2. HashiCorp Vault

### Can You Store SSH Keys?
✅ Yes, and Vault also supports advanced workflows:

| Feature                   | Vault Support |
|---------------------------|---------------|
| Store static SSH keys     | ✅ Yes         |
| Issue dynamic SSH certs   | ✅ Yes         |
| Rotate or revoke keys     | ✅ Yes         |
| JIT (Just-In-Time) access | ✅ Yes         |
| Encryption operations     | ✅ Yes (Transit Engine) |

### 🧱 Static Key Example:
```bash
vault kv put secret/prod/app/keys \
    ssh_private="-----BEGIN RSA PRIVATE KEY-----\n..." \
    ssh_public="ssh-rsa AAAA..."
```

### ⚡ Dynamic SSH Cert Example:
```bash
vault write -field=signed_key ssh/sign/my-role \
    public_key=@/path/to/id_rsa.pub
```

---

## 🔐 Security Best Practices

| Practice                           | Recommended |
|-----------------------------------|-------------|
| Encrypt secrets at rest           | ✅ Yes       |
| Restrict access via policies      | ✅ Yes       |
| Rotate keys periodically          | ✅ Yes       |
| Avoid plaintext passphrases       | ✅ Yes       |
| Audit access                      | ✅ Yes       |

---

## 🧩 Usage in Salt

### AWS Secrets Manager (Jinja):
```jinja
# /etc/ssh/ssh_host_rsa_key
{{ pillar['aws_secrets']['ssh_private_key'] | replace('\\n', '\n') }}
```

### Vault (Jinja):
```jinja
# /etc/ssh/ssh_host_rsa_key
{{ pillar['vault_secrets']['ssh_private'] }}
```

> Be sure to use `file.managed` with proper permissions (e.g., `0600`, `root`).

---

## ✅ Summary

| Feature                   | AWS Secrets Manager         | HashiCorp Vault             |
|---------------------------|------------------------------|-----------------------------|
| Store SSH keys (static)   | ✅ Yes                        | ✅ Yes                       |
| Rotate or revoke keys     | ❌ Manual                     | ✅ Native rotation           |
| JIT SSH cert support      | ❌ No                         | ✅ Yes                       |
| Storage Limit             | ✅ 64KB                       | ✅ Unlimited                 |
| Best For AWS Apps         | ✅ Yes                        | ⚠️ Self-hosted or HCP only  |
| Salt Integration          | ✅ ext_pillar supported       | ✅ ext_pillar supported      |
