"use client";

import { JourneyMap } from "@/components/journey-map";
import { AppShell, useAccessToken } from "@/components/app-entry";

export default function JourneyPage() {
  const token = useAccessToken();
  return <AppShell><JourneyMap token={token} /></AppShell>;
}
