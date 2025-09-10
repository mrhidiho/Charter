## SaltStack integration with AWS Secrets Manager using ext_pillar
# This setup includes:
# - Python script to retrieve AWS secrets (with fallback to SSM Parameter Store)
# - Salt master config updates
# - Jinja template to inject secret into config
# - IAM policy example

# =============================
# 1. ext_pillar Python module
# =============================
# File: /srv/pillar/ext/secrets_manager.py

import boto3
import json

def ext_pillar(minion_id, pillar, *args, **kwargs):
    region = 'us-east-1'  # adjust as needed
    secret_id = 'prod/app/credentials'  # change to your secret name
    ssm_fallback_path = '/prod/app/credentials'  # fallback path in SSM Parameter Store

    secrets = {}
    try:
        client = boto3.client('secretsmanager', region_name=region)
        response = client.get_secret_value(SecretId=secret_id)
        secrets = json.loads(response['SecretString'])
    except Exception as e:
        try:
            ssm = boto3.client('ssm', region_name=region)
            response = ssm.get_parameters_by_path(
                Path=ssm_fallback_path,
                WithDecryption=True
            )
            for param in response['Parameters']:
                key = param['Name'].split('/')[-1]
                secrets[key] = param['Value']
        except Exception as e2:
            # log both errors if needed
            pass

    return {'aws_secrets': secrets}


# ==========================
# 2. Salt master config
# ==========================
# File: /etc/salt/master

ext_pillar:
  - secrets_manager: {}

# Restart the salt-master to apply changes:
#   sudo systemctl restart salt-master


# ===============================
# 3. Jinja config template
# ===============================
# File: /srv/salt/app/files/config.ini.j2

[database]
username = {{ pillar['aws_secrets']['username'] }}
password = {{ pillar['aws_secrets']['password'] }}
host = db.internal.charter.net

[api]
token = {{ pillar['aws_secrets']['api_key'] }}


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
# 5. IAM Policy (attach to EC2 instance profile)
# ===============================
# Use in AWS Console or Terraform to allow the instance/minion access

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "ssm:GetParametersByPath"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/app/credentials-*",
        "arn:aws:ssm:us-east-1:123456789012:parameter/prod/app/credentials*"
      ]
    }
  ]
}

# ===============================
# DONE: After setup
# ===============================
# - Run `salt-call pillar.items` to confirm secrets are loading
# - Run `salt-call state.apply app` to deploy the config
# - Check /etc/app/config.ini on the minion