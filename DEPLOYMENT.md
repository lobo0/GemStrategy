# 🚀 GemStrategy Deployment Guide

This guide covers deploying the GemStrategy application to both **Vercel** and **Google Cloud Platform**.

## 📋 Prerequisites

### For Vercel Deployment:
- [Node.js](https://nodejs.org/) (v16 or higher)
- [Vercel CLI](https://vercel.com/cli) (will be installed automatically)
- Vercel account

### For Google Cloud Platform:
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
- [Docker](https://www.docker.com/) (for Cloud Run deployment)
- Google Cloud account with billing enabled
- Active Google Cloud project

## 🌐 Vercel Deployment

Vercel is perfect for serverless deployment with automatic scaling and global CDN.

### Quick Deploy:
```bash
# Make script executable (Linux/Mac)
chmod +x deploy-vercel.sh
./deploy-vercel.sh

# Or run manually
npm install -g vercel
vercel login
vercel --prod
```

### Manual Steps:
1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   vercel --prod
   ```

4. **Environment Variables:**
   - Set `ENVIRONMENT=production`
   - Set `API_DEBUG=false`

### Vercel Features:
- ✅ Automatic HTTPS
- ✅ Global CDN
- ✅ Automatic scaling
- ✅ Zero-downtime deployments
- ✅ Preview deployments for PRs

## ☁️ Google Cloud Platform Deployment

### Option 1: Google App Engine (Recommended for beginners)

App Engine provides managed infrastructure with automatic scaling.

#### Quick Deploy:
```bash
# Make script executable (Linux/Mac)
chmod +x deploy-gcp.sh
./deploy-gcp.sh

# Windows PowerShell
.\deploy-gcp.ps1
```

#### Manual Steps:
1. **Set your project:**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Deploy:**
   ```bash
   gcloud app deploy app.yaml
   ```

3. **View your app:**
   ```bash
   gcloud app browse
   ```

### Option 2: Google Cloud Run (Recommended for advanced users)

Cloud Run provides containerized deployment with pay-per-use pricing.

#### Quick Deploy:
```bash
# Make script executable (Linux/Mac)
chmod +x deploy-gcp.sh
./deploy-gcp.sh

# Windows PowerShell
.\deploy-gcp.ps1
```

#### Manual Steps:
1. **Build and push Docker image:**
   ```bash
   docker build -t gcr.io/YOUR_PROJECT_ID/gemstrategy .
   docker push gcr.io/YOUR_PROJECT_ID/gemstrategy
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy gemstrategy \
     --image gcr.io/YOUR_PROJECT_ID/gemstrategy \
     --platform managed \
     --region europe-west1 \
     --allow-unauthenticated \
     --port 8080
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```bash
# Copy example environment file
cp env.example .env

# Edit with your production values
nano .env
```

### Required Environment Variables:
```env
ENVIRONMENT=production
API_DEBUG=false
API_TITLE=GemStrategy API
API_DESCRIPTION=Investment strategy analysis API
API_VERSION=1.0.0
DATA_CACHE_TTL_HOURS=4
DATA_MAX_RETRIES=3
```

## 📊 Monitoring and Health Checks

### Health Check Endpoint:
- **URL:** `/api/health`
- **Method:** GET
- **Response:** Application status and version info

### Logs:
- **Vercel:** Available in Vercel dashboard
- **GCP:** Available in Cloud Console > Logging

## 🚨 Troubleshooting

### Common Issues:

#### Vercel:
- **Build failures:** Check `requirements-vercel.txt` dependencies
- **Import errors:** Ensure all imports use absolute paths
- **Environment variables:** Verify they're set in Vercel dashboard

#### Google Cloud:
- **Authentication:** Run `gcloud auth login`
- **Project not set:** Run `gcloud config set project PROJECT_ID`
- **Docker build failures:** Check Dockerfile and requirements.txt
- **Permission errors:** Ensure proper IAM roles

### Debug Commands:
```bash
# Test locally
python -m uvicorn main:app --reload

# Check dependencies
pip list

# Verify configuration
python -c "from config_package.settings import get_settings; print(get_settings())"
```

## 🔄 Continuous Deployment

### GitHub Actions (Recommended):

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-vercel:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install -g vercel
      - run: vercel --prod --token ${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}

  deploy-gcp:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/setup-gcloud@v0
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}
      - run: gcloud app deploy app.yaml --quiet
```

## 💰 Cost Optimization

### Vercel:
- Free tier: 100GB bandwidth/month
- Pro: $20/month for unlimited bandwidth

### Google Cloud:
- App Engine: Pay per use, very cost-effective
- Cloud Run: Pay only when handling requests
- Free tier: $300 credit for new users

## 🔒 Security Considerations

### Production Checklist:
- [ ] HTTPS enabled (automatic on both platforms)
- [ ] Environment variables secured
- [ ] API rate limiting configured
- [ ] CORS policies set
- [ ] Input validation enabled
- [ ] Error messages don't expose sensitive data

### Security Headers:
Both platforms automatically add security headers, but you can customize them in your FastAPI app.

## 📞 Support

### Vercel:
- [Documentation](https://vercel.com/docs)
- [Community](https://github.com/vercel/vercel/discussions)

### Google Cloud:
- [Documentation](https://cloud.google.com/docs)
- [Support](https://cloud.google.com/support)

---

**Happy Deploying! 🚀**

For issues specific to GemStrategy, check the main repository or create an issue.
