from aws_cdk import (
    core,
)
from eks import EKS
from fis import CloudWatchAlarm
from fis import FIS
from ssm import DiskStressDocument

props = {'namespace': 'fisworkshop'}
app = core.App()

eks = EKS(app, f"{props['namespace']}-eks", props)
cw = CloudWatchAlarm(app, f"{props['namespace']}-cw", eks.outputs)
disk_stress = DiskStressDocument(app, f"{props['namespace']}-ssm-diskstress", cw.outputs)
fis = FIS(app, f"{props['namespace']}-fis", cw.outputs)

app.synth()
