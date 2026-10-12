# Eagle Eye

UNT computer science capstone, Team 1 A. Eagle Eye will help students plan campus travel, find classrooms, and compare parking options.

## Run locally

Install Node.js 24 (including npm) and pnpm 11, then run these commands from the repository folder:

```sh
cd web
pnpm install
pnpm dev
```

Open the local address printed in the terminal. Vite updates the page when you save a source file.

## Source files

- `web/src/main.tsx`: starts the React application.
- `web/src/App.tsx`: lays out the sign-in page.
- `web/src/components/SignInForm.tsx`: contains the inputs and form behavior.
- `web/src/styles.css`: contains the page styles.
- `Docs`: existing planning documents and campus data.

## Check the frontend

Run `pnpm build` and `pnpm lint` inside `web`.

## Run the backend

The `server` folder contains the Node.js + Express + TypeScript backend and uses Prisma 7 to connect to PostgreSQL. The database has a user table; account registration and sign-in are the next steps.

Complete the database setup below first. Then open a terminal from the repository folder:

```sh
cd server
pnpm install
pnpm dev
```

Keep this terminal running alongside the frontend terminal. The server uses `http://127.0.0.1:3001` by default. The frontend and backend run as separate programs; the sign-in form is not connected to the backend yet.

Opening `http://127.0.0.1:3001/health` returns:

```json
{"status":"ok","service":"eagle-eye-api"}
```

The server checks the database during startup. This health response reports that the server can handle a request; it does not recheck the database or sign anyone in. Unknown paths return HTTP 404 with `{"error":"Route not found"}`.

The server reads its address, port, and database URL from `server/.env` when it starts. The address and port have defaults; the database URL is required. Restart the server after changing these settings. `.env` is ignored by Git.

## Backend files and commands

- `server/src/app.ts`: defines the server's request handlers.
- `server/src/index.ts`: checks the database, starts the server, and closes the database connection during shutdown.
- `server/tsconfig.json`: configures TypeScript to compile `src` into JavaScript in `dist`.
- `server/package.json`: lists dependencies and commands.
- `server/pnpm-lock.yaml`: records dependency versions for repeatable installs.
- `server/pnpm-workspace.yaml`: allows the install scripts required by esbuild and Prisma.
- `server/.env.example`: documents the local settings without secrets.

Run these commands inside `server`:

- `pnpm dev`: runs TypeScript during development and restarts when source files change.
- `pnpm build`: generates the Prisma client, checks TypeScript, and produces JavaScript in `dist`.
- `pnpm start`: runs the compiled JavaScript; run `pnpm build` first.

## Set up the local database

For development, this project uses local Prisma Postgres, powered by PGlite. It runs through Prisma's tools without Docker or a separate PostgreSQL installation. It stores data locally between runs. Each teammate has their own development database.

Use a regular PostgreSQL server for a shared or deployed application. The local development database serves one connection at a time, so the application currently uses a one-connection pool. Review this setting in `server/src/lib/prisma.ts` when configuring a hosted database.

From the repository folder, open a database terminal:

```powershell
cd server
pnpm install
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
pnpm db:dev
```

Copy `.env.example` only when creating `.env` for the first time, so you keep any existing local settings. A standard Node.js installation includes npm, which Prisma's local database starter needs. Installing the project also generates Prisma's client code.

Keep the database terminal running. The `eagle-eye` database uses port 51214, with a separate temporary database on port 51215 for checking schema changes. Its connection strings match `.env.example`. These are development-only settings for your own computer.

Open another terminal to apply the saved database changes and start the backend:

```powershell
cd server
pnpm db:deploy
pnpm dev
```

The backend sends a small database query before accepting requests. If the database is stopped or `DATABASE_URL` is incorrect, startup reports an error. Stop the backend with Ctrl+C before stopping the database. In the database terminal, press `q` to stop it; its saved data remains available next time you run `pnpm db:dev`.

Run the frontend in its own terminal using the commands above. Development currently uses three programs: the database, the backend, and the frontend.

## Database files and commands

- `server/prisma/schema.prisma`: describes the user table and generates the database client.
- `server/prisma/migrations`: saved database changes that belong in Git.
- `server/prisma.config.ts`: tells Prisma where the schema, migrations, and connection settings are.
- `server/src/lib/prisma.ts`: shares one Prisma client across the backend.
- `server/src/generated/prisma`: generated code; ignored by Git and recreated during install or build.

The user table stores an ID, name, unique email, email-verification status, optional image URL, and creation/update times. There are no user records yet and no registration endpoint. Better Auth will add its remaining authentication tables in a later commit.

Run these commands inside `server`:

- `pnpm db:dev`: starts the local database and keeps the terminal occupied.
- `pnpm db:deploy`: applies migrations already saved in the repository.
- `pnpm db:migrate --name describe_change`: creates and applies a migration after you edit the schema.
- `pnpm db:generate`: regenerates the TypeScript client after a schema change.
- `pnpm db:stop`: stops the named local database from another terminal.

After creating a migration, run `pnpm db:generate` and commit both the schema and migration files. Migrations describe table changes; they do not contain users' records. Keep private `.env` settings and database files out of Git.
