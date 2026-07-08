## 2. Embedding service

- [x]  Create:

```
app/services/embedding_service.py
```

- [x]  Choose embeddings:
    - [x]  Deterministic mock embeddings for local tests
    - [ ]  API embeddings
- [x]  Create function to generate embeddings for chunks.
- [x]  Create function to generate embedding for query.
- [x]  Normalize text before embedding.
- [x]  Handle empty text.
- [x]  Handle embedding service failure.
- [x]  Add mock embedding mode for tests.

---

## 3. RAG search service

- [x]  Create:

```
app/services/rag_search_service.py
```

- [x]  Accept query.
- [x]  Retrieve top relevant chunks.
- [x]  Return source filenames.
- [x]  Return confidence score.
- [x]  Return relevant passages.
- [x]  Filter weak results.
- [x]  Apply confidence threshold.
- [x]  Return no-answer fallback when confidence is low.
- [x]  Ensure result does not depend only on model memory.

## 4. RAG answer generation service

- [x]  Create:

```
app/services/response_generation_service.py
```

- [x]  Accept:
    - [x]  Ticket message
    - [x]  Customer context
    - [x]  Retrieved knowledge passages
- [x]  Generate customer-facing answer.
- [x]  Include source filenames.
- [x]  Include confidence.
- [x]  Avoid unsupported claims.
- [x]  Avoid saying anything not found in retrieved documents.
- [x]  Return structured JSON only.

Expected output:

```
{
  "answer":"I understand your subscription was charged but is not active yet. Please try refreshing your billing page and confirm whether the payment receipt appears...",
  "sources": ["subscription_activation.md"],
  "confidence":0.84
}
```

---

## 5. No-answer fallback

- [x]  Detect low retrieval confidence.
- [x]  Return no-answer fallback instead of hallucinating.
- [x]  Use fallback response:

```
{
  "answer":"I do not have enough verified information to answer this safely. A support agent should review this ticket.",
  "sources": [],
  "confidence":0.0
}
```

- [x]  Trigger escalation decision when confidence is low.
- [x]  Add tests for unrelated queries.
