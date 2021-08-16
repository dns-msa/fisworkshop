#!/bin/bash
set -e

SCRIPT_DIR_NAME=`dirname "$0"`
WORK_DIR_PATH=`cd ${SCRIPT_DIR_NAME}; pwd -P`

. ${WORK_DIR_PATH}/chaos-env.sh

CHAOS_BUCKET_NAME=`cat ${CDK_OUTPUT_FILE_CHAOS_BASE_STACK} | jq -r '.ChaosBaseStack.chaosBucketName'`
cd ${WORK_DIR_PATH}/product-composite && ./mvnw -DskipTests=true clean package
aws s3 cp ${WORK_DIR_PATH}/product-composite/target/product-composite.jar s3://${CHAOS_BUCKET_NAME}/

aws ssm send-command \
	--targets '[{"Key":"tag:Name","Values":["ChaosProductCompositeStack/productCompositeAsg"]}]' \
	--document-name "AWS-RunShellScript" \
	--max-concurrency 1 \
	--parameters '{"commands":["#!/bin/bash","pkill -f java && sleep 5", "cd /root/product-composite && sudo sh start.sh 1>/dev/null 2>&1 &", "sleep 30"]}'
	#--output text

exit 0;