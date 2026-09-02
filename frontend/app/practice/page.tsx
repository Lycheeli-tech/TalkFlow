"use client";

import { useState } from "react";

import { PracticeHub } from "@/components/practice-hub";
import { AppShell } from "@/components/app-entry";
import { getMessages, getStoredLocale } from "@/lib/i18n";

export default function PracticePage() {
  const [token] = useState(() =>
    typeof window === "undefined" ? "" : sessionStorage.getItem("fluentloop_access_token") ?? "",
  );
  return <AppShell labels={getMessages(getStoredLocale()).navigation}><PracticeHub token={token} /></AppShell>;
}
