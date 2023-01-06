from typing import Any, List

import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_cloudfront_origins as origins
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as targets
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_iam as iam
from aws_cdk import RemovalPolicy, Stack, ArnFormat, Duration
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
        """
        Handle the frontend part :
        - S3 bucket for the react website
        - Cloudfront in front of the bucket
        - Cloudfront OAC to make the bucket accessible only through CF
        - Arecord and Alias record for the distribution 
        """

        super().__init__(scope, id_)
        # S3 bucket
        s3_front = s3.Bucket(
            self,
            "digidexapi-front",
            public_read_access=False,
            removal_policy=RemovalPolicy.RETAIN,
            encryption=s3.BucketEncryption.S3_MANAGED,
            # website_index_document="index.html",
        )

        cfn_OAC = cloudfront.CfnOriginAccessControl(
            self,
            "DigidexApiFrontOAC",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="DigidexApiFrontOACConfig",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4",
                # the properties below are optional
                description="AOC configuration for digidex api",
            ),
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
        distribution = cloudfront.Distribution(
            self,
            "digidexapi-dist",
            default_behavior=cloudfront.BehaviorOptions(
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                compress=True,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                origin=origins.S3Origin(
                    s3.Bucket.from_bucket_name(
                        self,
                        "BucketOrigin",
                        bucket_name=s3_front.bucket_name,
                    ),
                ),
            ),
            default_root_object="index.html",
            error_responses=[cloudfront.ErrorResponse(
                http_status=403,
                # the properties below are optional
                response_http_status=200,
                response_page_path="/",
                ttl=Duration.minutes(30),
            )],
            domain_names=domain_names,
            certificate=digidexapi_certificate,
            enable_ipv6=True,
        )

        cfnDistribution = distribution.node.default_child
        cfnDistribution.add_property_override(
            "DistributionConfig.Origins.0.S3OriginConfig.OriginAccessIdentity",
            "",
        )
        cfnDistribution.add_property_override(
            "DistributionConfig.Origins.0.OriginAccessControlId",
            cfn_OAC.get_att("Id"),
        )

        s3_front.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                ],
                principals=[iam.ServicePrincipal("cloudfront")],
                resources=[s3_front.arn_for_objects("*")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": Stack.of(self).format_arn(
                            service="cloudfront",
                            resource="distribution",
                            resource_name=distribution.distribution_id,
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            region="",
                        ),
                    },
                },
            ),
        )

        # Alias reccord
        route53.AaaaRecord(
            self,
            "Alias",
            zone=self.public_hosted_zone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution)
            ),
        )
        # ARecord
        route53.ARecord(
            self,
            "ARecord",
            zone=self.public_hosted_zone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution)
            ),
        )
