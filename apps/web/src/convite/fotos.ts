/**
 * Fotos da galeria de um evento: <CELEBRAMOS_DADOS>/eventos/<slug>/img/<ficheiro>.
 * As rotas só as servem a quem pode ver o convite (link geral activo ou token válido) e, em qualquer
 * falha, devolvem o mesmo 404 do convite, para não revelar o que existe.
 */
import { naoEncontrado } from "./respostas";
import { armazenamento } from "@/lib/armazenamento";

/** Só um nome de ficheiro de imagem: sem pastas, sem «..» e sem ficheiros escondidos. */
const NOME_FOTO = /^[A-Za-z0-9][A-Za-z0-9._-]{0,99}\.(webp|jpe?g|png|avif)$/i;
const TIPOS: Record<string, string> = {
  webp: "image/webp",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  avif: "image/avif",
};

const caminhoFoto = (slug: string, ficheiro: string) => `eventos/${slug}/img/${ficheiro}`;

export async function responderFoto(req: Request, slug: string, ficheiro: string): Promise<Response> {
  const extensao = NOME_FOTO.exec(ficheiro)?.[1].toLowerCase();
  if (!extensao) return naoEncontrado();
  const lido = await armazenamento().lerFicheiro(caminhoFoto(slug, ficheiro));
  if (!lido) return naoEncontrado();
  const cabecalhos = {
    "Content-Type": TIPOS[extensao],
    // privada: a cache do NGINX no cPanel não a guarda, por isso a regra de acesso vale em cada pedido
    "Cache-Control": "private, max-age=3600",
    ETag: lido.etag,
    "X-Robots-Tag": "noindex, nofollow",
    "X-Content-Type-Options": "nosniff",
  };
  if (req.headers.get("if-none-match") === lido.etag) return new Response(null, { status: 304, headers: cabecalhos });
  return new Response(new Uint8Array(lido.dados), { headers: cabecalhos });
}
