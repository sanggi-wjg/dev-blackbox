from dev_blackbox.domain.chunker import chunk_content


class ChunkerTest:

    def test_빈_콘텐츠는_빈_리스트_반환(self):
        # given / when / then
        assert chunk_content("") == []
        assert chunk_content("   ") == []

    def test_짧은_콘텐츠는_단일_청크_반환(self):
        # given
        content = "짧은 업무 내용입니다."

        # when
        result = chunk_content(content)

        # then
        assert len(result) == 1
        assert result[0] == content

    def test_max_chunk_chars_이하면_단일_청크(self):
        # given
        content = "A" * 2000

        # when
        result = chunk_content(content, chunk_size=2000)

        # then
        assert len(result) == 1

    def test_헤딩_기준_섹션_분할(self):
        # given
        content = (
            "### GitHub 작업\n\n커밋 내용입니다.\n\n"
            "### Jira 작업\n\nJira 이슈 처리했습니다.\n\n"
            "### Slack 메시지\n\n채널에서 논의했습니다."
        )

        # when
        result = chunk_content(content, chunk_size=50, split_separator="### ")

        # then — 각 섹션이 별도 청크로 분할
        assert len(result) == 3
        assert result[0].startswith("### GitHub 작업")
        assert result[1].startswith("### Jira 작업")
        assert result[2].startswith("### Slack 메시지")

    def test_긴_섹션은_단락_기준_재분할(self):
        # given
        paragraph = "A" * 100
        content = f"{paragraph}\n\n{paragraph}\n\n{paragraph}"

        # when
        result = chunk_content(content, chunk_size=250, overlap_size=50)

        # then — 여러 청크로 분할됨
        assert len(result) > 1

    def test_분할_불가능한_긴_텍스트는_문자_단위_슬라이싱(self):
        # given
        content = "A" * 5000

        # when
        result = chunk_content(content, chunk_size=2000, overlap_size=400)

        # then
        assert len(result) > 1
        assert all(len(chunk) <= 2000 for chunk in result)

    def test_overlap_적용_확인(self):
        # given — 3개의 단락, 각 150자
        paragraph_a = "A" * 150
        paragraph_b = "B" * 150
        paragraph_c = "C" * 150
        content = f"{paragraph_a}\n\n{paragraph_b}\n\n{paragraph_c}"

        # when — max_chunk_chars=350이면 2개씩 묶이고 overlap 발생
        result = chunk_content(content, chunk_size=350, overlap_size=200)

        # then — 두 번째 청크에 이전 청크의 일부가 포함됨
        assert len(result) >= 2
        # overlap으로 인해 paragraph_b가 두 청크 모두에 등장
        assert "B" * 150 in result[0]
        assert "B" * 150 in result[1]

    def test_None_content는_빈_리스트_반환(self):
        # given / when / then
        assert chunk_content("") == []
