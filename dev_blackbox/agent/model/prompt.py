from llama_index.core.prompts import PromptTemplate, PromptType

GITHUB_COMMIT_SUMMARY_PROMPT = PromptTemplate(
    """\
당신은 GitHub 커밋 데이터를 기반으로 업무 일지를 작성하는 개발자입니다.

아래의 커밋 상세 정보를 분석하여 간결한 업무 일지를 작성하세요.

## 규칙
- 같은 목적의 커밋은 하나의 작업 항목으로 묶어서 정리하세요.
- 각 항목에 대해 무엇을 했는지, 왜 했는지를 1-2문장으로 요약하세요.
- 커밋 메시지가 모호한 경우, 코드 변경 내용에서 의도를 추론하세요.
- 사소한 변경(포맷팅, 공백, lock 파일, 자동 생성 코드)은 무시하세요.
- 한국어로 작성하세요.

## 출력 형식
### [레포지토리명]
- [작업 요약]
  - 주요 변경: [중요 파일 변경 사항 간략 설명]

## 커밋 상세 정보
{commit_message}

## 업무 일지
""",
    prompt_type=PromptType.SUMMARY,
)
