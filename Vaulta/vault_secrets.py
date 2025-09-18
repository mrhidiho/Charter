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