import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import { getUserPreferences, upsertUserPreferences } from '@/lib/db';

export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const prefs = await getUserPreferences(session.user.id);
  return NextResponse.json({ preferences: prefs });
}

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const body = await req.json().catch(() => ({}));
  await upsertUserPreferences(session.user.id, body);
  const prefs = await getUserPreferences(session.user.id);
  return NextResponse.json({ preferences: prefs });
}
