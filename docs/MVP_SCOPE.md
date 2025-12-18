# Noxis — MVP Scope (v0.1)

## 1. Objetivo do MVP

O MVP do **Noxis** tem como objetivo entregar um **engenheiro companheiro funcional e utilizável no dia a dia**, mantendo total alinhamento com a arquitetura final do sistema.

Este MVP não é descartável. Todo código aqui produzido deve ser **evolutivo**, testável e compatível com futuras extensões.

---

## 2. Princípios do MVP

- Utilidade imediata
- Arquitetura já definitiva
- Escopo intencionalmente limitado
- Nenhuma automação destrutiva
- IA apenas como assistente explicativo

---

## 3. Funcionalidades Incluídas

### 3.1 CLI

Comandos suportados:

- `noxis init`
- `noxis scan`
- `noxis doctor`
- `noxis ai explain`

A CLI deve ser rápida, clara e previsível.

---

### 3.2 Context Engine (v0)

Capacidades mínimas:

- Detectar linguagens principais do repositório
- Identificar estrutura básica (mono ou single repo)
- Identificar presença de ferramentas comuns (ex.: requirements.txt, pyproject.toml)

Produz obrigatoriamente um `ProjectModel` válido.

---

### 3.3 Plugin System (v0)

- Interface de plugin definida e estável
- Carregamento dinâmico de plugins
- **1 plugin real implementado** (Python)

O Core não deve conter nenhuma lógica específica de linguagem.

---

### 3.4 Análise Determinística

- O comando `scan` executa ao menos uma análise real
- Resultados são normalizados em `Result`
- Saída humana e estruturada (JSON)

---

### 3.5 AI Layer (v0)

Funcionalidade suportada:

- `ai explain`

A IA deve:

- Explicar erros reais
- Analisar estrutura do projeto
- Sugerir melhorias conceituais

A IA **não deve**:

- Gerar ou alterar código
- Aplicar patches

---

### 3.6 Storage (v0)

- Diretório `.noxis/` criado no `init`
- Arquivos:
  - `project.yml`
  - `policies.yml`

- SQLite local para:
  - histórico de execuções
  - histórico de respostas da IA

---

## 4. Funcionalidades Explicitamente Fora do MVP

- Geração automática de código
- Refatoração com patches
- Execução silenciosa de mudanças
- Múltiplos plugins avançados
- Fine-tuning de modelos

Essas funcionalidades fazem parte do roadmap, não do MVP.

---

## 5. Critérios de Aceite do MVP

O MVP é considerado completo quando:

- É possível rodar `noxis init` em um repositório vazio
- `noxis scan` detecta corretamente o projeto
- `noxis doctor` aponta dependências ausentes
- `noxis ai explain` fornece explicações úteis e contextuais
- O próprio repositório do Noxis pode ser analisado pelo Noxis

---

## 6. Postura de Evolução

Após o MVP:

- O escopo é congelado
- Melhorias são feitas via incrementos pequenos
- O Noxis passa a ser usado para evoluir o Noxis

---

## 7. Versão

- MVP Version: **0.1**
- Status: **Em definição / implementação**
