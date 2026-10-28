import { oauth2Client, SCOPES } from '@/lib/googleAuth';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const uid = searchParams.get('uid');

  if (!uid) {
    return NextResponse.json({ error: 'User UID is required' }, { status: 400 });
  }

  const url = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent',
    state: uid, // Pass UID as state to retrieve it in the callback
  });

  return NextResponse.redirect(url);
}
