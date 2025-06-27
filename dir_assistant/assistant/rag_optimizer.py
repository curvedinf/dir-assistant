import math
import time
from collections import defaultdict


class RagOptimizer:
    """
    Optimizes the order and content of RAG artifacts to improve caching and relevance.
    """

    ARTIFACT_SEPARATOR = "<--|-->"

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
        #print("artifact_metadata", [repr(v)[:100] for k, v in artifact_metadata.items()])
        print(f"RAG Optimizer: Received {len(prefix_cache_metadata)} cached prefixes.")
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

        # IGNORE artifact_excludable_factor -> keep **all** artifacts
        final_candidate_artifacts = set(artifact_distances.keys())
        print(f"RAG Optimizer: Final candidate artifacts (count: {len(final_candidate_artifacts)})")

        if not final_candidate_artifacts:
            return [], ""

        current_time = time.time()

        def sort_key(artifact_id):
            """Defines the sorting logic: score (desc), then distance (asc)."""
            score = self._score_artifact(artifact_id, artifact_metadata, current_time)
            distance = artifact_distances.get(artifact_id, float("inf"))
            return -score, distance

        # ------------------------------------------------------------------
        # 1. Find the LONGEST cached prefix that is fully contained
        #    within the current set of artifacts.
        #    If several prefixes share the same length, prefer the one with
        #    the highest historical hit count. This guarantees that the most
        #    frequently used of the longest prefixes is selected.
        # ------------------------------------------------------------------
        candidate_prefixes = [
            p for p in prefix_cache_metadata if set(p.split(self.ARTIFACT_SEPARATOR)).issubset(final_candidate_artifacts)
        ]
        print(f"RAG Optimizer: Found {len(candidate_prefixes)} candidate prefixes.")

        best_prefix = ""
        if candidate_prefixes:
            # Find maximum length first
            max_len = max(len(p.split(self.ARTIFACT_SEPARATOR)) for p in candidate_prefixes)
            longest_candidates = [p for p in candidate_prefixes if len(p.split(self.ARTIFACT_SEPARATOR)) == max_len]

            if len(longest_candidates) == 1:
                best_prefix = longest_candidates[0]
            else:
                # Tie-break using historical hit count
                def get_historical_hits(prefix_str):
                    p_artifacts = prefix_str.split(self.ARTIFACT_SEPARATOR)
                    len_p = len(p_artifacts)
                    count = 0
                    for hist_entry in prompt_history:
                        hist_artifacts = hist_entry.get("artifacts", [])
                        if len(hist_artifacts) >= len_p and hist_artifacts[:len_p] == p_artifacts:
                            count += 1
                    return count

                best_prefix = max(
                    longest_candidates,
                    key=get_historical_hits,
                )

        if best_prefix:
            prefix_artifacts = best_prefix.split(self.ARTIFACT_SEPARATOR)
            print(f"RAG Optimizer: Best prefix found: '{best_prefix[:100]}' with length {len(prefix_artifacts)}")
            remaining_artifacts = final_candidate_artifacts - set(prefix_artifacts)
            sorted_remaining = sorted(list(remaining_artifacts), key=sort_key)
            return prefix_artifacts + sorted_remaining, best_prefix

        # ------------------------------------------------------------------
        # 2. No cached prefix intersects all artifacts -> just sort everything.
        # ------------------------------------------------------------------
        print("RAG Optimizer: No suitable cached prefix found. Sorting all artifacts.")
        fallback_sorted_artifacts = sorted(list(final_candidate_artifacts), key=sort_key)
        return fallback_sorted_artifacts, ""