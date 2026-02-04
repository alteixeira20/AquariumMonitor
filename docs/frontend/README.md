# Frontend overview

The frontend is a Next.js (App Router) dashboard built with TypeScript and Tailwind. It includes the setup wizard, auth flow, and the initial dashboard experience.

Current scope:
- Setup flow UI (storage selection, backup policy, owner account)
- Setup API wiring (`/v1/setup/status`, `/v1/setup`) with validation and progress UI
- Login screen for `/v1/login` and auth‑gated dashboard routes
- Dashboard shell with overview, aquariums, and devices
- Aquarium create/edit/delete flows
- Shared help modal component for context and onboarding
- Ocean‑palette theme aligned with the product identity

Planned scope:
- Live metrics per aquarium and per device
- Time‑range charts for temperature, pH, and TDS
- Read‑only demo access

## Run locally
Requirements:
- Node.js 20.9+ (matching Next.js 16)

From the repo root:
```
make frontend-dev
```

Run backend + frontend together:
```
make dev-full
```

From inside the frontend directory:
```
cd apps/frontend
npm install
npm run dev
```

Optional environment overrides:
```
# apps/frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

The frontend will consume the backend endpoints documented in [API reference](../backend/api.md).
