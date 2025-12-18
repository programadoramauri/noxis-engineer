# Noxis — Project Structure

Este documento define a **estrutura oficial do repositório do Noxis**. Ela reflete diretamente a arquitetura do sistema e foi desenhada para **não precisar ser refeita** conforme o projeto evolui.

Cada diretório existe por um motivo claro. Não há pastas genéricas ou provisórias.

---

## 1. Visão Geral da Estrutura

```
noxis/
├── cli/
│   └── main.py
│
├── core/
│   ├── orchestrator.py
│   ├── execution.py
│   ├── results.py
│   └── policies.py
│
├── context/
│   ├── discovery.py
│   └── model.py
│
├── plugins/
│   ├── base.py
│   └── python/
│       └── plugin.py
│
├── adapters/
│   └── tools/
│       └── base.py
│
├── ai/
│   ├── context_builder.py
│   ├── explain.py
│   └── provider.py
│
├── storage/
│   ├── memory.py
│   └── cache.py
│
├── policies/
│   └── defaults.yml
│
├── .noxis/
│   ├── project.yml
│   └── policies.yml
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── MVP_SCOPE.md
│
├── tests/
│
└── pyproject.toml
```

---

## 2. Diretórios e Responsabilidades

### `cli/`

**Interface do sistema.**

Responsabilidades:

- Parse de comandos e argumentos
- Chamada do Core
- Formatação de saída

Não contém lógica de negócio.

---

### `core/`

**Coração do Noxis.** Coordena todo o fluxo.

Componentes:

- `orchestrator.py`: coordenação de pipelines
- `execution.py`: execução paralela/incremental
- `results.py`: normalização e agregação de resultados
- `policies.py`: aplicação de regras e guardrails

---

### `context/`

Responsável por entender o projeto analisado.

Componentes:

- `discovery.py`: inspeção do filesystem e configs
- `model.py`: definição do `ProjectModel`

---

### `plugins/`

Unidade de extensão do sistema.

- `base.py`: contrato base de plugin
- Cada subdiretório representa uma linguagem ou stack

Exemplo inicial:

- `python/plugin.py`

---

### `adapters/`

Isolamento de integrações externas.

- `tools/`: execução e parsing de ferramentas
- `base.py`: contrato comum de adapters

---

### `ai/`

Camada de IA (augmentação cognitiva).

Componentes:

- `context_builder.py`: seleção de contexto relevante
- `explain.py`: lógica do `ai explain`
- `provider.py`: abstração do backend de IA

---

### `storage/`

Persistência local.

Componentes:

- `memory.py`: memória do projeto (SQLite)
- `cache.py`: cache por hash

---

### `policies/`

Policies padrão do sistema.

- `defaults.yml`: regras globais

---

### `.noxis/`

Estado do projeto analisado.

- `project.yml`: informações descobertas
- `policies.yml`: overrides do projeto

Este diretório é criado pelo comando `noxis init`.

---

### `docs/`

Documentação viva do projeto.

Inclui:

- Arquitetura
- Escopo do MVP

---

### `tests/`

Testes automatizados do próprio Noxis.

---

## 3. Princípios da Estrutura

- Cada diretório mapeia diretamente uma camada arquitetural
- Nenhuma pasta é genérica
- Plugins são isolados
- IA não invade o Core
- Evolução ocorre por adição, não por refatoração estrutural

---

## 4. Estabilidade

Esta estrutura é considerada **estável a partir do MVP**.

Mudanças estruturais só devem ocorrer se:

- Um novo eixo arquitetural surgir
- Houver justificativa documentada

---

## 5. Conclusão

Esta estrutura permite que o Noxis cresça como um sistema vivo, mantendo clareza, previsibilidade e manutenibilidade ao longo do tempo.
