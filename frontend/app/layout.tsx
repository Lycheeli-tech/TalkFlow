import type { Metadata } from "next";
import type { ReactNode } from "react";

import { InterfaceLocaleProvider } from "@/components/interface-locale-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "FluentLoop",
  description: "Turn what you know into what you can say.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body><InterfaceLocaleProvider>{children}</InterfaceLocaleProvider></body>
    </html>
  );
}
