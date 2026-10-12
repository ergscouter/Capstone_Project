# Eagle Eye

UNT computer science capstone, Team 1 A. Eagle Eye will help students plan campus travel, find classrooms, and compare parking options.

## Run locally

Install Node.js 24 and pnpm 11, then run these commands from the repository folder:

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

The `server` folder contains the Node.js + Express + TypeScript backend. It currently provides a server health response. Accounts and database storage are the next steps.

Open a second terminal from the repository folder:

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

This response means the server can handle a request. It does not check a database or sign anyone in. Unknown paths return HTTP 404 with `{"error":"Route not found"}`.

To change the server address or port, copy `server/.env.example` to `server/.env` and edit its values. The server reads `.env` when it starts, and uses defaults if that file is absent. Restart the server after changing these settings. `.env` is ignored by Git.

## Backend files and commands

- `server/src/app.ts`: defines the server's request handlers.
- `server/src/index.ts`: reads settings and starts the server.
- `server/tsconfig.json`: configures TypeScript to compile `src` into JavaScript in `dist`.
- `server/package.json`: lists dependencies and commands.
- `server/pnpm-lock.yaml`: records dependency versions for repeatable installs.
- `server/pnpm-workspace.yaml`: allows the esbuild install script used by the TypeScript development runner.
- `server/.env.example`: documents the local settings without secrets.

Run these commands inside `server`:

- `pnpm dev`: runs TypeScript during development and restarts when source files change.
- `pnpm build`: checks TypeScript and produces JavaScript in `dist`.
- `pnpm start`: runs the compiled JavaScript; run `pnpm build` first.
