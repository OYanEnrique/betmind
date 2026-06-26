# BetMind

<p align="center">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="128" height="128">
    <defs>
      <!-- Calming Slate & Mint Gradient -->
      <linearGradient id="readme-mind-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#00e699" />
        <stop offset="100%" stop-color="#00b386" />
      </linearGradient>
    </defs>
    <!-- Outer Centering Circle Frame -->
    <circle cx="128" cy="128" r="112" fill="none" stroke="url(#readme-mind-grad)" stroke-width="8" stroke-linecap="round" />
    <!-- Stylized Brain Contour (Left Hemisphere) -->
    <path d="M 120,80 C 95,80 75,95 75,120 C 75,140 85,150 85,160 C 85,175 95,188 120,188" fill="none" stroke="url(#readme-mind-grad)" stroke-width="10" stroke-linecap="round" />
    <!-- Stylized Brain Contour (Right Hemisphere) -->
    <path d="M 136,80 C 161,80 181,95 181,120 C 181,140 171,150 171,160 C 171,175 161,188 136,188" fill="none" stroke="url(#readme-mind-grad)" stroke-width="10" stroke-linecap="round" />
    <!-- Core Mindfulness Wave inside Left Hemisphere -->
    <path d="M 95,120 C 105,110 115,130 120,120" fill="none" stroke="url(#readme-mind-grad)" stroke-width="6" stroke-linecap="round" opacity="0.8" />
    <!-- Core Mindfulness Wave inside Right Hemisphere -->
    <path d="M 161,120 C 151,110 141,130 136,120" fill="none" stroke="url(#readme-mind-grad)" stroke-width="6" stroke-linecap="round" opacity="0.8" />
    <!-- Center Diamond Spark of Focus/Concentration -->
    <path d="M 128,112 L 138,128 L 128,144 L 118,128 Z" fill="url(#readme-mind-grad)" />
  </svg>
</p>

<p align="center">
  <b>Um Agente de IA Baseado em Evidências e Cliente Minimalista para Redução de Danos em Apostas Esportivas e Controle de Impulsos.</b>
</p>

<p align="center">
  <a href="README.md">Read this README in English</a>
</p>

---

Desenvolvido por [Yan Enrique](https://github.com/OYanEnrique) como o Projeto Capstone para a competição **AI Agents: Intensive Vibe Coding Capstone Project** no Kaggle, sob a categoria **Agents for Good**.

---

## Visão e História do Projeto

As apostas esportivas passaram de uma atividade física para uma experiência digital instantânea e altamente gamificada. Com a popularização das casas de apostas móveis, o apostador pode fazer uma aposta em segundos, muitas vezes movido por distorções cognitivas ou impulsos emocionais agudos. Durante essas janelas críticas de vulnerabilidade (impulsos de jogo), as intervenções tradicionais, como números de telefone de suporte ou artigos estáticos, são passivas e não conseguem engajar o usuário.

O BetMind foi concebido para preencher essa lacuna como um acompanhante digital ativo, compassivo e clinicamente informado. Em vez de agir como um formulário estático, o BetMind é um parceiro de conversa que guia o usuário em momentos de crise em tempo real. Ele equilibra a versatilidade de conversação dos Grandes Modelos de Linguagem com limites programáticos de segurança aplicados para fornecer um ambiente seguro e estruturado para redução de danos comportamentais.

![Interface do Aplicativo BetMind](assets/screenshot_001.png)

---

## Contexto da Competição Capstone

Este projeto foi construído durante o curso de 5 dias **AI Agents: Intensive Vibe Coding Course With Google** no Kaggle e submetido como parte do capstone oficial:
- **Página do Curso**: [5-Day AI Agents Course Overview](https://www.kaggle.com/competitions/5-day-ai-agents-intensive-vibecoding-course-with-google/overview)
- **Página do Capstone**: [Kaggle Capstone Project Registry](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project)
- **Trilha/Categoria**: Agents for Good

---

## Funcionalidades do Sistema

O BetMind integra cinco módulos principais:

1. **Guia de Intervenção de Impulsos**: Gerenciamento ativo e compassivo de crises quando os usuários experimentam impulsos de aposta ativos.
2. **Técnicas de Distração Cognitiva**: Acesso direto a protocolos de respiração guiada (BREATHE478) e exercícios de ancoragem sensorial (DISTRACT5M) para redirecionar a atenção do usuário.
3. **Avaliação PGSI (Problem Gambling Severity Index)**: Uma implementação conversacional do questionário padrão de 9 itens do PGSI. O agente administra as perguntas uma a uma, calcula a pontuação final, determina o nível de gravidade (Jogador não problemático, Baixo risco, Médio risco ou Jogador compulsivo) e fornece um feedback clínico acolhedor e sem julgamentos.
4. **Rastreador de Resiliência**: Um ciclo gamificado de recompensas onde os usuários ganham Pontos de Resiliência (10 pontos para respiração, 20 pontos para ancoragem) após confirmarem programaticamente a conclusão de um exercício.
5. **Console Administrativo**: Uma interface que permite aos administradores do sistema ativar ou desativar protocolos de crise específicos em tempo real.

---

## Arquitetura Técnica e Limites de Segurança

O BetMind é projetado com uma divisão rígida de responsabilidades através de uma arquitetura cliente-servidor:

```
[ Frontend: HTML5/CSS3/JS ]  <---(REST / SSE)--->  [ Backend: FastAPI Server ]
- Interface Material Design 3                       - Agente em Google ADK
- Alternador de Temas (Claro/Escuro)                - Modelo Gemini 2.5 Flash
- Logotipo de Foco Mental em SVG                    - Banco de Dados de Sessão
- Loop de Atualização de Estado                     - Ferramentas Locais em Python
```

### 1. O Backend (Google ADK & FastAPI)
- **Google Agent Development Kit (ADK)**: Usado para definir o agente, instruções do sistema e bindings de ferramentas.
- **Modelo**: O `gemini-2.5-flash` atua como o motor cognitivo, gerando respostas e invocando ferramentas.
- **Limites de segurança programáticos**:
  - **Bloqueio de Registro**: Os usuários devem registrar um User ID no estado da sessão antes que a ferramenta `retrieve_intervention_exercise` permita o acesso aos exercícios.
  - **Toggles de Protocolo**: Apenas usuários com a função `"admin"` têm permissão para modificar os status dos protocolos via `update_protocol_status`.
  - **Aplicação de Desativação**: A ferramenta `retrieve_intervention_exercise` verifica o banco de dados da sessão e bloqueia qualquer protocolo desativado, retornando um erro estruturado para o agente.
  - **Log de Auditoria**: Intervenções bem-sucedidas chamam a ferramenta `process_session_resolution`, que salva os metadados da sessão no log de auditoria local e bloqueia o estado da sessão.

### 2. O Frontend (Material Design 3 Expressive)
- **Estética Minimalista**: Estilizado para caber exatamente no viewport do navegador (`100dvh`), removendo qualquer distração para manter o usuário concentrado.
- **Tema de Cores Calmas (Slate & Mint)**: Opções de modo escuro (fundo chumbo com detalhes em verde-menta) e modo claro (fundo cinza ardósia suave) para reduzir o cansaço visual.
- **Diagnósticos de Conexão**: Implementa uma verificação rápida usando chamadas com `mode: 'no-cors'` para verificar se o servidor está online.
- **Decodificador de Fluxo SSE**: Lê o fluxo de Server-Sent Events (SSE) caractere por caractere, acumulando dados parciais para exibição incremental em tempo real e corrigindo bugs de repetição.
- **Sincronização de Sessão**: Consulta o backend após cada turno de conversa para atualizar os pontos e os protocolos ativos.

---

## Instruções de Configuração e Execução Local

Para executar os servidores de backend e frontend do BetMind localmente em sua máquina, siga os passos abaixo:

### Pré-requisitos
- Python 3.12 ou superior.
- [Astral uv](https://github.com/astral-sh/uv) (gerenciador de pacotes Python).
- Uma chave de API válida do Gemini obtida no Google AI Studio.

### Passo 1: Configurar Ambiente do Backend
1. Navegue até a subpasta `betmind`:
   ```bash
   cd betmind
   ```
2. Crie um arquivo `.env` dentro da pasta `betmind` e adicione sua chave de API do Gemini:
   ```env
   GEMINI_API_KEY="sua-chave-api-do-gemini-aqui"
   ```

### Passo 2: Iniciar o Servidor do Backend
Inicie o servidor FastAPI na porta 8000. No Windows (PowerShell), habilite a permissão de origens cruzadas (CORS) para aceitar conexões vindas do frontend local:
```powershell
$env:ALLOW_ORIGINS="*"
uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000
```
Verifique se o servidor está rodando acessando `http://127.0.0.1:8000/health` no seu navegador.

### Passo 3: Iniciar o Servidor do Frontend
Abra um novo terminal na pasta raiz do projeto (`c:\Users\Yan Enrique\Documents\betmind`) e sirva os arquivos estáticos:
```bash
python -m http.server 3000
```
Abra o navegador e acesse `http://localhost:3000` para interagir com o aplicativo.

<div align="center">

<br>

**Autor do Projeto:** [Yan Enrique (OYanEnrique)](https://github.com/OYanEnrique)  
*(Cientista de Dados | Engenheiro de Machine Learning)*

</div>

---

## Licença

Este projeto é licenciado sob a Licença Apache 2.0.

```
Copyright 2026 Yan Enrique

Licenciado sob a Licença Apache, Versão 2.0 (a "Licença");
você não pode usar este arquivo exceto em conformidade com a Licença.
Você pode obter uma cópia da Licença em

    http://www.apache.org/licenses/LICENSE-2.0

A menos que exigido pela lei aplicável ou acordado por escrito, o software
distribuído sob a Licença é distribuído "NO ESTADO EM QUE SE ENCONTRA",
SEM GARANTIAS OU CONDIÇÕES DE QUALQUER TIPO, expressas ou implícitas.
Consulte a Licença para obter as permissões e limitações específicas sob a Licença.
```
