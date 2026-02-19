# StudioBridge Deployment Guide

## Docker Deployment (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- Git

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd StudioBridge

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Environment Variables

Edit `.env` file with your production values:

```bash
# Database (automatically configured by docker-compose)
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/StudioBridge

# JWT - CHANGE THIS IN PRODUCTION!
SECRET_KEY=your-super-secret-key-change-me

# TossPayments
TOSS_CLIENT_KEY=your-client-key
TOSS_SECRET_KEY=your-secret-key
TOSS_WEBHOOK_SECRET=your-webhook-secret

# Application
APP_ENV=production
DEBUG=false
```

### Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head
```

## Render Deployment

### Backend (FastAPI)

1. Create a new **Web Service** on Render
2. Connect your GitHub repository
3. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `SECRET_KEY`: Your JWT secret
   - Other environment variables

### Frontend (Streamlit)

1. Create a new **Web Service** on Render
2. Connect your GitHub repository
3. Configure:
   - **Root Directory**: `frontend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Add environment variables:
   - `API_BASE_URL`: Your backend URL (e.g., `https://StudioBridge-api.onrender.com`)

### Database

1. Create a **PostgreSQL** database on Render
2. Copy the internal connection URL
3. Run migrations after deploy:
   ```bash
   # Connect to backend service shell
   alembic upgrade head
   ```

## Railway Deployment

### Using Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy backend
cd backend
railway up

# Deploy frontend
cd ../frontend
railway up
```

### Configuration

1. Create PostgreSQL add-on in Railway
2. Set environment variables in Railway dashboard
3. Configure domains for both services

## PWA Configuration (Streamlit)

Streamlit doesn't natively support PWA, but you can add basic PWA features:

### Option 1: Service Worker (Manual)

Create `frontend/static/sw.js`:

```javascript
self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open('StudioBridge-v1').then(function(cache) {
      return cache.addAll([
        '/',
      ]);
    })
  );
});

self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});
```

### Option 2: Use stpyvista or similar packages

Add to `frontend/requirements.txt`:
```
streamlit-pwa
```

## Monitoring

### Health Checks

Backend health endpoint: `GET /health`

```bash
curl https://your-api-url.com/health
```

### Logging

- Docker: `docker-compose logs -f backend`
- Render: Check service logs in dashboard
- Railway: `railway logs`

## SSL/HTTPS

- Docker: Use Nginx reverse proxy with Let's Encrypt
- Render/Railway: Automatic HTTPS provided

## Scaling

### Docker
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
```

### Render/Railway
Configure auto-scaling in dashboard

## Backup

### Database Backup
```bash
# Docker
docker-compose exec db pg_dump -U postgres StudioBridge > backup.sql

# Restore
docker-compose exec -T db psql -U postgres StudioBridge < backup.sql
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=false in production
- [ ] Configure CORS appropriately
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Configure rate limiting
- [ ] Review TossPayments webhook security
