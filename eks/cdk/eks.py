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

        mng = eks.add_nodegroup_capacity("mng",
            instance_types = [aws_ec2.InstanceType("t3.small")],
            desired_size = 3,
            min_size = 3,
            max_size = 9,
            tags = {'env': 'prod'}
        )

        mng.role.add_managed_policy(aws_iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchAgentServerPolicy"))

        eks.add_helm_chart("aws-cloudwatch-metrics",
            chart = "aws-cloudwatch-metrics",
            repository = "https://aws.github.io/eks-charts",
            namespace = "amazon-cloudwatch",
            values = {'clusterName': eks.cluster_name}
        )

        eks.add_helm_chart("aws-for-fluent-bit",
            chart = "aws-for-fluent-bit",
            repository = "https://aws.github.io/eks-charts",
            namespace = "kube-system",
            values = {
                'cloudWatch.region': core.Stack.of(self).region,
                'cloudWatch.logGroupName': f"/aws/containerinsights/{eks.cluster_name}/application"
            }
        )

        self.output_props = props.copy()
        self.output_props['asg_name']= mng.nodegroup_name
        self.output_props['asg_arn']= mng.nodegroup_arn

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
