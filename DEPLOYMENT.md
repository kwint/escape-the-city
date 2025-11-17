# Deployment Guide

This guide explains how to deploy the Escape The City scavenger hunt app using Docker.

## Prerequisites

- Docker and Docker Compose installed on your server
- A reverse proxy (like Nginx or Traefik) handling SSL/HTTPS
- Domain name pointed to your server

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository (or copy files to your server)
cd /path/to/escape-the-city

# Create environment file
cp .env.example .env
```

### 2. Edit Environment Variables

Edit the `.env` file with your production settings:

```bash
nano .env
```

**Required settings:**

```env
# Generate a new secret key (use: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DJANGO_SECRET_KEY=your-very-long-random-secret-key-here

# Set to False for production
DJANGO_DEBUG=False

# Your domain names (comma-separated, no spaces)
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Your full URLs with https:// (comma-separated, no spaces)
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 3. Build and Start

```bash
# Build the Docker image
docker-compose build

# Start the container
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 4. Create Admin User

```bash
# Create a superuser account
docker-compose exec web uv run python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 5. Configure Reverse Proxy

Your reverse proxy should handle three things:
1. **SSL/HTTPS** - Automatic with Caddy, manual with Nginx
2. **Static files** (`/static/`) - CSS, JS, and Django admin assets
3. **Media files** (`/media/`) - User-uploaded PDFs
4. **Dynamic requests** - Everything else proxied to Django

**Why serve static/media files from the reverse proxy?**
- Better performance (no Django processing)
- Efficient caching
- Reduced load on the Django application

#### Nginx Example

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL configuration (handled by your setup)
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    client_max_body_size 20M;

    # Serve static files directly (CSS, JS, admin assets)
    location /static/ {
        alias /path/to/escape-the-city/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Serve media files directly (uploaded PDFs)
    location /media/ {
        alias /path/to/escape-the-city/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy everything else to Django app
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Traefik Example (docker-compose.yml labels)

Add these labels to your `web` service:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.scavenger-hunt.rule=Host(`yourdomain.com`)"
  - "traefik.http.routers.scavenger-hunt.entrypoints=websecure"
  - "traefik.http.routers.scavenger-hunt.tls.certresolver=letsencrypt"
  - "traefik.http.services.scavenger-hunt.loadbalancer.server.port=8000"
```

#### Caddy Example (Caddyfile)

Create or edit your `Caddyfile`:

```caddy
yourdomain.com, www.yourdomain.com {
    # Automatic HTTPS via Let's Encrypt

    # Set maximum upload size for PDF uploads
    request_body {
        max_size 20MB
    }

    # Root directory for static files
    root * /path/to/escape-the-city

    # Serve static files directly (CSS, JS, admin assets)
    handle /static/* {
        file_server {
            root /path/to/escape-the-city
        }
        encode gzip
    }

    # Serve media files directly (uploaded PDFs)
    handle /media/* {
        file_server {
            root /path/to/escape-the-city
        }
    }

    # Proxy everything else to Django app
    handle {
        reverse_proxy localhost:8000 {
            header_up Host {host}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # Enable compression for proxied content
    encode gzip

    # Security headers
    header {
        # Remove server information
        -Server
        # Enable HSTS
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    }
}
```

**Note:** Replace `/path/to/escape-the-city` with the actual path where your app is deployed (e.g., `/home/user/escape-the-city`).

**Reload Caddy after changes:**
```bash
# If running as a service
sudo systemctl reload caddy

# If running Caddy directly
caddy reload --config /path/to/Caddyfile
```

## Data Persistence

The following directories are mounted as volumes and will persist data:

- `./db/` - SQLite database
- `./media/` - Uploaded PDF files
- `./staticfiles/` - Static assets (CSS, JS, admin interface)

**Important:** Back up `db/` and `media/` directories regularly! The `staticfiles/` directory is regenerated from the app so doesn't need backup.

## Maintenance

### View Logs

```bash
docker-compose logs -f
```

### Restart Application

```bash
docker-compose restart
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Backup Database and Media

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup database
cp -r db/ backups/$(date +%Y%m%d)/

# Backup media files
cp -r media/ backups/$(date +%Y%m%d)/
```

### Restore from Backup

```bash
# Stop the application
docker-compose down

# Restore database
cp -r backups/20241122/db/ .

# Restore media files
cp -r backups/20241122/media/ .

# Start the application
docker-compose up -d
```

## Troubleshooting

### Check if container is running

```bash
docker-compose ps
```

### View application logs

```bash
docker-compose logs web
```

### Access Django shell

```bash
docker-compose exec web uv run python manage.py shell
```

### Run migrations manually

```bash
docker-compose exec web uv run python manage.py migrate
```

### Clear all data and start fresh

```bash
docker-compose down
rm -rf db/ media/
docker-compose up -d
docker-compose exec web uv run python manage.py createsuperuser
```

## Security Notes

1. **Never commit `.env` file to git** - it's already in `.gitignore`
2. **Use strong SECRET_KEY** - generate a new one for production
3. **Set DEBUG=False** in production
4. **Use HTTPS** - configure your reverse proxy properly
5. **Regular backups** - backup `db/` and `media/` directories
6. **Update dependencies** - keep Django and other packages updated

## Performance

The application uses:
- **Gunicorn** with 4 workers
- **SQLite** database (suitable for small to medium traffic)
- **120-second timeout** for long-running requests

For higher traffic, consider:
- Increasing Gunicorn workers (in `docker-entrypoint.sh`)
- Using PostgreSQL instead of SQLite
- Adding Redis for caching

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify environment variables in `.env`
3. Ensure reverse proxy is configured correctly
4. Check Django admin is accessible at `/admin/`
