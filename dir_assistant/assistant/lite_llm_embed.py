from time import sleep

from litellm import embedding
from litellm import exceptions as litellm_exceptions
from litellm import token_counter

from dir_assistant.assistant.base_embed import BaseEmbed


class LiteLlmEmbed(BaseEmbed):
    def __init__(
        self, lite_llm_embed_completion_options, lite_llm_embed_context_size, delay=0
    ):
        self.lite_llm_embed_completion_options = lite_llm_embed_completion_options
        self.chunk_size = lite_llm_embed_context_size
        self.delay = delay

    def create_embedding(self, text):
        # Hardcoded retry settings
        max_retries = 3
        retry_delay_seconds = 1

        if self.delay:
            sleep(self.delay)

        # Ensure text is not None, empty, or just whitespace,
        # as some APIs reject such inputs.
        if not text or text.isspace():
            text_to_embed = "--empty--"
        else:
            text_to_embed = text

        current_retry = 0
        while current_retry <= max_retries:
            try:
                # Use text_to_embed which has been sanitized
                response = embedding(
                    **self.lite_llm_embed_completion_options, input=text_to_embed
                )
                return response["data"][0]["embedding"]
            except litellm_exceptions.APIConnectionError as e:
                current_retry += 1
                if current_retry > max_retries:
                    raise
                sleep(retry_delay_seconds)

        # This line should ideally not be reached if the loop logic is correct (always returns or raises).
        # Added for robustness in case of unforeseen loop exit.
        raise Exception(
            f"[dir-assistant] LiteLlmEmbed Error: Embedding failed for '{text_to_embed[:50]}...' "
            "after exhausting retries or due to an unhandled state."
        )

    def get_chunk_size(self):
        return self.chunk_size

    def count_tokens(self, text):
        # Ensure text is not None, empty, or just whitespace,
        # as some APIs reject such inputs.
        if not text or text.isspace():
            text_to_embed = "--empty--"
        else:
            text_to_embed = text
        return token_counter(
            model=self.lite_llm_embed_completion_options["model"],
            messages=[{"role": "user", "content": text_to_embed}],
        )

    def get_config(self):
        return self.lite_llm_embed_completion_options
