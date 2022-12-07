import os

import aws_cdk as cdk
from dotenv import load_dotenv

from digidexapi.component import DigidexAPI
from toolchain import Toolchain

load_dotenv()
app = cdk.App()
front_cert_arn = "arn:aws:acm:us-east-1:324873085553:certificate/eeeb907a-ccc9-4a23-a504-197152bbe67f"
front_domain_name = ["www.digidexapi.com", "digidexapi.com"]
api_cert_arn = "arn:aws:acm:eu-west-3:324873085553:certificate/e2f883ba-17bf-4aea-a4df-08d5abe9067a"
api_domain_name = "api.digidexapi.com"
db_user = "digidex_api"


digidexapi = DigidexAPI(
    app,
    "DigidexApi",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
    frontend_cert_arn=front_cert_arn,
    backend_cert_arn=api_cert_arn,
    frontend_domain_names=front_domain_name,
    api_domain_name=api_domain_name,
    db_user=db_user,
)

# Toolchain stack (defines the continuous deployment pipeline)
Toolchain(
    app,
    "DigidexApiToolchain",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
    frontend_cert_arn=front_cert_arn,
    backend_cert_arn=api_cert_arn,
    frontend_domain_names=front_domain_name,
    api_domain_name=api_domain_name,
    db_user=db_user,
)


# Uncomment the next line if you know exactly what Account and Region you
# want to deploy the stack to. */

# env=cdk.Environment(account='123456789012', region='us-east-1'),

# For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html

cdk.Tags.of(digidexapi).add("app", "digidexapi")
app.synth()
