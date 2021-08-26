from aws_cdk import (
    aws_cloudwatch as aws_cw,
    aws_iam as aws_iam,
    aws_fis as aws_fis,
    core,
)
import os

class CloudWatchAlarm(core.Stack):
    def __init__(self, app: core.App, id: str, props, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        alarm = aws_cw.Alarm(self, "cpu-alarm",
            metric = aws_cw.Metric(
                namespace = "ContainerInsights",
                metric_name = "pod_cpu_utilization",
                statistic = "Average",
                period = core.Duration.seconds(30),
                dimensions = dict(
                    Namespace = "sockshop",
                    Service = "front-end",
                    ClusterName = f"{props['eks'].cluster_name}"
                )
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

        # copy properties
        self.output_props = props.copy()

        # iam role
        role = aws_iam.Role(self, "fis-role", assumed_by = aws_iam.ServicePrincipal("fis.amazonaws.com"))
        role.add_managed_policy(aws_iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"))

        # terminate eks nodes experiment
        terminate_nodes_target = aws_fis.CfnExperimentTemplate.ExperimentTemplateTargetProperty(
            resource_type = "aws:eks:nodegroup",
            resource_arns = [f"{props['ng_arn']}"],
            selection_mode = "ALL"
        )

        terminate_nodes_action = aws_fis.CfnExperimentTemplate.ExperimentTemplateActionProperty(
            action_id = "aws:eks:terminate-nodegroup-instances",
            parameters = dict(instanceTerminationPercentage = "40"),
            targets = {'Nodegroups': 'eks-nodes'}
        )

        aws_fis.CfnExperimentTemplate(
            self, "eks-terminate-nodes",
            description = "Terminate EKS nodes",
            role_arn = role.role_arn,
            targets = {'eks-nodes': terminate_nodes_target},
            actions = {'eks-terminate-nodes': terminate_nodes_action},
            stop_conditions = [aws_fis.CfnExperimentTemplate.ExperimentTemplateStopConditionProperty(
                source = "aws:cloudwatch:alarm",
                value = f"{props['alarm_arn']}"
            )],
            tags = {'Name': 'Terminate EKS nodes'}
        )

        # cpu stress experiment
        cpu_stress_target = aws_fis.CfnExperimentTemplate.ExperimentTemplateTargetProperty(
            resource_type = "aws:ec2:instance",
            resource_tags ={'env': 'prod'},
            selection_mode = "PERCENT(80)"
        )

        cpu_stress_action = aws_fis.CfnExperimentTemplate.ExperimentTemplateActionProperty(
            action_id = "aws:ssm:send-command",
            parameters = dict(
                duration = "PT10M",
                documentArn = "arn:aws:ssm:" + self.region + "::document/AWSFIS-Run-CPU-Stress",
                documentParameters = "{\"DurationSeconds\": \"600\", \"InstallDependencies\": \"True\", \"CPU\": \"0\"}"
            ),
            targets = {'Instances': 'eks-nodes'}
        )

        aws_fis.CfnExperimentTemplate(
            self, "eks-cpu-stress",
            description = "CPU stress on EKS nodes",
            role_arn = role.role_arn,
            targets = {'eks-nodes': cpu_stress_target},
            actions = {'eks-cpu-stress': cpu_stress_action},
            stop_conditions = [aws_fis.CfnExperimentTemplate.ExperimentTemplateStopConditionProperty(
                source = "aws:cloudwatch:alarm",
                value = f"{props['alarm_arn']}"
            )],
            tags = {'Name': 'CPU stress on EKS nodes'}
        )

        # disk stress experiment
        disk_stress_target = aws_fis.CfnExperimentTemplate.ExperimentTemplateTargetProperty(
            resource_type = "aws:ec2:instance",
            resource_tags ={'env': 'prod'},
            selection_mode = "COUNT(1)"
        )

        disk_stress_action = aws_fis.CfnExperimentTemplate.ExperimentTemplateActionProperty(
            action_id = "aws:ssm:send-command",
            parameters = dict(
                duration = "PT10M",
                documentArn = "arn:aws:ssm:" + self.region + ":" + self.account + ":document/FIS-Run-Disk-Stress",
                documentParameters = "{\"DurationSeconds\": \"600\", \"InstallDependencies\": \"True\", \"Workers\": \"4\"}"
            ),
            targets = {'Instances': 'eks-nodes'}
        )

        aws_fis.CfnExperimentTemplate(
            self, "eks-disk-stress",
            description = "Disk stress on EKS nodes",
            role_arn = role.role_arn,
            targets = {'eks-nodes': disk_stress_target},
            actions = {'eks-disk-stress': disk_stress_action},
            stop_conditions = [aws_fis.CfnExperimentTemplate.ExperimentTemplateStopConditionProperty(
                source = "aws:cloudwatch:alarm",
                value = f"{props['alarm_arn']}"
            )],
            tags = {'Name': 'Disk stress on EKS nodes'}
        )

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
