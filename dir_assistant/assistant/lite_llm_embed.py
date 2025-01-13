from time import sleep

from litellm import embedding, token_counter

from dir_assistant.assistant.base_embed import BaseEmbed


class LiteLlmEmbed(BaseEmbed):
    def __init__(self, lite_llm_embed_model, chunk_size=8192, delay=0):
        self.lite_llm_model = lite_llm_embed_model
        self.chunk_size = chunk_size
        self.delay = delay

    def create_embedding(self, text):
        if self.delay:
            sleep(self.delay)
        return embedding(model=self.lite_llm_model, input=text, timeout=600)["data"][0][
            "embedding"
        ]

    def get_chunk_size(self):
        return self.chunk_size

    def count_tokens(self, text):
        return token_counter(
            model=self.lite_llm_model, messages=[{"user": "role", "content": text}]
        )
