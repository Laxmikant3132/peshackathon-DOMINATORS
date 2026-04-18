import { getGmailInbox, deleteGmailMessage } from '@/lib/gmail';
import { NextResponse } from 'next/server';
import { db } from '@/services/firebaseConfig';
import { collection, query, where, getDocs, deleteDoc } from 'firebase/firestore';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const uid = searchParams.get('uid');

  if (!uid) {
    return NextResponse.json({ error: 'User UID is required' }, { status: 400 });
  }

  try {
    const emails = await getGmailInbox(uid);
    return NextResponse.json(emails);
  } catch (error: any) {
    console.error('Error fetching Gmail inbox:', error);
    if (error.message === 'Gmail not connected') {
      return NextResponse.json({ error: 'Not authenticated with Gmail' }, { status: 401 });
    }
    return NextResponse.json({ error: 'Failed to fetch emails' }, { status: 500 });
  }
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
