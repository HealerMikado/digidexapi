from typing import Any

import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
from constructs import Construct

from digidexapi.backend.api.infrastructure import API
from digidexapi.backend.database.infrastructure import Database
from digidexapi.backend.images_bucket.infrastructure import ImagesBucket
from digidexapi.backend.network.infrastructure import Network


class Backend(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        api_lambda_reserved_concurrency: int,
        certificate_arn: str = "",
        public_hosted_zone=None,
        api_domain_name=None,
        db_user: str = "",
        **kwargs: Any,
    ):
        super().__init__(scope, id_, **kwargs)

        network = Network(self, "Network")
        image_bucket = ImagesBucket(self, "ImageBucket")

        database = Database(
            self,
            "Database",
            vpc=network.vpc,
        )

        api = API(
            self,
            "API",
            vpc=network.vpc,
            db_enpoint=database.db_instance.db_instance_endpoint_address,
            db_user=db_user,
            certificate_arn=certificate_arn,
            public_hosted_zone=public_hosted_zone,
            api_domain_name=api_domain_name,
            port=database.port,
            image_bucket=image_bucket.bucket,
        )

        database.db_sg.add_ingress_rule(
            api.lambda_sg,
            ec2.Port.tcp(database.port),
            f"Allow port {database.port} for database connection from digidexapi lambda",
        )
        api.lambda_sg.add_egress_rule(
            database.db_sg,
            ec2.Port.tcp(database.port),
            f"Allow SG to access {database.port} for database connection",
        )

        self.api_endpoint = cdk.CfnOutput(
            self,
            "DigidexapiEndpoint",
            # API doesn't disable create_default_stage, hence URL will be defined
            value=api.api_gw.url,  # type: ignore
        )
