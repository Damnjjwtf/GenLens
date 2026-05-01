import NextAuth from 'next-auth';
import Resend from 'next-auth/providers/resend';
import GitHub from 'next-auth/providers/github';
import PostgresAdapter from '@auth/pg-adapter';
import { Pool } from '@neondatabase/serverless';

const pool = process.env.DATABASE_URL
  ? new Pool({ connectionString: process.env.DATABASE_URL })
  : null;

export const { handlers, signIn, signOut, auth } = NextAuth({
  adapter: pool ? PostgresAdapter(pool as never) : undefined,
  providers: [
    Resend({
      apiKey: process.env.RESEND_API_KEY,
      from: process.env.EMAIL_FROM ?? 'brief@genlens.local',
    }),
    GitHub({
      clientId: process.env.GITHUB_ID,
      clientSecret: process.env.GITHUB_SECRET,
    }),
  ],
  pages: {
    signIn: '/',
    verifyRequest: '/auth/verify',
  },
  session: { strategy: 'database' },
});
