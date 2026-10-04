# WhatToWatch frontend

Next.js interface for registration, login, home feed and movie details. Browser requests go through Next.js API routes to the Spring Boot backend.

See the repository root README for MySQL setup and backend commands. Docker is optional when MySQL is already installed.

From `frontend/`:

```bash
cp .env.example .env.local
npm ci
npm run dev
```

Open http://localhost:3000 for the original Nextflix landing page. Register at `/register`, log in at `/login`, then browse at `/browse`. Movie details use the original modal layout at `/movies/[id]`. `BACKEND_URL` defaults to `http://localhost:8080/movie-recommendation`.
