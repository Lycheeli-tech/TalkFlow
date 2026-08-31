"use client";

import { useEffect, useState } from "react";

import { API_BASE_URL } from "@/lib/api";

type Status = "checking" | "online" | "offline";

interface FoundationStatusProps {
  checkingLabel: string;
  onlineLabel: string;
  offlineLabel: string;
}

export function FoundationStatus({
  checkingLabel,
  onlineLabel,
  offlineLabel,
}: FoundationStatusProps) {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    const controller = new AbortController();

    async function checkApi() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
          signal: controller.signal,
        });
        setStatus(response.ok ? "online" : "offline");
      } catch {
        if (!controller.signal.aborted) {
          setStatus("offline");
        }
      }
    }

    void checkApi();
    return () => controller.abort();
  }, []);

  const labels: Record<Status, string> = {
    checking: checkingLabel,
    online: onlineLabel,
    offline: offlineLabel,
  };

  return (
    <div className="status-row" role="status" aria-live="polite">
      <span className="status-indicator" data-state={status} aria-hidden="true" />
      <span>{labels[status]}</span>
    </div>
  );
}
