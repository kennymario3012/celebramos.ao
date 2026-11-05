/** Configuração do convite: o contrato do renderizador (docs/04 §1, docs/esquemas/convite.schema.json). */
export interface ImagemTema {
  src: string;
  w: number;
  h: number;
}

export interface ConfiguracaoConvite {
  id: string;
  tipo?: string;
  demonstracao?: boolean;
  tema: {
    id: string;
    nome?: string;
    tokens: Record<string, string>;
    selo: { brilho: string; base: string; sombra: string; anel: string };
    imagens: {
      papel: string;
      canto: string;
      cantoAlt: string;
      grinalda: string;
      ilustracao: ImagemTema | string;
      mensagem: ImagemTema | string;
    };
  };
  seccoes?: string[];
  decoracao?: Record<string, string>;
  debutante: string;
  nomeCompleto?: string;
  monograma: string;
  tituloPagina: string;
  data: { iso: string; dia: number; mes: number; ano: number; diaSemana: string; hora: string };
  calendario: { titulo: string; inicioUTC: string; fimUTC: string; local: string; detalhes: string; ics?: string };
  confirmacao: { ate: string; nota: string; botoes: { rotulo: string; telefone: string }[]; mensagem: string };
  galeria: { subtitulo: string; fotos: { src: string; alt: string }[] };
  convidadoGenerico: string;
  convidadoDemonstracao?: string;
  convidados: Record<string, { nome: string; pessoas?: number }>;
  convidadoActual?: { nome: string; pessoas?: number };
  registo?: string;
  // restantes campos (textos e listas das secções) passam sem alteração para o template
  [campo: string]: unknown;
}

export interface PinGuardado {
  sal: string;
  hash: string;
}

/** Evento guardado na plataforma: a configuração do convite e os dados de gestão. */
export interface Evento {
  slug: string;
  configuracao: ConfiguracaoConvite;
  linkGeralActivo?: boolean;
  gestao?: {
    /** PIN de acesso da família à zona de gestão (scrypt). */
    pin?: PinGuardado;
    /** Mensagem por omissão para enviar o convite pelo WhatsApp. */
    mensagemEnvio?: string;
  };
}

export type EstadoConfirmacao = "pendente" | "confirmado" | "recusado";

export interface Convidado {
  /** 22 caracteres base64url (128 bits): identifica o convidado e faz parte do link pessoal. */
  token: string;
  nome: string;
  pessoas: number;
  telefone?: string;
  grupo?: string;
  notas?: string;
  estado: EstadoConfirmacao;
  pessoasConfirmadas?: number;
  enviadoEm?: string;
  criadoEm: string;
  actualizadoEm: string;
}

export interface ListaConvidados {
  versao: 1;
  mensagemEnvio?: string;
  convidados: Convidado[];
}

export interface Actividade {
  aberturas: number;
  abertoEm?: string;
  ultimaAberturaEm?: string;
  confirmarEm?: string;
}
