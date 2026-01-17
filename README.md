# Noxis

**Noxis** é um _engenheiro companheiro local-first_ para projetos de software. Ele combina ferramentas determinísticas (lint, test, build, security) com IA para auxiliar no desenvolvimento, sempre de forma **revisável, validável e explicável**.

Este README descreve **como instalar, configurar e rodar o sistema localmente**.

---

## 📦 Pré-requisitos

### Sistema

- Linux ou macOS (Windows via WSL2 recomendado)
- Git
- Python **3.11+**

### Ferramentas opcionais (detectadas via `doctor`)

Dependendo do projeto analisado:

- Docker
- Make
- Node.js
- PHP
- Lua
- Ferramentas de lint/test específicas da stack

> O Noxis **não exige** todas essas ferramentas — ele apenas utiliza o que for detectado no projeto.

---

## 📥 Instalação

### 1. Clone o repositório

```bash
git clone <repo-url>
cd noxis
```

### 2. Crie o ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

> Caso o projeto utilize `pyproject.toml`:

```bash
pip install -e .
```

---

## ⚙️ Configuração Inicial

### Estrutura gerada

Ao rodar o Noxis pela primeira vez, será criada a pasta:

```
.noxis/
 ├── config.yml
 ├── memory.yml
 └── cache/
```

- `config.yml` → preferências do projeto
- `memory.yml` → memória arquitetural e feedback
- `cache/` → dados descartáveis

---

## 🩺 Verificação do Ambiente

Antes de usar, execute:

```bash
noxis doctor
```

Isso irá:

- Verificar Python, plugins e ferramentas externas
- Validar versões
- Sugerir correções quando algo estiver ausente

---

## 🚀 Uso Básico

Todos os comandos devem ser executados **na raiz do projeto alvo**.

### Inicializar contexto

```bash
noxis scan
```

Detecta linguagens, ferramentas e estrutura do projeto.

---

### Lint

```bash
noxis lint
```

Executa linters disponíveis via plugins detectados.

---

### Testes

```bash
noxis test
```

Roda a suíte de testes existente do projeto.

---

### Geração de testes com IA

```bash
noxis ai tests
```

Fluxo:

1. Analisa o código existente
2. Gera propostas de testes
3. Executa os testes
4. Exibe relatório consolidado

Nenhum código é alterado sem aprovação explícita.

---

### Refatoração assistida

```bash
noxis ai refactor
```

Fluxo controlado:

- Plano explícito
- Patches pequenos
- Validação automática a cada passo

---

## 🧠 Princípios Importantes

- A IA **nunca altera código silenciosamente**
- Toda ação gera resultados estruturados
- Ferramentas determinísticas têm prioridade
- Tudo é reversível

---

## 🧩 Plugins

O Noxis funciona por **plugins**.

Exemplos:

- `python-plugin`
- `php-plugin`
- `lua-plugin`
- `devops-plugin`

Cada plugin declara _capabilities_ (`lint`, `test`, `build`, `ai_*`).

---

## 🧪 Execução em CI

O Noxis pode ser usado em pipelines:

```bash
noxis scan --format=json
```

Saídas estruturadas facilitam integração com CI/CD.

---

## 🛠️ Desenvolvimento do Noxis

### Rodar localmente em modo desenvolvimento

```bash
python -m noxis.cli.main <command>
```

Exemplo:

```bash
python -m noxis.cli.main scan
```

---

## 📚 Arquitetura

A arquitetura completa está documentada em:

- `ARCHITECTURE.md`

Recomenda-se a leitura para contribuir ou estender o sistema.

---

## 🤝 Contribuindo

- Código limpo e legível
- SOLID e separação de responsabilidades
- Patches pequenos e revisáveis
- Testes sempre que possível

---

## 📄 Licença

Definir conforme o projeto.

---

**Noxis não é um atalho.**
Ele é um parceiro técnico projetado para projetos que precisam viver por anos.
