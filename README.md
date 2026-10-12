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