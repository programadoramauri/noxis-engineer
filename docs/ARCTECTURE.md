# Noxis — Architecture Overview

## 1. Visão Geral

O **Noxis** é um **engenheiro companheiro local-first**, projetado para auxiliar na criação, manutenção e evolução de projetos de software escritos em múltiplas linguagens.

Ele combina **ferramentas determinísticas** (lint, test, build, security) com **inteligência artificial** para propor código, gerar testes, sugerir refatorações e explicar problemas — sempre de forma **explicável, revisável e validável**.

> Princípio central: **a IA nunca substitui a verdade das ferramentas**; ela complementa com heurística e criatividade.

---

## 2. Objetivos Arquiteturais

- Local-first e rápido
- Modular e extensível por plugins
- Baixo acoplamento e alta coesão
- Seguro por padrão (guardrails explícitos)
- Determinístico sempre que possível
- Aprendizado contínuo via memória e feedback

---

## 3. Visão em Camadas

```
CLI
 └── Core Orchestrator
      ├── Context Engine
      ├── Plugin Manager
      ├── Tools Adapters
      ├── Rules & Policies
      ├── AI Augmentation Layer
      └── Storage
```

Cada camada tem responsabilidades bem definidas e se comunica por **contratos explícitos**.

---

## 4. Camadas e Componentes

### 4.1 CLI (Interface)

Responsável por:

- Receber comandos (`init`, `scan`, `doctor`, `lint`, `test`, `fix`, `ai`)
- Validar entrada do usuário
- Exibir resultados em modo humano ou estruturado (CI)

A CLI **não executa lógica de domínio**; ela apenas aciona o Core.

---

### 4.2 Core Orchestrator

Coordena toda a execução do sistema.

Responsabilidades:

- Roteamento de comandos → pipelines
- Execução paralela e incremental
- Aplicação de políticas antes/depois das ações
- Consolidação de resultados

Subcomponentes:

- **Command Router**
- **Execution Engine**
- **Result Aggregator**
- **Policy Gate**

---

### 4.3 Context Engine

Produz o **ProjectModel**, a representação canônica do projeto.

Detecta:

- Linguagens e frameworks
- Estrutura do repositório (mono ou single)
- Ferramentas existentes (CI, Docker, lockfiles)
- Convenções e policies

Saída:

- `ProjectModel`
- `Capabilities`

---

### 4.4 Plugin Manager

Gerencia plugins como unidades de extensão.

Responsabilidades:

- Descobrir e carregar plugins
- Validar compatibilidade
- Expor capabilities implementadas

O Core **não conhece linguagens**, apenas plugins.

---

### 4.5 Plugins

Cada plugin representa uma linguagem ou stack.

Características:

- Detecta aplicabilidade no `ProjectModel`
- Declara capabilities (`lint`, `test`, `build`, `ai_*`, etc.)
- Executa ações via adapters

Exemplos:

- `python-plugin`
- `php-plugin`
- `lua-plugin`
- `devops-plugin`

---

### 4.6 Tools Adapters

Isolam ferramentas externas.

Responsabilidades:

- Executar binários ou containers
- Normalizar saída e erros
- Verificar instalação e versões (`doctor`)

Permitem trocar ferramentas sem impactar o Core.

---

### 4.7 AI Augmentation Layer

Camada responsável por uso controlado de IA.

Componentes:

- **AI Context Builder**: constrói contexto enxuto e relevante
- **Intent Engine**: traduz pedidos em intenções técnicas
- **Strategy Engine**: define abordagem (plano, patch, geração incremental)
- **LLM Provider Adapter**: abstrai o backend de IA
- **Output Normalizer**: converte respostas em propostas concretas

A IA:

- Nunca altera código silenciosamente
- Sempre gera propostas revisáveis (diff)
- Sempre passa por validação automática

---

### 4.8 Storage

#### Cache (descartável)

- Baseado em hash de arquivos e configurações
- Otimiza performance

#### Memória do Projeto (persistente)

- Decisões arquiteturais
- Preferências do projeto
- Histórico de propostas (aceitas/rejeitadas)
- Resultados de validações

Armazenamento recomendado:

- SQLite (histórico e telemetria local)
- YAML versionado em `.noxis/`

---

## 5. Contratos Internos

### 5.1 ProjectModel

Representa o estado do projeto:

- `root_path`
- `repo_type`
- `languages_detected[]`
- `packages[]`
- `tooling`
- `policies_ref`

---

### 5.2 Result Schema

Todas as execuções produzem `Result`:

- `type` (lint, test, build, security, ai)
- `severity` (info, warn, error)
- `file`, `line`, `col`
- `tool` + versão
- `message`
- `remediation`
- `timing`, `cache_hit`

---

### 5.3 ProposedChange

Toda saída da IA vira uma proposta explícita:

- `diff` ou arquivos novos
- `rationale`
- `risk`
- `validation_plan`
- `policy_notes`

---

## 6. Fluxos Principais

### scan

Context → plugins → ferramentas → relatório consolidado.

### doctor

Verificação de tooling e dependências → guia de correção.

### fix

Correções determinísticas seguras → revalidação.

### ai tests

Geração de testes → execução → relatório.

### ai refactor

Plano → patches pequenos → validação contínua.

---

## 7. Aprendizado Contínuo

O Noxis aprende como **sistema**, não como modelo treinado:

- Memória do projeto (RAG local)
- Feedback explícito do usuário
- Resultados reais de validação automática

Isso melhora sugestões futuras mantendo previsibilidade.

---

## 8. Princípios Não-Negociáveis

- IA apenas propõe, nunca impõe
- Tudo é revisável e reversível
- Ferramentas determinísticas têm prioridade
- Plugins são a unidade de evolução
- Pensamento de longo prazo

---

## 9. Conclusão

Esta arquitetura foi desenhada para evoluir por **extensão**, não por reescrita. O Noxis deve se comportar como um engenheiro sênior: cuidadoso, rápido, opinativo e responsável.
