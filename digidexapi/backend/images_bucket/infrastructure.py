import aws_cdk.aws_s3 as s3
from aws_cdk import RemovalPolicy
from constructs import Construct


class ImagesBucket(Construct):
    def __init__(self, scope: Construct, id_: str) -> None:
        """
        The bucket with the images
        """
        super().__init__(scope, id_)

        self.bucket = s3.Bucket(
            self,
            "digidexapi-images",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
        )
