"use client";

import { useState } from "react";

import { MyEnglish } from "@/components/my-english";
import { AppShell } from "@/components/app-entry";
import { getMessages, getStoredLocale } from "@/lib/i18n";

export default function MyEnglishPage() {
  const [token] = useState(() =>
    typeof window === "undefined" ? "" : sessionStorage.getItem("fluentloop_access_token") ?? "",
  );
  return <AppShell labels={getMessages(getStoredLocale()).navigation}><MyEnglish token={token} /></AppShell>;
}
