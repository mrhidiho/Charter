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