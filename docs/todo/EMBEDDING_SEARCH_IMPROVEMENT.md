# Embedding Search 적중률 개선 계획

임베딩 기반 시맨틱 검색의 적중률(relevance)을 높이기 위한 개선 전략.

> 현재 검색 구현은 `service/search_service.py`, `storage/rds/repository/platform_work_log_chunk_repository.py` 참고.

## 현재 상태

| 항목     | 현재 구현                                                                         |
|--------|-------------------------------------------------------------------------------|
| 임베딩 모델 | `bge-m3:latest` (1024차원, Ollama), 다국어 특화 모델                                   |
| 청킹     | `chunk_size=512`, `overlap_size=50`, 섹션 인식 분할 (`"- "` 구분자)                    |
| 벡터 인덱스 | HNSW (`m=16`, `ef_construction=64`, `vector_cosine_ops`)                      |
| 검색 대상  | `PlatformWorkLogChunk` 청크 단위 검색, work_log_id 기준 중복 제거 (최소 distance 유지)        |
| 검색 방식  | cosine distance 기반, similarity threshold 적용 후 top-k 반환                        |
| 쿼리 전처리 | 없음 (raw text → 임베딩)                                                           |
| 필터링    | `user_id` + `embedding IS NOT NULL` + similarity threshold + platform + 날짜 범위 |

### 검색 흐름

```
GET /api/v1/search?query=...&limit=10&similarity=0.5&platform=GITHUB&from_date=...&to_date=...
       │
       ├── SearchParam → SearchQuery 변환
       │
       ├── EmbeddingAgent.get_embedding(query_text)  ← 쿼리 임베딩
       │
       ├── PlatformWorkLogChunkRepository.find_similar_by_embedding()
       │       ├── user_id 필터
       │       ├── cosine_distance < (1.0 - similarity)  ← threshold 적용
       │       ├── platform 필터 (옵셔널)
       │       ├── target_date >= from_date (옵셔널)
       │       ├── target_date <= to_date (옵셔널)
       │       └── limit * 3 (중복 제거 버퍼)
       │
       ├── work_log_id 기준 중복 제거 (최소 distance 유지)
       │
       ├── PlatformWorkLogRepository.find_all_by_id()  ← 원본 조회
       │
       └── PlatformWorkLogSearchResponseDto 반환 (score = 1.0 - distance)
```

### 식별된 약점

1. **Semantic Gap** — 짧은 쿼리와 긴 요약문 간 임베딩 공간 불일치
2. **단일 검색 전략** — 벡터 검색만 사용, 키워드 정확 매칭 불가

---

## 개선 전략

### ~~1. Score Threshold 필터링~~ (구현 완료)

`SearchParam.similarity` (0.0~1.0, 기본값 0.5)로 구현 완료.

Repository에서 `cosine_distance < (1.0 - similarity)` 조건으로 threshold 미달 결과를 필터링한다.

- `SearchParam`: `similarity: float` (0.0~1.0, default=0.5)
- `SearchQuery`: `similarity: float` 전달
- `PlatformWorkLogChunkRepository.find_similar_by_embedding()`: distance threshold 적용

---

### ~~2. 메타데이터 필터링~~ (구현 완료)

`SearchParam`에 `platform`, `from_date`, `to_date` 옵셔널 파라미터로 구현 완료.

모든 필터는 옵셔널이며, 지정 시 기존 벡터 검색에 AND 조건으로 추가된다.

```
GET /api/v1/search?query=배포&platform=GITHUB&from_date=2026-03-01&to_date=2026-03-15
```

- `SearchParam`: `platform: PlatformEnum | None`, `from_date: date | None`, `to_date: date | None`
- `SearchQuery`: 동일 필드 전달
- `PlatformWorkLogChunkRepository.find_similar_by_embedding()`: `PlatformWorkLog` JOIN에 조건 추가

---

### 3. HyDE (Hypothetical Document Embedding)

**난이도**: 중 | **효과**: 상 | **우선순위**: 2

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

**난이도**: 중 | **효과**: 상 | **우선순위**: 3

**문제**: `"JIRA-1234"`, `"NPE"` 같은 정확한 키워드 매칭에서 벡터 검색의 한계.

**방안**: PostgreSQL full-text search + pgvector 벡터 검색을 RRF (Reciprocal Rank Fusion)로 결합.

```sql
-- platform_work_log_chunk에 tsvector 컬럼 추가 (generated column)
ALTER TABLE platform_work_log_chunk
    ADD COLUMN chunk_text_tsv tsvector
        GENERATED ALWAYS AS (to_tsvector('simple', chunk_text)) STORED;
CREATE INDEX idx_platform_work_log_chunk_tsv ON platform_work_log_chunk USING gin(chunk_text_tsv);
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

- `init.sql`에 `chunk_text_tsv` generated column + GIN 인덱스 추가
- `PlatformWorkLogChunkRepository`에 full-text search 메서드 추가
- `SearchService`에 RRF 결합 로직 추가
- `PlatformWorkLogChunk` Entity에 `chunk_text_tsv` 컬럼 매핑 (read-only)

**검증**: 키워드 정확 매칭 쿼리 (이슈 번호, 에러명 등)에서 적중률 비교.

**참고**: RRF는 순위(rank) 기반이므로 벡터 유사도와 BM25 점수의 스케일 차이를 정규화할 필요가 없음.

---

### ~~5. 임베딩 모델 교체 (다국어 특화)~~ (구현 완료)

`bge-m3:latest` (1024차원, 다국어 특화) 모델로 교체 완료.

- `EmbeddingOllamaConfig.model`: `bge-m3:latest`
- 임베딩 차원: 1024 (`Vector(1024)`)
- HNSW 인덱스: `vector_cosine_ops`, `m=16`, `ef_construction=64`

---

### 6. HNSW 인덱스 튜닝

**난이도**: 낮음 | **효과**: 저~중 | **우선순위**: 4

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
  ✅ Score Threshold 필터링 (구현 완료)
  ✅ 임베딩 모델 교체 — bge-m3 (구현 완료)
  ✅ 메타데이터 필터링 — platform, from_date, to_date (구현 완료)

Phase 2 (적중률 핵심 개선) ────────────────────────────
  #3 HyDE (Hypothetical Document Embedding)
  #4 Hybrid Search (키워드 + 벡터, RRF)

Phase 3 (기반 개선) ───────────────────────────────────
  #6 HNSW 인덱스 튜닝
```

## 참고 자료

- [HyDE 논문](https://arxiv.org/abs/2212.10496) — Precise Zero-Shot Dense Retrieval without Relevance Labels
- [RRF 논문](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) — Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods
- [pgvector HNSW 튜닝](https://github.com/pgvector/pgvector#hnsw) — ef_search, ef_construction 파라미터 가이드
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) — 임베딩 모델 벤치마크 비교
- [bge-m3](https://huggingface.co/BAAI/bge-m3) — 현재 사용 중인 다국어 임베딩 모델
