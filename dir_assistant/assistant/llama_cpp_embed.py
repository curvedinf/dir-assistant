import sys

try:
    from llama_cpp import Llama
except:
    pass

from dir_assistant.assistant.base_embed import BaseEmbed


class LlamaCppEmbed(BaseEmbed):
    def __init__(self, model_path, embed_options):
        try:
            self.embed = Llama(model_path=model_path, embedding=True, **embed_options)
        except NameError:
            sys.stderr.write(
                "You currently have ACTIVE_EMBED_IS_LOCAL set to true but have not installed llama-cpp-python. "
                "Choose one of the following to continue:\n"
                "1) Set ACTIVE_EMBED_IS_LOCAL to false. Open the config file with 'dir-assistant config open'\n"
                "2) Run 'pip install llama-cpp-python' and try again.\n"
            )
            sys.stderr.flush()
            sys.exit(1)

    def create_embedding(self, text):
        return self.embed.create_embedding([text])["data"][0]["embedding"]

    def get_chunk_size(self):
        return self.embed.context_params.n_ctx

    def count_tokens(self, text):
        return len(self.embed.tokenize(bytes(text, "utf-8")))
