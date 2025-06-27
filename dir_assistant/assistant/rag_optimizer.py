import math
import time
from collections import defaultdict


class RagOptimizer:
    """
    Optimizes the order and content of RAG artifacts to improve caching and relevance.
    """

    def __init__(self, weights, artifact_excludable_factor):
        """
        Initializes the RagOptimizer.
        Args:
            weights (dict): A dictionary of weights for scoring. It can include
                            weights for 'frequency', 'position', 'stability',
                            'historical_hits', and 'prefix_length'.
            artifact_excludable_factor (float): The percentile of the most distant RAG
                                                results that can be replaced.
        """
        self.weights = weights
        self.artifact_excludable_factor = artifact_excludable_factor

    def _calculate_average(self, lst):
        """Calculates the average of a list, returning 0 for an empty list."""
        return sum(lst) / len(lst) if lst else 0

    def _score_artifact(self, artifact_id, artifact_metadata, current_time):
        """Calculates a general-purpose score for a single artifact."""
        stats = artifact_metadata.get(artifact_id)
        if not stats:
            return 0  # Return a neutral score if no metadata exists

        frequency = stats.get("frequency", 0)
        positions = stats.get("positions", [])
        last_modified = stats.get("last_modified_timestamp", current_time)

        stability_score = current_time - last_modified
        avg_position = self._calculate_average(positions)

        final_score = (
                (self.weights.get("frequency", 1.0) * frequency)
                - (self.weights.get("position", 1.0) * avg_position)
                + (self.weights.get("stability", 1.0) * stability_score)
        )
        return final_score

    def optimize_rag_for_caching(
            self,
            k_nearest_neighbors_with_distances,
            prompt_history,
            artifact_metadata,
            prefix_cache_metadata,
    ):
        print("artifact_metadata", [v for k, v in artifact_metadata.items()])
        print("prefix_cache_metadata", [v for k, v in prefix_cache_metadata.items()])
        """
        Optimizes RAG artifacts by finding the longest possible cached prefix.

        This method is reworked to provide stable ordering, especially when
        metadata is not available, by using the initial semantic search
        distance as a tie-breaker.

        The method follows a three-tiered strategy:
        1.  **Full Match:** Attempts to find a complete cached prefix that
            can be fully constructed from the available artifacts.
        2.  **Partial Match:** If no full match is found, it searches for the
            longest possible partial prefix that can be constructed.
        3.  **Fallback:** If no prefix overlap is found, it orders all artifacts
            by their historical scores, falling back to the original semantic
            search order.
        """
        # This initial input processing block is preserved for compatibility.
        processed_neighbors = []
        if k_nearest_neighbors_with_distances and isinstance(
                k_nearest_neighbors_with_distances[0], dict
        ):
            for i, chunk in enumerate(k_nearest_neighbors_with_distances):
                processed_neighbors.append((chunk.get("text", ""), i))
        else:
            processed_neighbors = k_nearest_neighbors_with_distances
        if (
                processed_neighbors
                and isinstance(processed_neighbors[0], (list, tuple))
                and len(processed_neighbors[0]) > 0
                and isinstance(processed_neighbors[0][0], list)
        ):
            processed_neighbors = [
                (item[0][0], item[1]) for item in processed_neighbors if item[0]
            ]
        k_nearest_neighbors_with_distances = [
            item for item in processed_neighbors if len(item) == 2
        ]

        if not k_nearest_neighbors_with_distances:
            return [], ""

        # Create a lookup for original semantic distance (lower is better).
        # This will be the ultimate tie-breaker to ensure stable ordering.
        # Assumes input is sorted by relevance (ascending distance).
        artifact_distances = {
            art_id: dist for art_id, dist in k_nearest_neighbors_with_distances
        }

        k = len(k_nearest_neighbors_with_distances)
        current_time = time.time()

        # 1. Create the artifact pool
        num_to_replace = math.floor(k * self.artifact_excludable_factor)

        sorted_neighbors_desc = sorted(
            k_nearest_neighbors_with_distances, key=lambda item: item[1], reverse=True
        )

        excludable_artifacts = {
            art_id for art_id, dist in sorted_neighbors_desc[:num_to_replace]
        }
        core_artifacts = set(artifact_distances.keys()) - excludable_artifacts

        cache_replacement_candidates = defaultdict(int)
        for prefix in prefix_cache_metadata:
            for artifact in prefix.split():
                if artifact not in artifact_distances:
                    cache_replacement_candidates[artifact] += 1

        sorted_cache_candidates = sorted(
            cache_replacement_candidates.items(), key=lambda item: item[1], reverse=True
        )
        top_cache_candidates = {
            art_id for art_id, score in sorted_cache_candidates[:num_to_replace]
        }
        final_candidate_artifacts = core_artifacts.union(top_cache_candidates)

        if not final_candidate_artifacts:
            return [], ""

        def sort_key(artifact_id):
            """Defines the sorting logic: score (desc), then distance (asc)."""
            score = self._score_artifact(artifact_id, artifact_metadata, current_time)
            distance = artifact_distances.get(artifact_id, float('inf'))
            return -score, distance

        # 2. Score and sort known prefixes
        scored_prefixes = {}
        for prefix in prefix_cache_metadata:
            historical_hits = sum(
                1 for prompt in prompt_history if prompt.startswith(prefix)
            )
            score = (historical_hits * self.weights.get("historical_hits", 1.0)) + (
                    len(prefix.split()) * self.weights.get("prefix_length", 0.1)
            )
            scored_prefixes[prefix] = score

        sorted_cached_prefixes = sorted(
            scored_prefixes.keys(), key=lambda p: scored_prefixes[p], reverse=True
        )

        # 3. Primary Goal: Find a full prefix match
        for prefix in sorted_cached_prefixes:
            prefix_artifacts = prefix.split()
            if set(prefix_artifacts).issubset(final_candidate_artifacts):
                remaining_artifacts = final_candidate_artifacts - set(prefix_artifacts)
                sorted_remaining = sorted(list(remaining_artifacts), key=sort_key)
                return prefix_artifacts + sorted_remaining, prefix

        # 4. Secondary Goal: Find the best partial prefix match
        best_partial_prefix_list = []
        for prefix in sorted_cached_prefixes:
            prefix_artifacts = prefix.split()
            current_partial_match = [
                art for art in prefix_artifacts if art in final_candidate_artifacts
            ]
            # Only consider sequential matches from the start of the prefix
            if len(current_partial_match) == len(prefix_artifacts) or (
                    current_partial_match and prefix_artifacts[:len(current_partial_match)] == current_partial_match
            ):
                if len(current_partial_match) > len(best_partial_prefix_list):
                    best_partial_prefix_list = current_partial_match

        if best_partial_prefix_list:
            best_prefix_string = " ".join(best_partial_prefix_list)
            remaining_artifacts = final_candidate_artifacts - set(best_partial_prefix_list)
            sorted_remaining = sorted(list(remaining_artifacts), key=sort_key)
            return best_partial_prefix_list + sorted_remaining, best_prefix_string

        # 5. Fallback: No prefix overlap found
        fallback_sorted_artifacts = sorted(list(final_candidate_artifacts), key=sort_key)
        return fallback_sorted_artifacts, ""