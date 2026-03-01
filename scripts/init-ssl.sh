#!/bin/bash
# Initialize Let's Encrypt SSL certificates for PilaMatch
# Usage: ./scripts/init-ssl.sh your-domain.com your-email@example.com

set -e

DOMAIN=${1:-pilamatch.com}
EMAIL=${2:-admin@pilamatch.com}
COMPOSE_CMD="docker-compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== PilaMatch SSL Certificate Initialization ==="
echo "Domain: $DOMAIN"
echo "Email:  $EMAIL"
echo ""

# Step 1: Create a temporary nginx config that only serves HTTP (for ACME challenge)
echo "[1/4] Creating temporary nginx config for ACME challenge..."
TMP_CONF=$(mktemp)
cat > "$TMP_CONF" <<'NGINX_CONF'
events { worker_connections 1024; }
http {
    server {
        listen 80;
        server_name _;
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        location / {
            return 200 'PilaMatch SSL init in progress';
            add_header Content-Type text/plain;
        }
    }
}
NGINX_CONF

# Step 2: Start nginx with temporary config
echo "[2/4] Starting nginx for ACME challenge..."
$COMPOSE_CMD run -d --name pilamatch-nginx-init \
    -v "$TMP_CONF:/etc/nginx/nginx.conf:ro" \
    -p 80:80 \
    nginx || {
    # If container approach fails, use the regular compose
    echo "  Falling back to compose-based nginx start..."
    cp "$TMP_CONF" ./nginx/nginx.conf.tmp
    $COMPOSE_CMD up -d nginx
}

# Step 3: Request certificate
echo "[3/4] Requesting SSL certificate from Let's Encrypt..."
$COMPOSE_CMD run --rm certbot \
    certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

# Step 4: Cleanup and restart
echo "[4/4] Cleaning up and restarting with production config..."
docker rm -f pilamatch-nginx-init 2>/dev/null || true
rm -f "$TMP_CONF" ./nginx/nginx.conf.tmp 2>/dev/null || true

$COMPOSE_CMD down
$COMPOSE_CMD up -d

echo ""
echo "=== SSL initialization complete ==="
echo "Verify: curl -I https://$DOMAIN"
echo ""
echo "Certificate auto-renewal is handled by the certbot container."
echo "Certificates will be renewed every 12 hours if expiring within 30 days."
