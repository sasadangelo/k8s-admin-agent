# Kubernetes Admin Agent - Guida all'Uso

Questa guida spiega come utilizzare il Kubernetes Admin Agent per amministrare il tuo cluster Kubernetes.

## Panoramica

L'agent supporta le seguenti operazioni principali:
- **logs**: Visualizzare i log dei container
- **delete**: Eliminare risorse
- **describe**: Ottenere dettagli su una risorsa
- **get**: Recuperare informazioni su risorse
- **restart**: Riavviare pod (tramite delete)
- **scale**: Scalare deployment

## Risorse Supportate

- **Pod**: Container in esecuzione
- **Deployment**: Gestione delle applicazioni
- **ConfigMap**: Configurazioni
- **Secret**: Dati sensibili

## Esempi di Utilizzo

### 1. Listare Namespace

**Richiesta:**
```
Lista tutti i namespace
```

**Cosa fa l'agent:**
- Chiama `namespaces_list` per ottenere tutti i namespace del cluster
- Mostra nome, stato e età di ogni namespace

---

### 2. Listare Pod in un Namespace

**Richiesta:**
```
Lista i pod nel namespace default
```

**Cosa fa l'agent:**
- Chiama `pods_list_in_namespace` con `namespace: "default"`
- Mostra nome, stato, restart, età e nodo per ogni pod

**Richiesta alternativa:**
```
Mostrami tutti i pod in produzione
```
(L'agent capirà che "produzione" è il namespace)

---

### 3. Ottenere Dettagli di un Pod

**Richiesta:**
```
Descrivi il pod nginx-deployment-6cfb64b7c5-7xlcg nel namespace default
```

**Cosa fa l'agent:**
- Chiama `pods_get` con nome e namespace
- Mostra dettagli completi: container, volumi, eventi, condizioni

---

### 4. Visualizzare Log di un Pod

**Richiesta:**
```
Mostra i log del pod nginx-deployment-6cfb64b7c5-7xlcg
```

**Cosa fa l'agent:**
- Chiama `pods_log` con nome pod e namespace
- Se il pod ha più container, potrebbe chiedere quale container

**Con container specifico:**
```
Mostra i log del container app nel pod nginx-deployment-6cfb64b7c5-7xlcg
```

---

### 5. Eliminare un Pod

**Richiesta:**
```
Elimina il pod nginx-deployment-6cfb64b7c5-7xlcg nel namespace default
```

**Cosa fa l'agent:**
1. **Chiede conferma** prima di procedere
2. Spiega le conseguenze (il pod verrà ricreato se parte di un deployment)
3. Dopo conferma, chiama `pods_delete`
4. Verifica che il pod sia stato eliminato

---

### 6. Listare Deployment

**Richiesta:**
```
Lista tutti i deployment nel namespace default
```

**Cosa fa l'agent:**
- Chiama `resources_list` con `kind: "Deployment"`
- Mostra nome, repliche desiderate/disponibili, età

---

### 7. Scalare un Deployment

**Richiesta:**
```
Scala il deployment nginx a 5 repliche
```

**Cosa fa l'agent:**
1. Verifica lo stato attuale del deployment
2. Chiama `resources_scale` con il numero di repliche
3. Conferma che lo scaling è avvenuto
4. Mostra il nuovo stato

**Esempio con namespace esplicito:**
```
Scala il deployment api-server nel namespace production a 10 repliche
```

---

### 8. Ottenere Dettagli di un Deployment

**Richiesta:**
```
Descrivi il deployment nginx nel namespace default
```

**Cosa fa l'agent:**
- Chiama `resources_get` con `kind: "Deployment"`
- Mostra strategia di deployment, selettori, template pod

---

### 9. Eliminare un Deployment

**Richiesta:**
```
Elimina il deployment nginx
```

**Cosa fa l'agent:**
1. **Chiede conferma** (operazione distruttiva!)
2. Avverte che tutti i pod del deployment verranno eliminati
3. Dopo conferma, chiama `resources_delete`
4. Verifica l'eliminazione

---

### 10. Gestire ConfigMap

**Listare ConfigMap:**
```
Lista tutte le configmap nel namespace default
```

**Visualizzare una ConfigMap:**
```
Mostra la configmap app-config
```

**Eliminare una ConfigMap:**
```
Elimina la configmap old-config
```

---

### 11. Gestire Secret

**Listare Secret:**
```
Lista tutti i secret nel namespace default
```

**Visualizzare un Secret:**
```
Mostra il secret database-credentials
```

**Nota:** I valori dei secret sono codificati in base64

---

### 12. Riavviare un Pod

**Richiesta:**
```
Riavvia il pod nginx-deployment-6cfb64b7c5-7xlcg
```

**Cosa fa l'agent:**
1. Spiega che riavviare = eliminare (Kubernetes lo ricreerà)
2. Chiede conferma
3. Elimina il pod
4. Verifica che il nuovo pod sia stato creato

---

### 13. Visualizzare Eventi del Cluster

**Richiesta:**
```
Mostra gli eventi recenti nel namespace default
```

**Cosa fa l'agent:**
- Chiama `events_list`
- Mostra eventi ordinati per timestamp
- Evidenzia warning ed errori

---

## Richieste Complesse

L'agent può gestire richieste più complesse combinando operazioni:

### Esempio 1: Troubleshooting
```
Il pod api-server-xyz non funziona, aiutami a capire perché
```

**L'agent:**
1. Ottiene dettagli del pod (`pods_get`)
2. Controlla lo stato e gli eventi
3. Recupera i log (`pods_log`)
4. Analizza e suggerisce soluzioni

### Esempio 2: Scaling Intelligente
```
Ho troppo carico sul deployment frontend, cosa posso fare?
```

**L'agent:**
1. Controlla lo stato attuale del deployment
2. Verifica l'utilizzo risorse (`pods_top` se disponibile)
3. Suggerisce un numero appropriato di repliche
4. Scala il deployment dopo conferma

### Esempio 3: Pulizia Risorse
```
Elimina tutti i pod in stato Error nel namespace test
```

**L'agent:**
1. Lista tutti i pod nel namespace
2. Identifica quelli in Error
3. Chiede conferma per ognuno
4. Elimina i pod confermati

---

## Suggerimenti per l'Uso

### 1. Sii Specifico
✅ **Buono:** "Lista i pod nel namespace production"
❌ **Meno chiaro:** "Mostrami i pod"

### 2. Usa Nomi Completi
✅ **Buono:** "Scala il deployment nginx-deployment a 5 repliche"
❌ **Incompleto:** "Scala nginx"

### 3. Specifica il Namespace
✅ **Buono:** "Elimina il pod xyz nel namespace test"
❌ **Ambiguo:** "Elimina il pod xyz"

### 4. Conferma Operazioni Distruttive
L'agent chiederà sempre conferma per:
- Delete
- Scale a 0 repliche
- Operazioni che impattano la produzione

### 5. Usa il Linguaggio Naturale
L'agent capisce sia italiano che inglese:
- "Lista i pod" = "List pods"
- "Scala il deployment" = "Scale the deployment"
- "Mostra i log" = "Show logs"

---

## Limitazioni Attuali

1. **Operazioni Batch**: Non supporta operazioni su più risorse contemporaneamente
2. **Editing YAML**: Non può modificare direttamente i manifest YAML
3. **Rollback**: Non gestisce automaticamente i rollback dei deployment
4. **Monitoring**: Non ha accesso a metriche avanzate (Prometheus, etc.)

---

## Risoluzione Problemi

### L'agent non trova il pod
- Verifica che il nome sia corretto (case-sensitive)
- Specifica il namespace corretto
- Usa `Lista i pod` per vedere tutti i pod disponibili

### L'agent non esegue l'operazione
- Controlla di aver confermato operazioni distruttive
- Verifica i permessi del service account
- Controlla i log dell'agent per errori

### Timeout nelle operazioni
- Alcune operazioni (es. log di pod con molto output) possono richiedere tempo
- L'agent ha un timeout di 30 secondi per operazione

---

## Esempi Avanzati

### Debugging Completo
```
Il servizio api non risponde, fai un'analisi completa
```

L'agent eseguirà:
1. Lista pod del servizio
2. Controlla stato di ogni pod
3. Recupera log recenti
4. Controlla eventi del namespace
5. Verifica configurazioni (configmap/secret)
6. Fornisce diagnosi e suggerimenti

### Deployment Update
```
Voglio aggiornare il deployment frontend, come procedo?
```

L'agent fornirà:
1. Stato attuale del deployment
2. Best practices per l'update
3. Comandi per verificare il rollout
4. Strategie di rollback se necessario

---

## Prossimi Sviluppi

Funzionalità in arrivo:
- [ ] Supporto per Service e Ingress
- [ ] Operazioni batch su più risorse
- [ ] Integrazione con metriche (Prometheus)
- [ ] Rollback automatico dei deployment
- [ ] Export/Import di configurazioni
- [ ] Backup e restore di risorse

---

## Supporto

Per problemi o domande:
- GitHub Issues: [k8s-admin-agent/issues](https://github.com/your-org/k8s-admin-agent/issues)
- Documentazione: [docs/](../docs/)

---

**Nota**: Questo agent è uno strumento potente. Usa sempre cautela con operazioni distruttive,
specialmente in ambienti di produzione!