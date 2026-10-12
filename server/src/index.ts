import app from './app.js'

const host = process.env.HOST ?? '127.0.0.1'
const port = Number(process.env.PORT ?? 3001)

if (host.trim() === '') {
  throw new Error('HOST must not be empty.')
}

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error('PORT must be a whole number between 1 and 65535.')
}

const server = app.listen(port, host)

server.on('listening', () => {
  console.log(`Eagle Eye API is running at http://${host}:${port}`)
})

server.on('error', (error) => {
  console.error(`Could not start Eagle Eye API: ${error.message}`)
  process.exitCode = 1
})
