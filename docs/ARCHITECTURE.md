# Architecture

## 시스템 개요

Dev-Blackbox는 개발 플랫폼(GitHub, Jira 등)에서 활동 데이터를 수집하고,
LLM을 통해 일일 업무 일지를 자동 생성하는 시스템이다.

## 레이어 구조

Layered Architecture (Controller → Service → Repository → Entity)

```
main.py                          # FastAPI 앱 진입점
dev_blackbox/
├── controller/                  # REST API 엔드포인트, DTO, Param, 보안, 예외 핸들러
│   ├── api/                     # 사용자 API (dto/, param/)
│   ├── admin/                   # 관리자 API (dto/)
│   └── config/                  # 보안, 예외 핸들러, 인증 모델 (model/)
├── service/                     # 비즈니스 로직, 트랜잭션 조율
│   ├── command/                 # Command 객체 (쓰기 작업 입력)
│   ├── query/                   # Query 객체 (조회 조건)
│   └── model/                   # Service Model (실질적 변환 로직이 있는 경우만)
├── storage/rds/                 # Repository + Entity (SQLAlchemy)
├── client/                      # 외부 API 클라이언트 (GitHub, Jira, Slack)
├── agent/                       # LLM 에이전트 (Ollama + LlamaIndex)
├── task/                        # APScheduler 백그라운드 태스크
│   └── context/                 # 태스크 실행 컨텍스트 모델
├── core/                        # 설정, DB, Redis, 캐시, 예외, Enum, JWT, Password
└── util/                        # 분산 락, 날짜, 마스킹, 멱등성
```

## 데이터 수집 파이프라인

상세: [파이프라인 문서](PIPELINE.md)
