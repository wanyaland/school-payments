# Kustomization Guide

Kustomize is a Kubernetes configuration management tool that allows you to customize raw YAML files for different environments without duplication.

## Project Structure

```
k8s/
├── base/           # Common manifests for all environments
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── web-deployment.yaml
│   ├── web-service.yaml
│   ├── celery-worker-deployment.yaml
│   ├── celery-beat-deployment.yaml
│   └── kustomization.yaml
└── overlays/       # Environment-specific customizations
    ├── dev/
    │   ├── kustomization.yaml
    │   └── replicas.yaml
    ├── staging/
    │   ├── kustomization.yaml
    │   └── config-patch.yaml
    └── prod/
        ├── kustomization.yaml
        ├── config-patch.yaml
        └── replicas-prod.yaml
```

## Base Configuration

The `base/` directory contains shared resources that are common across all environments:

- **configmap.yaml**: Environment variables like Django settings, Celery config
- **secret.yaml**: Sensitive data placeholders (database URLs, API keys)
- **web-deployment.yaml**: Django application deployment
- **web-service.yaml**: Service to expose the web app
- **celery-worker-deployment.yaml**: Background task workers
- **celery-beat-deployment.yaml**: Periodic task scheduler
- **kustomization.yaml**: Lists all resources and defines image transformations

## Overlays

Each overlay in `overlays/` customizes the base configuration for specific environments:

### Dev Overlay
- Reduces replicas to 1 for cost efficiency
- Uses `dev-latest` image tag
- Inherits all other base settings

### Staging Overlay
- Uses production QuickBooks settings (`QBO_IS_SANDBOX: false`)
- Uses `staging-latest` image tag
- 2 replicas for web and worker

### Prod Overlay
- 3 replicas for high availability
- Disables debug mode
- Uses semantic version tags (e.g., `v1.0.0`)
- Production QuickBooks settings

## Usage

### Build manifests for an environment:
```bash
kubectl kustomize k8s/overlays/dev/
```

### Apply directly to cluster:
```bash
kubectl apply -k k8s/overlays/dev/
```

### Dry run to see changes:
```bash
kubectl kustomize k8s/overlays/dev/ | kubectl apply --dry-run=client -f -
```

## Key Features Used

1. **Strategic Merge Patches**: Modify specific fields in base resources
2. **JSON Patches**: Advanced modifications using JSON patch syntax
3. **Image Transformations**: Update container images per environment
4. **Namespace Management**: Automatic namespace assignment
5. **Resource Customization**: Replica counts, environment variables

## Benefits

- **DRY Principle**: No YAML duplication across environments
- **Version Control**: Changes tracked in git
- **Environment Parity**: Consistent base configuration
- **Easy Maintenance**: Single source of truth for common configs
- **CI/CD Integration**: Automated manifest generation