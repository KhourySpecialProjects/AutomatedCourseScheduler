# Coolify Deployment (`develop`)

Runbook for deploying the Automated Course Scheduler to a Coolify server from the
`develop` branch. This path is **self-hosted** and independent of the AWS
`deploy.yml` workflow (which still targets `main`; see [Coexistence with AWS](#coexistence-with-the-aws-workflow)).

Prerequisites:

- A running Coolify server you can reach, with ports 80/443 open.
- The **Coolify GitHub App** installed in the org that owns this repo.
- Access to the project's Auth0 tenant (SPA app + API).
- Control of a DNS zone for the hostnames below.

## What gets deployed

Coolify builds from [`docker-compose.coolify.yaml`](../docker-compose.coolify.yaml)
— three services:

| Service | Image / build | Internal port | Public domain | Notes |
|---|---|---|---|---|
| `db` | `postgres:16` | 5432 | **none** | Not internet-reachable. Data in the `postgres_data` named volume. |
| `api` | built from `backend/` | 8000 | `api.dev.example.com` | FastAPI/uvicorn. SPA calls it cross-origin. |
| `frontend` | built from `frontend/` | 80 | `app.dev.example.com` | nginx serving the static Vite bundle (SPA fallback only — **no `/api` proxy**). |

Two facts that shape the steps:

- **No migrations.** `backend/app/main.py` runs `Base.metadata.create_all()` on
  startup, so tables self-create on first boot. There is no Alembic step.
- **`VITE_*` are baked at _build_ time** (Docker `build.args`, not runtime env).
  They must be present when the `frontend` image builds, or the bundle ships with
  blank Auth0 config and **login silently breaks**.

> Replace `app.dev.example.com` / `api.dev.example.com` throughout with your real
> hostnames.

## 1. Choose two hostnames

| Purpose | Example host | Routes to |
|---|---|---|
| Frontend (SPA) | `app.dev.example.com` | `frontend` service, port `80` |
| API (HTTP + WebSocket) | `api.dev.example.com` | `api` service, port `8000` |

Decide these first — several env values are literally these URLs.

## 2. DNS

Point both names at the Coolify server's public IP (add `AAAA` too if it has IPv6):

```
app.dev.example.com   A   <coolify_server_ip>
api.dev.example.com   A   <coolify_server_ip>
```

If a `*.dev.example.com` wildcard already resolves to the server, explicit records
can be skipped. Let DNS resolve before deploying — Coolify's Let's Encrypt issuance
needs the names resolving to the box.

## 3. Auth0

On the **SPA application** in the Auth0 dashboard, add the frontend origin to:

- **Allowed Callback URLs:** `https://app.dev.example.com`
- **Allowed Logout URLs:** `https://app.dev.example.com`
- **Allowed Web Origins:** `https://app.dev.example.com`

Confirm the **API Identifier** exists (this is `AUTH0_AUDIENCE`, e.g. `https://acs-api`).
Note the tenant domain (`AUTH0_DOMAIN`, bare host — no `https://`, no trailing slash)
and the SPA **Client ID** (`AUTH0_SPA_CLIENT_ID`).

## 4. Create the Coolify resource

1. **+ New → Resource → Private Repository (with GitHub App)** → select the org's
   GitHub App → pick this repository.
2. **Branch:** `develop`.
3. **Build Pack:** **Docker Compose**.
4. **Compose file path:** `docker-compose.coolify.yaml` (not the default
   `docker-compose.yaml`).
5. Save. Coolify parses the file and shows `db`, `api`, `frontend`. The GitHub App
   also wires a push webhook, so future pushes to `develop` auto-redeploy.

## 5. Environment variables

Add these under the resource's **Environment Variables**. Generate the DB password
with `openssl rand -hex 32` — hex is URL-safe; base64 can emit `+ / =` and break the
`DATABASE_URL` connection string.

**Runtime** (consumed by `api` + `db`):

```
POSTGRES_USER=scheduler
POSTGRES_PASSWORD=<openssl rand -hex 32>
POSTGRES_DB=scheduler_db
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://acs-api
AUTH0_SPA_CLIENT_ID=<spa client id>
CORS_ORIGINS=https://app.dev.example.com
APP_BASE_URL=https://app.dev.example.com
```

Leave `DATABASE_URL` unset — the compose default builds it from the `POSTGRES_*`
values and targets the bundled `db`. Only set it to point at an external Postgres.

**Build args** (consumed by the `frontend` image build):

```
VITE_AUTH0_DOMAIN=your-tenant.us.auth0.com
VITE_AUTH0_CLIENT_ID=<spa client id>
VITE_AUTH0_AUDIENCE=https://acs-api
VITE_API_BASE_URL=https://api.dev.example.com
```

> **Critical:** enable Coolify's **"Build Variable / Available at buildtime"** toggle
> for each of the four `VITE_*` vars. They are `build.args` — if absent at build time,
> the bundle ships with blank Auth0 config and login breaks. Because they are baked in,
> changing any of them later requires a **rebuild**, not just a restart.

`CORS_ORIGINS` and `APP_BASE_URL` must be the frontend origin **exactly** (scheme +
host, no trailing slash), or the API rejects the browser and the Auth0 signup redirect
misfires.

## 6. Map domains to service ports

In the resource's per-service domain settings:

- `frontend` → `https://app.dev.example.com`, port **80**
- `api` → `https://api.dev.example.com`, port **8000**
- `db` → no domain (internal only)

Coolify's Traefik proxy provisions TLS for both and proxies WebSocket upgrades
automatically, so `wss://api.dev.example.com` (derived by the SPA from
`VITE_API_BASE_URL`) works without extra config.

## 7. Deploy

Hit **Deploy** and watch the build logs. Expected: the `frontend` image builds the
Vite bundle with the args baked in, `db` comes up healthy, and `api` boots and
auto-creates its tables on first start.

## 8. Post-deploy

1. **Create the first admin** (there are no seeded users otherwise). Open the `api`
   service's terminal in Coolify and run:

   ```bash
   python bootstrap_admin.py \
     --nuid <your_nuid> --first-name <First> --last-name <Last> \
     --email <your_auth0_login_email>
   ```

   The email **must** match your Auth0 login — the backend links your `auth0_sub` on
   the first `GET /users/me`.

2. **Smoke test:**
   - `https://api.dev.example.com/` → `{"message":"Automated Course Scheduler API"}`
   - `https://api.dev.example.com/docs` → Swagger loads
   - `https://app.dev.example.com` → SPA loads, Auth0 login round-trips, you land
     authenticated as ADMIN

3. **(Optional) seed demo data:** the repo ships `backend/seed.py` with
   `Sections.csv` / `Faculty.csv`. Run it from the `api` terminal only if you want
   sample data.

## Gotchas

- **Build-time `VITE_*` vars** — the most common failure. See step 5.
- **The DB password is permanent on first deploy.** It is baked into the
  `postgres_data` volume; rotating later means recreating the volume (data loss) or an
  in-DB `ALTER ROLE`.
- **No `api` healthcheck** is defined (only `db` has one), so Coolify may not report
  `api` health — cosmetic. `GET /` is a fine health target if one is added later.

## Coexistence with the AWS workflow

`.github/workflows/deploy.yml` still runs the AWS pipeline (S3 + CloudFront + ECS) on
push to `main`. This Coolify path deploys from `develop` via its own webhook, so the
two do not collide today. Reconciling them — deciding whether Coolify replaces AWS and,
if so, retiring/gating `deploy.yml` and its AWS secrets/variables — is tracked
separately (SSIP-143) and should be settled before pushing to `main`.
