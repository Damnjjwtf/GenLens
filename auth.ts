import NextAuth from 'next-auth';
import Resend from 'next-auth/providers/resend';
import PostgresAdapter from '@auth/pg-adapter';
import { Pool } from '@neondatabase/serverless';
import { cookies } from 'next/headers';
import { consumeInviteCode } from '@/lib/db';
import { INVITE_COOKIE } from '@/lib/constants';

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
  ],
  pages: {
    signIn: '/auth/invite',
    verifyRequest: '/auth/verify',
  },
  session: { strategy: 'database' },
  events: {
    async createUser({ user }) {
      if (!user.id) return;
      const inviteCode = cookies().get(INVITE_COOKIE)?.value;
      if (inviteCode) {
        try {
          await consumeInviteCode(inviteCode, user.id);
        } catch (e) {
          console.error('Failed to consume invite code', e);
        }
        cookies().delete(INVITE_COOKIE);
      }
    },
  },
});
