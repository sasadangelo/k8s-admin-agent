# AgentStack API Endpoints

This document describes the main entities and endpoints available in the AgentStack API.

## Base URL

```
http://localhost:8333/api/v1
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8333/api/v1/docs
- ReDoc: http://localhost:8333/api/v1/redoc

## Entity Relationships

```
User
 ├── Creates → N Contexts
 ├── Creates → N Providers (Agents)
 ├── Uploads → N Files
 ├── Creates → N Vector Stores
 └── Has → N Variables (User Variables)

Model Provider
 └── Used by → N Providers

Provider (Agent)
 ├── Belongs to → 1 Model Provider
 ├── Has → N Contexts
 ├── Has → N Variables (Provider Variables)
 ├── May have → 1 Vector Store (dedicated knowledge base)
 └── Can access → N Files (through contexts or vector store)

Context
 ├── Belongs to → 1 Provider
 ├── Belongs to → 1 User (created_by)
 ├── Has → N Messages (History)
 └── May have → N Files (attachments)

Vector Store
 ├── Belongs to → 1 User (created_by)
 ├── May belong to → 1 Provider (dedicated to agent)
 └── Contains → N Files (indexed documents)

Files
 ├── Belongs to → 1 User (uploaded_by)
 ├── May belong to → 1 Context (attachment)
 ├── May belong to → 1 Vector Store (indexed document)
 └── Can be accessed by → Providers (through context or vector store)
```

### Key Relationships

1. **User ↔ Context**: Un utente crea e possiede multiple conversazioni
2. **User ↔ Provider**: Un utente può registrare multipli agents
3. **Provider ↔ Context**: Ogni conversazione è associata a uno specifico agent
4. **Provider ↔ Model Provider**: Gli agents usano model providers per le capacità LLM
5. **Provider ↔ Vector Store**: Un agent può avere un vector store dedicato per la sua knowledge base
6. **Context ↔ Files**: I files possono essere allegati a conversazioni specifiche
7. **Vector Store ↔ Files**: I files possono essere indicizzati nei vector stores per RAG
8. **Provider ↔ Files**: Gli agents possono accedere ai files attraverso contexts o vector stores

---

## 1. Context (Conversazione)

Represents a conversation/session with an agent.

### Fields

| Field            | Type          | Description                           |
| ---------------- | ------------- | ------------------------------------- |
| `id`             | string (UUID) | Unique context identifier             |
| `created_at`     | datetime      | Creation timestamp                    |
| `updated_at`     | datetime      | Last update timestamp                 |
| `last_active_at` | datetime      | Last activity timestamp               |
| `created_by`     | string (UUID) | Creator user ID                       |
| `provider_id`    | string (UUID) | Provider/agent ID                     |
| `metadata`       | object        | Additional metadata (key-value pairs) |

### Endpoints

| Method   | Endpoint                                | Description                      |
| -------- | --------------------------------------- | -------------------------------- |
| `POST`   | `/api/v1/contexts`                      | Create a new context             |
| `GET`    | `/api/v1/contexts`                      | List all contexts                |
| `GET`    | `/api/v1/contexts/{context_id}`         | Get a specific context           |
| `PUT`    | `/api/v1/contexts/{context_id}`         | Update a context                 |
| `DELETE` | `/api/v1/contexts/{context_id}`         | Delete a context                 |
| `POST`   | `/api/v1/contexts/{context_id}/history` | Add a message to context history |
| `GET`    | `/api/v1/contexts/{context_id}/history` | List messages in context history |

### Example Usage

```bash
# Create a new context
curl -X POST http://localhost:8333/api/v1/contexts \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "uuid-here",
    "metadata": {"key": "value"}
  }'

# Get context history
curl -X GET http://localhost:8333/api/v1/contexts/{context_id}/history
```

## 1. User

Represents a user in the system. Each user can create multiple conversations (contexts) and register multiple agents (providers).

### Fields

| Field           | Type          | Description                       |
| --------------- | ------------- | --------------------------------- |
| `id`            | string (UUID) | Unique user identifier            |
| `username`      | string        | Username                          |
| `email`         | string        | User email address                |
| `full_name`     | string        | User's full name                  |
| `created_at`    | datetime      | Account creation timestamp        |
| `updated_at`    | datetime      | Last update timestamp             |
| `last_login_at` | datetime      | Last login timestamp              |
| `is_active`     | boolean       | Account active status             |
| `role`          | string        | User role (e.g., "admin", "user") |
| `metadata`      | object        | Additional user metadata          |

### Relationships

- **Creates** → N Contexts (conversations)
- **Creates** → N Providers (agents)
- **Uploads** → N Files
- **Creates** → N Vector Stores
- **Has** → N Variables (user-specific configuration)

### Endpoints

| Method   | Endpoint             | Description                    |
| -------- | -------------------- | ------------------------------ |
| `POST`   | `/api/v1/users`      | Create a new user              |
| `GET`    | `/api/v1/users`      | List all users                 |
| `GET`    | `/api/v1/users/{id}` | Get a specific user            |
| `PATCH`  | `/api/v1/users/{id}` | Update a user                  |
| `DELETE` | `/api/v1/users/{id}` | Delete a user                  |
| `GET`    | `/api/v1/users/me`   | Get current authenticated user |

### Example Usage

```bash
# Get current user
curl -X GET http://localhost:8333/api/v1/users/me \
  -H "Authorization: Bearer YOUR_API_KEY"

# Update user profile
curl -X PATCH http://localhost:8333/api/v1/users/{id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "full_name": "John Doe",
    "metadata": {"preferences": {"theme": "dark"}}
  }'
```

---

---

## 3. Provider (Agent)

Represents a registered agent in the system.

### Fields

| Field               | Type          | Description                           |
| ------------------- | ------------- | ------------------------------------- |
| `id`                | string (UUID) | Unique provider identifier            |
| `name`              | string        | Provider/agent name                   |
| `description`       | string        | Provider description                  |
| `type`              | string        | Provider type (e.g., "agent", "tool") |
| `created_at`        | datetime      | Creation timestamp                    |
| `updated_at`        | datetime      | Last update timestamp                 |
| `created_by`        | string (UUID) | Creator user ID                       |
| `model_provider_id` | string (UUID) | Associated model provider ID          |
| `config`            | object        | Provider configuration                |
| `metadata`          | object        | Additional metadata                   |

### Relationships

- **Has many** Contexts (via `provider_id` in Context)
- **Belongs to** Model Provider (via `model_provider_id`)
- **Has many** Variables (provider-specific variables)
- **May have** Vector Store (dedicated knowledge base for the agent)
- **Can access** Files (through contexts or vector store)

### Endpoints

| Method   | Endpoint                 | Description             |
| -------- | ------------------------ | ----------------------- |
| `POST`   | `/api/v1/providers`      | Create a new provider   |
| `GET`    | `/api/v1/providers`      | List all providers      |
| `GET`    | `/api/v1/providers/{id}` | Get a specific provider |
| `PATCH`  | `/api/v1/providers/{id}` | Update a provider       |
| `DELETE` | `/api/v1/providers/{id}` | Delete a provider       |

### Example Usage

```bash
# List all providers
curl -X GET http://localhost:8333/api/v1/providers

# Get specific provider
curl -X GET http://localhost:8333/api/v1/providers/{id}

# Update provider
curl -X PATCH http://localhost:8333/api/v1/providers/{id} \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Agent Name"
  }'
```

---

## 5. Model Provider

Manages LLM providers (Ollama, OpenAI, etc.).

### Fields

| Field        | Type          | Description                                    |
| ------------ | ------------- | ---------------------------------------------- |
| `id`         | string (UUID) | Unique model provider identifier               |
| `name`       | string        | Model provider name (e.g., "ollama", "openai") |
| `type`       | string        | Provider type                                  |
| `base_url`   | string        | Base URL for API calls                         |
| `api_key`    | string        | API key (if required)                          |
| `config`     | object        | Provider-specific configuration                |
| `models`     | array         | Available models list                          |
| `created_at` | datetime      | Creation timestamp                             |
| `updated_at` | datetime      | Last update timestamp                          |
| `metadata`   | object        | Additional metadata                            |

### Relationships

- **Has many** Providers (agents using this model provider)

### Endpoints

| Method   | Endpoint                                      | Description                   |
| -------- | --------------------------------------------- | ----------------------------- |
| `GET`    | `/api/v1/model_providers`                     | List all model providers      |
| `POST`   | `/api/v1/model_providers`                     | Create a new model provider   |
| `GET`    | `/api/v1/model_providers/{model_provider_id}` | Get a specific model provider |
| `DELETE` | `/api/v1/model_providers/{model_provider_id}` | Delete a model provider       |

### Example Usage

```bash
# List model providers
curl -X GET http://localhost:8333/api/v1/model_providers

# Create a new model provider
curl -X POST http://localhost:8333/api/v1/model_providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ollama",
    "type": "ollama",
    "config": {
      "base_url": "http://localhost:11434"
    }
  }'
```

---

## 6. Variables

Manages user and provider variables. Variables are used to store configuration parameters, API keys, preferences, and other settings that can be used by users and providers (agents).

**Use Cases:**
- **User Variables**: Store user-specific settings like API keys, default namespaces, preferred regions, etc.
- **Provider Variables**: Store agent-specific configuration like model parameters, timeout values, retry limits, custom prompts, etc.

**Example Variables:**
- User: `KUBECONFIG`, `DEFAULT_NAMESPACE`, `OPENAI_API_KEY`
- Provider: `MAX_RETRIES`, `TIMEOUT_SECONDS`, `TEMPERATURE`, `SYSTEM_PROMPT`

### Fields

#### User Variables

| Field        | Type          | Description                              |
| ------------ | ------------- | ---------------------------------------- |
| `user_id`    | string (UUID) | User identifier                          |
| `key`        | string        | Variable name                            |
| `value`      | string        | Variable value                           |
| `type`       | string        | Variable type (e.g., "string", "secret") |
| `created_at` | datetime      | Creation timestamp                       |
| `updated_at` | datetime      | Last update timestamp                    |

#### Provider Variables

| Field         | Type          | Description                                |
| ------------- | ------------- | ------------------------------------------ |
| `provider_id` | string (UUID) | Provider identifier                        |
| `key`         | string        | Variable name                              |
| `value`       | string        | Variable value                             |
| `type`        | string        | Variable type                              |
| `scope`       | string        | Variable scope (e.g., "global", "context") |
| `created_at`  | datetime      | Creation timestamp                         |
| `updated_at`  | datetime      | Last update timestamp                      |

### Relationships

- **Belongs to** User (user variables)
- **Belongs to** Provider (provider variables)

### Endpoints

| Method | Endpoint                           | Description               |
| ------ | ---------------------------------- | ------------------------- |
| `GET`  | `/api/v1/variables`                | List user variables       |
| `PUT`  | `/api/v1/variables`                | Update user variables     |
| `GET`  | `/api/v1/providers/{id}/variables` | List provider variables   |
| `PUT`  | `/api/v1/providers/{id}/variables` | Update provider variables |

### Example Usage

```bash
# Get user variables
curl -X GET http://localhost:8333/api/v1/variables

# Update user variables
curl -X PUT http://localhost:8333/api/v1/variables \
  -H "Content-Type: application/json" \
  -d '{
    "KUBECONFIG": "/path/to/kubeconfig",
    "NAMESPACE": "default"
  }'

# Get provider variables
curl -X GET http://localhost:8333/api/v1/providers/{id}/variables

# Update provider variables
curl -X PUT http://localhost:8333/api/v1/providers/{id}/variables \
  -H "Content-Type: application/json" \
  -d '{
    "MAX_RETRIES": "3",
    "TIMEOUT": "30"
  }'
```

---

## 7. Files

File management for agent operations. Files can be uploaded by users and used in different contexts.

**Use Cases:**
- **Context Attachments**: Attach documents, images, or data files to a specific conversation for the agent to analyze
- **Vector Store Documents**: Upload documents to be indexed in a vector store for RAG (Retrieval-Augmented Generation)
- **Configuration Files**: Upload YAML, JSON, or other configuration files for the agent to process
- **Data Analysis**: Upload CSV, Excel, or other data files for analysis by the agent
- **Knowledge Base**: Build a knowledge base by uploading documentation, manuals, or reference materials

**Example Use Cases:**
- Upload a Kubernetes YAML file to analyze deployment configurations
- Upload documentation to create a searchable knowledge base via vector stores
- Attach log files to a conversation for troubleshooting
- Upload CSV data for analysis and visualization

### Fields

| Field             | Type          | Description                           |
| ----------------- | ------------- | ------------------------------------- |
| `id`              | string (UUID) | Unique file identifier                |
| `filename`        | string        | Original filename                     |
| `content_type`    | string        | MIME type                             |
| `size`            | integer       | File size in bytes                    |
| `storage_path`    | string        | Internal storage path                 |
| `uploaded_by`     | string (UUID) | Uploader user ID                      |
| `context_id`      | string (UUID) | Associated context ID (optional)      |
| `vector_store_id` | string (UUID) | Associated vector store ID (optional) |
| `created_at`      | datetime      | Upload timestamp                      |
| `metadata`        | object        | Additional file metadata              |
| `checksum`        | string        | File checksum (SHA-256)               |

### Relationships

- **Belongs to** User (via `uploaded_by`)
- **Belongs to** Context (optional, via `context_id`)
- **Belongs to** Vector Store (optional, via `vector_store_id`)

### Endpoints

| Method   | Endpoint                  | Description         |
| -------- | ------------------------- | ------------------- |
| `POST`   | `/api/v1/files`           | Upload a file       |
| `GET`    | `/api/v1/files`           | List all files      |
| `GET`    | `/api/v1/files/{file_id}` | Get a specific file |
| `DELETE` | `/api/v1/files/{file_id}` | Delete a file       |

### Example Usage

```bash
# Upload a file
curl -X POST http://localhost:8333/api/v1/files \
  -F "file=@/path/to/file.txt" \
  -F "metadata={\"description\":\"Configuration file\"}"

# List files
curl -X GET http://localhost:8333/api/v1/files

# Download a file
curl -X GET http://localhost:8333/api/v1/files/{file_id} \
  -o downloaded_file.txt

# Delete a file
curl -X DELETE http://localhost:8333/api/v1/files/{file_id}
```

---

## 8. Vector Stores

Manages vector stores for Retrieval-Augmented Generation (RAG).

### Fields

| Field             | Type          | Description                       |
| ----------------- | ------------- | --------------------------------- |
| `id`              | string (UUID) | Unique vector store identifier    |
| `name`            | string        | Vector store name                 |
| `description`     | string        | Vector store description          |
| `embedding_model` | string        | Embedding model used              |
| `dimension`       | integer       | Vector dimension                  |
| `provider_id`     | string (UUID) | Associated provider ID (optional) |
| `created_by`      | string (UUID) | Creator user ID                   |
| `created_at`      | datetime      | Creation timestamp                |
| `updated_at`      | datetime      | Last update timestamp             |
| `document_count`  | integer       | Number of documents stored        |
| `config`          | object        | Vector store configuration        |
| `metadata`        | object        | Additional metadata               |

### Relationships

- **Belongs to** User (via `created_by`)
- **Belongs to** Provider (optional, via `provider_id`)
- **Has many** Files (documents stored in the vector store)

### Endpoints

| Method   | Endpoint                                         | Description                 |
| -------- | ------------------------------------------------ | --------------------------- |
| `POST`   | `/api/v1/vector_stores`                          | Create a new vector store   |
| `GET`    | `/api/v1/vector_stores/{vector_store_id}`        | Get a specific vector store |
| `DELETE` | `/api/v1/vector_stores/{vector_store_id}`        | Delete a vector store       |
| `POST`   | `/api/v1/vector_stores/{vector_store_id}/search` | Perform vector search       |

### Example Usage

```bash
# Create a vector store
curl -X POST http://localhost:8333/api/v1/vector_stores \
  -H "Content-Type: application/json" \
  -d '{
    "name": "k8s-docs",
    "embedding_model": "text-embedding-ada-002",
    "dimension": 1536
  }'

# Get vector store
curl -X GET http://localhost:8333/api/v1/vector_stores/{vector_store_id}

# Perform vector search
curl -X POST http://localhost:8333/api/v1/vector_stores/{vector_store_id}/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to scale a deployment?",
    "top_k": 5
  }'

# Delete vector store
curl -X DELETE http://localhost:8333/api/v1/vector_stores/{vector_store_id}
```

---

## Common Response Formats

### Success Response

```json
{
  "status": "success",
  "data": {
    // Response data
  }
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE"
}
```

---

## Authentication

Currently, the API uses basic authentication or API keys. Include authentication headers in your requests:

```bash
curl -X GET http://localhost:8333/api/v1/contexts \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse:
- Default: 100 requests per minute per user
- Burst: 200 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

---

## Pagination

List endpoints support pagination using query parameters:

```bash
curl -X GET "http://localhost:8333/api/v1/contexts?page=1&page_size=20"
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 100,
    "total_pages": 5
  }
}
```

---

## Filtering and Sorting

Many list endpoints support filtering and sorting:

```bash
# Filter contexts by provider
curl -X GET "http://localhost:8333/api/v1/contexts?provider_id=uuid-here"

# Sort contexts by creation date
curl -X GET "http://localhost:8333/api/v1/contexts?sort_by=created_at&order=desc"
```

---

## WebSocket Support

Real-time updates are available via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8333/api/v1/ws/contexts/{context_id}');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('New message:', message);
};
```

---

## Additional Resources

- **Full API Documentation**: http://localhost:8333/api/v1/docs
- **AgentStack Concepts**: See [`AGENTSTACK_CONCEPTS.md`](./AGENTSTACK_CONCEPTS.md)
- **Usage Guide**: See [`USAGE.md`](./USAGE.md)
- **Setup Instructions**: See [`SETUP.md`](./SETUP.md)

---

## Support

For issues or questions:
1. Check the interactive API documentation at http://localhost:8333/api/v1/docs
2. Review the project documentation in the `docs/` directory
3. Open an issue on the project repository