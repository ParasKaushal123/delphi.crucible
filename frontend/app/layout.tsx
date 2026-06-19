import type { Metadata } from "next";
import "./globals.css";
import AnimatedBackground from "./components/AnimatedBackground";
import { WorkspaceProvider } from "./context/WorkspaceContext";
import NgrokBypass from "./components/NgrokBypass";

export const metadata: Metadata = {
  title: "The Delphi Crucible — Multi-Agent Investment Analysis",
  description:
    "A multi-agent AI investment analysis platform where AI agents debate stock picks in real-time. Generate institutional-grade investment memos with Bull/Bear debate and PM synthesis.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Outfit:wght@200..800&display=swap"
          rel="stylesheet"
        />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=settings" />
      </head>
      <body className="antialiased min-h-screen text-on-surface bg-[#1d1d1f] relative overflow-hidden">
        <NgrokBypass />
        {/* Background Gradients & Noise */}
        <AnimatedBackground />

        {/* Workspace Context Provider covers the whole app */}
        <WorkspaceProvider>
          {children}
        </WorkspaceProvider>
      </body>
    </html>
  );
}
