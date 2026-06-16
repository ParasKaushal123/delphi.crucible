import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Investment Memo Bench — Multi-Agent Analysis powered by Band.ai",
  description:
    "A multi-agent investment analysis platform where AI agents debate stock picks in real-time using Band.ai's multi-room architecture. Generate institutional-grade investment memos with Bull/Bear debate and PM synthesis.",
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
