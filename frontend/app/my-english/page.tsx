"use client";

import { useState } from "react";

import { MyEnglish } from "@/components/my-english";

export default function MyEnglishPage() {
  const [token] = useState(() =>
    typeof window === "undefined" ? "" : sessionStorage.getItem("fluentloop_access_token") ?? "",
  );
  return <MyEnglish token={token} />;
}
