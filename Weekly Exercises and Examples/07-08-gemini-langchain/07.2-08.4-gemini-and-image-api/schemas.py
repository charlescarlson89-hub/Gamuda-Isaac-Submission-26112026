"""Pydantic checks data arriving from the browser before Gemini is called."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from pdf_support import MAX_BASE64_CHARS
from image_support import MAX_IMAGE_BASE64_CHARS


class PDFDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(min_length=1, max_length=180)
    mime_type: Literal["application/pdf"] = "application/pdf"
    data: str = Field(min_length=1, max_length=MAX_BASE64_CHARS, repr=False)

    @field_validator("filename")
    @classmethod
    def filename_only(cls, value):
        if not value.lower().endswith(".pdf") or any(c in value for c in "/\\\r\n\x00"):
            raise ValueError("Choose a PDF filename without a directory path.")
        return value


class ImageAttachment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=180)
    mime_type: Literal["image/jpeg", "image/png"]
    data: str = Field(min_length=1, max_length=MAX_IMAGE_BASE64_CHARS, repr=False)

    @model_validator(mode="after")
    def filename_matches_format(self):
        extensions = (".jpg", ".jpeg") if self.mime_type == "image/jpeg" else (".png",)
        if (not self.filename.lower().endswith(extensions)
                or any(c in self.filename for c in "/\\\r\n\x00")):
            raise ValueError("Choose a JPG or PNG filename without a directory path.")
        return self


class Message(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    message: str = Field(min_length=1, max_length=2000)
    history: list[Message] = Field(default_factory=list, max_length=12)
    document: PDFDocument | None = None
    image: ImageAttachment | None = None

    @model_validator(mode="after")
    def check_history(self):
        if self.document and self.image:
            raise ValueError("Attach one PDF or one image per conversation.")
        # History contains completed user/assistant pairs only.
        if len(self.history) % 2:
            raise ValueError("History must contain complete conversation pairs.")
        for index, message in enumerate(self.history):
            expected = "user" if index % 2 == 0 else "assistant"
            if message.role != expected:
                raise ValueError("History must alternate user and assistant messages.")
        if len(self.message) + sum(len(m.content) for m in self.history) > 16000:
            raise ValueError("Conversation context is too long. Start a new chat.")
        return self


class ChatResponse(BaseModel):
    reply: str
    document_pages: int | None = None
    image_width: int | None = None
    image_height: int | None = None
