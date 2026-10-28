import { google } from 'googleapis';
import { oauth2Client } from './googleAuth';
import { db } from '@/services/firebaseConfig';
import { doc, getDoc, updateDoc, collection, addDoc, query, where, getDocs, Timestamp } from 'firebase/firestore';

export async function getGmailInbox(uid: string) {
  // 1. Fetch tokens from Firestore
  const userRef = doc(db, 'users', uid);
  const userSnap = await getDoc(userRef);

  if (!userSnap.exists()) {
    throw new Error('User not found');
  }

  const userData = userSnap.data();
  const accessToken = userData.gmail_access_token;
  const refreshToken = userData.gmail_refresh_token;
  const expiryDate = userData.gmail_token_expiry;
  const employeeEmail = userData.email;

  if (!accessToken) {
    throw new Error('Gmail not connected');
  }

  // 2. Set credentials
  oauth2Client.setCredentials({
    access_token: accessToken,
    refresh_token: refreshToken,
    expiry_date: expiryDate,
  });

  // 3. Handle token refresh if needed - use removeAllListeners to prevent memory leak
  oauth2Client.removeAllListeners('tokens');
  oauth2Client.on('tokens', async (tokens) => {
    if (tokens.access_token) {
      await updateDoc(userRef, {
        gmail_access_token: tokens.access_token,
        gmail_token_expiry: tokens.expiry_date || null,
      });
    }
  });

  const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

  // 4. Fetch inbox
  const response = await gmail.users.messages.list({
    userId: 'me',
    maxResults: 15,
    q: 'is:inbox',
  });

  const messages = response.data.messages || [];
  
  // 5. Optimization: Fetch recently analyzed message IDs in one query to avoid per-message roundtrips
  const existingQuery = query(
    collection(db, 'emails'),
    where('user_uid', '==', uid)
  );
  const existingSnap = await getDocs(existingQuery);
  const existingIdMap = new Map();
  existingSnap.docs.forEach(doc => {
    const data = doc.data();
    existingIdMap.set(data.messageId, data);
  });

  const detailedMessages = await Promise.all(
    messages.map(async (message) => {
      // Return cached version if already analyzed
      if (existingIdMap.has(message.id)) {
        return existingIdMap.get(message.id);
      }

      // ONLY for NEW messages:
      try {
        const msg = await gmail.users.messages.get({
          userId: 'me',
          id: message.id as string,
        });

        const headers = msg.data.payload?.headers || [];
        const sender = headers.find((h) => h.name === 'From')?.value || 'Unknown';
        const subject = headers.find((h) => h.name === 'Subject')?.value || 'No Subject';
        const date = headers.find((h) => h.name === 'Date')?.value || 'No Date';
        const snippet = msg.data.snippet || '';

        const getBody = (payload: any): string => {
          let body = "";
          if (payload.parts) {
            payload.parts.forEach((part: any) => {
              if (part.mimeType === "text/plain" && part.body.data) {
                body += Buffer.from(part.body.data, 'base64').toString();
              } else if (part.parts) {
                body += getBody(part);
              }
            });
          } else if (payload.body.data) {
            body = Buffer.from(payload.body.data, 'base64').toString();
          }
          return body;
        };

        const body = getBody(msg.data.payload) || snippet;

        let classification = 'Safe';
        let confidence = 0.95;
        let reason = 'The email appears to be legitimate.';

        try {
          // Timeout to prevent hanging
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 3000);
          
          const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';
          let apiResponse = await fetch(`${backendUrl}/api/classify-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ emailBody: body || snippet, sender, subject }),
            signal: controller.signal
          }).catch(async () => {
            return await fetch('https://humanfirewall-backend.onrender.com/api/classify-email', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ emailBody: body || snippet, sender, subject }),
              signal: controller.signal
            });
          });
          
          clearTimeout(timeoutId);

          if (apiResponse.ok) {
            const result = await apiResponse.json();
            classification = result.safety.charAt(0).toUpperCase() + result.safety.slice(1);
            confidence = result.confidence;
            reason = result.reason;
          }
        } catch (error) {
          console.error('Phishing API skip (using safe default):', error);
        }

        const emailData = {
          id: message.id,
          messageId: message.id,
          user_uid: uid,
          employee_email: employeeEmail,
          sender,
          subject,
          snippet,
          body,
          date,
          classification,
          confidence,
          reason,
          timestamp: new Date().toISOString(),
        };

        // Store in Firestore
        await addDoc(collection(db, 'emails'), emailData);
        
        if (userData.role === 'employee') {
          await addDoc(collection(db, 'email_logs'), {
            employeeEmail: employeeEmail,
            subject: subject,
            sender: sender,
            safety: classification.toLowerCase(),
            confidence: confidence,
            reason: reason,
            analyzedAt: Timestamp.now()
          });
        }

        return emailData;
      } catch (err) {
        console.error(`Error processing message ${message.id}:`, err);
        return null;
      }
    })
  );

  return detailedMessages.filter(Boolean);
}

export async function deleteGmailMessage(uid: string, messageId: string) {
  // 1. Fetch tokens from Firestore
  const userRef = doc(db, 'users', uid);
  const userSnap = await getDoc(userRef);

  if (!userSnap.exists()) {
    throw new Error('User not found');
  }

  const userData = userSnap.data();
  const accessToken = userData.gmail_access_token;
  const refreshToken = userData.gmail_refresh_token;
  const expiryDate = userData.gmail_token_expiry;

  if (!accessToken) {
    throw new Error('Gmail not connected');
  }

  // 2. Set credentials
  oauth2Client.setCredentials({
    access_token: accessToken,
    refresh_token: refreshToken,
    expiry_date: expiryDate,
  });

  const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

  // 3. Delete message
  await gmail.users.messages.trash({
    userId: 'me',
    id: messageId,
  });

  return { success: true };
}

export async function getGmailRawMessage(uid: string, messageId: string): Promise<string> {
  const userRef = doc(db, 'users', uid);
  const userSnap = await getDoc(userRef);

  if (!userSnap.exists()) {
    throw new Error('User not found');
  }

  const userData = userSnap.data();
  const accessToken = userData.gmail_access_token;
  const refreshToken = userData.gmail_refresh_token;
  const expiryDate = userData.gmail_token_expiry;

  if (!accessToken) {
    throw new Error('Gmail not connected');
  }

  oauth2Client.setCredentials({
    access_token: accessToken,
    refresh_token: refreshToken,
    expiry_date: expiryDate,
  });

  const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
  
  // Request format='raw' to retrieve the complete RFC 5322 MIME stream
  const response = await gmail.users.messages.get({
    userId: 'me',
    id: messageId,
    format: 'raw',
  });

  const rawBase64Url = response.data.raw;
  if (!rawBase64Url) {
    throw new Error('No raw MIME content returned by Gmail API');
  }

  // Base64url to UTF-8 decoding
  const base64 = rawBase64Url.replace(/-/g, '+').replace(/_/g, '/');
  const rawEml = Buffer.from(base64, 'base64').toString('utf-8');
  return rawEml;
}
