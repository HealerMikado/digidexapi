import typing

import constructs
from aws_cdk import Stack

from digidexapi.backend.component import Backend
from digidexapi.frontend.component import Frontend


class DigidexAPI(Stack):
    def __init__(
        self,
        scope: constructs.Construct,
        id_: str,
        *,
        api_lambda_reserved_concurrency: int = 1,
        frontend_cert_arn=None,
        backend_cert_arn=None,
        frontend_domain_names=None,
        api_domain_name=None,
        db_user: str = None,
        **kwargs: typing.Any
    ):
        super().__init__(scope, id_, **kwargs)

        front = Frontend(
            self,
            "DigidexApiFront",
            certificate_arn=frontend_cert_arn,
            domain_names=frontend_domain_names,
        )
        back = Backend(
            self,
            "DigidexApiBack",
            api_lambda_reserved_concurrency=1,
            certificate_arn=backend_cert_arn,
            public_hosted_zone=front.public_hosted_zone,
            api_domain_name=api_domain_name,
            db_user=db_user,
        )

        self.api_endpoint = back.api_endpoint
