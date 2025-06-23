'use client';
import { useEffect } from 'react';
import { signInWithPopup } from 'firebase/auth';
import { auth, provider } from '../lib/firebase';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();

  const handleLogin = async () => {
    try {
      const result = await signInWithPopup(auth, provider);
      const user = result.user;

      await fetch('http://localhost:8000/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uid: user.uid,
          email: user.email,
          name: user.displayName,
        }),
      });

      router.push(`/thread-list?uid=${user.uid}`);
    } catch (error) {
      console.error('ログイン失敗', error);
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <h1>Chat Appへようこそ</h1>
      <button onClick={handleLogin} style={{ padding: '1rem 2rem', backgroundColor: '#4CAF50', color: 'white', borderRadius: '8px' }}>
        Googleでログイン
      </button>
    </div>
  );
}