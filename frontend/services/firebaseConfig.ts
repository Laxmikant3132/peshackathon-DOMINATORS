import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

export const firebaseConfig = {
  apiKey: "AIzaSyD46hbkvc8_Oax6vQ1WXcH_2eVul30agoQ",
  authDomain: "peshackathon-f5f61.firebaseapp.com",
  projectId: "peshackathon-f5f61",
  storageBucket: "peshackathon-f5f61.firebasestorage.app",
  messagingSenderId: "711151271043",
  appId: "1:711151271043:web:bc9d7a1080f3eebd802fb6",
  measurementId: "G-4FXWFRKZBP"
};


// Initialize Firebase
const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

export { auth, db };
