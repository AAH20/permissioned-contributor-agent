# GraphRAG and agentic RAG: implemented retrieval and alternatives

This project implements **graph-assisted lexical retrieval**. It does not run a language model, create embeddings, or execute Microsoft's GraphRAG indexing pipeline. The narrower implementation makes provenance and access boundaries easy to inspect before testing a more expensive retrieval system.

A synthetic room is authorized before indexing. Its graph contains only permitted documents. Lexical overlap selects seed documents; one curated reference hop can add authorized context within `top_k`. Exact quotes are verified against the original supplied text. A foreign reference never creates an accessible foreign node.

| Project / service | Use | Benefit | Limitation |
|---|---|---|---|
| LangGraph (MIT) | Actual orchestration and human interrupt | Explicit state and control flow | Checkpointing is not authentication; production durability needs infrastructure |
| Due Diligence Agents (Apache-2.0) | Actual graph and citation guard; reference specialist templates | Reuses tested domain structures with pinned provenance | Selected modules only; no full model pipeline or professional judgment |
| NetworkX | Actual in-process document graph | Simple local graph inspection | Memory-limited; no database access-control boundary; DiGraph can collapse multiple edge types on a pair |
| Microsoft GraphRAG (MIT) | Design comparison only | Entity/community retrieval for cross-document questions | Model-generated graph errors, costly indexing, summary deletion/rebuild complexity |
| Qdrant (Apache-2.0) | OSS vector-store alternative, not deployed | Self-hosting and partition choices | Operator owns patching, backups and isolation; shared ranking statistics can affect tenants |
| Pinecone | Managed vector service; fake-index adapter tests | Managed vector retrieval and namespaces | Not an OSS graph database; service cost, residency and vendor dependency; no live benchmark here |

The Pinecone boundary derives its namespace from trusted grant identity, applies an allowed-document filter and rechecks consent on return. Index lifecycle, authentication, schema validation, provider errors, deletion and recovery remain integration work. Changing a grant digest changes the namespace; a production design must manage indexing and deletion accordingly. Do not let a caller choose a namespace directly.

Benchmark lexical-only, vector-only and graph-assisted retrieval on identical held-out cases. Compare recall, unsupported claims, latency, update cost and deletion completion. Graph complexity is justified only when it improves the actual task. Keep graph edges and summaries tenant/purpose-specific; public summaries must never inherit private source content.

Primary references: [LangGraph license](https://github.com/langchain-ai/langgraph/blob/main/LICENSE), [upstream diligence repository](https://github.com/AAH20/A2Z_due-diligence-agents), [Microsoft GraphRAG](https://microsoft.github.io/graphrag/), [Qdrant multitenancy](https://qdrant.tech/documentation/tutorials/multiple-partitions/), [Pinecone multitenancy](https://docs.pinecone.io/guides/index-data/implement-multitenancy).
