terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.9.0"
    }
  }

  backend "s3" {}
}

provider "aws" {
  region = "us-west-2"
  default_tags {
    tags = {
      project    = local.project_name
      git_branch = local.git_branch
      env        = local.env
    }
  }
}

locals {
  # Inputs
  project_name = "catan-tracker"

  # Computed
  api_endpoint = "${aws_api_gateway_deployment.dt.invoke_url}${aws_api_gateway_stage.stage.stage_name}"
  git_branch   = var.git_branch == null ? data.external.get_current_branch.result.branch : var.git_branch
  account_id   = data.aws_caller_identity.current.account_id
  region       = data.aws_region.current.name

  # Calculated based on env
  is_main     = local.git_branch == "main"
  env         = local.is_main ? "prod" : "feature"
  branch_hash = local.is_main ? "prod" : substr(md5(local.git_branch), 0, 8)
}

data "external" "get_current_branch" {
  program = [
    "sh",
    "get_git_branch.sh"
  ]
}