# Deploy CRM Dashboard (Windows + conda + nginx + winsw)

- **nginx:** `c:\nginx`
- **winsw:** `c:\services`
- **Django** `c:\serve`

## 1. Prepare app (conda)

```powershell
cd C:\serve\H.F-Capital-CRM
conda create -n dashboard python=3.13 -y
conda activate dashboard
pip install -r requirements.txt
```

## 2. Production settings

In `crm_project/settings.py`:

- **DEBUG:** Default is `True` on your dev machine. When the app runs under `start.ps1` on the server, `start.ps1` sets `DJANGO_PRODUCTION=True`, so DEBUG is `False` there. No need to set anything for local dev.
- `ALLOWED_HOSTS = ['hf.capital', 'localhost', '127.0.0.1']` (or your server name).
- `STATIC_ROOT = BASE_DIR / 'staticfiles'` (already added).

Then:

```powershell
conda activate dashboard
python manage.py collectstatic --noinput
python manage.py migrate
# Create superuser if needed: python create_admin.py
```

## 3. Test Waitress locally

```powershell
conda activate dashboard
python run_server.py
```

Open http://127.0.0.1:8000 — dashboard should load. (On dev, DEBUG is on by default.)

## 4. Install as Windows service (winsw in c:\services)

1. **Python path:** `start.ps1` tries `C:\ProgramData\miniconda3\envs\dashboard\python.exe` first (recommended for services). If your conda is elsewhere, set `$CondaPython` at the top of `start.ps1` to the full path (e.g. from `conda activate dashboard; (Get-Command python).Source`).
2. Copy into `c:\services\`:
   - winsw exe → rename to `crm-dashboard.exe`
   - project file `crm-dashboard.xml` from repo
3. Install and start:

```powershell
cd c:\services
.\crm-dashboard.exe install
.\crm-dashboard.exe start
```

Check: `.\crm-dashboard.exe status`

**If the service reports “started” but status is Stopped:**  
- Check `C:\serve\H.F-Capital-CRM\logs\dashboard-service.log` for the error.  
- **"Python not found"** → Service runs as Local System and can't see `C:\Users\...\miniconda3`. **Recommended (no password):** install Miniconda in `C:\ProgramData\miniconda3`, create env `dashboard` there, and run `pip install -r requirements.txt`; `start.ps1` will use that path automatically. Alternatively run the service as Administrator by adding `<serviceaccount>` only on the server (never commit the password).  
- Other errors: run manually `cd C:\serve\H.F-Capital-CRM; .\start.ps1` and watch the console.

## 5. nginx (c:\nginx)

This project’s **`nginx.conf`** is the full config for hf.capital: static site (root) + CRM at **/dashboard/**.

1. Backup existing config, then copy this repo’s `nginx.conf` to `c:\nginx\conf\nginx.conf`.
2. Adjust SSL paths and `root`/`alias` if your paths differ.
3. Reload nginx (run PowerShell as Administrator if needed): `cd c:\nginx; .\nginx.exe -s reload`. If you get 502 at `/dashboard/`, ensure the CRM service is running on 127.0.0.1:8000 (see section 6).

- **https://hf.capital/** → static site (C:/serve/HF-website)
- **https://hf.capital/dashboard/** → CRM (Waitress on 127.0.0.1:8000)

`start.ps1` sets `DJANGO_SCRIPT_NAME=/dashboard` so Django generates correct URLs under the subpath.

**Optional:** For AI enrichment, ensure `keys.env` (or `.env`) in the project root contains `GENAI_API_KEY` and `OPENAI_API_KEY` on the server; the app loads them when present.

## 6. Restarting and controlling the service

From **c:\services**:

| Action   | Command                      |
|----------|------------------------------|
| Restart  | `.\crm-dashboard.exe restart` |
| Stop     | `.\crm-dashboard.exe stop`    |
| Start    | `.\crm-dashboard.exe start`   |
| Status   | `.\crm-dashboard.exe status`  |

After restart, confirm **status** shows **Running**. If it shows **Stopped**, check:

- `C:\serve\H.F-Capital-CRM\logs\crm-dashboard.err.log`
- `C:\serve\H.F-Capital-CRM\logs\dashboard-service.log`

## 7. Turning DEBUG on on the server

The service runs with DEBUG off because `start.ps1` sets `DJANGO_PRODUCTION=True`. To get tracebacks in the browser when debugging on the server:

1. On the server, edit `C:\serve\H.F-Capital-CRM\start.ps1`.
2. Comment out the line `$env:DJANGO_PRODUCTION = "True"` (add `#` at the start of the line).
3. Restart the service from **c:\services**: `.\crm-dashboard.exe restart`.
4. When done, uncomment `$env:DJANGO_PRODUCTION = "True"` again and run `.\crm-dashboard.exe restart`.
