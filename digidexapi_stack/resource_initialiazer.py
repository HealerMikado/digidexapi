import json
from typing import Any

from aws_cdk import Stack, Duration
from constructs import Construct
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_lambda as lambda_
import aws_cdk.custom_resources as custom_resources
import aws_cdk.aws_iam as iam
import aws_cdk.aws_logs as aws_logs

import hashlib


class CdkResourceInitializer(Construct):
    def __init__(self, scope: Construct, id: str,
                 vpc: ec2.IVpc,
                 subnetsSelection: ec2.SelectedSubnets,
                 fnSecurityGroups: ec2.ISecurityGroup,
                 fnTimeout: Duration,
                 fnCode: lambda_.DockerImageCode,
                 fnLogRetention: aws_logs.RetentionDays,
                 config: Any,
                 *, prefix=None):
        super().__init__(scope, id)
        stack = Stack.of(self)

        fnSg = ec2.SecurityGroup(
            self, 'ResourceInitializerFnSg',
            security_group_name=f"{id}ResourceInitializerFnSg",
            vpc=vpc,
            allow_all_outbound=True)

        fn = lambda_.DockerImageFunction(
            self,
            "ResourceInitializerFn",
            memory_size=128,
            function_name=f"{id}-{stack.stack_name}",
            code=fnCode,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            vpc=vpc,
            security_groups=[fnSg].extend(fnSecurityGroups),
            timeout=fnTimeout,
            log_retention=fnLogRetention,
            allow_all_outbound=True
        )

        payload = json.dumps(
            {"params": {
                "config": config
            }}
        )
        payloadHashPrefix = hashlib.md5(payload.encode()).hexdigest()[0:6]

        sdkCall = custom_resources.AwsSdkCall(
            service='Lambda',
            action='invoke',
            parameters={
                "FunctionName": fn.function_name,
                "Payload": payload
            },
            physical_resource_id=custom_resources.PhysicalResourceId.of(
                f"{id}-AwsSdkCall-{fn.current_version.version}{payloadHashPrefix}")
        )

        customResourceFnRole = iam.Role(
            self,
            'AwsCustomResourceRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        )

        customResourceFnRole.add_to_policy(
            iam.PolicyStatement(
                resources=[f'arn:aws:lambda:{stack.region}:{stack.account}:function:*-ResInit{stack.stack_name}'],
                actions=['lambda:InvokeFunction']
            )
        )

        self.custom_resource = custom_resources.AwsCustomResource(
            self,
            'AwsCustomResource',
            policy=custom_resources.AwsCustomResourcePolicy.from_sdk_calls(
                resources=custom_resources.AwsCustomResourcePolicy.ANY_RESOURCE),
            on_update=sdkCall,
            timeout=Duration.minutes(1),
            role=customResourceFnRole
        )

        self.response = self.custom_resource.get_response_field('Payload')
        self.function = fn
