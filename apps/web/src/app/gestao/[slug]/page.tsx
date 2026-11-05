import type { Metadata } from "next";
import Gestao from "./Gestao";

export const metadata: Metadata = {
  title: "Gestão de convidados",
  robots: { index: false, follow: false },
};

export default async function Pagina({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <Gestao slug={slug} />;
}
