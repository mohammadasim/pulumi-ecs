import pulumi_aws as aws
from utils import env


def create_secret(
        secret_name: str,
        secret_value: str,
) -> aws.secretsmanager.Secret:
    """Creates a secret manager secret"""
    secret = aws.secretsmanager.Secret(
        f"{secret_name}",
        args=aws.secretsmanager.SecretArgs(
            name=f"{secret_name}"
        ),
    )
    aws.secretsmanager.SecretVersion(
        f"{secret_name}",
        secret_id=secret.id,
        secret_string=secret_value,
    )
    return secret
