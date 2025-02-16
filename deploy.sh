#!/bin/bash

echo "🚀 Starting deployment..."

# SSH into the server and execute deployment commands
ssh root@209.97.129.64 << 'EOF'
echo "1️⃣ Installing system dependencies..."
apt update
apt install -y python3-dev default-libmysqlclient-dev build-essential pkg-config

echo "2️⃣ Setting up project directory..."
# Create project directory if it doesn't exist
mkdir -p /root/saleswise-backend

# Navigate to project directory
cd /root/saleswise-backend

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git remote add origin https://github.com/ewarhou/saleswise-backend.git
fi

echo "3️⃣ Pulling latest changes..."
git fetch --all
git reset --hard origin/main

echo "4️⃣ Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "5️⃣ Installing/updating dependencies..."
pip install --upgrade pip
pip install wheel
pip install -r requirements.txt

echo "6️⃣ Running database migrations..."
python manage.py migrate

echo "7️⃣ Collecting static files..."
python manage.py collectstatic --noinput

echo "8️⃣ Setting up systemd service..."
cat > /etc/systemd/system/saleswise.service << 'EOL'
[Unit]
Description=Saleswise Backend
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/root/saleswise-backend
ExecStart=/root/saleswise-backend/venv/bin/gunicorn saleswise.wsgi:application --bind unix:/run/saleswise.sock
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Enable the service
systemctl enable saleswise

echo "9️⃣ Setting proper permissions..."
# Create static and media directories if they don't exist
mkdir -p /root/saleswise-backend/static/
mkdir -p /root/saleswise-backend/media/

# Set proper permissions
chmod -R 755 /root/saleswise-backend/static/
chmod -R 755 /root/saleswise-backend/media/

echo "🔟 Restarting services..."
systemctl daemon-reload
systemctl restart saleswise

echo "✅ Deployment completed successfully!"
EOF 