"""An AWS Python Pulumi program"""

import pulumi
import pulumi_awsx as awsx
import pulumi_aws as aws
from utils import conf, env

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
            to_port=443,
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

# Create Nginx ECS service
nginx_service = awsx.ecs.FargateService(
    f"{env}-nginx-service",
    cluster=cluster.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=vpc.private_subnet_ids,
        security_groups=[security_group.id],
    ),
    desired_count=2,
    task_definition_args=awsx.ecs.FargateServiceTaskDefinitionArgs(
        container=awsx.ecs.TaskDefinitionContainerDefinitionArgs(
            image="nginx:latest",
            cpu=512,
            memory=128,
            essential=True,
            port_mappings=[
                awsx.ecs.TaskDefinitionPortMappingArgs(
                    target_group=alb.default_target_group,
                )
            ],
        )
    ),
)

# Export the vpc_id
pulumi.export("vpc_id", vpc.vpc_id)

pulumi.export("url", alb.load_balancer.dns_name)
