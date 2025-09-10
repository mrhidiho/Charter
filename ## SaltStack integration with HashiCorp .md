## SaltStack integration with HashiCorp Vault using ext_pillar
# This setup includes:
# - Python script to retrieve secrets from Vault
# - Salt master config updates
# - Jinja template to inject secret into config
# - Vault policy example

# =============================
# 1. ext_pillar Python module
# =============================
# File: /srv/pillar/ext/vault_secrets.py

import hvac
import os

def ext_pillar(minion_id, pillar, *args, **kwargs):
    vault_addr = os.environ.get('VAULT_ADDR', 'https://vault.mycompany.net')
    token = os.environ.get('VAULT_TOKEN')  # best to use vault-agent or approle auth

    client = hvac.Client(url=vault_addr, token=token)

    path = 'secret/data/prod/app/credentials'  # Vault KV v2 path

    secrets = {}
    try:
        read_response = client.secrets.kv.v2.read_secret_version(path=path)
        secrets = read_response['data']['data']
    except Exception as e:
        pass

    return {'vault_secrets': secrets}


# ==========================
# 2. Salt master config
# ==========================
# File: /etc/salt/master

ext_pillar:
  - vault_secrets: {}

# Restart the salt-master to apply changes:
#   sudo systemctl restart salt-master


# ===============================
# 3. Jinja config template
# ===============================
# File: /srv/salt/app/files/config.ini.j2

[database]
username = {{ pillar['vault_secrets']['username'] }}
password = {{ pillar['vault_secrets']['password'] }}
host = db.internal.charter.net

[api]
token = {{ pillar['vault_secrets']['api_key'] }}


# ===============================
# 4. Salt state to deploy config
# ===============================
# File: /srv/salt/app/init.sls

/etc/app/config.ini:
  file.managed:
    - source: salt://app/files/config.ini.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0600'


# ===============================
# 5. Vault Policy (bind to Salt role/token)
# ===============================
# Example Vault ACL policy for reading secrets

path "secret/data/prod/app/credentials" {
  capabilities = ["read"]
}

# ===============================
# DONE: After setup
# ===============================
# - Ensure VAULT_ADDR and VAULT_TOKEN are exported in Salt master env
# - Run `salt-call pillar.items` to confirm secrets are loading
# - Run `salt-call state.apply app` to deploy the config
# - Check /etc/app/config.ini on the minion

# ===============================
# Optional: Vault Agent with AppRole Auth
# ===============================
# - Use vault-agent to auto-renew tokens and inject into Salt runtime
# - Use Kubernetes or EC2 auth method to avoid static tokens