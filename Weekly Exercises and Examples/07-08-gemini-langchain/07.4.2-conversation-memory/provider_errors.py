"""Convert provider exceptions into fixed, credential-free diagnostics."""

import httpx
from google.genai.errors import APIError


class EmptyReplyError(Exception):
    """Gemini completed without a usable text reply."""


def safe_provider_error(error: Exception) -> tuple[int, str, str]:
    current = error
    seen = set()
    for _ in range(8):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        if isinstance(current, EmptyReplyError):
            return 502, "empty_reply", "Gemini returned no text. Try a shorter question or start a new conversation."
        if isinstance(current, (TimeoutError, httpx.TimeoutException)):
            return 504, "provider_timeout", "The Google AI request timed out. Your message was kept; wait a moment before retrying."
        if isinstance(current, APIError):
            # Never stringify the exception: its message/details may contain secrets.
            code = current.code
            if code == 429:
                return 429, "provider_quota", "Google's rate or quota limit was reached. Check your usage in AI Studio; wait for the applicable limit to reset."
            if code in (401, 403):
                return 502, "provider_access", "Google rejected access. Check your key restrictions, project permissions, and model access in AI Studio."
            if code == 402:
                return 503, "provider_billing", "Google reports a billing or credit requirement. Check your project in AI Studio before retrying."
            if code == 404:
                return 502, "provider_model", "Google could not find the selected model or resource. Check GEMINI_MODEL and your project's model access."
            if code in (408, 504):
                return 504, "provider_timeout", "The Google AI request timed out. Your message was kept; wait a moment before retrying."
            if code >= 500:
                return 503, "provider_unavailable", "Google's AI service is temporarily unavailable. Wait a moment before retrying."
            if code == 400:
                return 502, "provider_request", "Google rejected the model request. Check model settings and your project's API prerequisites."
        if isinstance(current, httpx.TransportError):
            return 502, "provider_network", "Could not connect to Google. Check your internet connection and try again."
        current = current.__cause__ or current.__context__
    return 502, "provider_unknown", "Kazu could not complete the AI request. The backend logged a safe error category; your key was not included."
