import math
import time
from collections import defaultdict
from itertools import permutations


class RagOptimizer:
    """
    Optimizes the order and content of RAG artifacts to improve caching and relevance.
    """

    def __init__(self, weights, artifact_excludable_factor):
        """
        Initializes the RagOptimizer.

        Args:
            weights (dict): A dictionary of weights for scoring.
            artifact_excludable_factor (float): The percentile of the most distant RAG
                                                results that can be replaced.
        """
        self.weights = weights
        self.artifact_excludable_factor = artifact_excludable_factor
        self.TOP_N_PERMUTATIONS = 4  # Number of top artifacts to test permutations on

    def _calculate_average(self, lst):
        if not lst:
            return 0
        return sum(lst) / len(lst)

    def optimize_rag_for_caching(
        self,
        k_nearest_neighbors_with_distances,
        prompt_history,
        artifact_metadata,
        prefix_cache_metadata,
    ):
        """
        Implements the RAG optimization algorithm based on distance, cache hits, and
        historical usage.
        """
        k_nearest_neighbors_with_distances = [
            item for item in k_nearest_neighbors_with_distances if len(item) == 2
        ]
        k = len(k_nearest_neighbors_with_distances)
        if k == 0:
            return [], ""

        # 1. Identify Replaceable Artifacts
        num_to_replace = math.floor(k * self.artifact_excludable_factor)
        sorted_neighbors = sorted(
            k_nearest_neighbors_with_distances, key=lambda item: item[1], reverse=True
        )
        core_artifacts = {
            art_id for art_id, dist in sorted_neighbors[num_to_replace:]
        }
        all_rag_artifacts = {art_id for art_id, dist in sorted_neighbors}

        # 2. Find Strong Cache Candidates for Replacement
        cache_replacement_candidates = defaultdict(int)
        for prefix in prefix_cache_metadata:
            artifacts_in_prefix = prefix.split()
            for artifact in artifacts_in_prefix:
                if artifact not in all_rag_artifacts:
                    cache_replacement_candidates[artifact] += 1

        # 3. Perform the Replacement
        sorted_cache_candidates = sorted(
            cache_replacement_candidates.items(), key=lambda item: item[1], reverse=True
        )
        top_cache_candidates = [
            art_id for art_id, score in sorted_cache_candidates[:num_to_replace]
        ]
        final_candidate_artifacts = list(core_artifacts) + top_cache_candidates

        # 4. Score and Predictively Reorder the Final Candidate Set
        scored_artifacts = {}
        for artifact_id in final_candidate_artifacts:
            stats = artifact_metadata.get(artifact_id)
            if not stats:
                continue

            frequency = stats.get("frequency", 0)
            positions = stats.get("positions", [])
            last_modified = stats.get("last_modified_timestamp", time.time())
            stability_score = time.time() - last_modified
            avg_position = self._calculate_average(positions)

            final_score = (
                (self.weights.get("frequency", 1.0) * frequency)
                - (self.weights.get("position", 1.0) * avg_position)
                + (self.weights.get("stability", 1.0) * stability_score)
            )
            scored_artifacts[artifact_id] = final_score

        initial_sorted_artifacts = [
            art_id
            for art_id, score in sorted(
                scored_artifacts.items(), key=lambda item: item[1], reverse=True
            )
        ]

        # 5. Find the Best Prefix Order for Maximum Cache Hits
        if not initial_sorted_artifacts:
            return [], ""

        best_ordering = initial_sorted_artifacts
        max_prefix_match_score = -1
        best_prefix_string = ""

        n_to_permute = min(len(initial_sorted_artifacts), self.TOP_N_PERMUTATIONS)
        top_n_artifacts = initial_sorted_artifacts[:n_to_permute]

        for p in permutations(top_n_artifacts):
            perm = list(p)
            current_prefix_string = " ".join(perm)

            historical_hits = sum(
                1
                for prompt in prompt_history
                if prompt.startswith(current_prefix_string)
            )
            is_in_active_cache = 1 if current_prefix_string in prefix_cache_metadata else 0

            current_prefix_score = (historical_hits * self.weights.get("historical_hits", 1.0)) + \
                                   (is_in_active_cache * self.weights.get("cache_hits", 1.0))

            if current_prefix_score > max_prefix_match_score:
                max_prefix_match_score = current_prefix_score
                remaining_artifacts = [art for art in initial_sorted_artifacts if art not in perm]
                best_ordering = perm + remaining_artifacts
                best_prefix_string = current_prefix_string

        # 6. Return the final, optimized order and the matched prefix
        return best_ordering, best_prefix_string
