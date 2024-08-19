from llama_cpp import Llama

from dir_assistant.assistant.base_embed import BaseEmbed


class LlamaCppEmbed(BaseEmbed):
    def __init__(self, model_path, embed_options):
        self.embed = Llama(model_path=model_path, embedding=True, **embed_options)

    def create_embedding(self, text):
        return self.embed.create_embedding([text])["data"][0]["embedding"]

    def get_chunk_size(self):
        return self.embed.context_params.n_ctx

    def count_tokens(self, text):
        return len(self.embed.tokenize(bytes(text, "utf-8")))
