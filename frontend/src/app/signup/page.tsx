'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" aria-hidden>
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1Z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23Z" />
      <path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 0 1 0-4.2V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84Z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06L5.84 9.9C6.71 7.31 9.14 5.38 12 5.38Z" />
    </svg>
  )
}

const proof = [
  { initials: 'JD', src: 'https://cdn.21st.dev/assets/mirror/86/8699bcf7115ba5cf371e7804acbfb1cd93f09fa1124b315685e5f1bb6a098507.jpg' },
  { initials: 'MK', src: 'https://cdn.21st.dev/assets/mirror/ad/ade85b97e2f191d13489861a366b539d9fe63a902c85dda70870494ed94cc745.jpg' },
  { initials: 'AR', src: 'https://cdn.21st.dev/assets/mirror/70/70436f1dfb4838c62f26c292e1046b6293b843bf2f60d888d8624211075572af.jpg' },
]

export default function SignupPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Redirect if already logged in
  useEffect(() => {
    if (!loading && user) {
      router.replace(user.onboarding_done ? '/jobs' : '/onboarding');
    }
  }, [user, loading, router]);

  const handleEmailSignup = (e: React.FormEvent) => {
    e.preventDefault();
    alert("Email registration is currently disabled in this demo. Please use the Google Sign-up.");
  };

  return (
    <main className="flex min-h-svh w-full items-center justify-center p-6 bg-slate-50 relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-blue-50/80 via-white to-blue-100/50 -z-10" />
      <div className="absolute -top-40 -right-40 w-96 h-96 bg-blue-400/20 rounded-full blur-[100px] -z-10" />
      <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-600/10 rounded-full blur-[100px] -z-10" />

      <div className="w-full max-w-4xl relative z-10">
        <Card className="grid w-full gap-0 p-0 md:grid-cols-2 overflow-hidden border-slate-100 shadow-2xl rounded-[2rem]">
          <div className="bg-gradient-to-br from-blue-600 to-blue-800 text-white relative hidden flex-col justify-between overflow-hidden p-10 md:flex">
            <div className="bg-white/10 pointer-events-none absolute -top-24 -right-24 size-64 rounded-full blur-3xl" />

            <div className="relative flex items-center gap-2.5">
              <div className="bg-white/15 ring-white/25 flex size-8 items-center justify-center rounded-lg ring-1">
                <div className="text-white font-bold text-sm">S</div>
              </div>
              <span className="text-sm font-semibold tracking-tight">Startive</span>
            </div>

            <h2 className="relative mt-auto max-w-[15ch] text-[32px] leading-[1.15] font-semibold tracking-tight text-balance">
              Where teams finance together.
            </h2>

            <div className="relative mt-8 flex items-center gap-3">
              <div className="flex -space-x-2.5">
                {proof.map((p) => (
                  <Avatar key={p.initials} className="ring-blue-600 size-8 ring-2">
                    <AvatarImage src={p.src} alt="" className="object-cover" />
                    <AvatarFallback className="bg-white text-blue-600 text-[10px] font-medium">{p.initials}</AvatarFallback>
                  </Avatar>
                ))}
              </div>
              <span className="text-white/90 text-xs font-medium">Join 40,000+ teams on Startive</span>
            </div>
          </div>

          <div className="flex flex-col justify-center gap-5 p-8 sm:p-12 bg-white">
            <div className="flex flex-col gap-1">
              <span className="text-2xl font-semibold text-slate-900">Create an account</span>
              <span className="text-slate-500 text-sm">Join Startive to automate your financial operations.</span>
            </div>

            <a
              href={`${API}/auth/google/login`}
              className="w-full flex items-center justify-center gap-3 bg-white text-slate-700 font-medium px-4 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 hover:border-slate-300 transition-all duration-200 shadow-sm h-11"
            >
              <GoogleIcon />
              Continue with Google
            </a>

            <div className="flex items-center gap-3">
              <span className="bg-slate-200 h-px flex-1" />
              <span className="text-slate-400 text-[11px] uppercase font-medium">or</span>
              <span className="bg-slate-200 h-px flex-1" />
            </div>

            <form onSubmit={handleEmailSignup} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="su-name" className="text-xs font-medium text-slate-700">Full Name</Label>
                <Input id="su-name" type="text" required value={name} onChange={e => setName(e.target.value)} placeholder="Jane Doe" className="h-11 shadow-sm" />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="su-email" className="text-xs font-medium text-slate-700">Email</Label>
                <Input id="su-email" type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@startive.com" autoComplete="email" className="h-11 shadow-sm" />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="su-password" className="text-xs font-medium text-slate-700">Password</Label>
                <Input id="su-password" type="password" required value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" autoComplete="new-password" className="h-11 shadow-sm" />
              </div>

              <Button type="submit" className="w-full h-11 bg-slate-900 hover:bg-slate-800 mt-2 text-white">Sign up</Button>
            </form>

            <p className="text-slate-500 text-center text-xs mt-2">
              Already have an account?{' '}
              <Link href="/login" className="text-blue-600 font-medium hover:underline">Sign in</Link>
            </p>
          </div>
        </Card>
      </div>
    </main>
  );
}
