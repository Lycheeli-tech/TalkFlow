"use client";

import { MyEnglish } from "@/components/my-english";
import { AppShell, useAccessToken } from "@/components/app-entry";

export default function MyEnglishPage() {
  const token = useAccessToken();
  return <AppShell><MyEnglish token={token} /></AppShell>;
}
