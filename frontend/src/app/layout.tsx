import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { DataProvider } from "@/context/DataContext";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Gastor | Trading Analysis Platform",
  description: "Plataforma de análise de trading com estratégias automatizadas e validação FTMO",
  keywords: ["trading", "crypto", "bitcoin", "estratégias", "backtest", "FTMO"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="dark">
      <body className={`${inter.variable} font-sans bg-slate-950 text-slate-100 antialiased`}>
        <DataProvider>
          <Navbar />
          <main className="min-h-screen">
            {children}
          </main>
        </DataProvider>
      </body>
    </html>
  );
}
