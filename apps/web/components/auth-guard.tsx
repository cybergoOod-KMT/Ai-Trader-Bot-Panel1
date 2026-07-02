"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import { normalizeError } from "@/lib/utils";
import { PageLoader } from "@/components/page-loader";

export function AuthGuard({
  children,
}: {
  children: (user: User) => React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .me()
      .then((result) => {
        if (!active) return;
        if (!result.authenticated || !result.user) {
          router.replace("/login");
          return;
        }
        if (result.user.force_password_change && pathname !== "/force-change-password") {
          router.replace("/force-change-password");
          return;
        }
        if (!result.user.force_password_change && pathname === "/force-change-password") {
          router.replace("/dashboard");
          return;
        }
        setUser(result.user);
      })
      .catch((err) => {
        if (!active) return;
        setError(normalizeError(err));
        router.replace("/login");
      });

    return () => {
      active = false;
    };
  }, [pathname, router]);

  if (!user) {
    return <PageLoader />;
  }

  if (error) {
    return <div className="text-sm text-rose-300">{error}</div>;
  }

  return <>{children(user)}</>;
}
