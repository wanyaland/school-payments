# AWS Configuration
aws_region = "eu-west-1"

# Environment Configuration
environment = "staging"

# EKS Cluster Configuration
cluster_name    = "school-payments-staging"
cluster_version = "1.29"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"

# Subnet Configuration
private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

# Node Group Configuration
node_group_name     = "general-purpose"
node_instance_types = ["t3.medium"]
node_disk_size      = 20
node_desired_size   = 3
node_min_size       = 2
node_max_size       = 5

# Feature Flags
enable_cluster_autoscaler = true
enable_container_insights = true

# Additional Tags
tags = {
  Owner       = "DevOps Team"
  CostCenter  = "Engineering"
  Project     = "School Payments"
}