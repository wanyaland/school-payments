# EKS Cluster Setup for Staging

This guide covers setting up an Amazon EKS cluster for the staging environment using two approaches:

1. **eksctl** (Recommended for quick setup and learning)
2. **Terraform CLI** (Recommended for production and Infrastructure as Code)

## Prerequisites

- AWS CLI configured with appropriate permissions
- kubectl installed
- Helm 3.x installed

### For eksctl approach:
- eksctl installed

### For Terraform CLI approach:
- Terraform 1.5.0 or later
- AWS CLI configured with credentials

## Option 1: Terraform CLI (Infrastructure as Code)

### Local Setup

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

### Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration (creates EKS cluster, VPC, subnets, and ECR repository)
terraform apply
```

### Benefits of Terraform CLI

- **Local Control**: Full control over execution and debugging
- **State Management**: Local state file (can be configured for remote storage)
- **Cost Effective**: No additional cloud service costs
- **Version Control**: State can be committed to git (not recommended for production)
- **Flexibility**: Easy to modify and test locally
- **Integration**: Works with existing AWS CLI and SDK configurations

## Option 2: eksctl (Quick Setup)

## Cluster Creation

### 1. Create EKS Cluster

```bash
# Create cluster configuration file
cat > cluster.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: school-payments-staging
  region: eu-west-1
  version: "1.28"

vpc:
  cidr: "10.0.0.0/16"
  nat:
    gateway: HighlyAvailable

managedNodeGroups:
  - name: general-purpose
    instanceType: t3.medium
    desiredCapacity: 3
    minSize: 2
    maxSize: 5
    volumeSize: 20
    iam:
      withAddonPolicies:
        autoScaler: true
        cloudWatch: true
        ebs: true
        fsx: true
        efs: true

addons:
  - name: vpc-cni
    version: latest
  - name: coredns
    version: latest
  - name: kube-proxy
    version: latest

iam:
  withOIDC: true
EOF

# Create the cluster
eksctl create cluster -f cluster.yaml
```

### 2. Configure kubectl

```bash
# Update kubeconfig
aws eks update-kubeconfig --region eu-west-1 --name school-payments-staging

# Verify connection
kubectl get nodes
kubectl get pods -n kube-system
```

## Networking Setup

### 1. Install AWS Load Balancer Controller

```bash
# Create IAM policy
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.0/docs/install/iam_policy.json
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam-policy.json

# Create service account
eksctl create iamserviceaccount \
  --cluster=school-payments-staging \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::ACCOUNT-ID:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Install controller
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=school-payments-staging \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### 2. Install NGINX Ingress Controller

```bash
# Add Helm repo
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install NGINX
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/aws-load-balancer-type"="nlb"
```

## Storage Setup

### 1. Create EBS Storage Class

```bash
# Apply storage class
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
parameters:
  type: gp3
  encrypted: "true"
EOF
```

### 2. Set as default storage class

```bash
kubectl patch storageclass ebs-sc -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

## Database Setup

### 1. Create RDS PostgreSQL

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name school-payments-staging \
  --db-subnet-group-description "Staging database subnet group" \
  --subnet-ids subnet-12345 subnet-67890

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier school-payments-staging \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username admin \
  --master-user-password "CHANGE_THIS_PASSWORD" \
  --allocated-storage 20 \
  --db-subnet-group-name school-payments-staging \
  --vpc-security-group-ids sg-12345 \
  --backup-retention-period 7 \
  --no-publicly-accessible
```

### 2. Create ElastiCache Redis

```bash
# Create subnet group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name school-payments-staging \
  --cache-subnet-group-description "Staging Redis subnet group" \
  --subnet-ids subnet-12345 subnet-67890

# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id school-payments-staging \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --cache-subnet-group-name school-payments-staging \
  --security-group-ids sg-12345 \
  --snapshot-retention-limit 7
```

## Monitoring Setup

### 1. Install Metrics Server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### 2. Install CloudWatch Container Insights

```bash
# Create IAM policy for CloudWatch
cat > cloudwatch-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData",
                "ec2:DescribeTags",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
                "logs:DescribeLogGroups",
                "logs:CreateLogStream",
                "logs:CreateLogGroup"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam create-policy \
  --policy-name CloudWatchContainerInsightsPolicy \
  --policy-document file://cloudwatch-policy.json

# Create service account
eksctl create iamserviceaccount \
  --cluster=school-payments-staging \
  --namespace=amazon-cloudwatch \
  --name=cloudwatch-agent \
  --role-name CloudWatchAgentRole \
  --attach-policy-arn=arn:aws:iam::ACCOUNT-ID:policy/CloudWatchContainerInsightsPolicy \
  --approve

# Install CloudWatch agent
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml
```

## Security Setup

### 1. Create Namespaces

```bash
# Create namespaces
kubectl create namespace school-payments-staging
kubectl create namespace argocd
kubectl create namespace ingress-nginx
kubectl create namespace monitoring
```

### 2. Network Policies

```bash
# Apply network policies
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: school-payments-staging
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web
  namespace: school-payments-staging
spec:
  podSelector:
    matchLabels:
      app: school-payments-web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
EOF
```

### 3. RBAC Setup

```bash
# Create service account for ArgoCD
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: argocd-manager
  namespace: argocd
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: argocd-manager-role
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: argocd-manager-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: argocd-manager-role
subjects:
- kind: ServiceAccount
  name: argocd-manager
  namespace: argocd
EOF
```

## ArgoCD Installation

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## Application Deployment

### 1. Configure Secrets

```bash
# Create secrets for staging
kubectl create secret generic school-payments-secret \
  --namespace=school-payments-staging \
  --from-literal=DATABASE_URL="postgresql://admin:PASSWORD@school-payments-staging.cluster-xyz.eu-west-1.rds.amazonaws.com:5432/school_payments" \
  --from-literal=SECRET_KEY="your-django-secret-key" \
  --from-literal=QBO_CLIENT_ID="your-qbo-client-id" \
  --from-literal=QBO_CLIENT_SECRET="your-qbo-client-secret" \
  --from-literal=SCHOOL_API_BASE_URL="https://api.school.edu" \
  --from-literal=SCHOOL_API_TOKEN="your-api-token"
```

### 2. Deploy Applications

```bash
# Apply ArgoCD applications
kubectl apply -f argocd/

# Sync applications
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
argocd login localhost:8080 --username admin --password <password>
argocd app sync school-payments-staging
```

## Cost Optimization

### 1. Auto Scaling

```bash
# Enable cluster autoscaler
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  labels:
    app: cluster-autoscaler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      serviceAccountName: cluster-autoscaler
      containers:
      - name: cluster-autoscaler
        image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.27.3
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/school-payments-staging
EOF
```

### 2. Spot Instances (Optional)

```yaml
# Add to cluster.yaml for spot instances
managedNodeGroups:
  - name: spot-nodes
    instanceType: t3.medium
    desiredCapacity: 2
    minSize: 0
    maxSize: 10
    spot: true
    volumeSize: 20
```

## Backup and Disaster Recovery

### 1. Velero for Backup

```bash
# Install Velero
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
helm install velero vmware-tanzu/velero \
  --namespace velero \
  --create-namespace \
  --set configuration.provider=aws \
  --set configuration.backupStorageLocation.bucket=school-payments-staging-backups \
  --set configuration.backupStorageLocation.config.region=eu-west-1 \
  --set configuration.volumeSnapshotLocation.config.region=eu-west-1 \
  --set image.repository=velero/velero \
  --set image.tag=v1.11.0 \
  --set image.pullPolicy=IfNotPresent \
  --set initContainers[0].name=velero-plugin-for-aws \
  --set initContainers[0].image=velero/velero-plugin-for-aws:v1.7.0 \
  --set initContainers[0].volumeMounts[0].mountPath=/target \
  --set initContainers[0].volumeMounts[0].name=plugins
```

## Monitoring and Alerting

### 1. Prometheus and Grafana

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --create-namespace

# Install Grafana
helm install grafana stable/grafana \
  --namespace monitoring \
  --set adminPassword='admin'
```

## Cleanup

```bash
# Delete cluster (when done)
eksctl delete cluster --name school-payments-staging

# Delete RDS
aws rds delete-db-instance --db-instance-identifier school-payments-staging --skip-final-snapshot

# Delete ElastiCache
aws elasticache delete-cache-cluster --cache-cluster-id school-payments-staging