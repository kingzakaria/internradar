import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "InternRadar — Find your next opportunity",
  description: "Discover internships that match your goals and your next big idea.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
