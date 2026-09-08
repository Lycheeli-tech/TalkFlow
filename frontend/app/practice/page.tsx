"use client";

import { PracticeHub } from "@/components/practice-hub";
import { AppShell, useAccessToken } from "@/components/app-entry";

export default function PracticePage() {
  const token = useAccessToken();
  return <AppShell><PracticeHub token={token} /></AppShell>;
}
