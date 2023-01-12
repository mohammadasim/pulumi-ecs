"""An AWS Python Pulumi program"""
import pulumi
import pulumi_awsx as awsx
import pulumi_aws as aws
from utils import conf, env
from ecr import create_ecr_repo
from rds import create_rds_instance, rds_conf
from secrets import create_secret
from iam import create_iam_role, create_inline_policy

# Create vpc
vpc_config = conf.get_object("vpc")
vpc = awsx.ec2.Vpc(
    f"{env}-ecs-vpc",
    cidr_block=vpc_config.get("vpc_cidr"),
    enable_dns_hostnames=True,
    enable_dns_support=True,
)

# Creat security group
security_group = aws.ec2.SecurityGroup(
    f"{env}-ecs-sg",
    description="Allow all outbound and inbound traffic",
    vpc_id=vpc.vpc_id,
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol=-1,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
)
# Create services security-group
postgres_sg = aws.ec2.SecurityGroup(
    f"{env}-postgres-sg",
    description="Allow outbound traffic",
    vpc_id=vpc.vpc_id,
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol=-1,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            from_port=5432,
            to_port=5432,
            protocol="tcp",
            cidr_blocks=[f"{vpc_config.get('vpc_cidr')}"]
        )
    ]
)
# Create RDS instance
rds = create_rds_instance(vpc, postgres_sg.id)

# Create db password secret
db_password_secret = create_secret(
    f"{env}-pgsql-db-pasw",
    pulumi.Output.secret(rds_conf.get("password"))
)
# Create db hostname secret
db_host_secret = create_secret(
    f"{env}-pgsql-db-host",
    rds.address
)
secret_key_secret = create_secret(
    f"{env}-secret-key",
    pulumi.Output.secret(
        conf.get_object("app").get("secret_key")
    )
)
# Create application inline policy
secrets_inline_policy = create_inline_policy(
    f"{env}-app-secrets-policy",
    ["secretsmanager:GetSecretValue"],
    [db_password_secret.arn, db_host_secret.arn, secret_key_secret.arn]
)
# Create application task execution role
app_execution_role = create_iam_role(
    f"{env}-app-service-execution-role",
    [secrets_inline_policy],
    "ecs-tasks.amazonaws.com",
    managed_policies=[aws.iam.get_policy(name="AmazonECSTaskExecutionRolePolicy").arn]
)

# Creat ECS cluster
cluster = aws.ecs.Cluster(
    f"{env}-ecs-cluster",
    name=f"{env}-ecs-cluster",
)

# Create an ALB
alb = awsx.lb.ApplicationLoadBalancer(
    f"{env}-ecs-alb",
    security_groups=[security_group.id],
    subnet_ids=vpc.public_subnet_ids,
)

app_service = awsx.ecs.FargateService(
    f"{env}-app-service",
    cluster=cluster.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=vpc.private_subnet_ids,
        security_groups=[security_group.id],
    ),
    desired_count=1,

    task_definition_args=awsx.ecs.FargateServiceTaskDefinitionArgs(
        execution_role=awsx.awsx.DefaultRoleWithPolicyArgs(role_arn=app_execution_role.arn),
        container=awsx.ecs.TaskDefinitionContainerDefinitionArgs(
            image="191998317647.dkr.ecr.eu-west-1.amazonaws.com/mfdw_site:0.6",
            cpu=512,
            memory=128,
            essential=True,
            port_mappings=[
                awsx.ecs.TaskDefinitionPortMappingArgs(
                    target_group=alb.default_target_group,
                )
            ],
            secrets=[
                awsx.ecs.TaskDefinitionSecretArgs(
                    name="PGSQL_DB_PASW",
                    value_from=db_password_secret.arn
                ),
                awsx.ecs.TaskDefinitionSecretArgs(
                    name="PGSQL_DB_HOST",
                    value_from=db_host_secret.arn
                ),
                awsx.ecs.TaskDefinitionSecretArgs(
                    name="SECRET_KEY",
                    value_from=secret_key_secret.arn
                )
            ],
            environment=[
                awsx.ecs.TaskDefinitionKeyValuePairArgs(
                    name="ALLOWED_HOSTS",
                    value="*"
                )
            ]
        ),
    ),
)
# Create ECR repo
ecr_conf = conf.get_object("ecr")
if ecr_conf:
    for ecr in ecr_conf:
        create_ecr_repo(ecr.get("name"))

# Export the vpc_id
pulumi.export("vpc_id", vpc.vpc_id)

pulumi.export("url", alb.load_balancer.dns_name)
