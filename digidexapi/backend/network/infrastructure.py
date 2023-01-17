import aws_cdk.aws_ec2 as ec2
from constructs import Construct


class Network(Construct):
    """
    The VPC for this app is really simple. We only need a private
    one for the DB and the lambdas. I create a public one too to
    have the possibility to run an ec2 to access the DB.
    Lambdas won't need to access the Internet, so no need of a
    PRIVATE_WITH_EGRESS subnet (NAT gtw cost ~40€/month).
    """

    def __init__(self, scope: Construct, id_: str) -> None:
        super().__init__(scope, id_)
        self.vpc = ec2.Vpc(
            self,
            "Digidexapi_VPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/22"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    cidr_mask=26,
                    name="rds",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                ),
                ec2.SubnetConfiguration(
                    cidr_mask=26,
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                ),
            ],
        )
