import { getGmailInbox, deleteGmailMessage, getGmailRawMessage } from '@/lib/gmail';
import { NextResponse } from 'next/server';
import { db } from '@/services/firebaseConfig';
import { collection, query, where, getDocs, deleteDoc } from 'firebase/firestore';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const uid = searchParams.get('uid');
  const messageId = searchParams.get('messageId');
  const raw = searchParams.get('raw');

  if (!uid) {
    return NextResponse.json({ error: 'User UID is required' }, { status: 400 });
  }

  // If specific message requested with raw=true, fetch full RFC 5322 EML
  if (messageId && raw === 'true') {
    try {
      const rawEml = await getGmailRawMessage(uid, messageId);
      return NextResponse.json({ raw_eml: rawEml, messageId });
    } catch (error: any) {
      console.error('Error fetching raw Gmail message:', error);
      return NextResponse.json({
        error: 'Failed to fetch raw message',
        message: error?.message || String(error)
      }, { status: 500 });
    }
  }

  try {
    const emails = await getGmailInbox(uid);
    await enrichWithForensics(uid, emails);
    return NextResponse.json(emails);
  } catch (error: any) {
    console.error('Error fetching Gmail inbox:', error);
    if (error.message === 'Gmail not connected') {
      return NextResponse.json({ error: 'Not authenticated with Gmail' }, { status: 401 });
    }
    return NextResponse.json({ 
      error: 'Failed to fetch emails', 
      message: error?.message || String(error),
      code: error?.code || null
    }, { status: 500 });
  }
}

/**
 * Near-real-time forensic triage integration: for each inbox message, POST its
 * observable headers/subject/snippet to the backend /api/email/auto-triage
 * pipeline (best-effort, fire-and-forget). High-risk results are surfaced as
 * `forensics` on the message and auto-create backend investigation cases.
 * This never fails the inbox request and is disabled unless
 * BACKEND_FORENSICS_URL is configured.
 */
async function enrichWithForensics(uid: string, emails: any[]) {
  const backendUrl = process.env.BACKEND_FORENSICS_URL;
  if (!backendUrl || !Array.isArray(emails) || emails.length === 0) return;

  const tasks = emails.slice(0, 20).map(async (email) => {
    try {
      const headers = Array.isArray(email?.payload?.headers)
        ? email.payload.headers.map((h: any) => ({ name: h.name, value: h.value }))
        : (email?.headers || []);
      const sender = email?.from || email?.sender || 'Unknown';
      const subject = email?.subject || '';
      const body = email?.snippet || '';
      const resp = await fetch(`${backendUrl}/api/email/auto-triage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uid, messageId: email?.id, sender, subject, body, headers }),
      });
      if (resp.ok) {
        const triage = await resp.json();
        if (triage?.high_risk) {
          email.forensics = {
            high_risk: true,
            score: triage.score,
            classification: triage.safety,
            case_id: triage.case_id,
            alert: triage.alert?.reason,
          };
        }
      }
    } catch (e) {
      // Best-effort integration: never block the inbox on forensics.
      console.error('Forensic triage skipped for message:', String(e));
    }
  });
  await Promise.allSettled(tasks);
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const uid = searchParams.get('uid');
  const messageId = searchParams.get('messageId');

  if (!uid || !messageId) {
    return NextResponse.json({ error: 'User UID and Message ID are required' }, { status: 400 });
  }

  try {
    // 1. Delete from Gmail (Trash)
    await deleteGmailMessage(uid, messageId);

    // 2. Delete from Firestore
    try {
      const emailQuery = query(
        collection(db, 'emails'),
        where('messageId', '==', messageId),
        where('user_uid', '==', uid)
      );
      const emailSnap = await getDocs(emailQuery);
      
      for (const doc of emailSnap.docs) {
        await deleteDoc(doc.ref);
      }
    } catch (fsError) {
      console.error('Error deleting from Firestore (continuing):', fsError);
      // We continue because the Gmail deletion (primary) succeeded
    }

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error('Error deleting email:', error);
    const status = error.message?.includes('Insufficient Permission') ? 403 : 500;
    return NextResponse.json({ 
      error: error.message || 'Failed to delete email',
      insufficient_scope: status === 403
    }, { status });
  }
}
