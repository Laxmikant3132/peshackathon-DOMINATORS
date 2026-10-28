import { oauth2Client } from '@/lib/googleAuth';
import { NextResponse } from 'next/server';
import { db } from '@/services/firebaseConfig';
import { doc, updateDoc } from 'firebase/firestore';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');
  const uid = searchParams.get('state'); // UID passed as state

  if (!code || !uid) {
    return NextResponse.redirect(new URL('/inbox?error=missing_params', request.url));
  }

  try {
    const { tokens } = await oauth2Client.getToken(code);
    
    // Store tokens in Firestore PER USER
    const userRef = doc(db, 'users', uid);
    await updateDoc(userRef, {
      gmail_access_token: tokens.access_token,
      gmail_refresh_token: tokens.refresh_token || null,
      gmail_token_expiry: tokens.expiry_date || null,
    });

    return NextResponse.redirect(new URL('/inbox?success=gmail_connected', request.url));
  } catch (error) {
    console.error('Error exchanging code for tokens:', error);
    return NextResponse.redirect(new URL('/inbox?error=token_exchange_failed', request.url));
  }
}
