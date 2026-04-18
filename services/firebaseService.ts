import { initializeApp, deleteApp } from "firebase/app";
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  sendPasswordResetEmail,
  getAuth,
  type User
} from "firebase/auth";

import { 
  doc, 
  setDoc, 
  getDoc, 
  collection, 
  addDoc, 
  query, 
  where, 
  getDocs,
  orderBy,
  limit,
  Timestamp,
  serverTimestamp
} from "firebase/firestore";
import { auth, db, firebaseConfig } from "./firebaseConfig";

export interface UserProfile {
  uid: string;
  name: string;
  email: string;
  organization?: string;
  role: "user" | "employee" | "admin";
  adminKey?: string;
  createdAt: Timestamp;
}

const ADMIN_EMAIL = "laxmikanttalli303@gmail.com";
const VALID_ADMIN_KEY = "HF-ADMIN-2026"; // Mock valid admin key for employees
const ADMIN_PASSWORD = "talli@1234";



export const registerEmployee = async (name: string, email: string, pass: string, organization: string) => {
  const secondaryApp = initializeApp(firebaseConfig, "Secondary");
  const secondaryAuth = getAuth(secondaryApp);
  
  try {
    const userCredential = await createUserWithEmailAndPassword(secondaryAuth, email, pass);
    const user = userCredential.user;

    const userProfile: any = {
      uid: user.uid,
      name,
      email: user.email,
      organization,
      role: "employee",
      createdAt: serverTimestamp(),
    };

    await setDoc(doc(db, "users", user.uid), userProfile);
    await deleteApp(secondaryApp);
    return userProfile;
  } catch (error) {
    await deleteApp(secondaryApp);
    throw error;
  }
};

export const registerUser = async (name: string, email: string, pass: string, adminKey?: string) => {
  const userCredential = await createUserWithEmailAndPassword(auth, email, pass);
  const user = userCredential.user;

  let role: "user" | "employee" | "admin" = "user";
  
  if (email === ADMIN_EMAIL) {
    role = "admin";
  } else if (adminKey === VALID_ADMIN_KEY) {
    role = "employee";
  }

  const userProfile: any = {
    uid: user.uid,
    name,
    email: user.email,
    role,
    adminKey: adminKey || "",
    createdAt: serverTimestamp(),
  };

  await setDoc(doc(db, "users", user.uid), userProfile);
  return userProfile;
};

export const loginUser = async (email: string, pass: string) => {
  // Hardcoded Admin Bypass for development/testing
  if (email === ADMIN_EMAIL && pass === ADMIN_PASSWORD) {
    const adminProfile: UserProfile = {
      uid: "admin-id",
      name: "Admin",
      email: ADMIN_EMAIL,
      role: "admin",
      createdAt: Timestamp.now()
    };
    
    // Ensure the document exists in Firestore so tokens can be saved
    try {
      const adminRef = doc(db, "users", "admin-id");
      const adminSnap = await getDoc(adminRef);
      if (!adminSnap.exists()) {
        await setDoc(adminRef, adminProfile);
      }
    } catch (err) {
      console.error("Error ensuring admin firestore doc:", err);
    }
    
    if (typeof window !== "undefined") {
      localStorage.setItem("hf_admin_bypass", JSON.stringify(adminProfile));
    }
    
    return adminProfile;

  }

  const userCredential = await signInWithEmailAndPassword(auth, email, pass);


  const userDoc = await getDoc(doc(db, "users", userCredential.user.uid));
  const profile = userDoc.data() as UserProfile;
  if (typeof window !== "undefined") {
    localStorage.setItem("user_profile", JSON.stringify(profile));
  }
  return profile;
};

export const logoutUser = async () => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("hf_admin_bypass");
    localStorage.removeItem("user_profile");
  }
  await signOut(auth);
};

export const resetPassword = async (email: string) => {
  return await sendPasswordResetEmail(auth, email);
};

export const getUserProfile = async (uid: string) => {

  const userDoc = await getDoc(doc(db, "users", uid));
  return userDoc.exists() ? (userDoc.data() as UserProfile) : null;
};

// Firestore helper functions
export const saveEmailAnalysis = async (uid: string, analysis: any) => {
  return await addDoc(collection(db, "emails"), {
    user_uid: uid,
    ...analysis,
    timestamp: Timestamp.now()
  });
};

export const saveUPIAnalysis = async (uid: string, analysis: any) => {
  return await addDoc(collection(db, "upi_scans"), {
    user_uid: uid,
    ...analysis,
    timestamp: Timestamp.now()
  });
};

export const getEmailsByUserId = async (uid: string) => {
  const q = query(
    collection(db, "emails"), 
    where("user_uid", "==", uid),
    orderBy("timestamp", "desc")
  );
  const querySnapshot = await getDocs(q);
  return querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
};

export const saveUserAction = async (uid: string, action: any) => {
  return await addDoc(collection(db, "userActions"), {
    uid,
    ...action,
    timestamp: Timestamp.now()
  });
};
