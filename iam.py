import json

import pulumi_aws as aws
from typing import Sequence


def create_iam_role(
        role_name: str,
        inline_policies: Sequence[aws.iam.Role],
        service: str,
        managed_policies: Sequence[str] = None,
) -> aws.iam.Role:
    """Creates and returns IAM role"""
    trust_policy = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": f"{service}"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    )
    return aws.iam.Role(
        f"{role_name}",
        name=role_name,
        assume_role_policy=trust_policy,
        managed_policy_arns=managed_policies,
        inline_policies=inline_policies,
    )


def create_inline_policy(
        policy_name: str,
        actions: Sequence[str],
        resources: Sequence[str],
        effect: str = "Allow",
) -> aws.iam.RoleInlinePolicyArgs:
    """Generates and returns IAM policy document in json format"""
    inline_policy = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                effect=effect,
                actions=actions,
                resources=resources,
            )
        ]
    ).json
    return aws.iam.RoleInlinePolicyArgs(name=policy_name, policy=inline_policy)
