import type { MetadataRoute } from "next";

// /c/ não é bloqueado: o WhatsApp precisa de ler os metadados para a pré-visualização (as páginas levam noindex).
export default function robots(): MetadataRoute.Robots {
  return { rules: [{ userAgent: "*", disallow: ["/gestao/", "/api/"] }] };
}
