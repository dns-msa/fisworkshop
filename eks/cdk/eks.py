from aws_cdk import (
    aws_ec2 as aws_ec2,
    aws_eks as aws_eks,
    aws_iam as aws_iam,
    core,
)

class EKS(core.Stack):
    def __init__(self, app: core.App, id: str, props, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        vpc = aws_ec2.Vpc(self, "vpc", nat_gateways = 1)
        eks = aws_eks.Cluster(self, "eks",
            vpc = vpc,
            version = aws_eks.KubernetesVersion.V1_20,
            default_capacity = 0
        )

        nodegroup = eks.add_auto_scaling_group_capacity("asg",
            instance_type = aws_ec2.InstanceType("t3.small"),
            desired_capacity = 3,
            min_capacity = 3,
            max_capacity = 9,
        )

        self.output_props = props.copy()
        self.output_props['asg']= nodegroup.auto_scaling_group_name

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props