# Embedding Search 적중률 개선 계획

임베딩 기반 시맨틱 검색의 적중률(relevance)을 높이기 위한 개선 전략.

> 현재 검색 구현은 `service/search_service.py`, `storage/rds/repository/platform_work_log_repository.py` 참고.

## 현재 상태

| 항목     | 현재 구현                                                    |
|--------|----------------------------------------------------------|
| 임베딩 모델 | `qwen3-embedding:4b` (2560차원, Ollama), 청크 단위 임베딩        |
| 벡터 인덱스 | HNSW (`m=16`, `ef_construction=64`, `vector_cosine_ops`) |
| 검색 대상  | `PlatformWorkLog`만 검색 (`DailyWorkLog` 미검색)               |
| 검색 방식  | 순수 벡터 cosine distance, top-k 반환                          |
| 쿼리 전처리 | 없음 (raw text → 임베딩)                                      |
| 필터링    | `user_id` + `embedding IS NOT NULL`만 적용                  |
| 결과 필터링 | score threshold 없음 (관련성 낮아도 반환)                          |

### 식별된 약점

1. **Semantic Gap** — 짧은 쿼리와 긴 요약문 간 임베딩 공간 불일치
2. **노이즈 반환** — score 임계값 없이 top-k만 반환하여 관련 없는 결과 포함
3. **메타데이터 미활용** — 날짜 범위, 플랫폼 타입 필터 없음
4. **단일 검색 전략** — 벡터 검색만 사용, 키워드 정확 매칭 불가
5. **한국어 최적화 부족** — `mxbai-embed-large`는 다국어 특화 모델이 아님

---

## 개선 전략

### 1. Score Threshold 필터링

**난이도**: 낮음 | **효과**: 중 | **우선순위**: 1

**문제**: 관련 없는 결과도 top-k에 포함되어 체감 품질 저하.

**방안**: cosine distance 임계값 추가.

```python
# repository에서 distance threshold 적용
.where(
    PlatformWorkLog.embedding.cosine_distance(query_embedding) < threshold,
)
```

**구현 범위**:

- `SearchParam`에 `threshold` 파라미터 추가 (기본값 0.5)
- `SearchQuery`에 `threshold` 필드 추가
- `PlatformWorkLogRepository.find_similar_by_embedding()`에 threshold 조건 추가

**검증**: 기존 검색 결과에서 score < 0.5인 결과를 분석하여 적절한 임계값 결정.

---

### 2. 메타데이터 필터링

**난이도**: 낮음 | **효과**: 중 | **우선순위**: 2

**문제**: "지난주 GitHub 작업" 같은 범위 한정 검색 불가. 전체 데이터에서 검색하여 불필요한 결과 포함.

**방안**: 날짜 범위, 플랫폼 타입 필터 추가.

```
GET /api/v1/search?query=배포&platform=GITHUB&date_from=2026-03-01&date_to=2026-03-15
```

**구현 범위**:

- `SearchParam`에 `platform`, `date_from`, `date_to` 파라미터 추가
- `SearchQuery`에 해당 필드 추가
- Repository 쿼리에 WHERE 조건 추가

**검증**: 필터 적용 전후 검색 결과 비교. 범위 한정 시 상위 결과의 관련성 향상 확인.

---

### 3. HyDE (Hypothetical Document Embedding)

**난이도**: 중 | **효과**: 상 | **우선순위**: 3

**문제**: 사용자 쿼리 `"배포 이슈"` (2단어)와 임베딩된 긴 요약문 간 semantic gap. 같은 주제라도 벡터 거리가 멀 수 있음.

**방안**: 쿼리를 LLM으로 "가상 문서"로 변환한 뒤 임베딩하여 검색. 쿼리가 실제 문서와 같은 임베딩 공간에 위치하게 됨.

```python
# SearchService에서
hypothetical_doc = llm_agent.query(
    f"다음 검색어에 대한 개발자 업무 일지를 작성해줘: {query_text}"
)
query_embedding = embedding_agent.get_embedding(hypothetical_doc)
# 이후 기존 벡터 검색 동일
```

**구현 범위**:

- `SearchService`에 HyDE 프롬프트 템플릿 추가
- `LLMAgent`를 `SearchService`에서 호출하여 가상 문서 생성
- 가상 문서를 임베딩하여 벡터 검색 수행
- HyDE 사용 여부를 파라미터로 제어 (LLM 호출 비용 고려)

**검증**: 동일 쿼리에 대해 HyDE 적용 전후 top-5 결과의 관련성 비교.

**트레이드오프**: LLM 호출이 추가되어 응답 시간 증가 (Ollama 로컬이므로 ~1-3초 예상). 실시간 검색에서는 옵션으로 제공.

---

### 4. Hybrid Search (키워드 + 벡터, RRF)

**난이도**: 중 | **효과**: 상 | **우선순위**: 4

**문제**: `"JIRA-1234"`, `"NPE"` 같은 정확한 키워드 매칭에서 벡터 검색의 한계.

**방안**: PostgreSQL full-text search + pgvector 벡터 검색을 RRF (Reciprocal Rank Fusion)로 결합.

```sql
-- tsvector 컬럼 추가 (generated column)
ALTER TABLE platform_work_log
    ADD COLUMN content_tsv tsvector
        GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED;
CREATE INDEX idx_platform_work_log_tsv ON platform_work_log USING gin(content_tsv);
```

```python
# RRF (Reciprocal Rank Fusion)
# score(doc) = sum(1 / (k + rank_in_source)) for each source
def reciprocal_rank_fusion(
    vector_results: list,
    keyword_results: list,
    k: int = 60,
) -> list:
    scores: dict[int, float] = {}
    for rank, doc in enumerate(vector_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank)
    for rank, doc in enumerate(keyword_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**구현 범위**:

- `init.sql`에 `content_tsv` generated column + GIN 인덱스 추가
- `PlatformWorkLogRepository`에 full-text search 메서드 추가
- `SearchService`에 RRF 결합 로직 추가
- 기존 Entity에 `content_tsv` 컬럼 매핑 (read-only)

**검증**: 키워드 정확 매칭 쿼리 (이슈 번호, 에러명 등)에서 적중률 비교.

**참고**: RRF는 순위(rank) 기반이므로 벡터 유사도와 BM25 점수의 스케일 차이를 정규화할 필요가 없음.

---

### 5. 임베딩 모델 교체 (다국어 특화)

**난이도**: 낮음 | **효과**: 상 | **우선순위**: 5

**문제**: `mxbai-embed-large`는 영어 중심 모델. 한국어 업무 일지의 시맨틱 표현력이 부족할 수 있음.

**방안**: 다국어 특화 임베딩 모델로 교체.

| 모델                               | 차원   | 특징                            |
|----------------------------------|------|-------------------------------|
| `mxbai-embed-large` (현재)         | 1024 | 영어 중심, MTEB 중상위               |
| `bge-m3`                         | 1024 | 다국어 특화, MTEB 최상위, Ollama 지원   |
| `multilingual-e5-large-instruct` | 1024 | 다국어, instruction 기반, 쿼리 의도 반영 |
| `nomic-embed-text`               | 768  | 경량, 한국어 양호, 차원 변경 필요          |

**구현 범위**:

- `EmbeddingOllamaConfig.model` 변경
- 차원이 다른 모델 선택 시: Entity, `init.sql`, HNSW 인덱스 재생성
- 기존 임베딩 데이터 재생성 (배치 마이그레이션)

**검증**: 동일 쿼리셋에 대해 모델별 top-5 적중률 비교. 한국어 쿼리에 대한 결과 품질 평가.

**주의**: 모델 교체 시 기존 임베딩과 호환되지 않으므로 전체 재임베딩 필요. `embedding` 컬럼을 NULL로 리셋 후 `generate_embeddings_task()`로 재생성.

---

### 6. HNSW 인덱스 튜닝

**난이도**: 낮음 | **효과**: 저~중 | **우선순위**: 6

**문제**: `ef_construction=64`는 보수적 설정. 데이터 증가 시 recall 저하 가능.

**방안**:

```sql
-- 검색 시 ef_search 증가 (정확도 ↑, 속도 ↓)
SET
hnsw.ef_search = 100;  -- 기본값 40

-- 인덱스 재생성 시 ef_construction 증가
CREATE INDEX...WITH (m = 16, ef_construction = 128);
```

**구현 범위**:

- `SearchService`에서 검색 전 `SET hnsw.ef_search` 실행
- 또는 PostgreSQL 세션 기본값 설정

**검증**: 데이터 1만 건 이상에서 ef_search 값별 recall 비교. 현재 데이터가 적다면 효과 미미.

---

## 추천 구현 순서

```
Phase 1 (즉시 적용 — 코드 변경 최소) ─────────────────
  #1 Score Threshold 필터링
  #2 메타데이터 필터링 (날짜, 플랫폼)

Phase 2 (적중률 핵심 개선) ────────────────────────────
  #3 HyDE (Hypothetical Document Embedding)
  #4 Hybrid Search (키워드 + 벡터, RRF)

Phase 3 (기반 개선) ───────────────────────────────────
  #5 임베딩 모델 교체 (bge-m3)
  #6 HNSW 인덱스 튜닝
```

## 참고 자료

- [HyDE 논문](https://arxiv.org/abs/2212.10496) — Precise Zero-Shot Dense Retrieval without Relevance Labels
- [RRF 논문](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) — Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods
- [pgvector HNSW 튜닝](https://github.com/pgvector/pgvector#hnsw) — ef_search, ef_construction 파라미터 가이드
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) — 임베딩 모델 벤치마크 비교
