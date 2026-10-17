# RAG faithfulness & response time (2026-10-18)

LLM: ollama / qwen2.5:3b · retrieval: TF-IDF (word + bigram) · profiles: 50

## Program explanations
- LLM calls succeeded: 50/50
- Reasons proposed by the LLM: 171 · kept: 73 · blocked for unsupported claims about the student: 80 · blocked as off-task: 14 · invalid (wrong id / duplicate / length): 4
- Coverage: 73/208 programs shown (35%) got an AI explanation; the rest use rule-based reasons
- Of the 73 AI reasons shown: cross-program mentions 0 (0%), unsupported facts 0 (0%), weak lexical support 20 (27%)
- Mean lexical support: 0.68

## Response time (seconds per LLM call)
- Program explanation: p50 3.6 · p95 5.4 · max 5.9
- Next-question choice: p50 1.1 · p95 1.3 · max 1.4 · LLM choice accepted 49/50

Automatic checks are proxies. Human rating sheet: reports/07_rag_review.csv
