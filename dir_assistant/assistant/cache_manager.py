import json
import time
from collections import defaultdict

from sqlitedict import SqliteDict


class CacheManager:
    """
    Manages caching for RAG optimization, including a prefix cache for API query reuse
    and a prompt history for metadata computation, using SqliteDict for both.
    """

    def __init__(
        self,
        prefix_cache_path: str,
        prompt_history_path: str,
        api_context_cache_ttl: int,
    ):
        """
        Initializes the CacheManager.

        Args:
            prefix_cache_path (str): Path to the prefix cache SQLite database.
            prompt_history_path (str): Path to the prompt history SQLite database.
            api_context_cache_ttl (int): Time-to-live for cache entries in seconds.
        """
        self.api_context_cache_ttl = api_context_cache_ttl

        self.prefix_cache = SqliteDict(prefix_cache_path, autocommit=True)
        self.prompt_history = SqliteDict(prompt_history_path, autocommit=True)

    def get_non_expired_prefixes(self) -> dict:
        """
        Retrieves non-expired prefixes from the cache and cleans up expired ones.

        Returns:
            dict: A dictionary of {prefix_string: metadata}.
        """
        now = time.time()
        expired_keys = [
            key
            for key, value in self.prefix_cache.items()
            if not isinstance(value, dict)
            or now - value.get("last_hit_timestamp", 0) >= self.api_context_cache_ttl
        ]

        for key in expired_keys:
            del self.prefix_cache[key]

        return dict(self.prefix_cache.items())

    def update_prefix_hit(self, prefix_artifacts: list):
        """
        Updates the last hit timestamp for a given prefix.

        Args:
            prefix_artifacts (list): The prefix artifacts that had a cache hit.
        """
        # Convert list to a canonical string representation for use as a key
        prefix_string = json.dumps(sorted(prefix_artifacts))
        self.prefix_cache[prefix_string] = {"last_hit_timestamp": time.time()}

    def add_prompt_to_history(self, prompt_string: str, ordered_artifacts: list):
        """
        Adds a processed prompt and its associated artifacts to the history.

        Args:
            prompt_string (str): The full prompt string sent to the LLM.
            ordered_artifacts (list): A list of artifact IDs (chunk texts) in the order they appeared.
        """
        timestamp = time.time()
        # Use a unique key, like timestamp, for each entry
        self.prompt_history[str(timestamp)] = {
            "prompt": prompt_string,
            "artifacts": ordered_artifacts,
        }

    def get_prompt_history(self) -> list:
        """
        Retrieves all prompt history entries from the history, sorted by timestamp.

        Returns:
            list: A list of all prompt history entries.
        """
        # Sorting by the key (timestamp) to maintain order
        return [
            item
            for _, item in sorted(
                self.prompt_history.items(), key=lambda x: float(x[0])
            )
        ]

    def compute_artifact_metadata_from_history(self) -> dict:
        """
        Computes artifact frequency and positions based on the entire prompt history.

        Returns:
            dict: A dictionary of {artifact_id: {'frequency': int, 'positions': list}}.
        """
        artifact_stats = defaultdict(lambda: {"frequency": 0, "positions": []})
        for _, entry in self.prompt_history.items():
            artifacts = entry.get("artifacts", [])
            for i, artifact_id in enumerate(artifacts):
                artifact_stats[artifact_id]["frequency"] += 1
                artifact_stats[artifact_id]["positions"].append(i)
        return dict(artifact_stats)

    def close(self):
        """Closes the connections to the caches."""
        self.prefix_cache.close()
        self.prompt_history.close()
