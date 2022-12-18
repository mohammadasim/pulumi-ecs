import pulumi_aws as aws
from utils import env


def create_ecr_repo(
        repo_name: str
) -> aws.ecr.Repository:
    """Creates and returns ecr repo"""
    return aws.ecr.Repository(
        f"{env}-{repo_name}",
        name=repo_name
    )
