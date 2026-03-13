#!/bin/bash

# Force script to run from its own directory
cd "$(dirname "$0")"

echo "==================================================="
echo "      Auto-Attendance Bot Setup & Launcher"
echo "==================================================="
echo ""

# --- 1. CHECK IF DOCKER IS INSTALLED ---
if ! command -v docker &> /dev/null; then
    echo "[!] Docker is not installed."
    echo "[*] Attempting to install Docker Engine..."

    if command -v apt-get &> /dev/null; then
        # Debian / Ubuntu
        sudo apt-get update -qq
        sudo apt-get install -y ca-certificates curl gnupg
        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
            sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update -qq
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        sudo usermod -aG docker "$USER"
    elif command -v dnf &> /dev/null; then
        # Fedora / RHEL
        sudo dnf -y install dnf-plugins-core
        sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
        sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        sudo usermod -aG docker "$USER"
    elif command -v pacman &> /dev/null; then
        # Arch
        sudo pacman -Sy --noconfirm docker docker-compose
        sudo usermod -aG docker "$USER"
    else
        echo "[!] Could not detect package manager. Install Docker manually:"
        echo "    https://docs.docker.com/engine/install/"
        exit 1
    fi

    echo ""
    echo "==================================================="
    echo "[!] Docker installed. Please LOG OUT and LOG BACK IN"
    echo "    so group permissions take effect, then run this"
    echo "    script again."
    echo "==================================================="
    exit 0
fi

# --- 2. CHECK IF DOCKER DAEMON IS RUNNING ---
echo "[*] Checking Docker daemon status..."
if ! docker info &> /dev/null; then
    echo "[*] Docker is not running. Starting it..."
    sudo systemctl start docker 2>/dev/null || open --background -a Docker 2>/dev/null
    echo "[*] Waiting for Docker daemon to start..."
    while ! docker info &> /dev/null; do
        echo "   ...still waiting..."
        sleep 5
    done
fi
echo "[V] Docker daemon is online!"
echo ""

# --- 3. CHECK DOCKER COMPOSE ---
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo "[!] docker-compose not found. Installing..."
    sudo apt-get install -y docker-compose-plugin 2>/dev/null || \
    sudo pip3 install docker-compose 2>/dev/null || true
fi

# Prefer the newer plugin syntax, fall back to standalone
COMPOSE_CMD="docker compose"
docker compose version &> /dev/null 2>&1 || COMPOSE_CMD="docker-compose"

# --- 4. START N8N AND EVOLUTION API ---
echo "[*] Booting up n8n and WhatsApp API..."
cd local-browser-bridge
$COMPOSE_CMD up -d
cd ..
echo "[V] Background services are live!"
echo ""

# --- 5. PREPARE PYTHON ENVIRONMENT ---
echo "[*] Preparing the Python Bot..."
cd python-bot

# Ensure python3 + pip are available
if ! command -v python3 &> /dev/null; then
    echo "[!] python3 not found. Installing..."
    sudo apt-get install -y python3 python3-pip python3-venv 2>/dev/null || \
    sudo dnf install -y python3 python3-pip 2>/dev/null || \
    sudo pacman -Sy --noconfirm python python-pip 2>/dev/null
fi

# Create venv on first run
if [ ! -d "venv" ]; then
    echo "[*] First-time setup: Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "[*] Activating environment and checking dependencies..."
source venv/bin/activate
pip install flask playwright --quiet
playwright install chromium --quiet
echo "[V] Python environment ready!"
echo ""

# --- 6. LAUNCH ---
echo "==================================================="
echo "        ALL SYSTEMS GO — LAUNCHING BOT"
echo "==================================================="
echo "[*] Opening Control Panel in your browser..."
sleep 2

# Open browser cross-platform
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5000 &
elif command -v gnome-open &> /dev/null; then
    gnome-open http://localhost:5000 &
elif command -v open &> /dev/null; then
    open http://localhost:5000 &
fi

echo "[*] DO NOT CLOSE THIS TERMINAL while the bot is active."
echo ""
python app.py
