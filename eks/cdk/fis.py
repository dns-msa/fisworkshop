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
                namespace = "AWS/EC2",
                metric_name = "CPUUtilization",
                statistic = "Average",
                dimensions = dict(AutoScalingGroupName= f"{props['asg']}")
            ),
            comparison_operator = aws_cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            threshold = 60,
            evaluation_periods = 3,
            datapoints_to_alarm = 1
        )

        self.output_props = props.copy()

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
