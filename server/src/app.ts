import express from 'express'

const app = express()

app.disable('x-powered-by')

// This checks the server only, not the database.
app.get('/health', (_request, response) => {
  response.json({ status: 'ok', service: 'eagle-eye-api' })
})

app.use((_request, response) => {
  response.status(404).json({ error: 'Route not found' })
})

export default app
