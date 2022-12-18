# Pulumi-ECS
In this project I use `pulumi` to provision the following resources in `AWS`
1. A `vpc` to host the `ECS` cluster and `rds` instance.
2. An `ecs` cluster to deploy a `Django` application.
3. An `IAM role` to be used as the executing role for the service.
4. An `ECR` repo to host the application image.
5. An `ALB` to access the application over http.
6. An `ecs service` and `ecs task` to deploy the application to the cluster.
7. Application secrets are stored in the `secret manager` and passed to the task.
8. Two security groups are provisioned for `ALB` and `Postgres`

All the secrets in the project are encrypted with KMS key.