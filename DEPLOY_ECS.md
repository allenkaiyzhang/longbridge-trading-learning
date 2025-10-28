# Deployment Guide for Aliyun Ubuntu ECS

This document explains how to deploy the realtime quotes script on an Alibaba Cloud (Aliyun) ECS instance running Ubuntu 22.04 or later.

## Requirements

- An Aliyun ECS instance with Ubuntu 22.04 or later.
- Python 3 installed (preferably >= 3.10).
- Git installed.
- Access credentials for LongPort API (`LONGPORT_APP_KEY`, `LONGPORT_APP_SECRET`, `LONGPORT_ACCESS_TOKEN`).
- A comma-separated list of stock symbols to subscribe to, specified in the `SYMBOLS` environment variable.

## Steps

1. **Update the system and install dependencies**

   ```sh
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3 python3-venv python3-pip git
   ```

2. **Clone the repository**

   ```sh
   git clone https://github.com/allenkaiyzhang/longbridge-trading-learning.git
   cd longbridge-trading-learning
   git checkout realtime-quotes
   ```

3. **Create a Python virtual environment and install dependencies**

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -U pip
   pip install longport python-dotenv
   ```

4. **Create a `.env` file**

   Create a file named `.env` in the project root with the following content, replacing the placeholder values with your actual credentials and desired settings:

   ```env
   LONGPORT_APP_KEY=your_app_key
   LONGPORT_APP_SECRET=your_app_secret
   LONGPORT_ACCESS_TOKEN=your_access_token
   SYMBOLS=700.HK,AAPL.US
   # Optional: override API endpoints for test environment
   # LONGPORT_HTTP_URL=
   # LONGPORT_QUOTE_WS_URL=
   ```

5. **Run the script**

   Activate your virtual environment and run the realtime quotes script:

   ```sh
   source .venv/bin/activate
   python realtime_quotes.py
   ```

   The script will subscribe to the symbols specified in the `SYMBOLS` environment variable and print real-time quote updates to the console.

6. **(Optional) Run as a systemd service**

   To keep the script running in the background, you can create a systemd unit. Create a file at `/etc/systemd/system/longbridge-quotes.service` with the following content (adjust the paths and user names as needed):

   ```ini
   [Unit]
   Description=Longbridge Realtime Quotes Service
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/path/to/longbridge-trading-learning
   Environment=ENVFILE=/path/to/longbridge-trading-learning/.env
   ExecStart=/path/to/longbridge-trading-learning/.venv/bin/python realtime_quotes.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

   Then reload systemd and enable the service:

   ```sh
   sudo systemctl daemon-reload
   sudo systemctl enable --now longbridge-quotes
   sudo journalctl -u longbridge-quotes -f
   ```

---

Refer to the `README.md` or inline comments for more details about customizing subscriptions and output.
