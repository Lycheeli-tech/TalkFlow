import { FoundationStatus } from "@/components/foundation-status";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getMessages } from "@/lib/i18n";

export default function HomePage() {
  const messages = getMessages("en");

  return (
    <main className="page-shell">
      <section className="hero" aria-labelledby="foundation-title">
        <div className="eyebrow">{messages.foundation.eyebrow}</div>
        <h1 id="foundation-title">{messages.foundation.title}</h1>
        <p className="hero-copy">{messages.foundation.description}</p>
        <div className="hero-actions">
          <Button disabled>{messages.foundation.primaryAction}</Button>
          <span className="supporting-copy">{messages.foundation.actionHint}</span>
        </div>
      </section>

      <Card className="status-card">
        <FoundationStatus
          checkingLabel={messages.foundation.statusChecking}
          onlineLabel={messages.foundation.statusOnline}
          offlineLabel={messages.foundation.statusOffline}
        />
      </Card>
    </main>
  );
}

