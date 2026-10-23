# Deploy the Flask App to EC2 with Apache

This runbook deploys the Flask/PostgreSQL app in this repository to an Ubuntu EC2 instance using Apache and `mod_wsgi`.

## Prerequisites

- The RDS PostgreSQL database is **Available** and in the same VPC as the EC2 instance.
- RDS is not publicly accessible. Its security group allows inbound PostgreSQL (`TCP 5432`) only from `project-ec2-sg`.
- The EC2 security group allows SSH (`TCP 22`) from your current IP and HTTP (`TCP 80`) from the internet.
- The RDS database name, endpoint, username, and password are available. Do not put real credentials in this document or commit `.env`.

## 1. Connect to EC2 from Fedora

Replace the key path and public IP with your own values:

```bash
KEY="$HOME/Downloads/your-key-pair.pem"
EC2_PUBLIC_IP="YOUR_EC2_PUBLIC_IPV4"
chmod 400 "$KEY"
ssh -i "$KEY" "ubuntu@$EC2_PUBLIC_IP"
```

The Ubuntu AMI uses `ubuntu` as the SSH username. If your public IP changes, update the EC2 security group's SSH source to your current IP.

## 2. Install Apache and clone the repository

Run these commands in the EC2 SSH session:

```bash
sudo apt update
sudo apt install -y apache2 libapache2-mod-wsgi-py3 git python3-venv
sudo systemctl enable --now apache2
sudo systemctl status apache2 --no-pager
sudo git clone https://github.com/ErickColombo/trabalho-cloud.git /var/www/trabalho-cloud
```

The Apache default page at `http://YOUR_EC2_PUBLIC_IPV4` confirms that HTTP access works. It is only a temporary connectivity test; the Flask app is configured below.

## 3. Create a virtual environment and install Python dependencies

```bash
cd /var/www/trabalho-cloud
sudo python3 -m venv /var/www/trabalho-cloud/venv
sudo /var/www/trabalho-cloud/venv/bin/pip install -r /var/www/trabalho-cloud/requirements.txt
```

## 4. Configure the RDS credentials on EC2

The repository's `.env` is ignored by Git, so cloning the repository does not deploy it. Create the file on EC2 from the example:

```bash
cd /var/www/trabalho-cloud
sudo cp -n .env.example .env
sudo nano /var/www/trabalho-cloud/.env
```

Set the values to match the RDS database. Use the RDS endpoint as `DB_HOST` (hostname only: no `https://` and no `:5432`). Use the exact initial database name configured in RDS.

```dotenv
DB_HOST=your-rds-endpoint
DB_NAME=trabalho_cloud
DB_USER=your-rds-username
DB_PASS=your-rds-password
DB_PORT=5432
FLASK_DEBUG=false
```

If RDS manages the master credentials in AWS Secrets Manager, use **Retrieve secret value** in the AWS console and copy its username and password into this EC2-only `.env` file. The current app reads `.env`; it does not fetch Secrets Manager values automatically. Never paste the password into chat, add it to Git, or place it in a shell command.

Save in `nano` with `Ctrl+O`, `Enter`, then `Ctrl+X`. Restrict access so the Apache `www-data` user can read the file:

```bash
sudo chown root:www-data /var/www/trabalho-cloud/.env
sudo chmod 640 /var/www/trabalho-cloud/.env
```

## 5. Test the app and its database connection

This import also creates the app's `usuarios` table if it does not exist:

```bash
sudo -u www-data bash -c 'cd /var/www/trabalho-cloud && /var/www/trabalho-cloud/venv/bin/python -c "import app; print(\"Application and database connection OK\")"'
```

If the error says it tried `localhost`, check that `DB_HOST` in `.env` is the RDS endpoint and that the file is readable:

```bash
sudo -u www-data grep '^DB_HOST=' /var/www/trabalho-cloud/.env
```

Do not print or share the `DB_PASS` value. A timeout after the error shows the RDS endpoint usually points to a VPC/security-group issue. A password-authentication error usually points to the username or password.

## 6. Configure Apache to serve Flask with `mod_wsgi`

Create the WSGI entry point:

```bash
sudo tee /var/www/trabalho-cloud/wsgi.py >/dev/null <<'PY'
from app import app as application
PY

sudo chown root:www-data /var/www/trabalho-cloud/wsgi.py
sudo chmod 640 /var/www/trabalho-cloud/wsgi.py
sudo a2enmod wsgi
```

Create the Apache virtual host:

```bash
sudo tee /etc/apache2/sites-available/trabalho-cloud.conf >/dev/null <<'APACHE'
<VirtualHost *:80>
    WSGIDaemonProcess trabalho_cloud python-home=/var/www/trabalho-cloud/venv python-path=/var/www/trabalho-cloud
    WSGIProcessGroup trabalho_cloud
    WSGIApplicationGroup %{GLOBAL}
    WSGIScriptAlias / /var/www/trabalho-cloud/wsgi.py

    <Directory /var/www/trabalho-cloud>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/trabalho-cloud-error.log
    CustomLog ${APACHE_LOG_DIR}/trabalho-cloud-access.log combined
</VirtualHost>
APACHE

sudo a2ensite trabalho-cloud.conf
sudo a2dissite 000-default.conf
sudo apache2ctl configtest
```

Only continue if the config test reports `Syntax OK`:

```bash
sudo systemctl restart apache2
```

Open `http://YOUR_EC2_PUBLIC_IPV4` in a browser. The EC2 security group must allow inbound HTTP on port `80`.

## Troubleshooting

View Apache application errors:

```bash
sudo tail -n 60 /var/log/apache2/trabalho-cloud-error.log
```

- **Connection to `localhost` refused:** `DB_HOST` is missing or still set to `localhost` in `.env`.
- **Timeout connecting to the RDS endpoint:** verify the database is `Available`, both resources use `project-vpc`, and the RDS security group allows `TCP 5432` from `project-ec2-sg`.
- **Password authentication failed:** verify `DB_USER` and `DB_PASS` against the RDS credentials/Secrets Manager value. Do not share the password.
- **The browser cannot connect:** verify the EC2 security group allows HTTP (`TCP 80`) from the internet and Apache is running.

If the RDS password is changed or rotated, update the EC2 `.env` as well; this app does not refresh Secrets Manager credentials automatically.
