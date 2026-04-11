import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuantForge — Trading Strategy Stress Testing",
  description:
    "Describe a trading strategy in plain English. QuantForge generates 200 plausible market histories and shows whether your strategy is robust or just lucky.",
};

export default function RootLayout({
  children,
}: {
  readonly children: React.ReactNode;
}): JSX.Element {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-bg font-sans text-white antialiased">
        <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
      </body>
    </html>
  );
}
