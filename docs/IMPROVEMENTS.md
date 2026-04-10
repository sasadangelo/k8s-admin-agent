# Miglioramenti al Kubernetes Admin Agent

Questo documento descrive i miglioramenti apportati all'agent per renderlo più efficace nell'amministrazione di cluster Kubernetes.

## Data: 10 Aprile 2026

## Problema Iniziale

Durante i test, l'agent mostrava questi problemi:

1. **Errore nel chiamare i tool**: L'agent tentava di chiamare un tool inesistente chiamato "Kubernetes" invece di usare correttamente `kubernetes_mcp`
2. **Istruzioni poco chiare**: Le istruzioni non specificavano chiaramente il formato delle chiamate ai tool
3. **Mancanza di esempi pratici**: Non c'erano esempi concreti per le operazioni comuni
4. **Documentazione limitata**: Mancava una guida dettagliata per gli utenti

### Output dell'Errore

```
{"input":{"tool_name":"Kubernetes","arguments":{"namespace":"default","resource_type":"pods"}},
 "output":{"result":null,"success":false,
 "error":"MCP Error: {'code': -32602, 'message': 'unknown tool \"Kubernetes\"'}"}}
```

## Soluzioni Implementate

### 1. Miglioramento delle Istruzioni dell'Agent

**File modificato**: [`src/k8s_admin_agent/agent.py`](../src/k8s_admin_agent/agent.py)

#### Modifiche principali:

1. **Formato delle chiamate tool più chiaro**:
   ```python
   ## Tool Usage
   You MUST use the kubernetes_mcp tool to execute ALL Kubernetes operations.
   The tool name is "kubernetes_mcp" and you specify the operation in the tool_name parameter.

   ### IMPORTANT: Tool Call Format
   When calling kubernetes_mcp, you MUST use this exact format:
   {
       "tool_name": "operation_name",
       "arguments": {
           "param1": "value1",
           "param2": "value2"
       }
   }
   ```

2. **Esempi specifici per ogni operazione**:
   - Namespace operations (namespaces_list)
   - Pod operations (pods_list, pods_get, pods_delete, pods_log, pods_exec)
   - Deployment operations (resources_list, resources_get, resources_scale, resources_delete)
   - ConfigMap operations
   - Secret operations

3. **Sezione "Common User Requests"**:
   Mappatura diretta tra richieste utente comuni e chiamate tool:
   ```
   1. "List all namespaces" or "Lista tutti i namespace"
      → Use: {"tool_name": "namespaces_list", "arguments": {}}

   2. "List pods in default namespace" or "Lista i pod nel namespace default"
      → Use: {"tool_name": "pods_list_in_namespace", "arguments": {"namespace": "default"}}
   ```

4. **Supporto multilingua**:
   - Aggiunto supporto esplicito per italiano e inglese
   - Esempi in entrambe le lingue

### 2. Documentazione Completa per gli Utenti

**File creato**: [`docs/USAGE.md`](USAGE.md)

Questa guida completa include:

#### Sezioni principali:

1. **Panoramica delle operazioni supportate**:
   - logs, delete, describe, get, restart, scale
   - Pod, Deployment, ConfigMap, Secret

2. **13 esempi pratici dettagliati**:
   - Listare namespace
   - Listare pod in un namespace
   - Ottenere dettagli di un pod
   - Visualizzare log
   - Eliminare pod
   - Gestire deployment (list, scale, delete)
   - Gestire ConfigMap e Secret
   - Riavviare pod
   - Visualizzare eventi

3. **Richieste complesse**:
   - Troubleshooting guidato
   - Scaling intelligente
   - Pulizia risorse

4. **Best practices**:
   - Come formulare richieste chiare
   - Quando specificare namespace
   - Gestione operazioni distruttive

5. **Esempi avanzati**:
   - Debugging completo
   - Deployment update
   - Analisi problemi

### 3. Miglioramento del README

**File modificato**: [`README.md`](../README.md)

#### Modifiche:

1. **Sezione "Example Interactions" migliorata**:
   - Esempi più realistici con output formattato
   - Tabella delle operazioni supportate
   - Link alla documentazione dettagliata

2. **Esempi in italiano e inglese**:
   ```
   User: Lista tutti i namespace
   Agent: Ecco tutti i namespace nel cluster:
          - default (Active, 38d)
          - kube-system (Active, 38d)
          ...
   ```

3. **Tabella operazioni supportate**:
   | Operation    | Resources                     | Example                 |
   | ------------ | ----------------------------- | ----------------------- |
   | List         | Namespaces, Pods, Deployments | "Lista i pod"           |
   | Get/Describe | All resources                 | "Descrivi il pod nginx" |
   | Logs         | Pods                          | "Mostra i log"          |
   | Scale        | Deployments                   | "Scala a 5 repliche"    |
   | Delete       | All resources                 | "Elimina il pod"        |
   | Restart      | Pods                          | "Riavvia il pod"        |

## Operazioni Supportate

### Namespace
- ✅ List all namespaces

### Pod
- ✅ List all pods (all namespaces)
- ✅ List pods in specific namespace
- ✅ Get pod details
- ✅ Delete pod
- ✅ Get pod logs
- ✅ Execute command in pod
- ✅ Restart pod (via delete)

### Deployment
- ✅ List deployments
- ✅ Get deployment details
- ✅ Scale deployment
- ✅ Delete deployment

### ConfigMap
- ✅ List configmaps
- ✅ Get configmap details
- ✅ Delete configmap

### Secret
- ✅ List secrets
- ✅ Get secret details
- ✅ Delete secret

### Altri
- ✅ List cluster events
- ✅ Describe any resource

## Benefici delle Modifiche

### 1. Maggiore Affidabilità
- L'agent ora usa correttamente i tool MCP
- Riduzione degli errori di chiamata tool
- Formato delle richieste standardizzato

### 2. Migliore User Experience
- Istruzioni chiare in italiano e inglese
- Esempi pratici per ogni operazione
- Guida completa per troubleshooting

### 3. Documentazione Completa
- Guida dettagliata per utenti (USAGE.md)
- README migliorato con esempi realistici
- Best practices documentate

### 4. Facilità di Manutenzione
- Codice ben documentato
- Esempi facilmente estendibili
- Struttura chiara delle istruzioni

## Test Consigliati

Per verificare i miglioramenti, eseguire questi test:

### Test Base
```bash
# 1. Lista namespace
agentstack run "Kubernetes Admin" "Lista tutti i namespace"

# 2. Lista pod
agentstack run "Kubernetes Admin" "Lista i pod nel namespace default"

# 3. Dettagli pod
agentstack run "Kubernetes Admin" "Descrivi il pod <pod-name>"
```

### Test Operazioni
```bash
# 4. Log
agentstack run "Kubernetes Admin" "Mostra i log del pod <pod-name>"

# 5. Scale
agentstack run "Kubernetes Admin" "Scala il deployment nginx a 3 repliche"

# 6. Delete (con conferma)
agentstack run "Kubernetes Admin" "Elimina il pod test-xyz"
```

### Test Multilingua
```bash
# Inglese
agentstack run "Kubernetes Admin" "List all pods in default namespace"

# Italiano
agentstack run "Kubernetes Admin" "Lista tutti i pod nel namespace default"
```

## Prossimi Passi

### Miglioramenti Futuri

1. **Operazioni Batch**:
   - Supporto per operazioni su più risorse contemporaneamente
   - Esempio: "Elimina tutti i pod in stato Error"

2. **Editing YAML**:
   - Capacità di modificare manifest YAML
   - Validazione prima dell'applicazione

3. **Rollback Automatico**:
   - Gestione automatica dei rollback dei deployment
   - Monitoraggio post-deployment

4. **Metriche Avanzate**:
   - Integrazione con Prometheus
   - Analisi utilizzo risorse
   - Alert e notifiche

5. **Service e Ingress**:
   - Gestione completa di Service
   - Configurazione Ingress
   - Troubleshooting networking

6. **Backup e Restore**:
   - Export configurazioni
   - Backup risorse
   - Restore da backup

## Conclusioni

Le modifiche apportate risolvono i problemi iniziali e forniscono:

1. ✅ **Agent funzionante**: Usa correttamente i tool MCP
2. ✅ **Istruzioni chiare**: Formato chiamate ben definito
3. ✅ **Documentazione completa**: Guida dettagliata per utenti
4. ✅ **Esempi pratici**: 13+ esempi per operazioni comuni
5. ✅ **Supporto multilingua**: Italiano e inglese

L'agent è ora pronto per l'uso in produzione per amministrare cluster Kubernetes in modo sicuro ed efficiente.

## Riferimenti

- [Guida Utente Completa](USAGE.md)
- [README Principale](../README.md)
- [Codice Agent](../src/k8s_admin_agent/agent.py)
- [Tool MCP](../src/k8s_admin_agent/tools/k8s_mcp_tool.py)