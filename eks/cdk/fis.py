from aws_cdk import (
    aws_cloudwatch as aws_cw,
    aws_iam as aws_iam,
    aws_fis as aws_fis,
    core,
)

class CloudWatchAlarm(core.Stack):
    def __init__(self, app: core.App, id: str, props, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        alarm = aws_cw.Alarm(self, "cpu-alarm",
            metric = aws_cw.Metric(
                namespace = "AWS/AutoScaling",
                metric_name = "CPUUtilization",
                statistic = "Average",
                dimensions = dict(AutoScalingGroupName = f"{props['asg_name']}")
            ),
            comparison_operator = aws_cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            threshold = 60,
            evaluation_periods = 1,
            datapoints_to_alarm = 1
        )

        self.output_props = props.copy()
        self.output_props['alarm_arn'] = alarm.alarm_arn

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props


class FIS(core.Stack):
    def __init__(self, app: core.App, id: str, props, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        role = aws_iam.Role(self, "fis-role", assumed_by = aws_iam.ServicePrincipal("fis.amazonaws.com"))
        role.add_managed_policy(aws_iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"))

        target = aws_fis.CfnExperimentTemplate.ExperimentTemplateTargetProperty(
            resource_type = "aws:eks:nodegroup",
            resource_arns = [f"{props['asg_arn']}"],
            selection_mode = "ALL"
        )

        action = aws_fis.CfnExperimentTemplate.ExperimentTemplateActionProperty(
            action_id = "aws:eks:terminate-nodegroup-instances",
            parameters = dict(instanceTerminationPercentage = "40"),
            targets = {'Nodegroups': 'eks-nodes'}
        )

        aws_fis.CfnExperimentTemplate(
            self, "eks-terminate-nodes",
            description = "Terminate EKS nodes",
            role_arn = role.role_arn,
            targets = {'eks-nodes': target},
            actions = {'eks-terminate-nodes': action},
            stop_conditions = [aws_fis.CfnExperimentTemplate.ExperimentTemplateStopConditionProperty(
                source = "aws:cloudwatch:alarm",
                value = f"{props['alarm_arn']}"
            )],
            tags = {'Name': 'Terminate EKS nodes'}
        )

        self.output_props = props.copy()

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
