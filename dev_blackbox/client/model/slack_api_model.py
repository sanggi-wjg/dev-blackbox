from pydantic import BaseModel


class SlackChannelModel(BaseModel):
    id: str  # 채널 ID (C로 시작)
    name: str  # 채널 이름
    is_private: bool


class SlackMessageModel(BaseModel):
    ts: str  # 메시지 타임스탬프 (Slack 고유 ID)
    user: str  # Slack member ID (U로 시작)
    text: str  # 메시지 본문
    thread_ts: str | None = None  # 스레드 부모 타임스탬프
    latest_reply: str | None = None  # 스레드 마지막 답글 타임스탬프

    def message_detail_text(self, channel_name: str) -> str:
        return f"[#{channel_name}] {self.text}"
