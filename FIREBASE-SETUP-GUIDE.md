# Firebase Setup Guide for Coinbase Embedded Wallet Integration

## Overview
This guide documents the exact Firebase Console configuration required for email/SMS authentication with the Clockchain platform. Firebase handles the OTP delivery for passwordless authentication.

## Prerequisites
- Firebase project created
- Firebase credentials added to environment variables:
  - `FIREBASE_API_KEY`
  - `FIREBASE_AUTH_DOMAIN`
  - `FIREBASE_PROJECT_ID`
  - `FIREBASE_APP_ID`

## Step 1: Enable Authentication Methods

### 1.1 Enable Email/Password Provider
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Navigate to **Authentication** → **Sign-in method**
4. Click on **Email/Password**
5. Enable **Email/Password** (first toggle)
6. Enable **Email link (passwordless sign-in)** (second toggle)
7. Click **Save**

### 1.2 Enable Phone Authentication (Optional)
1. In **Sign-in method**, click on **Phone**
2. Enable **Phone** provider
3. Add test phone numbers for development:
   - Click "Phone numbers for testing"
   - Add: `+1 555 0123` with verification code: `123456`
   - Add: `+1 555 0124` with verification code: `654321`
4. Click **Save**

## Step 2: Configure Email Templates

### 2.1 Customize Email Templates
1. Go to **Authentication** → **Templates**
2. Click on **Email address verification**
3. Customize the template:
   ```
   Subject: Verify your Clockchain account
   
   Message:
   Hello,
   
   Click the link below to verify your email and access your Clockchain wallet:
   %LINK%
   
   This link will expire in 1 hour.
   
   If you didn't request this, please ignore this email.
   
   Thanks,
   The Clockchain Team
   ```
4. Click **Save**

### 2.2 Configure Passwordless Email Template
1. Click on **Email link sign-in**
2. Customize similarly to above
3. Click **Save**

## Step 3: Set Authorized Domains

### 3.1 Add Your Domain
1. Go to **Authentication** → **Settings**
2. Under **Authorized domains**, add:
   - Development: `localhost`
   - Production: `yourdomain.com`
3. Click **Add domain**

### 3.2 Configure Action URL
1. In **Authentication** → **Settings**
2. Under **Action URL**, set:
   - Development: `http://localhost:5000/api/embedded/verify-email`
   - Production: `https://yourdomain.com/api/embedded/verify-email`

## Step 4: Security Rules

### 4.1 Configure API Key Restrictions
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project
3. Navigate to **APIs & Services** → **Credentials**
4. Click on your Firebase Web API key
5. Under **Application restrictions**:
   - Select **HTTP referrers**
   - Add:
     - `https://*.repl.co/*`
     - `https://yourdomain.com/*`
6. Under **API restrictions**:
   - Select **Restrict key**
   - Enable only:
     - Identity Toolkit API
     - Firebase Authentication API
7. Click **Save**

## Step 5: Enable Firebase Admin SDK (For Server-Side)

### 5.1 Generate Service Account Key
1. Go to **Project settings** → **Service accounts**
2. Click **Generate new private key**
3. Save the JSON file securely
4. Add to Replit Secrets as `FIREBASE_SERVICE_ACCOUNT` (JSON string)

### 5.2 Initialize Admin SDK
The service account enables:
- Custom token generation
- User management from server
- Bypassing client-side requirements

## Step 6: Configure Rate Limits

### 6.1 Set Authentication Limits
1. Go to **Authentication** → **Settings**
2. Under **User limits**:
   - Same IP address limit: 100 requests/hour
   - Same email limit: 10 requests/hour
3. Click **Save**

## Step 7: Test Configuration

### 7.1 Test Mode
When `FLASK_ENV=testing`, the OTP verification accepts test code `123456` for any email. This allows testing without actual email delivery.

### 7.2 Test Email Verification
1. Visit: `http://localhost:5000/api/embedded/test`
2. Enter test email: `test@example.com`
3. In test mode, use OTP code: `123456`
4. In production, check email for verification code

### 7.3 Monitor Authentication
1. Go to **Authentication** → **Users**
2. Verify new users appear after testing
3. Check **Usage** tab for email sends

## Production Checklist

Before going live:
- [ ] Remove test phone numbers
- [ ] Set production authorized domains
- [ ] Configure custom email domain (optional)
- [ ] Enable App Check for additional security
- [ ] Set up monitoring alerts
- [ ] Configure backup authentication methods
- [ ] Test rate limiting

## Troubleshooting

### Common Issues

#### Emails Not Sending
- Check spam folder
- Verify domain is authorized
- Check Firebase project quota
- Ensure Email/Password is enabled

#### "Invalid API Key" Error
- Verify API key in Replit Secrets
- Check API key restrictions
- Ensure project ID matches

#### Phone Auth Not Working
- Phone auth requires client-side reCAPTCHA
- Use Firebase JavaScript SDK for phone auth
- Test numbers work without SMS sending

## Cost Considerations

Firebase Free Tier includes:
- 10,000 email verifications/month
- 10,000 SMS verifications/month
- Unlimited authentication requests

Paid tier (Blaze plan):
- $0.06 per SMS verification after free tier
- $0.01 per email after 10,000
- No charge for authentication checks

## Next Steps

1. Complete all configuration steps above
2. Test authentication flow end-to-end
3. Implement Coinbase Embedded Wallet creation after auth
4. Add transaction signing with wallet
5. Integrate USDC payments on BASE

## Support Resources

- [Firebase Auth Documentation](https://firebase.google.com/docs/auth)
- [Firebase Auth REST API](https://firebase.google.com/docs/reference/rest/auth)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Troubleshooting Guide](https://firebase.google.com/docs/auth/admin/errors)