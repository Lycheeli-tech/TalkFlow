"use client";

import { useState } from "react";

import { PracticeHub } from "@/components/practice-hub";
import { AppShell } from "@/components/app-entry";

export default function PracticePage() {
  const [token] = useState(() =>
    typeof window === "undefined" ? "" : sessionStorage.getItem("fluentloop_access_token") ?? "",
  );
  return <AppShell><PracticeHub token={token} /></AppShell>;
}
