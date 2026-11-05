# Avisos de terceiros

Recursos de terceiros usados no protótipo e na arte gerada. **Qualquer recurso novo (fonte, ícone, imagem, biblioteca distribuída, música) tem de ser registado aqui antes de ser integrado**, com a licença e a forma de uso.

## Ícones

### Tabler Icons — MIT

- Origem: <https://tabler.io/icons> (pacote npm `@tabler/icons`).
- Uso: os caminhos SVG dos ícones usados estão copiados em `prototipo/icones.json` e são embutidos no HTML do convite.

```
MIT License

Copyright (c) 2020-2026 Paweł Kuna

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

O ícone `vestido` (definido em `prototipo/template.html`) é original deste projecto, desenhado no mesmo estilo.

## Fontes — SIL Open Font License 1.1

Todas as fontes estão sob a [SIL Open Font License 1.1](https://openfontlicense.org), que permite o uso comercial, a incorporação em páginas web e em imagens. Os ficheiros de fonte não podem ser vendidos isoladamente, e os nomes reservados não podem ser usados em versões modificadas. No convite, as fontes são carregadas do Google Fonts (protótipo) ou dos pacotes `@fontsource` (testes locais e pipeline de arte). O texto da licença acompanha cada pacote em `prototipo/node_modules/@fontsource/<fonte>/LICENSE` (depois de `npm install`).

| Fonte | Direitos de autor | Uso |
|---|---|---|
| Allura | Copyright 2010 The Allura Project Authors (https://github.com/googlefonts/allura) | Convite (manuscrito) |
| Cormorant SC | Copyright 2015 The Cormorant Project Authors (github.com/CatharsisFonts/Cormorant) | Convite (versaletes) |
| EB Garamond | Copyright 2017 The EB Garamond Project Authors (https://github.com/octaviopardo/EBGaramond12) | Convite (texto) |
| Cinzel | Copyright 2020 The Cinzel Project Authors (https://github.com/NDISCOVER/Cinzel) | Pipeline de arte: o «15» dourado das ilustrações (convertido em imagem) |
| Playfair Display | Copyright 2017 The Playfair Display Project Authors (https://github.com/clauseggers/Playfair-Display), com o nome reservado «Playfair Display» | Disponível no pipeline de arte (não usada nas imagens actuais) |

## Plataforma (`apps/web`)

| Biblioteca | Licença | Uso |
|---|---|---|
| Next.js | MIT | Servidor e aplicação. O código cliente vai para o navegador na zona de gestão. |
| React, React DOM | MIT | Interface da zona de gestão (o convite não usa React). |
| @vercel/blob | Apache-2.0 | Armazenamento, só no servidor. |
| TypeScript, tipos `@types/*` | Apache-2.0 / MIT | Só desenvolvimento. |

## Ferramentas de desenvolvimento (não distribuídas)

Usadas para construir, gerar arte e testar. Não fazem parte do convite publicado.

| Ferramenta | Licença |
|---|---|
| Playwright (Python) e Chromium | Apache-2.0 (Playwright). Chromium: licença BSD e componentes de terceiros |
| Pillow | MIT-CMU (HPND) |
| NumPy | BSD-3-Clause |
| jsonschema | MIT |

## Arte

Todas as imagens dos temas (`prototipo/temas/`) e as fotografias de exemplo da galeria do tema «Jardim Rosé» são **originais**: foram geradas por código neste repositório (`prototipo/arte/`). Não contêm personagens, marcas ou obras de terceiros.

## Inspiração de experiência

A experiência do convite (envelope animado, secções em ecrã inteiro, confirmação por WhatsApp) foi estudada a partir de um convite público em [convitesdigitais.ao](https://convitesdigitais.ao). **Nenhum código, imagem, texto ou outro recurso desse serviço foi copiado.** A implementação, a arte e os textos deste repositório foram criados de raiz.
