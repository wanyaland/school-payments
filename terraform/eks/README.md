# School Payments EKS Infrastructure

This Terraform configuration creates an EKS cluster with VPC, subnets, and node groups for the School Payments application.

## Prerequisites

- Terraform 1.5.0 or later
- AWS CLI configured with appropriate permissions
- Terraform Cloud account (optional, for remote execution)

## Required Permissions

Your AWS account needs the following IAM permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "eks:*",
                "ec2:*",
                "iam:*",
                "autoscaling:*",
                "cloudwatch:*"
            ],
            "Resource": "*"
        }
    ]
}
```

## Quick Start

1. **Clone and navigate to the terraform directory:**
   ```bash
   cd terraform/eks
   ```

2. **Copy the example variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. **Edit the variables file** with your specific values:
   ```bash
   nano terraform.tfvars
   ```

4. **Initialize Terraform:**
   ```bash
   terraform init
   ```

5. **Review the plan:**
   ```bash
   terraform plan
   ```

6. **Apply the configuration:**
   ```bash
   terraform apply
   ```

## Local CLI Setup

For local development and execution:

1. **Configure AWS CLI** with your credentials:
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, region (eu-west-1), and output format
   ```

2. **Navigate to terraform directory**:
   ```bash
   cd terraform/eks
   ```

3. **Copy and edit variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your specific values
   ```

4. **Initialize and run locally**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region | `eu-west-1` |
| `environment` | Environment name | `staging` |
| `cluster_name` | EKS cluster name | `school-payments-staging` |
| `cluster_version` | Kubernetes version | `1.28` |

### VPC Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `vpc_cidr` | VPC CIDR block | `10.0.0.0/16` |
| `private_subnets` | Private subnet CIDRs | `["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]` |
| `public_subnets` | Public subnet CIDRs | `["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]` |

### Node Group Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `node_instance_types` | EC2 instance types | `["t3.medium"]` |
| `node_disk_size` | Disk size in GB | `20` |
| `node_desired_size` | Desired node count | `3` |
| `node_min_size` | Minimum node count | `2` |
| `node_max_size` | Maximum node count | `5` |

## Outputs

After successful deployment, the following outputs are available:

- `cluster_endpoint`: EKS API endpoint
- `cluster_name`: Cluster name for kubectl config
- `vpc_id`: VPC ID for additional resources
- `private_subnet_ids`: Private subnet IDs
- `kubectl_config`: Command to configure kubectl

## Connecting to the Cluster

After deployment, configure kubectl:

```bash
# Using the output command
$(terraform output kubectl_config)

# Or manually
aws eks update-kubeconfig --region eu-west-1 --name school-payments-staging
```

Verify connection:
```bash
kubectl get nodes
kubectl get pods -A
```

## Next Steps

1. **Install Kubernetes add-ons** (refer to EKS_SETUP.md)
2. **Deploy ArgoCD** for GitOps
3. **Apply application manifests**
4. **Set up monitoring and logging**

## Cost Optimization

- Use spot instances for non-production workloads
- Configure auto-scaling based on workload
- Set up resource requests and limits
- Use appropriate instance types

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**: If you see "No valid credential sources found":
   - Ensure AWS credentials are set as **Environment Variables** in Terraform Cloud workspace
   - Mark `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as "Sensitive"
   - Do not set them as Terraform variables

2. **IAM Permissions**: Ensure your AWS user/role has required permissions

3. **Region Availability**: Check if EKS is available in your chosen region

4. **Quota Limits**: Verify EC2 and EKS service quotas

5. **State Lock**: If using Terraform Cloud, check for state locks in the workspace

### Cleanup

To destroy the infrastructure:

```bash
terraform destroy
```

**⚠️ Warning**: This will delete all resources including the EKS cluster, VPC, and associated resources.