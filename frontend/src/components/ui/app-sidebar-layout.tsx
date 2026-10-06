"use client";
import * as React from "react";
import { Sidebar, SidebarFooter, SidebarHeader, SidebarItem, SidebarNav, SidebarSection, SidebarToggle, useSidebar } from "@/components/ui/sidebar";
import { IconBriefcase, IconSettings, IconUserCircle, IconLogout, IconMail, IconRadar, IconLayoutDashboard } from "@tabler/icons-react";
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { logout as logoutAPI } from '@/lib/api';

function WorkspaceMark() {
  const { collapsed } = useSidebar();
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-blue-600 shadow-sm border border-blue-500">
        <div className="flex size-[22px] items-center justify-center rounded-[7px] bg-white/20 ring-1 ring-white/30 text-white font-bold text-[13px]">
          S
        </div>
      </div>
      {!collapsed && (
        <span className="truncate text-[15px] font-semibold leading-none text-slate-900 tracking-wide">
          Scanner
        </span>
      )}
    </div>
  );
}

function UserFooter() {
  const { collapsed } = useSidebar();
  const { user } = useAuth();
  return (
    <div className="flex items-center gap-2.5">
      {user?.avatar ? (
        <img
          src={user.avatar}
          alt=""
          className="size-7 shrink-0 rounded-full object-cover border border-slate-200"
        />
      ) : (
        <div className="size-7 shrink-0 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center">
          <IconUserCircle className="size-5 text-slate-400" />
        </div>
      )}
      {!collapsed && (
        <div className="min-w-0 flex-1">
          <div className="truncate text-[13px] font-medium leading-tight text-slate-800">
            {user?.name || 'Loading...'}
          </div>
          <div className="truncate text-[11px] leading-tight text-slate-500">
            {user?.email || ''}
          </div>
        </div>
      )}
    </div>
  );
}

export function AppSidebarLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  
  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#f4f4f5] text-slate-900">
      <Sidebar 
        variant="collapsible" 
        width={240} 
        aria-label="Main navigation"
        className="border-r border-black/[0.08] bg-white [&_[data-slot=sidebar-item][data-active]]:bg-slate-200/70 [&_[data-slot=sidebar-item][data-active]]:text-blue-700 [&_[data-slot=sidebar-item][data-active]_svg]:text-slate-900"
      >
        <SidebarHeader>
          <WorkspaceMark />
          <SidebarToggle className="ml-auto hover:bg-slate-100" />
        </SidebarHeader>
        <SidebarNav>
          <SidebarSection label="Dashboard">
            <SidebarItem
              icon={<IconBriefcase className="size-[18px]" stroke={1.75} />}
              active={pathname === '/jobs'}
              onClick={() => router.push('/jobs')}
            >
              Job Matches
            </SidebarItem>
            <SidebarItem
              icon={<IconRadar className="size-[18px]" stroke={1.75} />}
              active={pathname === '/scraping'}
              onClick={() => router.push('/scraping')}
            >
              Scan Status
            </SidebarItem>
            <SidebarItem
              icon={<IconMail className="size-[18px]" stroke={1.75} />}
              active={pathname === '/email'}
              onClick={() => router.push('/email')}
            >
              Cold Email
            </SidebarItem>
            <SidebarItem
              icon={<IconSettings className="size-[18px]" stroke={1.75} />}
              active={pathname === '/onboarding'}
              onClick={() => router.push('/onboarding')}
            >
              Edit Preferences
            </SidebarItem>
          </SidebarSection>
          
          <SidebarSection label="Account" className="mt-4">
            <SidebarItem
              icon={<IconLogout className="size-[18px]" stroke={1.75} />}
              onClick={async () => {
                try {
                  await logoutAPI();
                  router.push('/login');
                } catch (e) {
                  console.error(e);
                }
              }}
            >
              Sign out
            </SidebarItem>
          </SidebarSection>
        </SidebarNav>
        <SidebarFooter>
          <UserFooter />
        </SidebarFooter>
      </Sidebar>
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
