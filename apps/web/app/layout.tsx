import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hive Strategy",
  description: "Let a hive of AI agents stress-test your idea",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
