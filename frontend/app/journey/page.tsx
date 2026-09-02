"use client";

import { useState } from "react";

import { JourneyMap } from "@/components/journey-map";
import { AppShell } from "@/components/app-entry";

export default function JourneyPage() {
  const [token] = useState(() =>
    typeof window === "undefined" ? "" : sessionStorage.getItem("fluentloop_access_token") ?? "",
  );
  return <AppShell><JourneyMap token={token} /></AppShell>;
}
