import pulumi
import pulumi_aws as aws
from utils import conf, env

rds_conf = conf.get_object("rds")


def create_rds_instance(
        vpc: aws.ec2.Vpc,
        security_group_id: str,
) -> aws.rds.Instance:
    """Creates and returns rds instance"""
    subnet_group = aws.rds.SubnetGroup(
        f"{env}-subnet-group",
        subnet_ids=vpc.private_subnet_ids,
    )
    parameter_group = aws.rds.ParameterGroup(
        f"{env}-rds-pg",
        args=aws.rds.ParameterGroupArgs(
            family="postgres13",
            name=f"{env}-rds-parameter-group",
        )
    )
    return aws.rds.Instance(
        f"{env}-rds",
        args=aws.rds.InstanceArgs(
            allocated_storage=rds_conf.get("allocated_storage"),
            db_name=pulumi.Output.secret(rds_conf.get("db_name")),
            availability_zone=rds_conf.get("availability_zone"),
            backup_window=rds_conf.get("backup_window"),
            instance_class=rds_conf.get("instance_class"),
            db_subnet_group_name=subnet_group.name,
            engine=rds_conf.get("engine"),
            engine_version=rds_conf.get("engine_version"),
            identifier=f"{env}-rds",
            maintenance_window=rds_conf.get("maintenance_window"),
            multi_az=rds_conf.get("multi_az"),
            password=pulumi.Output.secret(rds_conf.get("password")),
            username=pulumi.Output.secret(rds_conf.get("username")),
            vpc_security_group_ids=[security_group_id],
            parameter_group_name=parameter_group.name,
        )
    )
