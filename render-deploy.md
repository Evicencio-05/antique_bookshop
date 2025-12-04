# Render Deployment Guide

## Overview
This guide will help you deploy your Antique Bookshop Django application to Render's free tier.

## Prerequisites
- A GitHub account with your project repository
- A Render account at https://render.com/

## Step-by-Step Instructions

### 1. Commit Your Changes
```bash
git add -A
git commit -m "Add Render deployment configuration"
git push origin Create-web-page
```

### 2. Set Up Render Account
1. Go to https://render.com/
2. Click "Sign Up" and create an account
3. Connect your GitHub account to Render

### 3. Create a New Web Service
1. In your Render dashboard, click "New +" then "Web Service"
2. Select your GitHub repository (antique_bookshop)
3. Choose the "Create-web-page" branch
4. Configure your service:
   - Name: `antique-bookshop`
   - Environment: `Python 3`
   - Build Context: Root Directory
   - Build Command: `uv sync && python manage.py collectstatic --noinput`
   - Start Command: `uv run gunicorn bookshop.wsgi:application --bind 0.0.0.0:$PORT`
   - Instance Type: `Free`

### 4. Create a Database
1. In your Render dashboard, click "New +" then "PostgreSQL"
2. Configure your database:
   - Name: `antique-bookshop-db`
   - Database Name: `bookshop_db`
   - User Name: `postgres`
   - Instance Type: `Free`
3. After creation, click on your database and copy the connection URL (internal)

### 5. Set Environment Variables
In your web service settings, add these environment variables:

1. **DJANGO_SETTINGS_MODULE**: `bookshop.settings`
2. **SECRET_KEY**: Generate a secure key at https://djecrety.com/
3. **DATABASE_URL**: Paste the PostgreSQL connection URL from step 4
4. **DEBUG**: `false`
5. **ALLOWED_HOSTS**: `localhost,127.0.0.1,.onrender.com`
6. **DJANGO_SUPERUSER_USERNAME**: Your desired admin username (e.g., `admin`)
7. **DJANGO_SUPERUSER_EMAIL**: Your admin email (e.g., `admin@example.com`)
8. **DJANGO_SUPERUSER_PASSWORD**: A strong password for the admin account

**Important**: The superuser will be created automatically during the build process using the credentials you provide.

### 6. Deploy Your Application
Once all environment variables are set, Render will automatically:
- Run database migrations
- Collect static files
- Create your superuser account
- Start the application

You can monitor the build progress in the Render dashboard logs.

### 7. Access Your Application
Your deployed application will be available at:
`https://antique-bookshop.onrender.com`

## Troubleshooting

### Build Fails
- Ensure your branch is up to date
- Check the error logs in your Render dashboard

### Static Files Not Loading
- Verify your build command includes `collectstatic`
- Ensure `whitenoise` is properly configured in settings

### Database Connection Issues
- Double-check your `DATABASE_URL` environment variable
- Make sure your database service is running

### Server Error (500)
- Check the logs in the Render dashboard
- Try accessing the `/admin/` page to test basic functionality

## Important Notes

- The free tier has a limited amount of usage hours (750 hours per month)
- Free tier PostgreSQL databases sleep after inactivity and may spin up slowly
- Free web services also sleep after inactivity (spin-up can take ~30 seconds)
- Your free services will automatically be deleted after 30 days of inactivity
