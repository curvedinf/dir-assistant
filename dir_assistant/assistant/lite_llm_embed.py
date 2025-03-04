from time import sleep

from litellm import embedding, token_counter

from dir_assistant.assistant.base_embed import BaseEmbed


class LiteLlmEmbed(BaseEmbed):
    def __init__(self, lite_llm_embed_completion_options, lite_llm_embed_context_size, delay=0):
        self.lite_llm_embed_completion_options = lite_llm_embed_completion_options
        self.chunk_size = lite_llm_embed_context_size
        self.delay = delay

    def create_embedding(self, text):
        if self.delay:
            sleep(self.delay)
        if not text:
            text = "--empty--"
        return embedding(**self.lite_llm_embed_completion_options, input=text)["data"][0][
            "embedding"
        ]

    def get_chunk_size(self):
        return self.chunk_size

    def count_tokens(self, text):
        return token_counter(
            model=self.lite_llm_embed_completion_options["model"], messages=[{"role": "user", "content": text}]
        )
