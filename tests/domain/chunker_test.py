from dev_blackbox.domain.chunker import chunk_work_log_content


class ChunkWorkLogContentTest:

    def test_빈_콘텐츠는_빈_리스트_반환(self):
        # given / when / then
        assert chunk_work_log_content("") == []
        assert chunk_work_log_content("   ") == []

    def test_짧은_콘텐츠는_단일_청크_반환(self):
        # given
        content = "짧은 업무 내용입니다."

        # when
        result = chunk_work_log_content(content)

        # then
        assert len(result) == 1
        assert result[0] == content

    def test_섹션_헤더별로_분리(self):
        # given
        content = (
            "### [#squad-commerce]\n"
            "- 수정 사항에 대한 추가 반영 및 배포를 완료함\n"
            "  - 주요 내용: 수정 건에 대한 코드 추가 및 운영 환경 배포 완료\n"
            "### [#hotline-voc-it]\n"
            "- 요청된 시스템 변경 사항 반영 완료\n"
            "  - 주요 내용: VOC 관련 IT 변경 요청 사항에 대한 수정 및 적용 완료"
        )

        # when
        result = chunk_work_log_content(content)

        # then
        assert len(result) == 2
        assert result[0].startswith("### [#squad-commerce]")
        assert result[1].startswith("### [#hotline-voc-it]")

    def test_동일_섹션_내_여러_항목은_개별_청크로_분리(self):
        # given
        content = (
            "### [fitpetmall-backend]\n"
            "- 시스템 의존성 라이브러리 버전 업데이트 및 보안 강화\n"
            "  - 주요 변경: boto3, botocore 등 주요 패키지를 최신 버전으로 업그레이드\n"
            "- Kafka 메시지 발행 안정성 및 신뢰성 확보\n"
            "  - 주요 변경: Kafka Producer의 enable.idempotence 옵션을 활성화\n"
            "- 프로젝트 유지보수 효율화를 위한 설정 파일 정리\n"
            "  - 주요 변경: 사용하지 않는 lint 설정 삭제"
        )

        # when — chunk_size를 작게 설정하여 섹션 전체가 들어가지 않도록
        result = chunk_work_log_content(content, chunk_size=200)

        # then — 3개 항목이 각각 분리되고 모두 섹션 헤더를 포함
        assert len(result) == 3
        assert all(chunk.startswith("### [fitpetmall-backend]") for chunk in result)
        assert "boto3" in result[0]
        assert "Kafka" in result[1]
        assert "lint" in result[2]

    def test_하위_항목은_상위_항목에_포함(self):
        # given
        content = (
            "### [Sub-task]\n"
            "- [FMP-4939] 스프링 Kafka consumer config 변경\n"
            "  - 상태 변경: Backlog → In Progress → IN DEV REVIEW\n"
            "  - 주요 내용: V4 환경의 Kafka 컨슈머 설정을 수정하고 개발 리뷰를 요청함"
        )

        # when
        result = chunk_work_log_content(content)

        # then — 하위 상세가 포함된 하나의 청크
        assert len(result) == 1
        assert "상태 변경" in result[0]
        assert "주요 내용" in result[0]

    def test_헤더_없는_콘텐츠도_항목_단위로_분리(self):
        # given
        content = (
            "- 첫 번째 작업 항목\n"
            "  - 주요 내용: 상세 설명\n"
            "- 두 번째 작업 항목\n"
            "  - 주요 내용: 상세 설명"
        )

        # when
        result = chunk_work_log_content(content, chunk_size=50)

        # then — 헤더 없이 항목별 분리
        assert len(result) == 2
        assert "첫 번째" in result[0]
        assert "두 번째" in result[1]

    def test_여러_섹션과_여러_항목_복합_케이스(self):
        # given
        content = (
            "### [#guild_it_product_all]\n"
            "- KISA 보안 취약점 신고에 따른 KVE 번호 발급을 확인했습니다\n"
            "  - 주요 내용: 취약점 신고 결과 수신 및 관리\n"
            "- AWS 라이브러리 버전 충돌 문제를 해결하고 신규 이미지를 배포했습니다\n"
            "  - 주요 내용: Python 3.8 호환을 위한 boto3 버전 업데이트\n"
            "### [#squad-commerce-only]\n"
            "- 상용 K8s 팟 리소스 조정 이후의 후속 작업 일정 수립\n"
            "  - 주요 내용: Batch API 및 Argo Workflows 관련 업무 진행 예정"
        )

        # when
        result = chunk_work_log_content(content, chunk_size=200)

        # then
        assert len(result) == 3
        assert result[0].startswith("### [#guild_it_product_all]")
        assert "KISA" in result[0]
        assert result[1].startswith("### [#guild_it_product_all]")
        assert "AWS" in result[1]
        assert result[2].startswith("### [#squad-commerce-only]")
        assert "K8s" in result[2]

    def test_chunk_size_이내면_단일_청크(self):
        # given — 섹션 전체가 chunk_size 이내
        content = "### [#squad-commerce]\n" "- 수정 사항 반영 완료\n" "  - 주요 내용: 배포 완료"

        # when
        result = chunk_work_log_content(content, chunk_size=1000)

        # then
        assert len(result) == 1
        assert result[0] == content
