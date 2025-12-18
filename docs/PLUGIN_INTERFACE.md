# Noxis — Plugin Interface (v0.1)

Este documento define o **contrato oficial de plugins** do Noxis (versão v0.1). O objetivo é garantir extensibilidade com **baixo acoplamento**, mantendo o Core livre de lógica específica de linguagem/stack.

> Regra: o Core **orquestra**; plugins **implementam** capacidades.

---

## 1. Conceitos

### 1.1 Plugin

Unidade de extensão do Noxis. Um plugin pode representar:

- Linguagem (Python, PHP, Lua)
- Stack (DevOps, Terraform)
- Ferramenta (Security scanning, SAST)

### 1.2 Capability

Uma ação que o plugin sabe executar em um `ProjectModel`.

Exemplos determinísticos:

- `lint`
- `test`
- `format`
- `build`
- `scan`
- `doctor`

Exemplos assistidos por IA (não obrigatórios no MVP):

- `ai_explain`
- `ai_tests`
- `ai_refactor`

### 1.3 Result

Saída padronizada retornada por qualquer capability executada.

---

## 2. Requisitos de Design

- **Determinismo por padrão**: capabilities determinísticas devem ser reprodutíveis.
- **Idempotência sempre que possível**: rodar duas vezes deve produzir o mesmo efeito.
- **Sem side-effects silenciosos**: nenhuma capability deve alterar o repositório sem que o Core peça explicitamente.
- **Erro explícito**: falhas retornam `Result` com `severity=error`.
- **Isolamento**: execução de ferramentas externas deve ocorrer via `Tools Adapters`.

---

## 3. Contratos (Interfaces)

### 3.1 Identidade e Metadata

Todo plugin deve expor:

- `id`: string única (ex.: `python`)
- `version`: versão do plugin (semântica)
- `display_name`: nome amigável
- `supported_languages`: lista de linguagens/labels

---

### 3.2 Detectabilidade

Plugins devem declarar se são aplicáveis a um projeto.

- `detect(project: ProjectModel) -> Applicability`

`Applicability` deve conter:

- `is_applicable: bool`
- `confidence: float` (0.0 a 1.0)
- `reasons: list[str]` (explicações curtas)
- `scope_hints: list[str]` (opcional — pastas/pacotes relevantes)

---

### 3.3 Capabilities

- `capabilities(project: ProjectModel) -> list[CapabilitySpec]`

`CapabilitySpec` contém:

- `name: str` (ex.: `lint`)
- `description: str`
- `kind: deterministic | ai`
- `default_enabled: bool`
- `inputs: dict` (schema simples para options)

---

### 3.4 Execução

- `run(request: ActionRequest) -> list[Result]`

`ActionRequest` contém:

- `capability: str`
- `project: ProjectModel`
- `options: dict`
- `artifacts: dict` (opcional: logs anteriores, outputs de ferramentas)
- `io`: interface controlada para leitura/escrita (ver seção 4)

---

## 4. Segurança e IO controlado

Para evitar que plugins mexam no repositório de forma silenciosa, v0.1 define um **IO controlado**.

### 4.1 Princípio

- Plugins podem **ler** livremente dentro do `root_path`.
- Escrita deve ocorrer apenas via:
  - diretório `.noxis/` (estado do Noxis)
  - output de artifacts (relatórios)
  - ou mediante pedido explícito do Core (futuro: patches)

### 4.2 Interface sugerida (v0.1)

O Core fornece um objeto `io` para operações:

- `read_text(path)`
- `list_files(glob)`
- `write_text(path, content)` **somente** em caminhos permitidos
- `temp_dir()`

(Implementação real fica no Core; o plugin não acessa `open()` diretamente.)

---

## 5. Dependências e Doctor

Plugins devem declarar dependências de tooling para `doctor`:

- `requirements(project) -> list[ToolRequirement]`

`ToolRequirement` contém:

- `name` (ex.: `ruff`)
- `kind` (`binary` | `python_module` | `container_image`)
- `version_spec` (opcional)
- `install_hint` (string curta com instrução)

O Core executa verificações via `Tools Adapters`.

---

## 6. Versionamento e Compatibilidade

- Esta especificação é **v0.1**.
- Mudanças incompatíveis exigem:
  - incremento de versão major
  - documentação de migração

---

## 7. Esqueleto de Interface (Python, ilustrativo)

> Este trecho é ilustrativo. A implementação concreta será feita na fase de código.

```python
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Applicability:
    is_applicable: bool
    confidence: float
    reasons: list[str]
    scope_hints: list[str] | None = None


@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    description: str
    kind: str  # "deterministic" | "ai"
    default_enabled: bool = True
    inputs: dict[str, Any] | None = None


@dataclass(frozen=True)
class ActionRequest:
    capability: str
    project: Any  # ProjectModel
    options: dict[str, Any]
    artifacts: dict[str, Any] | None = None
    io: Any | None = None


class Plugin(Protocol):
    id: str
    version: str
    display_name: str
    supported_languages: list[str]

    def detect(self, project: Any) -> Applicability: ...
    def capabilities(self, project: Any) -> list[CapabilitySpec]: ...
    def requirements(self, project: Any) -> list[Any]: ...
    def run(self, request: ActionRequest) -> list[Any]: ...
```

---

## 8. Exemplo de Capability Set (Python Plugin v0.1)

- `scan` (detecta presença de pyproject/requirements e estrutura)
- `doctor` (verifica `python`, `pip`, `ruff`, `pytest` quando aplicável)
- `lint` (executa `ruff` se configurado)
- `test` (executa `pytest` se existir suíte)
- `ai_explain` (explica falhas de lint/test com base em artifacts)

No MVP, podemos iniciar com `scan` + `doctor` + `ai_explain` e evoluir.

---

## 9. Conclusão

A interface v0.1 foi desenhada para:

- manter o Core simples
- permitir crescimento por plugins
- suportar IA sem acoplamento
- impor guardrails para segurança
