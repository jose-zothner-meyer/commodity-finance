#!/bin/bash

# Portfolio Analytics Platform - Production Deployment Script
# This script automates the deployment process for production environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="portfolio-analytics"
PROJECT_DIR="/opt/portfolio-analytics"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="portfolio-analytics"
NGINX_SITE="portfolio-analytics"
LOG_DIR="/var/log/portfolio-analytics"

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    apt-get update
    apt-get install -y \
        python3.9 \
        python3.9-venv \
        python3-pip \
        postgresql \
        postgresql-contrib \
        redis-server \
        nginx \
        git \
        curl \
        htop \
        fail2ban \
        ufw \
        certbot \
        python3-certbot-nginx \
        libpq-dev \
        python3-dev \
        gcc
    
    print_success "System dependencies installed"
}

setup_firewall() {
    print_status "Configuring firewall..."
    
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable
    
    print_success "Firewall configured"
}

setup_postgresql() {
    print_status "Setting up PostgreSQL..."
    
    systemctl start postgresql
    systemctl enable postgresql
    
    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE portfolio_analytics;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE USER portfolio_user WITH PASSWORD 'secure_password_123';" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE portfolio_analytics TO portfolio_user;" 2>/dev/null || true
    
    print_success "PostgreSQL configured"
}

setup_redis() {
    print_status "Setting up Redis..."
    
    systemctl start redis-server
    systemctl enable redis-server
    
    # Configure Redis
    sed -i 's/# maxmemory <bytes>/maxmemory 512mb/' /etc/redis/redis.conf
    sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
    
    systemctl restart redis-server
    
    print_success "Redis configured"
}

setup_application() {
    print_status "Setting up application..."
    
    # Create project directory
    mkdir -p $PROJECT_DIR
    mkdir -p $LOG_DIR
    
    # Clone or copy application code
    if [ ! -d "$PROJECT_DIR/commodity-tracker-1" ]; then
        print_status "Cloning application repository..."
        # Replace with your actual repository URL
        git clone https://github.com/your-username/commodity-tracker-1.git $PROJECT_DIR/commodity-tracker-1
    fi
    
    cd $PROJECT_DIR/commodity-tracker-1
    
    # Create virtual environment
    python3.9 -m venv $VENV_DIR
    source $VENV_DIR/bin/activate
    
    # Install Python dependencies
    pip install --upgrade pip
    pip install -r requirements-production.txt
    
    print_success "Application dependencies installed"
}

setup_environment() {
    print_status "Setting up environment variables..."
    
    # Create environment file
    cat > /etc/environment << EOF
# Database configuration
DB_NAME=portfolio_analytics
DB_USER=portfolio_user
DB_PASSWORD=secure_password_123
DB_HOST=localhost
DB_PORT=5432

# Redis configuration
REDIS_URL=redis://127.0.0.1:6379/1

# Django configuration
DJANGO_SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DJANGO_SETTINGS_MODULE=energy_finance.production_settings

# Add your API keys here
FIN_MODELING_PREP_KEY=your_fmp_key_here
API_NINJAS_KEY=your_api_ninjas_key_here
COMMODITYPRICEAPI_KEY=your_commodity_api_key_here
EOF
    
    source /etc/environment
    
    print_success "Environment variables configured"
}

setup_django() {
    print_status "Setting up Django application..."
    
    cd $PROJECT_DIR/commodity-tracker-1
    source $VENV_DIR/bin/activate
    source /etc/environment
    
    # Run migrations
    python manage.py migrate
    
    # Collect static files
    python manage.py collectstatic --noinput
    
    # Create superuser (optional)
    # python manage.py createsuperuser --noinput --username admin --email admin@example.com
    
    print_success "Django application configured"
}

setup_systemd_service() {
    print_status "Setting up systemd service..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Portfolio Analytics Django Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR/commodity-tracker-1
Environment=PATH=$VENV_DIR/bin
EnvironmentFile=/etc/environment
ExecStart=$VENV_DIR/bin/gunicorn \\
    --workers 3 \\
    --bind 127.0.0.1:8000 \\
    --timeout 300 \\
    --max-requests 1000 \\
    --max-requests-jitter 100 \\
    --preload \\
    energy_finance.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Set ownership
    chown -R www-data:www-data $PROJECT_DIR
    chown -R www-data:www-data $LOG_DIR
    
    # Enable and start service
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    systemctl start $SERVICE_NAME
    
    print_success "Systemd service configured"
}

setup_nginx() {
    print_status "Setting up Nginx..."
    
    cat > /etc/nginx/sites-available/$NGINX_SITE << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Static files
    location /static/ {
        alias /opt/portfolio-analytics/commodity-tracker-1/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /opt/portfolio-analytics/commodity-tracker-1/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    nginx -t
    
    # Restart nginx
    systemctl restart nginx
    systemctl enable nginx
    
    print_success "Nginx configured"
}

setup_ssl() {
    print_status "Setting up SSL (you'll need to configure your domain)..."
    
    print_warning "To set up SSL, run: certbot --nginx -d your-domain.com"
    print_warning "Make sure your domain points to this server first"
}

setup_monitoring() {
    print_status "Setting up monitoring and health checks..."
    
    # Create health check script
    cat > /usr/local/bin/portfolio-health-check << 'EOF'
#!/bin/bash
curl -sf http://localhost/api/portfolio/sample > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Portfolio Analytics is healthy"
    exit 0
else
    echo "❌ Portfolio Analytics health check failed"
    exit 1
fi
EOF
    
    chmod +x /usr/local/bin/portfolio-health-check
    
    # Setup log rotation
    cat > /etc/logrotate.d/portfolio-analytics << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF
    
    print_success "Monitoring configured"
}

setup_backup() {
    print_status "Setting up backup system..."
    
    mkdir -p /var/backups/portfolio-analytics
    
    cat > /usr/local/bin/portfolio-backup << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/portfolio-analytics"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -h localhost -U portfolio_user portfolio_analytics | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Application backup
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /opt/portfolio-analytics/commodity-tracker-1 --exclude='*.pyc' --exclude='__pycache__' --exclude='venv'

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
EOF
    
    chmod +x /usr/local/bin/portfolio-backup
    
    # Setup daily backup cron
    echo "0 2 * * * /usr/local/bin/portfolio-backup" | crontab -
    
    print_success "Backup system configured"
}

run_tests() {
    print_status "Running system tests..."
    
    cd $PROJECT_DIR/commodity-tracker-1
    source $VENV_DIR/bin/activate
    source /etc/environment
    
    # Test Django
    python manage.py check
    
    # Test health check
    sleep 5  # Wait for services to start
    /usr/local/bin/portfolio-health-check
    
    # Test API endpoints
    curl -sf http://localhost/api/portfolio/sample > /dev/null && \
        print_success "API endpoints are working" || \
        print_error "API endpoints test failed"
    
    print_success "System tests completed"
}

print_summary() {
    print_success "=== Portfolio Analytics Platform Deployment Complete ==="
    echo ""
    echo "🚀 Services Status:"
    systemctl status postgresql --no-pager -l | head -3
    systemctl status redis --no-pager -l | head -3
    systemctl status $SERVICE_NAME --no-pager -l | head -3
    systemctl status nginx --no-pager -l | head -3
    echo ""
    echo "📊 Available Endpoints:"
    echo "  • Dashboard: http://your-server-ip/"
    echo "  • Sample Data: http://your-server-ip/api/portfolio/sample"
    echo "  • Portfolio Analysis: http://your-server-ip/api/portfolio/analyze"
    echo "  • Portfolio Optimization: http://your-server-ip/api/portfolio/optimize"
    echo "  • Monte Carlo Simulation: http://your-server-ip/api/portfolio/simulate"
    echo ""
    echo "🔧 Next Steps:"
    echo "  1. Configure your domain in /etc/nginx/sites-available/$NGINX_SITE"
    echo "  2. Set up SSL: certbot --nginx -d your-domain.com"
    echo "  3. Add your API keys to /etc/environment"
    echo "  4. Test the health check: /usr/local/bin/portfolio-health-check"
    echo ""
    echo "📝 Log Files:"
    echo "  • Application: $LOG_DIR/django.log"
    echo "  • Nginx: /var/log/nginx/access.log"
    echo "  • System: journalctl -u $SERVICE_NAME"
    echo ""
    print_success "Production deployment completed successfully! 🎉"
}

# Main execution
main() {
    print_status "Starting Portfolio Analytics Platform deployment..."
    
    check_root
    install_system_dependencies
    setup_firewall
    setup_postgresql
    setup_redis
    setup_application
    setup_environment
    setup_django
    setup_systemd_service
    setup_nginx
    setup_ssl
    setup_monitoring
    setup_backup
    run_tests
    print_summary
}

# Command line options
case "${1:-}" in
    --help|-h)
        echo "Portfolio Analytics Platform Deployment Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --test-only    Run tests only"
        echo "  --setup-ssl    Setup SSL only"
        echo ""
        echo "Run without options to perform full deployment"
        ;;
    --test-only)
        run_tests
        ;;
    --setup-ssl)
        setup_ssl
        ;;
    *)
        main
        ;;
esac
