"use client";

import { useState } from "react";

import { PracticeHub } from "@/components/practice-hub";

export default function PracticePage() {
  const [token] = useState(() =>
    typeof window === "undefined" ? "" : sessionStorage.getItem("fluentloop_access_token") ?? "",
  );
  return <PracticeHub token={token} />;
}
