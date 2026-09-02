"use client";

import { useState } from "react";

import { MyEnglish } from "@/components/my-english";
import { AppShell } from "@/components/app-entry";

export default function MyEnglishPage() {
  const [token] = useState(() =>
    typeof window === "undefined" ? "" : sessionStorage.getItem("fluentloop_access_token") ?? "",
  );
  return <AppShell><MyEnglish token={token} /></AppShell>;
}
