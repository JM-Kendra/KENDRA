import type { Metadata } from "next";
import type { ReactNode } from "react";

import { gitCommit } from "@/lib/config";

import "./globals.css";

export const metadata: Metadata = {
  title: "Kendra | Local readiness",
  description: "Kendra local application foundation readiness",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        {children}
        <footer className="build-footer">Build {gitCommit()}</footer>
      </body>
    </html>
  );
}
