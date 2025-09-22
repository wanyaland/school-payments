# AWS Domain Registration Guide for ngops.com

## Prerequisites
- AWS Account with billing enabled
- Access to Route53 service

## Step-by-Step Registration Process

### 1. Access Route53 Console
1. Log in to your AWS Management Console
2. Navigate to Route53 service (search for "Route53" in the services search bar)

### 2. Start Domain Registration
1. In the Route53 dashboard, click on "Domains" in the left sidebar
2. Click the "Register Domain" button

### 3. Search and Check Domain Availability
1. In the domain search box, enter: `ngops.com`
2. Click "Check" to verify availability
3. If available, click "Add to cart"

### 4. Enter Contact Information

Use the following details for all contact types (Registrant, Admin, Tech):

**Contact Type:** Person
**First Name:** Harold
**Last Name:** Wanyama
**Organization:** (leave blank)
**Email:** wanyaland2@gmail.com
**Phone:** +256788999982

**Address:**
- Street Address: Nansana
- City: Kampala
- State/Province: Central Region
- ZIP/Postal Code: 0000
- Country: Uganda

**Important:** Select the same contact information for:
- Registrant Contact
- Admin Contact
- Tech Contact

### 5. Configure Additional Settings
1. **Privacy Protection:** Enable (recommended for privacy)
2. **Auto-renew:** Enable (recommended)
3. **Transfer Lock:** Enable (recommended for security)

### 6. Review and Purchase
1. Review all information carefully
2. Check the total cost (domain registration typically costs ~$12/year)
3. Click "Complete Purchase"
4. Enter payment information if required

### Registration Timeline
- **Immediate:** Domain registration process starts (5-10 minutes)
- **Within 24 hours:** Domain appears in your Route53 "Registered domains" list
- **Within 48 hours:** Domain becomes active and resolvable (DNS propagation)
- **Up to 72 hours:** Full global DNS propagation (may take longer in some regions)
- **Within 15 days:** Email verification must be completed to avoid suspension

### 7. Domain Verification
1. After registration, AWS will send verification emails to the email address provided (lsmatovu@gmail.com)
2. Check your email from:
   - noreply@domainnameverification.net
   - noreply@registrar.amazon
3. Click the verification link within 15 days
4. **CRITICAL:** If verification is not received within 15 days, the domain will be suspended and no longer accessible on the internet
5. The domain will be fully active once verified

## Next Steps After Registration

Once the domain is registered and verified:

1. **Create Hosted Zone** (if not automatically created):
   - In Route53 console, go to "Hosted Zones"
   - Click "Create Hosted Zone"
   - Enter `ngops.com` as the domain name
   - Select "Public hosted zone"

2. **Configure DNS Records** for your application:
   - Add A records pointing to your load balancer
   - Add CNAME records as needed
   - Configure subdomains (staging.ngops.com, argocd.ngops.com, etc.)

## Cost Information
- Domain registration: ~$12/year
- Hosted Zone: $0.50/month
- DNS queries: Free tier available

## Troubleshooting
- If domain is not available, try variations or check for typos
- Ensure email is accessible for verification
- Contact AWS support if verification emails are not received

## Security Notes
- Keep domain contact information updated
- Enable auto-renewal to prevent expiration
- Consider enabling domain transfer lock