project=catantracker
service_account_id=catan-tracker-aws-lambda
workload_pool_id=catan-tracker-pool
workload_provider_name=catan-tracker-aws-lambda
aws_account_id=$(aws sts get-caller-identity --query 'Account' --output text)
aws_assumed_iam_role="arn:aws:sts::${aws_account_id}:assumed-role/catan-tracker-sms_interface-prod"
project_number=$(gcloud projects describe $(gcloud config get-value core/project) --format=value\(projectNumber\))
service_account_email=${service_account_id}@${project}.iam.gserviceaccount.com


#################
# Service account
#################

gcloud iam service-accounts create $service_account_id --project="$project"


#################
# Create workload pool and provider
#################

gcloud iam workload-identity-pools create $workload_pool_id \
    --location="global" \
     --project="$project"

gcloud iam workload-identity-pools  \
    providers create-aws $workload_provider_name  \
    --location="global"  \
    --workload-identity-pool=$workload_pool_id  \
    --attribute-condition="'$aws_assumed_iam_role' == attribute.aws_role" \
    --account-id=$aws_account_id \
    --project="$project"

gcloud iam service-accounts add-iam-policy-binding $service_account_email \
    --role=roles/iam.workloadIdentityUser \
    --member=principalSet://iam.googleapis.com/projects/$project_number/locations/global/workloadIdentityPools/$workload_pool_id/attribute.aws_role/$aws_assumed_iam_role \
    --project="$project"


#################
# Create creds
#################

gcloud iam workload-identity-pools create-cred-config \
    projects/$project_number/locations/global/workloadIdentityPools/$workload_pool_id/providers/$workload_provider_name \
    --service-account=$service_account_email \
    --aws \
    --output-file=googlecreds.json


#################
# Enable services
#################

gcloud services enable sts.googleapis.com && gcloud services enable iamcredentials.googleapis.com