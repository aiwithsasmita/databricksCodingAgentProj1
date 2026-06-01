import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NextGen Agentic Intelligence",
  description: "UnitedHealthcare · NextGen Agentic Intelligence · powered by Optum",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
