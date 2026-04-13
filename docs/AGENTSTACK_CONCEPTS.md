# AgentStack - Concetti Chiave per Sviluppatori

Questa guida copre i concetti essenziali per sviluppare agent efficaci con AgentStack.

## 1. 🏗️ Architettura AgentStack

### Stack Tecnologico
```
┌─────────────────────────────────────┐
│   Agent (Python/BeeAI Framework)   │
├─────────────────────────────────────┤
│   AgentStack SDK                    │
├─────────────────────────────────────┤
│   AgentStack Platform (Docker)      │
│   - API Server (FastAPI)            │
│   - PostgreSQL Database             │
│   - Redis Cache                     │
└─────────────────────────────────────┘
```

### Componenti Principali
1. **Agent**: Il tuo codice Python che usa BeeAI Framework
2. **AgentStack SDK**: Libreria per comunicare con la piattaforma
3. **AgentStack Platform**: Backend che gestisce conversazioni, memoria, autenticazione

## 2. 🔄 Gestione dello Stato della Conversazione

### Context e Task
```python
async def my_agent(
    input: Message,           # Messaggio corrente dell'utente
    context: RunContext,      # Contesto della conversazione
    ...
):
    # Salva il messaggio nel context
    await context.store(input)
```

**Concetti chiave**:
- **Context ID**: Identifica una conversazione unica
- **Task ID**: Identifica un'esecuzione specifica dell'agent
- **Message History**: Storico dei messaggi nella conversazione

### Come Funziona lo Stato
```
User Message 1 → Agent Response 1 → Context Store
                                          ↓
User Message 2 → Agent Response 2 → Context Store (append)
                                          ↓
User Message 3 → Agent Response 3 → Context Store (append)
```

**Nel nostro agent**:
```python
# src/k8s_admin_agent/agent.py
async def k8s_admin(input: Message, context: RunContext, ...):
    await context.store(input)  # Salva il messaggio corrente

    # Estrai il testo dal messaggio
    user_text = ""
    if input.parts:
        for part in input.parts:
            part_root = getattr(part, "root", None)
            if part_root is not None:
                text = getattr(part_root, "text", None)
                if text is not None:
                    user_text += text

    # Crea la history per l'agent
    history = [UserMessage(user_text)] if user_text else []
```

## 3. 🧠 Gestione della Memoria

### Tipi di Memoria in BeeAI Framework

1. **UnconstrainedMemory** (default)
   - Mantiene TUTTI i messaggi
   - Nessun limite di dimensione
   - Rischio: Context troppo grande

2. **SlidingMemory**
   - Mantiene solo gli ultimi N messaggi
   - Utile per conversazioni lunghe
   ```python
   from beeai_framework.memory import SlidingMemory

   agent = RequirementAgent(
       llm=llm,
       tools=tools,
       instructions=instructions,
       memory=SlidingMemory(max_messages=10)  # Solo ultimi 10 messaggi
   )
   ```

3. **TokenMemory**
   - Mantiene messaggi fino a un limite di token
   - Più preciso per gestire il context window
   ```python
   from beeai_framework.memory import TokenMemory

   agent = RequirementAgent(
       llm=llm,
       tools=tools,
       instructions=instructions,
       memory=TokenMemory(max_tokens=4000)  # Max 4000 token
   )
   ```

### Context Window Management

**Problema**: LLM hanno un limite di token (context window)
- GPT-4: 8K-128K token
- Ollama Qwen2.5-coder:14b: ~32K token

**Soluzione**: Shrink del contesto quando diventa troppo grande

```python
from beeai_framework.memory import TokenMemory

# Strategia 1: Sliding Window
memory = SlidingMemory(max_messages=20)

# Strategia 2: Token Limit
memory = TokenMemory(
    max_tokens=8000,  # Limite di token
    handler=lambda messages: messages[-10:]  # Mantieni ultimi 10 se supera
)

# Strategia 3: Summarization (custom)
class SummarizingMemory(BaseMemory):
    async def add(self, message: AnyMessage):
        if len(self.messages) > 20:
            # Riassumi i vecchi messaggi
            summary = await summarize_messages(self.messages[:10])
            self.messages = [summary] + self.messages[10:]
        self.messages.append(message)
```

## 4. 🔌 Integrazione con MCP Server

### Cos'è MCP (Model Context Protocol)
MCP è un protocollo per esporre tool/funzioni che l'agent può chiamare.

### Architettura MCP
```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Agent      │ ──────→ │  MCP Client  │ ──────→ │  MCP Server  │
│  (BeeAI)     │ ←────── │  (HTTP/SSE)  │ ←────── │  (FastAPI)   │
└──────────────┘         └──────────────┘         └──────────────┘
                                                           │
                                                           ↓
                                                   ┌──────────────┐
                                                   │  Kubernetes  │
                                                   │     API      │
                                                   └──────────────┘
```

### Implementazione MCP Tool

**Nel nostro agent**:
```python
# src/k8s_admin_agent/tools/k8s_mcp_tool.py
class K8sMCPTool(Tool):
    async def _run(self, input: K8sMCPToolInput, options, context):
        # 1. Connetti al MCP Server
        async with mcp.ClientSession(url, SSEServerTransport()) as session:
            # 2. Inizializza
            await session.initialize()

            # 3. Chiama il tool
            result = await session.call_tool(
                name=input.tool_name,
                arguments=input.arguments
            )

            return result
```

### Dynamic Tool Discovery
```python
async def get_available_tools(self):
    """Ottieni la lista dei tool disponibili dal MCP Server"""
    async with mcp.ClientSession(self.mcp_url, SSEServerTransport()) as session:
        await session.initialize()

        # Lista tutti i tool disponibili
        tools_result = await session.list_tools()
        return tools_result.tools
```

## 5. 📊 Entity Model e Database Schema

### Entità Principali

1. **Agent**
   - `id`: UUID dell'agent
   - `name`: Nome dell'agent
   - `description`: Descrizione
   - `skills`: Lista di skill disponibili

2. **Context**
   - `context_id`: UUID della conversazione
   - `agent_id`: Agent associato
   - `created_at`: Timestamp creazione
   - `metadata`: Dati aggiuntivi

3. **Task**
   - `task_id`: UUID del task
   - `context_id`: Context associato
   - `status`: running/completed/failed
   - `created_at`: Timestamp

4. **Message**
   - `message_id`: UUID del messaggio
   - `context_id`: Context associato
   - `role`: user/assistant/system
   - `content`: Contenuto del messaggio
   - `timestamp`: Quando è stato inviato

### Schema Database (PostgreSQL)

```sql
-- Agents
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    skills JSONB,
    created_at TIMESTAMP
);

-- Contexts (Conversazioni)
CREATE TABLE contexts (
    context_id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    metadata JSONB,
    created_at TIMESTAMP
);

-- Tasks (Esecuzioni)
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY,
    context_id UUID REFERENCES contexts(context_id),
    status VARCHAR(50),
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Messages (Storico)
CREATE TABLE messages (
    message_id UUID PRIMARY KEY,
    context_id UUID REFERENCES contexts(context_id),
    task_id UUID REFERENCES tasks(task_id),
    role VARCHAR(20),
    content JSONB,
    timestamp TIMESTAMP
);
```

## 6. 🔐 Autenticazione e Autorizzazione

### Platform Auth Backend
```python
from agentstack_sdk.server.middleware.platform_auth_backend import PlatformAuthBackend

server = Server(
    auth_backend=PlatformAuthBackend(),  # Gestisce auth con la piattaforma
    context_store=PlatformContextStore()  # Gestisce storage dei context
)
```

### Token JWT
- Ogni richiesta include un JWT token
- Il token contiene: user_id, agent_id, permissions
- Validato dal PlatformAuthBackend

## 7. 🎯 Extensions e Middleware

### Extensions Disponibili

1. **LLMServiceExtension**
   ```python
   llm_ext: Annotated[
       LLMServiceExtensionServer,
       LLMServiceExtensionSpec.single_demand()
   ]
   ```
   - Fornisce accesso al modello LLM configurato
   - Gestisce le credenziali API

2. **TrajectoryExtension**
   ```python
   trajectory: Annotated[
       TrajectoryExtensionServer,
       TrajectoryExtensionSpec()
   ]
   ```
   - Mostra il progresso dell'agent nella UI
   - Utile per debug e UX

3. **ErrorExtension**
   ```python
   _e: Annotated[
       ErrorExtensionServer,
       ErrorExtensionSpec(ErrorExtensionParams(include_stacktrace=True))
   ]
   ```
   - Gestisce gli errori in modo strutturato
   - Include stacktrace per debug

4. **PlatformApiExtension**
   ```python
   _p: Annotated[
       PlatformApiExtensionServer,
       PlatformApiExtensionSpec()
   ]
   ```
   - Accesso alle API della piattaforma
   - Gestione utenti, permessi, etc.

### Middleware
```python
from beeai_framework.middleware import GlobalTrajectoryMiddleware

agent = RequirementAgent(
    llm=llm,
    tools=tools,
    instructions=instructions,
    middlewares=[
        GlobalTrajectoryMiddleware(included=[Tool])  # Traccia l'uso dei tool
    ]
)
```

## 8. 🚀 Best Practices

### 1. Gestione Errori
```python
try:
    result = await tool.run(input)
except ToolError as e:
    logger.error(f"Tool error: {e}")
    yield trajectory.trajectory_metadata(
        title="Error",
        content=f"Failed to execute tool: {e}"
    )
```

### 2. Logging Strutturato
```python
from k8s_admin_agent.core import logger

logger.info("Starting agent execution")
logger.debug(f"Instructions: {instructions[:100]}...")
logger.error(f"Error occurred: {error}")
```

### 3. Sensitive Data Masking
```python
from k8s_admin_agent.core.log import mask_sensitive_data

masked = mask_sensitive_data(str(message))
logger.info(f"Message: {masked}")
```

### 4. Context Management
```python
# Sempre salvare i messaggi
await context.store(input)

# Usare memoria appropriata per il caso d'uso
memory = TokenMemory(max_tokens=8000)  # Per conversazioni lunghe
```

### 5. Tool Design
```python
class MyTool(Tool):
    name = "my_tool"
    description = "Clear, concise description"

    @property
    def input_schema(self):
        return MyToolInput  # Pydantic model con validazione

    async def _run(self, input, options, context):
        # Implementazione
        return result
```

## 9. 📚 Risorse Utili

### Documentazione
- AgentStack Docs: https://docs.agentstack.sh
- BeeAI Framework: https://github.com/i-am-bee/bee-agent-framework
- MCP Protocol: https://modelcontextprotocol.io

### API Swagger
- AgentStack Platform API: http://localhost:8333/docs
- Esplora gli endpoint disponibili
- Testa le API direttamente

### Comandi Utili
```bash
# Vedi i log della piattaforma
agentstack platform logs

# Restart della piattaforma
agentstack platform restart

# Vedi lo stato
agentstack platform status

# Debug dell'agent
agentstack run "Agent Name" "Test message" --debug
```

## 10. 🔍 Debugging

### Log Levels
```yaml
# config.yaml
logging:
  level: DEBUG  # INFO, DEBUG, WARNING, ERROR
  console: true
  file: logs/agent.log
```

### Inspect Context
```python
# Vedi il context corrente
logger.debug(f"Context ID: {context.context_id}")
logger.debug(f"Task ID: {context.task_id}")
logger.debug(f"Messages: {len(context.messages)}")
```

### Tool Execution Tracing
```python
# Usa GlobalTrajectoryMiddleware per vedere ogni tool call
middlewares=[GlobalTrajectoryMiddleware(included=[Tool])]
```

## Conclusione

I concetti chiave da padroneggiare sono:

1. ✅ **Context Management**: Come gestire lo stato della conversazione
2. ✅ **Memory Management**: Sliding window, token limits, summarization
3. ✅ **MCP Integration**: Come esporre e chiamare tool esterni
4. ✅ **Entity Model**: Agent, Context, Task, Message
5. ✅ **Extensions**: LLM, Trajectory, Error, Platform API
6. ✅ **Best Practices**: Logging, error handling, security

Con questi concetti puoi costruire agent robusti e scalabili con AgentStack!