"use client";

import { useState } from "react";

import { JourneyMap } from "@/components/journey-map";

export default function JourneyPage() {
  const [token] = useState(() =>
    typeof window === "undefined" ? "" : sessionStorage.getItem("fluentloop_access_token") ?? "",
  );
  return <JourneyMap token={token} />;
}
