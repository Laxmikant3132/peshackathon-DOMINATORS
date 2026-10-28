import { db } from '@/services/firebaseConfig';
import { collection, getDocs, query, where, orderBy } from 'firebase/firestore';
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // 1. Fetch employees from the users collection where role == "employee"
    const usersRef = collection(db, 'users');
    const employeeQuery = query(usersRef, where('role', '==', 'employee'));
    const employeeSnap = await getDocs(employeeQuery);

    // 2. Collect their UID values
    const employeeIds = new Set<string>();
    const employeeMap: Record<string, { name: string; email: string }> = {};
    
    employeeSnap.forEach((doc) => {
      const data = doc.data();
      employeeIds.add(doc.id);
      employeeMap[doc.id] = {
        name: data.name || 'Unknown',
        email: data.email || 'No Email'
      };
    });

    if (employeeIds.size === 0) {
      return NextResponse.json({
        stats: { totalEmails: 0, safeCount: 0, suspiciousCount: 0, dangerousCount: 0 },
        emails: [],
        employees: [],
      });
    }

    // 3. Fetch emails from the "email_logs" collection
    const emailLogsRef = collection(db, 'email_logs');
    const emailQuery = query(emailLogsRef, orderBy('analyzedAt', 'desc'));
    const emailSnap = await getDocs(emailQuery);

    const filteredEmails: any[] = [];
    let totalEmails = 0;
    let safeCount = 0;
    let suspiciousCount = 0;
    let dangerousCount = 0;

    const employeeStatsMap: Record<string, { scans: number; dangerousCount: number }> = {};

    emailSnap.forEach((doc) => {
      const data = doc.data();
      
      const analyzedAt = data.analyzedAt instanceof Object && 'toDate' in data.analyzedAt 
        ? data.analyzedAt.toDate().toISOString() 
        : new Date(data.analyzedAt).toISOString();

      const email = {
        id: doc.id,
        ...data,
        analyzedAt,
      };
      filteredEmails.push(email);

      // 5. Calculate metrics
      totalEmails++;
      const safety = data.safety?.toLowerCase();
      if (safety === 'safe') safeCount++;
      else if (safety === 'suspicious') suspiciousCount++;
      else if (safety === 'dangerous') dangerousCount++;

      // Track individual employee performance
      const empEmail = data.employeeEmail;
      if (empEmail) {
        if (!employeeStatsMap[empEmail]) {
          employeeStatsMap[empEmail] = { scans: 0, dangerousCount: 0 };
        }
        employeeStatsMap[empEmail].scans++;
        if (safety === 'dangerous') {
          employeeStatsMap[empEmail].dangerousCount++;
        }
      }
    });

    const employeesList = Object.values(employeeMap).map((info) => {
      const stats = employeeStatsMap[info.email] || { scans: 0, dangerousCount: 0 };

      let riskLevel = 'Low';
      if (stats.dangerousCount >= 3) riskLevel = 'High';
      else if (stats.dangerousCount >= 1) riskLevel = 'Medium';

      return {
        name: info.name,
        email: info.email,
        scans: stats.scans,
        risk: riskLevel,
        dangerousCount: stats.dangerousCount
      };
    });

    return NextResponse.json({
      stats: {
        totalEmails,
        safeCount,
        suspiciousCount,
        dangerousCount,
      },
      emails: filteredEmails.slice(0, 50),
      employees: employeesList,
    });
  } catch (error) {
    console.error('Error fetching admin stats:', error);
    return NextResponse.json({ error: 'Failed to fetch admin stats' }, { status: 500 });
  }
}
