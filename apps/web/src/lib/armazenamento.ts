/**
 * Armazenamento de dados da plataforma: documentos JSON em ficheiros, numa pasta fora da aplicação
 * (CELEBRAMOS_DADOS, ex.: /home/celebramos/celebramos-dados no cPanel).
 *
 * Escrita condicional por ETag (concorrência optimista) e bloqueio entre processos: o Passenger
 * do cPanel pode correr vários processos da aplicação ao mesmo tempo.
 * Outros destinos (S3, base de dados) podem implementar a mesma interface.
 */
import crypto from "node:crypto";
import { promises as fs } from "node:fs";
import path from "node:path";

export class ConflitoEscrita extends Error {
  constructor() {
    super("O registo foi alterado entretanto (conflito de escrita).");
  }
}

export interface Leitura<T> {
  dados: T;
  etag: string;
}

export interface ItemListado {
  caminho: string;
  criadoEm: Date;
}

export interface Armazenamento {
  lerJSON<T>(caminho: string): Promise<Leitura<T> | null>;
  /** Escreve só se o ETag coincidir (`etag`) ou se ainda não existir (`criar`). Senão: ConflitoEscrita. */
  escreverJSON(caminho: string, dados: unknown, condicao: { etag?: string; criar?: boolean }): Promise<void>;
  /** Cria um marcador vazio com sufixo aleatório (registos só de acrescentar). */
  criarMarcador(caminho: string): Promise<void>;
  listar(prefixo: string): Promise<ItemListado[]>;
}

/** Pasta dos dados. Em produção é obrigatória e tem de ficar fora da pasta da aplicação (sobrevive às actualizações). */
function raiz() {
  const definida = process.env.CELEBRAMOS_DADOS;
  if (definida) return path.resolve(/*turbopackIgnore: true*/ definida);
  if (process.env.NODE_ENV === "production") {
    throw new Error("Definir CELEBRAMOS_DADOS: a pasta dos dados, fora da pasta da aplicação.");
  }
  return path.join(/*turbopackIgnore: true*/ process.cwd(), ".dados-locais");
}

function seguro(caminho: string) {
  const base = raiz();
  const alvo = path.resolve(/*turbopackIgnore: true*/ base, caminho);
  if (!alvo.startsWith(base + path.sep)) throw new Error("caminho inválido");
  return alvo;
}

const etagDe = (texto: string) => '"' + crypto.createHash("sha1").update(texto).digest("hex") + '"';
const esperar = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Fila por ficheiro dentro do mesmo processo (evita esperas activas entre pedidos do mesmo processo). */
const filas = new Map<string, Promise<void>>();
async function emExclusivo<T>(chave: string, fn: () => Promise<T>): Promise<T> {
  const anterior = filas.get(chave) ?? Promise.resolve();
  let libertar!: () => void;
  const minha = anterior.then(() => new Promise<void>((r) => (libertar = r)));
  filas.set(chave, minha);
  await anterior;
  try {
    return await fn();
  } finally {
    libertar();
    if (filas.get(chave) === minha) filas.delete(chave);
  }
}

/**
 * Bloqueio entre processos: criar uma pasta é atómico. Um bloqueio com mais de 10 s
 * (processo que morreu a meio) é considerado abandonado e removido.
 */
async function comBloqueio<T>(alvo: string, fn: () => Promise<T>): Promise<T> {
  const bloqueio = `${alvo}.bloqueio`;
  const inicio = Date.now();
  await fs.mkdir(/*turbopackIgnore: true*/ path.dirname(alvo), { recursive: true });
  for (;;) {
    try {
      await fs.mkdir(/*turbopackIgnore: true*/ bloqueio);
      break;
    } catch (e) {
      if ((e as NodeJS.ErrnoException).code !== "EEXIST") throw e;
      try {
        const info = await fs.stat(/*turbopackIgnore: true*/ bloqueio);
        if (Date.now() - info.mtimeMs > 10_000) {
          await fs.rmdir(/*turbopackIgnore: true*/ bloqueio).catch(() => {});
          continue;
        }
      } catch {
        continue; // desapareceu entretanto: tentar outra vez
      }
      if (Date.now() - inicio > 15_000) throw new Error("O armazenamento está ocupado. Tente outra vez.");
      await esperar(15 + Math.random() * 35);
    }
  }
  try {
    return await fn();
  } finally {
    await fs.rmdir(/*turbopackIgnore: true*/ bloqueio).catch(() => {});
  }
}

const ficheiros: Armazenamento = {
  async lerJSON<T>(caminho: string) {
    try {
      const texto = await fs.readFile(/*turbopackIgnore: true*/ seguro(caminho), "utf8");
      return { dados: JSON.parse(texto) as T, etag: etagDe(texto) };
    } catch (e) {
      if ((e as NodeJS.ErrnoException).code === "ENOENT") return null;
      throw e;
    }
  },

  async escreverJSON(caminho, dados, condicao) {
    const alvo = seguro(caminho);
    await emExclusivo(alvo, () =>
      comBloqueio(alvo, async () => {
        const actual = await ficheiros.lerJSON(caminho);
        if (condicao.criar && actual) throw new ConflitoEscrita();
        if (!condicao.criar && condicao.etag && actual?.etag !== condicao.etag) throw new ConflitoEscrita();
        // escrever num temporário e mudar o nome: quem lê nunca vê um ficheiro a meio
        const temporario = `${alvo}.${crypto.randomBytes(6).toString("hex")}.tmp`;
        await fs.writeFile(/*turbopackIgnore: true*/ temporario, JSON.stringify(dados));
        await fs.rename(/*turbopackIgnore: true*/ temporario, alvo);
      }),
    );
  },

  async criarMarcador(caminho) {
    const alvo = seguro(`${caminho}-${crypto.randomBytes(8).toString("base64url")}`);
    await fs.mkdir(/*turbopackIgnore: true*/ path.dirname(alvo), { recursive: true });
    await fs.writeFile(/*turbopackIgnore: true*/ alvo, "1");
  },

  async listar(prefixo) {
    const base = raiz();
    const itens: ItemListado[] = [];
    async function percorrer(pasta: string) {
      let entradas;
      try {
        entradas = await fs.readdir(/*turbopackIgnore: true*/ pasta, { withFileTypes: true });
      } catch {
        return;
      }
      for (const e of entradas) {
        const completo = path.join(/*turbopackIgnore: true*/ pasta, e.name);
        if (e.isDirectory()) {
          if (!e.name.endsWith(".bloqueio")) await percorrer(completo);
        } else if (!e.name.endsWith(".tmp")) {
          const relativo = path.relative(base, completo).split(path.sep).join("/");
          if (relativo.startsWith(prefixo)) itens.push({ caminho: relativo, criadoEm: (await fs.stat(/*turbopackIgnore: true*/ completo)).mtime });
        }
      }
    }
    // começa na pasta mais funda que o prefixo garante
    await percorrer(path.join(/*turbopackIgnore: true*/ base, prefixo.slice(0, prefixo.lastIndexOf("/") + 1)));
    return itens;
  },
};

export function armazenamento(): Armazenamento {
  return ficheiros;
}
