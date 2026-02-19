# BookAI - Project Structure

## Repository Layout

```mermaid
graph TD
    ROOT["📁 BookAI (root)"]

    ROOT --> CLAUDE["📄 CLAUDE.md\nProject instructions"]
    ROOT --> BRAIN["📄 BRAINSTROMING.md\nProject vision notes"]
    ROOT --> NB["📓 ia.ipynb\nExploration notebook"]
    ROOT --> MCP_S["🐍 mcp_search_server.py\nMCP search server"]
    ROOT --> CSV["📄 best sellin books total.csv\nMerged dataset"]

    ROOT --> ARCHIVE["📁 archive/\nRaw yearly CSVs"]
    ARCHIVE --> CSV23["best sellin books 2023.csv"]
    ARCHIVE --> CSV24["best sellin books 2024.csv"]
    ARCHIVE --> CSV25["best sellin books 2025.csv"]

    ROOT --> SPECS["📁 specs/\nFeature specifications"]
    SPECS --> F001["📁 001-book-recommendations/"]
    F001 --> SPEC["spec.md"]
    F001 --> CHECK["📁 checklists/requirements.md"]
    SPECS --> SMAIN["📁 main/\nplan.md"]

    ROOT --> SPECIFY["📁 .specify/\nSpeckit system"]
    SPECIFY --> MEM["📁 memory/constitution.md"]
    SPECIFY --> TMPL["📁 templates/\n6 feature templates"]
    SPECIFY --> SCRIPTS["📁 scripts/powershell/\n5 automation scripts"]

    ROOT --> DOTCLAUDE["📁 .claude/\nClaude Code config"]
    DOTCLAUDE --> CMDS["📁 commands/\n9 speckit skills"]
    DOTCLAUDE --> SETTINGS["settings.local.json"]

    ROOT --> MCPJSON["📄 .mcp.json\nMCP servers config"]
```

---

## MCP Server Architecture

```mermaid
graph LR
    CC["Claude Code\n(AI Agent)"]

    CC --> MCP1["MCP: book-search\nmcp_search_server.py"]
    CC --> MCP2["MCP: serena\nSemantic code tools"]

    MCP1 --> TOOL1["search_books\nTF-IDF + cosine similarity"]
    MCP1 --> TOOL2["get_book_description\nFuzzy match + Google Books API"]

    TOOL1 --> DF["📊 DataFrame\nbest sellin books total.csv\n~deduplicated catalog"]
    TOOL2 --> DF
    TOOL2 --> GBOOKS["🌐 Google Books API\nOnline descriptions"]

    MCP2 --> CODE["📁 Codebase\nSymbol-level editing"]
```

---

## Speckit Development Workflow

```mermaid
flowchart LR
    A["/speckit.specify\nFeature description"] --> B["specs/###/spec.md\nUser stories + acceptance criteria"]
    B --> C["/speckit.clarify\nTargeted Q&A"]
    C --> D["/speckit.plan\nDesign artifacts"]
    D --> E["spec.md · plan.md\nresearch.md · data-model.md"]
    E --> F["/speckit.tasks\ntasks.md"]
    F --> G["/speckit.implement\nTDD cycle"]
    G --> H["✅ Feature complete"]

    style A fill:#4a90d9,color:#fff
    style H fill:#27ae60,color:#fff
```

---

## Feature 001 - Book Recommendations

```mermaid
graph TD
    USER["👤 User"]
    USER -->|"natural language query"| SEARCH["search_books\nTF-IDF semantic search"]
    USER -->|"book title"| DESC["get_book_description\nFuzzy title match"]

    SEARCH -->|"top-k results"| RANK["Ranked catalog results\n(relevance score)"]
    DESC -->|"catalog info + online desc"| INFO["Book details\n+ Google Books description"]

    RANK --> USER
    INFO --> USER

    subgraph "MCP Server (mcp_search_server.py)"
        SEARCH
        DESC
        CORPUS["Corpus builder\nname + author + genre + age + format"]
        TFIDF["TF-IDF Vectorizer\n+ cosine similarity"]
        FUZZY["difflib fuzzy matcher\n(close title options)"]
        SEARCH --> CORPUS --> TFIDF
        DESC --> FUZZY
    end
```

---

## Constitution Principles

```mermaid
mindmap
  root((BookAI\nConstitution v1.0.0))
    Modular Architecture
      Independent components
      Composable libraries
      Shared utilities
    TDD NON-NEGOTIABLE
      Red-Green-Refactor
      Tests before code
      80%+ coverage
    Responsible AI
      Validate all LLM outputs
      Bias audits
      Graceful fallbacks
    Performance First
      Searches under 200ms
      Recommendations under 1s
      Chatbot under 3s
    Observability
      Structured JSON logs
      LLM call tracing
      Cost tracking
    Simplicity YAGNI
      MVP first
      No premature abstraction
      Readable over clever
```
