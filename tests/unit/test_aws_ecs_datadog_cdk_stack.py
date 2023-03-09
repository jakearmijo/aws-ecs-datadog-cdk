import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_ecs_datadog_cdk.aws_ecs_datadog_cdk_stack import AwsEcsDatadogCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_ecs_datadog_cdk/aws_ecs_datadog_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsEcsDatadogCdkStack(app, "aws-ecs-datadog-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
