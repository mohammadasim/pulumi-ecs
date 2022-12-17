import pulumi

conf = pulumi.Config()
env = pulumi.get_stack().split("-")[0]
