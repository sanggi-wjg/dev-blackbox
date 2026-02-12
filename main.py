from dev_blackbox.agent.llm_agent import LLMAgent
from dev_blackbox.agent.model.llm_model import SummaryOllamaConfig
from dev_blackbox.agent.model.prompt import GITHUB_COMMIT_SUMMARY_PROMPT
from dev_blackbox.service.github_collect_service import GitHubCollectService

github_collect_service = GitHubCollectService()
results = github_collect_service.collect_yesterday_commit_info()

llm_agent = LLMAgent.create_with_ollama(SummaryOllamaConfig())
summary = llm_agent.query(GITHUB_COMMIT_SUMMARY_PROMPT, commit_message="\n".join(results))
print(summary)

"""
### [mall]

- **관리자 API(상품, 발주계획, 쿠폰) 컨트롤러 테스트 확충**
  - 주요 변경: 쿠폰 그룹 생성/관리, 스티커용 상품 리스트 조회, 발주 필요 SKU 엑셀 내보내기 등 주요 어드민 기능에 대한 테스트 케이스를 추가하여 테스트 커버리지를 확장했습니다.

- **도메인 엔티티 구조 개선 및 레포지토리 테스트 강화**
  - 주요 변경: 성분 타입(IngredientType) 및 상품 배너 매핑 관련 엔티티와 레포지토리를 신설하고, 주요 레포지토리의 벌크 연산 및 조건 검색 쿼리에 대한 단위 테스트를 작성하여 데이터 계층의 안정성을 확보했습니다.

- **공통 유틸리티 및 테스트 규칙 정립**
  - 주요 변경: 코드 생성, 정규식 검증, 카테시안 곱 등 유틸리티 클래스의 테스트를 보강하고, 테스트 코드 작성 시 엔티티 직접 생성 대신 Fixture를 사용하도록 가이드를 업데이트했습니다.

- **클라이언트 IP 식별 로직 개선 및 디버그 API 추가**
  - 주요 변경: `X-Forwarded-For` 헤더를 지원하도록 IP 추출 로직을 수정하여 프록시 환경에서도 실제 클라이언트 IP를 식별할 수 있게 개선했으며, IP 확인을 위한 디버그용 컨트롤러를 추가했습니다.
"""
