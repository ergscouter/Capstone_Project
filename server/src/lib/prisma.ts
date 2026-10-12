import { PrismaPg } from '@prisma/adapter-pg'
import { PrismaClient } from '../generated/prisma/client.js'

const connectionString = process.env.DATABASE_URL

if (!connectionString) {
  throw new Error('DATABASE_URL is missing. Copy .env.example to .env first.')
}

const adapter = new PrismaPg({
  connectionString,
  // The local Prisma database serves one connection at a time.
  max: 1,
  connectionTimeoutMillis: 5000,
  idleTimeoutMillis: 1000,
})

export const prisma = new PrismaClient({ adapter })
