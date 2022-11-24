import os
from os import path

import aws_cdk
import dotenv
import aws_cdk.aws_rds as rds
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_lambda_python_alpha as python
import aws_cdk.aws_apigateway as apigateway
import aws_cdk.aws_secretsmanager as secret
import aws_cdk.aws_iam as iam
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_cloudfront_origins as origins
import aws_cdk.aws_ssm as ssm
import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as targets
from aws_cdk import Stack, Duration, RemovalPolicy, CfnOutput, Token, Tags, SecretValue, BundlingOptions
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct

from digidexapi_stack.resource_initialiazer import CdkResourceInitializer


class DigiDexStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dotenv.load_dotenv()

        self.website_resources()
        distributionDomainName = 'digidexapi.com';



        self.build_stack()

    def website_resources(self):
        """
        Create the resources pour the website :
            - s3 bucket with website hosting
            - public hosted zone in R53
            - CloudFront distribution with an already existing cert
            - Alias record and ARecord for the distribution
        """
        # S3 bucket
        s3_front = s3.Bucket(
            self,
            "digidexapi-front",
            public_read_access=True,
            removal_policy=RemovalPolicy.RETAIN,
            website_index_document="index.html",
            bucket_name="digidexapi-front"
        )
        # Route 53 hosted zone
        self.publicHostedZone = route53.PublicHostedZone(
            self, 'digidexapiHostedZOne',
            zone_name='digidexapi.com',
        )
        # Certificate
        cert_arn = 'arn:aws:acm:us-east-1:324873085553:certificate/eeeb907a-ccc9-4a23-a504-197152bbe67f'
        digidexapi_certificate = acm.Certificate.from_certificate_arn(
            self,
            "digidexapi-certificate",
            cert_arn
        )
        # CloudFront distribution
        distribution_digidexapi = cloudfront.Distribution(
            self, "digidexapi-dist",
            default_behavior=cloudfront.BehaviorOptions(
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                origin=origins.S3Origin(s3_front)),
            domain_names=["www.digidexapi.com", "digidexapi.com"],
            certificate=digidexapi_certificate,
            enable_ipv6=True
        )
        # Alias reccord
        route53.AaaaRecord(
            self,
            'Alias',
            zone=self.publicHostedZone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution_digidexapi)
            )
        )
        # ARecord
        route53.ARecord(
            self,
            'ARecord',
            zone=self.publicHostedZone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution_digidexapi)
            )
        )

    def build_stack(self):
        engine = rds.DatabaseInstanceEngine.postgres(
            version=rds.PostgresEngineVersion.VER_13_7)
        instance_type = ec2.InstanceType.of(
            ec2.InstanceClass.T3, ec2.InstanceSize.MICRO)
        port = 5432
        db_name = "digidexapi_db"

        # Create VPC
        my_vpc = ec2.Vpc(
            self,
            'digidex-api-VPC',
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name='rds',
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name='public',
                    subnet_type=ec2.SubnetType.PUBLIC,
                )]
        )
        # Create security groups
        db_security_group, lambda_security_group = self.create_security_groups(my_vpc, port)
        db_instance = rds.DatabaseInstanceFromSnapshot(
            self,
            db_name,
            snapshot_identifier="digidexapi-db-snapshot",
            vpc=my_vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            instance_type=instance_type,
            engine=engine,
            port=port,
            allocated_storage=20,
            storage_type=rds.StorageType.GP2,
            security_groups=[db_security_group],
            backup_retention=Duration.days(0),
            delete_automated_backups=True,
            removal_policy=RemovalPolicy.DESTROY,
            credentials=rds.SnapshotCredentials.from_password(
                password=SecretValue.unsafe_plain_text(
                    ssm.StringParameter.value_for_string_parameter(
                        self, "/digimon-api/db/password"))
            ),
            enable_performance_insights=False
        )
        db_enpoint = db_instance.db_instance_endpoint_address

        s3_image = s3.Bucket(
            self,
            "digidexapi-images",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            bucket_name="digidexapi-images",
        )

        # Lambda
        lambda_role = iam.Role(
            self, "digidexapi-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        # It's ugly but bug in the cdk, cannot get the resource id.
        db_user_arn = f'arn:aws:rds-db:{Stack.of(self).region}:{Stack.of(self).account}:dbuser:*/postgres'
        iam.Grant.add_to_principal(
            grantee=lambda_role,
            actions=['rds-db:connect'],
            resource_arns=[db_user_arn],
        )
        s3_image.grant_read(lambda_role)
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(

        digidex_lambda = python.PythonFunction(
            self, "digidex-lambda",
            entry="../back-digidex/digidex-api",  # required
            runtime=lambda_.Runtime.PYTHON_3_9,  # required
            index="app.py",  # optional, defaults to 'index.py'
            handler="handler",
            role=lambda_role,
            environment={
                "DB_ENPOINT": db_enpoint,
                "DB_PASSWORD": ssm.StringParameter.value_for_string_parameter(
                    self, "/digimon-api/db/password"),
                "DB_USER": ssm.StringParameter.value_for_string_parameter(
                    self, "/digimon-api/db/user")
            },
            security_groups=[lambda_security_group],
            vpc=my_vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            memory_size=512,
            timeout=Duration.seconds(5)
        )
        # API gateway
        api_gw = apigateway.RestApi(
            self, "digimon-api"
            , domain_name=apigateway.DomainNameOptions(
                domain_name="api.digidexapi.com",
                certificate=acm.Certificate.from_certificate_arn(
                    self,
                    "digidexapi-certificate-apigw",
                    "arn:aws:acm:eu-west-3:324873085553:certificate/e2f883ba-17bf-4aea-a4df-08d5abe9067a"
                )
            ))
        route53.ARecord(self, "apigtwAlias",
                        record_name="api.digidexapi.com",
                        zone=self.publicHostedZone,
                        target=route53.RecordTarget.from_alias(targets.ApiGateway(api_gw))
                        )
        api_gw.root.add_proxy(
            default_integration=apigateway.LambdaIntegration(
                digidex_lambda),
            any_method=False,
        ).add_method("GET")

    def create_security_groups(self, my_vpc, port):
        # db SG
        db_security_group = ec2.SecurityGroup(
            self, "Digimon-db-SG", security_group_name="Digimon-db-SG",
            vpc=my_vpc,
            allow_all_outbound=False)
        # lambda SG
        lambda_security_group = ec2.SecurityGroup(
            self,
            "Lambda-SG",
            security_group_name="Lambda-SG",
            vpc=my_vpc
            , allow_all_outbound=False)
        db_security_group.add_ingress_rule(
            lambda_security_group,
            ec2.Port.tcp(port),
            f"Allow port {port} for databe connection from lambda SG")
        lambda_security_group.add_egress_rule(
            db_security_group,
            ec2.Port.tcp(port),
            f"Allow SG to access {port} for databasee connection")

        return db_security_group, lambda_security_group
