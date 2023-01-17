import pathlib

import aws_cdk.aws_apigateway as apigateway
import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_lambda_python_alpha as python
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as targets
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_ssm as ssm
from aws_cdk import Duration
from aws_cdk import Stack
from constructs import Construct


class API(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        vpc: ec2.Vpc,
        db_enpoint: str,
        db_user: str,
        certificate_arn: str,
        public_hosted_zone: route53.PublicHostedZone,
        api_domain_name,
        image_bucket: s3.Bucket,
        port: int = 5432,
    ) -> None:

        """
        Handle the webservice part. Will create :
        - role for the lambda :
            - grant rds-db access (authentification with IAM)
            - execution in VPC
        - a SG for the lambda for more security
        - the lambda with the python code and all env useful env var
        - the API gateway with Arecord and the proxy integration

        """
        super().__init__(scope, id_)

        # Lambda's role
        self.lambda_role = iam.Role(
            self,
            "Digidexapi_lambda_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name="Digidexapi_lambda_role",
        )

        # It's ugly but bug in the cdk, cannot get the resource id.
        # and rds.grand_connect() does not work (see doc :
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstance.html#aws_cdk.aws_rds.DatabaseInstance.grant_connect)
        db_user_arn = f"arn:aws:rds-db:{Stack.of(self).region}:{Stack.of(self).account}:dbuser:*/{db_user}"
        iam.Grant.add_to_principal(
            grantee=self.lambda_role,
            actions=["rds-db:connect"],
            resource_arns=[db_user_arn],
        )

        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaVPCAccessExecutionRole"
            )
        )
        image_bucket.grant_read(self.lambda_role)

        # lambda SG
        self.lambda_sg = ec2.SecurityGroup(
            self,
            "Digidexapi_lambda_SG",
            vpc=vpc,
            allow_all_outbound=False,
        )

        db_user = ssm.StringParameter.from_string_parameter_attributes(
            self, "digidex_api", parameter_name="/digimon-api/db/user"
        ).string_value
        digidex_lambda = python.PythonFunction(
            self,
            "Digidexapi_lambda",
            entry=str(
                pathlib.Path(__file__)
                .parent.joinpath("runtime", "digidex_api")
                .resolve()
            ),  # required
            runtime=lambda_.Runtime.PYTHON_3_9,  # required
            index="app.py",  # optional, defaults to 'index.py'
            handler="handler",
            role=self.lambda_role,
            environment={
                "DB_ENPOINT": db_enpoint,
                "DB_USER": ssm.StringParameter.value_for_string_parameter(
                    self, "/digimon-api/db/user"
                ),
                "DB_PORT": f"{port}",
                "S3_IMAGE_BUCKET": image_bucket.bucket_name,
            },
            security_groups=[self.lambda_sg],
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            memory_size=512,
            timeout=Duration.seconds(5),
        )
        # API gateway
        self.api_gw = apigateway.RestApi(
            self,
            "Digidexapi_apigw",
            domain_name=apigateway.DomainNameOptions(
                domain_name="api.digidexapi.com",
                certificate=acm.Certificate.from_certificate_arn(
                    self,
                    "digidexapi-certificate-apigw",
                    certificate_arn
                ),
            ),
        )
        route53.ARecord(
            self,
            "Digidexapi_apigtwAlias",
            record_name=api_domain_name,
            zone=public_hosted_zone,
            target=route53.RecordTarget.from_alias(targets.ApiGateway(self.api_gw)),
        )
        self.api_gw.root.add_proxy(
            default_integration=apigateway.LambdaIntegration(digidex_lambda),
            any_method=False,
        ).add_method("GET")
