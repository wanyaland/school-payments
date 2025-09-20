# ArgoCD Setup Guide

This guide covers installing and configuring ArgoCD for managing Kubernetes deployments.

## Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-managed)
- kubectl configured to access the cluster
- Helm 3.x installed

## Installation

### 1. Install ArgoCD using Helm

```bash
# Add ArgoCD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create namespace
kubectl create namespace argocd

# Install ArgoCD
helm install argocd argo/argo-cd \
  --namespace argocd \
  --version 5.46.0 \
  --set server.service.type=LoadBalancer \
  --set server.ingress.enabled=true \
  --set server.ingress.className=nginx \
  --set server.ingress.hosts[0]=argocd.yourdomain.com
```

### 2. Get ArgoCD admin password

```bash
# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### 3. Access ArgoCD UI

```bash
# Port forward (if not using LoadBalancer)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open https://localhost:8080
# Login with username: admin and the password from step 2
```

## Configuration

### 1. Create Projects

```bash
# Create project for school-payments
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: school-payments
  namespace: argocd
spec:
  description: School Payments Application
  sourceRepos:
    - 'https://github.com/your-org/school-payments'
  destinations:
    - namespace: 'school-payments-*'
      server: 'https://kubernetes.default.svc'
  clusterResourceWhitelist:
    - group: '*'
      kind: '*'
EOF
```

### 2. Deploy Applications

```bash
# Apply all ArgoCD applications
kubectl apply -f argocd/
```

### 3. Configure GitOps Repository

In ArgoCD UI:
1. Go to Settings → Repositories
2. Add repository: `https://github.com/your-org/school-payments`
3. Connect using GitHub token or SSH key

## Environment-Specific Setup

### Dev Environment
- Auto-sync enabled
- Prune resources on deletion
- Self-heal enabled

### Staging Environment
- Auto-sync enabled
- Prune resources on deletion
- Self-heal enabled

### Production Environment
- Manual sync only
- Requires approval for deployments
- No auto-pruning

## Monitoring and Troubleshooting

### Check application status
```bash
# List applications
argocd app list

# Get application details
argocd app get school-payments-dev

# View sync status
argocd app get school-payments-dev --hard-refresh
```

### Sync application manually
```bash
argocd app sync school-payments-prod
```

### View logs
```bash
# ArgoCD server logs
kubectl logs -n argocd deployment/argocd-server

# Application deployment logs
kubectl logs -n school-payments-dev deployment/school-payments-web
```

## Security Best Practices

1. **Change default password**: Update admin password after first login
2. **RBAC**: Configure role-based access control
3. **SSL/TLS**: Use HTTPS for ArgoCD UI
4. **GitOps**: Never modify resources directly in cluster
5. **Secrets Management**: Use external secret management (AWS Secrets Manager, etc.)

## Integration with CI/CD

The GitHub Actions pipeline automatically updates image tags in the repository. ArgoCD detects these changes and syncs the applications automatically (for dev/staging).

For production, create git tags and manually sync through ArgoCD UI or CLI.

## Backup and Recovery

```bash
# Backup ArgoCD configuration
argocd admin export > argocd-backup.yaml

# Restore (if needed)
kubectl apply -f argocd-backup.yaml
```

## Common Issues

### Application stuck in syncing
```bash
# Force refresh
argocd app get <app-name> --hard-refresh
argocd app sync <app-name>
```

### Permission denied
- Check repository access
- Verify ArgoCD service account permissions
- Ensure correct namespace in destination

### Image pull errors
- Verify ECR permissions
- Check image tag exists
- Confirm region settings