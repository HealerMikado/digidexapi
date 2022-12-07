from typing import Any, List

import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_cloudfront_origins as origins
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as targets
import aws_cdk.aws_s3 as s3
from aws_cdk import RemovalPolicy
from constructs import Construct


class Frontend(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        certificate_arn: str,
        domain_names: List[str],
        **kwargs: Any
    ) -> None:

        super().__init__(scope, id_)
        # S3 bucket
        s3_front = s3.Bucket(
            self,
            "digidexapi-front",
            public_read_access=True,
            removal_policy=RemovalPolicy.RETAIN,
            website_index_document="index.html",
        )
        # Route 53 hosted zone
        self.public_hosted_zone = route53.PublicHostedZone(
            self,
            "digidexapiHostedZOne",
            zone_name="digidexapi.com",
        )
        # Certificate
        digidexapi_certificate = acm.Certificate.from_certificate_arn(
            self, "digidexapi-certificate", certificate_arn=certificate_arn
        )
        # CloudFront distribution
        distribution_digidexapi = cloudfront.Distribution(
            self,
            "digidexapi-dist",
            default_behavior=cloudfront.BehaviorOptions(
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                origin=origins.S3Origin(s3_front),
            ),
            domain_names=domain_names,
            certificate=digidexapi_certificate,
            enable_ipv6=True,
        )
        # Alias reccord
        route53.AaaaRecord(
            self,
            "Alias",
            zone=self.public_hosted_zone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution_digidexapi)
            ),
        )
        # ARecord
        route53.ARecord(
            self,
            "ARecord",
            zone=self.public_hosted_zone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution_digidexapi)
            ),
        )
