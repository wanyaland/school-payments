# Deployment Testing Guide

This guide covers testing the Kubernetes deployment across different environments.

## Local Testing

### 1. Test Kustomize builds

```bash
# Test dev overlay
kubectl kustomize k8s/overlays/dev/

# Test staging overlay
kubectl kustomize k8s/overlays/staging/

# Test prod overlay
kubectl kustomize k8s/overlays/prod/
```

### 2. Dry-run deployment

```bash
# Dry run dev deployment
kubectl kustomize k8s/overlays/dev/ | kubectl apply --dry-run=server -f -

# Check for validation errors
kubectl kustomize k8s/overlays/dev/ | kubectl apply --dry-run=client -f -
```

## Environment Testing

### Dev Environment

```bash
# Deploy to dev
kubectl apply -k k8s/overlays/dev/

# Check deployment status
kubectl get pods -n school-payments-dev
kubectl get services -n school-payments-dev

# Check logs
kubectl logs -n school-payments-dev deployment/school-payments-web
kubectl logs -n school-payments-dev deployment/school-payments-celery-worker

# Test application
kubectl port-forward -n school-payments-dev svc/school-payments-web 8080:80
curl http://localhost:8080/health/
```

### Staging Environment

```bash
# Deploy to staging
kubectl apply -k k8s/overlays/staging/

# Verify configurations
kubectl get configmap -n school-payments-staging school-payments-config -o yaml
kubectl get secret -n school-payments-staging school-payments-secret -o yaml

# Test scaling
kubectl scale deployment school-payments-web -n school-payments-staging --replicas=3
kubectl get pods -n school-payments-staging
```

### Production Environment

```bash
# Deploy to prod
kubectl apply -k k8s/overlays/prod/

# Verify high availability
kubectl get pods -n school-payments-prod -o wide

# Test rolling updates
kubectl set image deployment/school-payments-web web=school-payments:v1.0.1 -n school-payments-prod
kubectl rollout status deployment/school-payments-web -n school-payments-prod
```

## Application Testing

### Health Checks

```bash
# Test health endpoint
curl -H "Host: school-payments-dev.yourdomain.com" http://load-balancer/health/

# Test webhook endpoint (mock data)
curl -X POST http://load-balancer/api/webhooks/SUREPAY \
  -H "Content-Type: application/json" \
  -H "X-School-Code: test" \
  -H "X-Signature: mock-signature" \
  -d '{"event_id": "test", "external_txn_id": "test", "amount": "100.00", "currency": "UGX", "status": "SUCCEEDED", "provider_student_id": "test"}'
```

### Database Connectivity

```bash
# Test database connection
kubectl exec -n school-payments-dev deployment/school-payments-web -- python manage.py dbshell --command="SELECT 1;"

# Run migrations
kubectl exec -n school-payments-dev deployment/school-payments-web -- python manage.py migrate

# Create superuser
kubectl exec -n school-payments-dev deployment/school-payments-web -- python manage.py createsuperuser --noinput
```

### Redis Connectivity

```bash
# Test Redis connection
kubectl exec -n school-payments-dev deployment/school-payments-web -- python manage.py shell -c "from django.core.cache import cache; print(cache.set('test', 'value')); print(cache.get('test'))"
```

## Load Testing

### Basic Load Test

```bash
# Install hey for load testing
# brew install hey

# Test with 10 concurrent users for 30 seconds
hey -n 1000 -c 10 http://load-balancer/health/

# Test webhook endpoint
hey -n 100 -c 5 -m POST \
  -H "Content-Type: application/json" \
  -H "X-School-Code: test" \
  -H "X-Signature: mock" \
  -d '{"event_id": "load-test", "external_txn_id": "load-test", "amount": "100.00", "currency": "UGX", "status": "SUCCEEDED", "provider_student_id": "load-test"}' \
  http://load-balancer/api/webhooks/SUREPAY
```

### Resource Monitoring

```bash
# Monitor resource usage
kubectl top pods -n school-payments-dev

# Check resource limits
kubectl describe pod -n school-payments-dev -l app=school-payments-web

# Monitor events
kubectl get events -n school-payments-dev --sort-by=.metadata.creationTimestamp
```

## ArgoCD Testing

### Sync Testing

```bash
# Check ArgoCD application status
argocd app get school-payments-dev

# Force sync
argocd app sync school-payments-dev

# Check sync history
argocd app history school-payments-dev
```

### Rollback Testing

```bash
# Rollback to previous version
argocd app rollback school-payments-dev HEAD-1

# Verify rollback
kubectl get pods -n school-payments-dev
```

## CI/CD Testing

### Test GitHub Actions

1. Push changes to dev branch
2. Monitor Actions tab for build status
3. Check ECR for new image
4. Verify ArgoCD auto-sync

### Test Release Process

1. Create release branch from dev
2. Push to trigger staging deployment
3. Verify staging environment
4. Create git tag for production
5. Manually sync prod application

## Troubleshooting

### Common Issues

1. **Image Pull Errors**
   ```bash
   # Check image exists
   aws ecr describe-images --repository-name school-payments --image-ids imageTag=dev-latest

   # Check pod events
   kubectl describe pod <pod-name> -n <namespace>
   ```

2. **Database Connection Issues**
   ```bash
   # Test connection from pod
   kubectl exec -it deployment/school-payments-web -n school-payments-dev -- python manage.py dbshell
   ```

3. **Permission Issues**
   ```bash
   # Check service account
   kubectl auth can-i --as=system:serviceaccount:school-payments-dev:default get pods
   ```

4. **Resource Constraints**
   ```bash
   # Check resource usage
   kubectl top pods -n school-payments-dev
   kubectl describe node
   ```

### Logs and Debugging

```bash
# Application logs
kubectl logs -f deployment/school-payments-web -n school-payments-dev

# Celery logs
kubectl logs -f deployment/school-payments-celery-worker -n school-payments-dev

# System logs
kubectl logs -f -n kube-system -l component=kube-apiserver

# Debug pod
kubectl run debug --image=busybox --rm -it --restart=Never -- sh
```

## Performance Benchmarks

- **Response Time**: < 500ms for health checks
- **Throughput**: > 100 requests/second
- **Error Rate**: < 1%
- **Resource Usage**: < 80% CPU/Memory limits

## Security Testing

```bash
# Test HTTPS redirect
curl -I http://load-balancer/

# Test security headers
curl -I https://load-balancer/

# Test authentication
curl -H "Authorization: Bearer invalid" https://load-balancer/api/
```

## Cleanup

```bash
# Remove test deployments
kubectl delete namespace school-payments-dev

# Clean up test resources
kubectl delete pvc -n school-payments-dev --all