# Running Alpha Report Lab on a Cloud-Hosted VM

This guide walks you through running the Alpha Report Lab (engine + frontend) on a remote
cloud VM (GCP Compute Engine in this example) and forwarding the service ports back to your
local machine over SSH so you can use it from your browser as if it were running locally.

> **Placeholders used throughout this doc:**
> - `<INSTANCE_NAME>` — the name of your VM (e.g. `alpha-report-generator`)
> - `<USERNAME>` — the SSH username on the VM (e.g. `mrplzdontmess`)
> - `<ZONE>` — the GCP zone (e.g. `us-central1-f`)
> - `<PROJECT_ID>` — your GCP project ID (only needed if not set as default)

---

## 1. Prerequisites

**On the VM:**
- Linux (Debian/Ubuntu recommended)
- `git`, `python3`, `python3-venv`, `python3-pip`, `nodejs` (v18+), `npm`

**On your local machine:**
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud`) authenticated:
  ```bash
  gcloud auth login
  gcloud config set project <PROJECT_ID>
  ```
- An SSH client (built into Windows 10+, macOS, and Linux)

---

## 2. Create / Configure the VM

Skip this section if your VM already exists.

```bash
gcloud compute instances create <INSTANCE_NAME> \
  --zone=<ZONE> \
  --machine-type=e2-standard-2 \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=20GB
```

Make sure IAP TCP forwarding is allowed (so you don't need a public IP):

```bash
gcloud compute firewall-rules create allow-iap-ssh \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=35.235.240.0/20
```

---

## 3. SSH Into the VM (with Port Forwarding)

Use IAP tunneling (no public IP required). The `--ssh-flag="-L ..."` option forwards
the frontend port from the VM's `localhost` back to your local machine, so the app
running on the VM is reachable in your local browser at `http://localhost:3000`.

```bash
gcloud compute ssh <USERNAME>@<INSTANCE_NAME> \
  --zone=<ZONE> \
  --tunnel-through-iap \
  --ssh-flag="-L 3000:localhost:3000"
```

> **Concrete example** (single-line, no backslash continuation):
> ```bash
> gcloud compute ssh mrplzdontmess@alpha-report-generator --zone=us-central1-f --project=custom-octagon-438612-f4 --tunnel-through-iap --ssh-flag="-L 3000:localhost:3000"
> ```
>
> This opens an interactive SSH session on the VM **and** simultaneously forwards VM port `3000` to your local machine's port `3000`. While this terminal stays open, `http://localhost:3000` in your browser loads the frontend running on the VM. Closing the terminal (or pressing `Ctrl+D` / `exit`) tears down both the SSH session and the tunnel.

**What `--ssh-flag="-L 3000:localhost:3000"` does:** opens local port `3000` on your
machine and tunnels all traffic to `localhost:3000` on the VM (where the frontend is
listening). The frontend talks to the engine internally on the VM, so you only need
to forward the frontend port.

---

## 4. Clone and Set Up the Repo on the VM

Once SSH'd in:

```bash
# Install system dependencies (Debian/Ubuntu)
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip nodejs npm

# Clone the repo
git clone <YOUR_REPO_URL> alpha-report-lab
cd alpha-report-lab

# Create .env files from templates
./tasks.sh setup

# Edit .env to add API keys, etc.
nano alpha-engine/.env
```

The `start-engine.sh` / `start-all.sh` scripts will automatically create a Python virtual
environment in `alpha-engine/.venv` and install requirements on first run.

---

## 5. Start the Services on the VM

Inside the SSH session, from the `alpha-report-lab` directory:

```bash
# Start both engine (port 8000) and frontend (port 3000)
./tasks.sh start
```

Or run them individually:

```bash
./tasks.sh run-engine     # engine only, port 8000
./tasks.sh run-frontend   # frontend only, port 3000
```

Leave this SSH session running while you use the app.

---

## 6. Access the Services Locally

If you used the SSH command from **Section 3** (with `--ssh-flag="-L 3000:localhost:3000"`),
the port is already being forwarded for the duration of that SSH session. While that
session is open, browse to:

- Frontend: http://localhost:3000

Closing the SSH session (or pressing `Ctrl+D` / `exit`) closes the tunnel.

### Alternative: Separate Tunnel Terminal

If you'd rather keep your "work" SSH session free of port-forwarding, open a **second
terminal on your local machine** dedicated to the tunnel:

```bash
gcloud compute ssh <USERNAME>@<INSTANCE_NAME> \
  --zone=<ZONE> \
  --tunnel-through-iap \
  --ssh-flag="-L 3000:localhost:3000"
```

Leave this terminal open while you use the app. `Ctrl+C` (or `exit`) closes the tunnel.

---

## 7. Optional: Run Services in the Background (`tmux` / `nohup`)

If you want the services to keep running after you disconnect SSH, start them in a `tmux`
session on the VM:

```bash
sudo apt-get install -y tmux
tmux new -s alpha
./tasks.sh start
# Detach with: Ctrl+B then D
```

To re-attach later: `tmux attach -t alpha`

This way, your local SSH tunnel from step 6 only needs to forward ports — the services
themselves keep running on the VM.

---

## 8. Stopping Everything

**On the VM:**
```bash
./tasks.sh stop
```

**On your local machine:** `Ctrl+C` in the tunnel terminal.

**To stop the VM (save costs):**
```bash
gcloud compute instances stop <INSTANCE_NAME> --zone=<ZONE>
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `bind: Address already in use` when opening tunnel | Local port 3000 is already taken. Stop the local process or change the local side: `-L 3001:localhost:3000` and browse to `http://localhost:3001`. |
| `Permission denied (publickey)` | Run `gcloud compute config-ssh` once, or ensure your SSH key is added: `gcloud compute os-login ssh-keys add --key-file=~/.ssh/id_rsa.pub`. |
| `python3-venv` missing | `sudo apt-get install -y python3-venv` then re-run `./tasks.sh run-engine`. |
| IAP tunnel hangs | Confirm the firewall rule for `35.235.240.0/20` exists and your account has the **IAP-secured Tunnel User** role. |
