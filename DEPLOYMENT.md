# 🚀 Deployment Guide - GCS Cost Simulator

This guide helps you deploy the GCS Cost Simulator to Google Cloud Run.

## 📋 Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Docker Desktop** installed and running
3. **Google Cloud CLI** installed ([Install guide](https://cloud.google.com/sdk/docs/install))
4. **Git** for version control

## 🔧 Quick Setup

### Method 1: Manual Deployment (Recommended for first-time)

1. **Clone and navigate to the repository:**

   ```bash
   git clone https://github.com/YOUR_USERNAME/gcs-cost-simulator.git
   cd gcs-cost-simulator
   ```

2. **Set your Google Cloud Project ID:**

   ```bash
   # Edit deploy.sh and replace PROJECT_ID="" with your actual project ID
   nano deploy.sh
   # Change line: PROJECT_ID="your-project-id-here"
   ```

3. **Run the deployment script:**

   ```bash
   ./deploy.sh
   ```

4. **Done!** Your app will be live at the URL shown in the terminal.

### Method 2: GitHub Actions (Automatic deployment)

1. **Fork this repository** to your GitHub account

2. **Set up GitHub Secrets:**

   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Add these secrets:
     - `GCP_PROJECT_ID`: Your Google Cloud project ID
     - `GCP_SA_KEY`: Service account key JSON (see setup below)

3. **Create a Google Cloud Service Account:**

   ```bash
   # Replace YOUR_PROJECT_ID with your actual project ID
   gcloud iam service-accounts create github-actions \
       --display-name="GitHub Actions" \
       --project=YOUR_PROJECT_ID

   # Grant permissions
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/run.admin"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/storage.admin"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/cloudbuild.builds.builder"

   # Create and download key
   gcloud iam service-accounts keys create key.json \
       --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

4. **Add the service account key to GitHub Secrets:**

   - Copy the contents of `key.json`
   - Paste it as the value for `GCP_SA_KEY` secret in GitHub

5. **Push to main branch** - deployment happens automatically!

## 🌍 Deployment Configuration

### Region Selection

- **Default**: `us-central1` (Iowa) - Cheapest + Low CO2
- **Alternatives**: `us-east1`, `us-west1`, `europe-west1`

### Resource Allocation

- **CPU**: 1 vCPU (adjustable)
- **Memory**: 1 GiB (adjustable)
- **Concurrency**: 80 requests per instance
- **Timeout**: 5 minutes
- **Auto-scaling**: 0-10 instances

## 💰 Cost Estimation

### Free Tier (Monthly)

- ✅ **240K vCPU-seconds** FREE
- ✅ **450K GiB-seconds** FREE
- ✅ **2M requests** FREE

### Your App's Usage

For a typical educational tool like this:

- **Light usage** (100 users/month): **$0/month** (within free tier)
- **Medium usage** (1000 users/month): **~$2-5/month**
- **Heavy usage** (10K users/month): **~$15-25/month**

### Cost Monitoring

- Monitor at: https://console.cloud.google.com/billing
- Set up budget alerts for cost control
- App automatically scales to zero when unused

## 🔧 Configuration Options

### Environment Variables

Add these to Cloud Run if needed:

```bash
# In deploy.sh, add to gcloud run deploy:
--set-env-vars="STREAMLIT_SERVER_HEADLESS=true"
--set-env-vars="STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"
```

### Custom Domain

```bash
# Map custom domain (after deployment)
gcloud run domain-mappings create \
    --service gcs-cost-simulator \
    --domain your-domain.com \
    --region us-central1
```

## 🔍 Monitoring & Debugging

### View Logs

```bash
# Real-time logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=gcs-cost-simulator"

# Historical logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gcs-cost-simulator" --limit 50
```

### Service Management

```bash
# Check service status
gcloud run services describe gcs-cost-simulator --region=us-central1

# Update service
gcloud run services update gcs-cost-simulator --region=us-central1 --memory=2Gi

# Delete service
gcloud run services delete gcs-cost-simulator --region=us-central1
```

## 🚨 Troubleshooting

### Common Issues

1. **"Permission denied" errors**

   - Ensure your service account has Cloud Run Admin role
   - Check if APIs are enabled: `gcloud services list --enabled`

2. **Container build fails**

   - Check Dockerfile syntax
   - Ensure all files are in the correct locations
   - Verify requirements.txt has all dependencies

3. **App crashes on startup**

   - Check logs: `gcloud logging tail`
   - Verify port configuration (must use PORT=8080)
   - Check memory allocation (increase if needed)

4. **Slow cold starts**
   - Consider setting minimum instances: `--min-instances=1`
   - This will increase costs but improve response time

### Performance Optimization

1. **Reduce cold starts:**

   ```bash
   # Set minimum instances (costs more but faster)
   gcloud run services update gcs-cost-simulator \
       --min-instances=1 \
       --region=us-central1
   ```

2. **Increase resources for heavy usage:**
   ```bash
   # More CPU and memory
   gcloud run services update gcs-cost-simulator \
       --cpu=2 \
       --memory=2Gi \
       --region=us-central1
   ```

## 🔒 Security Considerations

1. **Authentication**: Currently allows unauthenticated access (public)
2. **HTTPS**: Automatically provided by Cloud Run
3. **Rate limiting**: Consider adding rate limiting for production use
4. **Secrets**: Never commit API keys or credentials to Git

## 📈 Scaling Considerations

- **Automatic scaling**: 0-10 instances by default
- **Concurrency**: 80 requests per instance
- **For high traffic**: Increase max-instances and consider Load Balancer

## 🎯 Next Steps After Deployment

1. **Test your deployment** thoroughly
2. **Set up monitoring** and alerting
3. **Configure custom domain** if needed
4. **Set up budget alerts** for cost control
5. **Consider adding authentication** for internal use

---

## 📞 Support

For deployment issues:

1. Check the troubleshooting section above
2. Review Cloud Run logs
3. Consult [Google Cloud Run documentation](https://cloud.google.com/run/docs)

**Happy deploying! 🚀**
