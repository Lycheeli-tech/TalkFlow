"use client";

import { useState } from "react";

import { JourneyMap } from "@/components/journey-map";
import { AppShell } from "@/components/app-entry";
import { getMessages, getStoredLocale } from "@/lib/i18n";

export default function JourneyPage() {
  const [token] = useState(() =>
    typeof window === "undefined" ? "" : sessionStorage.getItem("fluentloop_access_token") ?? "",
  );
  return <AppShell labels={getMessages(getStoredLocale()).navigation}><JourneyMap token={token} /></AppShell>;
}
