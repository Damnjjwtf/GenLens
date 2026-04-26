import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { findInviteCode } from '@/lib/db';
import { INVITE_COOKIE, INVITE_COOKIE_TTL_SECONDS } from '@/lib/constants';

export async function POST(req: Request) {
  const { code } = (await req.json().catch(() => ({}))) as { code?: string };
  if (!code || typeof code !== 'string') {
    return NextResponse.json({ ok: false, error: 'Missing code' }, { status: 400 });
  }

  const trimmed = code.trim();
  const invite = await findInviteCode(trimmed);
  if (!invite || invite.uses >= invite.max_uses) {
    return NextResponse.json({ ok: false, error: 'Invalid or exhausted invite' }, { status: 401 });
  }

  cookies().set(INVITE_COOKIE, trimmed, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    maxAge: INVITE_COOKIE_TTL_SECONDS,
    path: '/',
  });

  return NextResponse.json({ ok: true });
}
