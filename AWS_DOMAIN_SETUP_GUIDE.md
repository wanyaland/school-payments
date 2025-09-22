# AWS Domain Setup Guide for tngsops.com

This guide covers the complete process of setting up a domain in AWS using Route53.

## Prerequisites
- AWS Account with billing enabled
- AWS CLI configured or access to AWS Console

## Step 1: Register Domain (if not already owned)

### Option A: Register through AWS Route53
```bash
# Check domain availability
aws route53domains check-domain-availability --domain-name tngsops.com

# Register domain (requires payment)
aws route53domains register-domain \
    --domain-name tngsops.com \
    --duration-in-years 1 \
    --admin-contact FirstName=YourName,LastName=YourLastName,ContactType=PERSON,AddressLine1="Your Address",City="Your City",CountryCode=UG,ZipCode="Your Zip",PhoneNumber="+256XXXXXXXXX",Email="your-email@example.com" \
    --registrant-contact FirstName=YourName,LastName=YourLastName,ContactType=PERSON,AddressLine1="Your Address",City="Your City",CountryCode=UG,ZipCode="Your Zip",PhoneNumber="+256XXXXXXXXX",Email="your-email@example.com" \
    --tech-contact FirstName=YourName,LastName=YourLastName,ContactType=PERSON,AddressLine1="Your Address",City="Your City",CountryCode=UG,ZipCode="Your Zip",PhoneNumber="+256XXXXXXXXX",Email="your-email@example.com"
```

### Option B: Use External Registrar (Recommended if cheaper)
If you register with another provider (Namecheap, GoDaddy, etc.), you'll need to:
1. Register `tngsops.com` with your preferred registrar
2. Update nameservers to AWS Route53 (shown in Step 2)

## Step 2: Create Hosted Zone in Route53

### Using AWS CLI:
```bash
# Create hosted zone
aws route53 create-hosted-zone \
    --name tngsops.com \
    --caller-reference $(date +%s) \
    --hosted-zone-config Comment="School Payments Production Domain"

# Get nameservers
aws route53 get-hosted-zone --id /hostedzone/YOUR_ZONE_ID
```

### Using AWS Console:
1. **Go to Route53** → Hosted zones
2. **Click "Create hosted zone"**
3. **Domain name**: `tngsops.com`
4. **Type**: Public hosted zone
5. **Comment**: "School Payments Production Domain"
6. **Click "Create hosted zone"**

## Step 3: Update Nameservers (if using external registrar)

After creating the hosted zone, you'll get 4 nameservers like:
```
ns-1234.awsdns-56.org
ns-789.awsdns-01.net
ns-012.awsdns-34.com
ns-567.awsdns-89.co.uk
```

**Update these nameservers with your domain registrar.**

## Step 4: Create DNS Records

### Using AWS CLI:
```bash
# Create a change batch file
cat > dns-records.json << EOF
{
    "Changes": [
        {
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "staging.tngsops.com",
                "Type": "CNAME",
                "TTL": 300,
                "ResourceRecords": [
                    {
                        "Value": "a50a1f3064c22428b9ac1fb2495ea081-496820501.eu-west-1.elb.amazonaws.com"
                    }
                ]
            }
        },
        {
            "Action": "CREATE", 
            "ResourceRecordSet": {
                "Name": "argocd.staging.tngsops.com",
                "Type": "CNAME",
                "TTL": 300,
                "ResourceRecords": [
                    {
                        "Value": "a50a1f3064c22428b9ac1fb2495ea081-496820501.eu-west-1.elb.amazonaws.com"
                    }
                ]
            }
        }
    ]
}
EOF

# Apply the changes
aws route53 change-resource-record-sets \
    --hosted-zone-id YOUR_ZONE_ID \
    --change-batch file://dns-records.json
```

### Using AWS Console:
1. **Go to Route53** → Hosted zones → `tngsops.com`
2. **Click "Create record"**

#### For Staging Application:
- **Record name**: `staging`
- **Record type**: CNAME
- **Value**: `a50a1f3064c22428b9ac1fb2495ea081-496820501.eu-west-1.elb.amazonaws.com`
- **TTL**: 300
- **Click "Create records"**

#### For ArgoCD:
- **Record name**: `argocd.staging`
- **Record type**: CNAME  
- **Value**: `a50a1f3064c22428b9ac1fb2495ea081-496820501.eu-west-1.elb.amazonaws.com`
- **TTL**: 300
- **Click "Create records"**

## Step 5: Verify DNS Propagation

### Check DNS propagation:
```bash
# Check domain NS records
dig NS tngsops.com

# Check subdomain resolution
dig staging.tngsops.com
dig argocd.staging.tngsops.com

# Online tools
# Visit: https://dnschecker.org/#CNAME/staging.tngsops.com
```

### Expected Results:
```bash
$ dig staging.tngsops.com
;; ANSWER SECTION:
staging.tngsops.com.    300    IN    CNAME    a50a1f3064c22428b9ac1fb2495ea081-496820501.eu-west-1.elb.amazonaws.com.
```

## Step 6: Test Access

### Once DNS propagates (5-60 minutes):
- **Staging App**: `https://staging.tngsops.com`
- **ArgoCD UI**: `https://argocd.staging.tngsops.com`

## Troubleshooting

### Domain not resolving:
1. **Check nameservers** are correctly set at registrar
2. **Wait for propagation** (up to 48 hours for NS changes)
3. **Verify hosted zone** has correct records

### Services not accessible:
1. **Check Kubernetes ingress**: `kubectl get ingress -A`
2. **Verify load balancer**: `kubectl get svc -n ingress-nginx`
3. **Test direct access**: Use load balancer URL with Host header

### Domain costs:
- **.com domains**: ~$12-15/year through Route53
- **Cheaper alternatives**: Use external registrar + Route53 for DNS only
- **Free alternative**: Use nip.io (e.g., `staging.1.2.3.4.nip.io`)

## Alternative: Using nip.io for Testing

If you want to test immediately without purchasing a domain:

```bash
# Update ingresses to use nip.io
kubectl patch ingress school-payments-web -n school-payments-staging --type='json' \
  -p='[{"op": "replace", "path": "/spec/rules/0/host", "value": "staging.a50a1f3064c22428b9ac1fb2495ea081-496820501.nip.io"}]'

kubectl patch ingress argocd-server -n argocd --type='json' \
  -p='[{"op": "replace", "path": "/spec/rules/0/host", "value": "argocd.a50a1f3064c22428b9ac1fb2495ea081-496820501.nip.io"}]'
```

Then access:
- **Staging**: `http://staging.a50a1f3064c22428b9ac1fb2495ea081-496820501.nip.io`
- **ArgoCD**: `http://argocd.a50a1f3064c22428b9ac1fb2495ea081-496820501.nip.io`

## Cost Estimation

### Route53 Only (if domain registered elsewhere):
- **Hosted zone**: $0.50/month
- **DNS queries**: $0.40 per million queries

### Route53 + Domain Registration:
- **Domain registration**: ~$12-15/year
- **Hosted zone**: $0.50/month
- **DNS queries**: $0.40 per million queries

Total: ~$18-21/year for complete setup