import sqlite3
import time
import json
from sqlitedict import SqliteDict
from collections import defaultdict

from dir_assistant.assistant.models import create_prompt_history_table

class CacheManager:
    """
    Manages caching for RAG optimization, including a prefix cache for API query reuse
    and a prompt history for metadata computation.
    """

    def __init__(self, prefix_cache_path, prompt_history_path, api_context_cache_ttl):
        """
        Initializes the CacheManager.

        Args:
            prefix_cache_path (str): Path to the prefix cache SQLite database.
            prompt_history_path (str): Path to the prompt history SQLite database.
            api_context_cache_ttl (int): Time-to-live for cache entries in seconds.
        """
        self.prefix_cache_path = prefix_cache_path
        self.prompt_history_path = prompt_history_path
        self.api_context_cache_ttl = api_context_cache_ttl
        
        self.prefix_cache = SqliteDict(self.prefix_cache_path, autocommit=True)
        self._initialize_prompt_history_db()

    def _initialize_prompt_history_db(self):
        """Creates the prompt_history table if it doesn't exist."""
        with sqlite3.connect(self.prompt_history_path) as conn:
            create_prompt_history_table(conn)

    def get_non_expired_prefixes(self):
        """
        Retrieves non-expired prefixes from the cache and cleans up expired ones.

        Returns:
            dict: A dictionary of {prefix_string: metadata}.
        """
        non_expired = {}
        now = time.time()
        
        keys = list(self.prefix_cache.keys())

        for prefix in keys:
            metadata = self.prefix_cache.get(prefix)
            if isinstance(metadata, dict) and now - metadata.get('last_hit_timestamp', 0) < self.api_context_cache_ttl:
                non_expired[prefix] = metadata
            else:
                if prefix in self.prefix_cache:
                    del self.prefix_cache[prefix]
        
        return non_expired

    def update_prefix_hit(self, prefix_string):
        """
        Updates the last hit timestamp for a given prefix string.

        Args:
            prefix_string (str): The prefix that had a cache hit.
        """
        self.prefix_cache[prefix_string] = {'last_hit_timestamp': time.time()}

    def add_prompt_to_history(self, prompt_string, ordered_artifacts):
        """
        Adds a processed prompt and its associated artifacts to the history.

        Args:
            prompt_string (str): The full prompt string sent to the LLM.
            ordered_artifacts (list): A list of artifact IDs (chunk texts) in the order they appeared.
        """
        artifacts_json = json.dumps(ordered_artifacts)
        with sqlite3.connect(self.prompt_history_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO prompt_history (prompt, artifacts_json, timestamp) VALUES (?, ?, ?)",
                (prompt_string, artifacts_json, time.time())
            )

    def get_prompt_history(self):
        """
        Retrieves all prompt strings from the history.

        Returns:
            list: A list of all prompt strings.
        """
        with sqlite3.connect(self.prompt_history_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT prompt FROM prompt_history ORDER BY timestamp ASC")
            return [row[0] for row in cursor.fetchall()]

    def compute_artifact_metadata_from_history(self):
        """
        Computes artifact frequency and positions based on the entire prompt history.

        Returns:
            dict: A dictionary of {artifact_id: {'frequency': int, 'positions': list}}.
        """
        artifact_stats = defaultdict(lambda: {'frequency': 0, 'positions': []})
        with sqlite3.connect(self.prompt_history_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT artifacts_json FROM prompt_history")
            for row in cursor.fetchall():
                try:
                    artifacts = json.loads(row[0])
                    for i, artifact_id in enumerate(artifacts):
                        artifact_stats[artifact_id]['frequency'] += 1
                        artifact_stats[artifact_id]['positions'].append(i)
                except json.JSONDecodeError:
                    continue
        return dict(artifact_stats)
    
    def close(self):
        """Closes the connection to the prefix cache."""
        self.prefix_cache.close()

