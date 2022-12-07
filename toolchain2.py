import json
import pathlib
import typing

import aws_cdk as cdk
import aws_cdk.aws_codebuild as codebuild
from aws_cdk import pipelines
from constructs import Construct

from digidexapi.component import DigidexAPI

GITHUB_OWNER = "HealerMikado"
GITHUB_REPO = "digidexapi"
GITHUB_TRUNK_BRANCH = "main"
PRODUCTION_ENV_NAME = "Production"
PRODUCTION_ENV_ACCOUNT = "324873085553"
PRODUCTION_ENV_REGION = "eu-west-3"


class Toolchain(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        api_lambda_reserved_concurrency: int = 1,
        frontend_cert_arn=None,
        backend_cert_arn=None,
        frontend_domain_names=None,
        api_domain_name=None,
        db_user: str = None,
        **kwargs: typing.Any,
    ):
        super().__init__(scope, id_, **kwargs)

        source = pipelines.CodePipelineSource.git_hub(
            repo_string="HealerMikado/digidexapi",
            branch="main",
            authentication=cdk.SecretValue.secrets_manager(
                "github_token", json_field="token"
            ),
        )

        build_spec = {"phases": {"install": {"runtime-versions": {"python": "3.9"}}}}
        synth = pipelines.CodeBuildStep(
            "Synth",
            input=source,
            partial_build_spec=codebuild.BuildSpec.from_object(build_spec),
            install_commands=[
                "chmod 777 ./scripts/install-deps.sh",
                "./scripts/install-deps.sh",
            ],
            commands=[
                "chmod 777 ./scripts/run-tests.sh",
                "./scripts/run-tests.sh",
                "npx cdk synth",
            ],
            primary_output_directory="cdk.out",
        )
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            cli_version=Toolchain._get_cdk_cli_version(),
            cross_account_keys=True,
            docker_enabled_for_synth=True,
            publish_assets_in_parallel=False,
            synth=synth,
        )
        Toolchain._add_production_stage(
            pipeline,
            frontend_cert_arn=frontend_cert_arn,
            backend_cert_arn=backend_cert_arn,
            frontend_domain_names=frontend_domain_names,
            api_domain_name=api_domain_name,
            db_user=db_user,
        )

    @staticmethod
    def _get_cdk_cli_version() -> str:
        package_json_path = (
            pathlib.Path(__file__).parent.joinpath("package.json").resolve()
        )
        with open(package_json_path, encoding="utf_8") as package_json_file:
            package_json = json.load(package_json_file)
        cdk_cli_version = str(package_json["dependencies"]["aws-cdk"])
        return cdk_cli_version

    @staticmethod
    def _add_production_stage(
        pipeline: pipelines.CodePipeline,
        frontend_cert_arn,
        backend_cert_arn,
        frontend_domain_names,
        api_domain_name,
        db_user,
    ) -> None:
        production = cdk.Stage(
            pipeline,
            PRODUCTION_ENV_NAME,
            env=cdk.Environment(
                account=PRODUCTION_ENV_ACCOUNT, region=PRODUCTION_ENV_REGION
            ),
        )
        digidex_api = DigidexAPI(
            production,
            "DigidexApi",
            frontend_cert_arn=frontend_cert_arn,
            backend_cert_arn=backend_cert_arn,
            frontend_domain_names=frontend_domain_names,
            api_domain_name=api_domain_name,
            db_user=db_user,
        )
        api_endpoint_env_var_name = "DigidexApi_API_ENDPOINT"
        smoke_test_commands = [f"curl ${api_endpoint_env_var_name}"]
        smoke_test = pipelines.ShellStep(
            "SmokeTest",
            env_from_cfn_outputs={api_endpoint_env_var_name: digidex_api.api_endpoint},
            commands=smoke_test_commands,
        )
        pipeline.add_stage(production, post=[smoke_test])
