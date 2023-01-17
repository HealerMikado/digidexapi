import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_rds as rds
import aws_cdk.aws_ssm as ssm
from aws_cdk import Duration
from aws_cdk import RemovalPolicy
from aws_cdk import SecretValue
from constructs import Construct

ENGINE = rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_13_7)
INSTANCE_TYPE = ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO)


class Database(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        vpc: ec2.Vpc,
        instance_type: ec2.InstanceType = INSTANCE_TYPE,
        engine: rds.IInstanceEngine = ENGINE,
        port: int = 5432
    ) -> None:
        """
        Handle the DB creation :
        - DB SG
        - DB instance
        """
        super().__init__(scope, id_)
        self.port = port

        # db SG
        self.db_sg = ec2.SecurityGroup(
            self,
            "Digidexapi_db_SG",
            vpc=vpc,
            allow_all_outbound=False,
        )

        self.db_instance = rds.DatabaseInstanceFromSnapshot(
            self,
            "Digidexapi_RDS",
            snapshot_identifier="digidexapi-db-snapshot",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            instance_type=instance_type,
            engine=engine,
            port=port,
            allocated_storage=20,
            storage_type=rds.StorageType.GP2,
            security_groups=[self.db_sg],
            backup_retention=Duration.days(0),
            delete_automated_backups=True,
            removal_policy=RemovalPolicy.DESTROY,
            credentials=rds.SnapshotCredentials.from_password(
                password=SecretValue.unsafe_plain_text(
                    ssm.StringParameter.value_for_string_parameter(
                        self, "/digimon-api/db/password"
                    )
                )
            ),
            enable_performance_insights=False,
        )
