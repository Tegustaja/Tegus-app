# Tegus Monorepo

Unified backend (FastAPI) and frontend (Expo React Native) project.

## Getting started

1. Copy env file

```bash
cp .env.example .env
```

2. Install deps

```bash
make install
```

3. Run dev (backend + frontend web)

```bash
make dev
```

- To run native bundler (Android/iOS), use:

```bash
make dev-native
```

4. Run tests

```bash
make test
```

## Docker (dev)

```bash
docker compose -f docker-compose.dev.yml up --build
```

The frontend will use `EXPO_PUBLIC_BACKEND_URL` pointing at the backend. Update `.env` as needed.
