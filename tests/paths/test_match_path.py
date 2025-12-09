"""Tests for the MatchPath class."""

import pytest
from src.paths.match_path import MatchPath
from src.core.match_score import MatchScore
from src.core.match_format import MatchFormat
from src.core.set_score import SetScore

# Default match formats for tests
BEST_OF_3 = MatchFormat(bestOfSets=3)
BEST_OF_5 = MatchFormat(bestOfSets=5)


class TestMatchPathInit:
    """Tests for MatchPath initialization."""

    def test_init_with_blank_score(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        path = MatchPath(ms)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].sets(pov=1) == (0, 0)

    def test_init_with_non_zero_score(self):
        ms = MatchScore(1, 0, BEST_OF_3)
        path = MatchPath(ms)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].sets(pov=1) == (1, 0)

    def test_init_with_final_score(self):
        ms = MatchScore(2, 0, BEST_OF_3)
        path = MatchPath(ms)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].isFinal

    def test_init_best_of_5(self):
        ms = MatchScore(1, 2, BEST_OF_5)
        path = MatchPath(ms)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].sets(pov=1) == (1, 2)

    def test_init_invalid_score_type(self):
        with pytest.raises(ValueError, match="initialScore must be a MatchScore"):
            MatchPath("invalid")
        with pytest.raises(ValueError, match="initialScore must be a MatchScore"):
            MatchPath(None)
        with pytest.raises(ValueError, match="initialScore must be a MatchScore"):
            MatchPath(42)

    def test_init_with_set_in_progress_raises(self):
        """Cannot create MatchPath with a set in progress."""
        ss = SetScore(3, 2, False, BEST_OF_3)
        ms = MatchScore(1, 0, BEST_OF_3, setScore=ss)
        with pytest.raises(ValueError, match="cannot have a set in progress"):
            MatchPath(ms)


class TestMatchPathScoreHistory:
    """Tests for scoreHistory property."""

    def test_score_history_returns_scores(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        path = MatchPath(ms)
        assert path.scoreHistory is path._scores

    def test_score_history_initial_length(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        path = MatchPath(ms)
        assert len(path.scoreHistory) == 1

    def test_score_history_entry_is_match_score(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        path = MatchPath(ms)
        assert isinstance(path.scoreHistory[0], MatchScore)


class TestMatchPathIncrement:
    """Tests for increment method."""

    def test_increment_from_blank(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        path = MatchPath(ms)
        result = path.increment()

        assert isinstance(result, tuple)
        assert len(result) == 2

        path1, path2 = result
        assert len(path1.scoreHistory) == 2
        assert len(path2.scoreHistory) == 2
        assert path1.scoreHistory[-1].sets(pov=1) == (1, 0)
        assert path2.scoreHistory[-1].sets(pov=1) == (0, 1)

    def test_increment_from_mid_match(self):
        ms = MatchScore(1, 0, BEST_OF_3)
        path = MatchPath(ms)
        result = path.increment()

        assert isinstance(result, tuple)
        path1, path2 = result
        assert path1.scoreHistory[-1].sets(pov=1) == (2, 0)
        assert path2.scoreHistory[-1].sets(pov=1) == (1, 1)

    def test_increment_from_final_score(self):
        ms = MatchScore(2, 0, BEST_OF_3)
        path = MatchPath(ms)
        result = path.increment()

        # Should return a copy of self, not a tuple
        assert isinstance(result, MatchPath)
        assert result is not path  # deepcopy
        assert len(result.scoreHistory) == 1
        assert result.scoreHistory[0].sets(pov=1) == (2, 0)

    def test_increment_preserves_original(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        path = MatchPath(ms)
        original_len = len(path.scoreHistory)

        path.increment()

        # Original path should be unchanged
        assert len(path.scoreHistory) == original_len

    def test_increment_creates_independent_copies(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        path = MatchPath(ms)
        path1, path2 = path.increment()

        # Modifying one shouldn't affect the other
        path1._scores.append(MatchScore(2, 0, BEST_OF_3))
        assert len(path2.scoreHistory) == 2


class TestMatchPathGenerateAllPaths:
    """Tests for generateAllPaths static method."""

    def test_generate_from_blank_best_of_3(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        # Should generate multiple paths
        assert len(paths) > 0

    def test_generate_from_blank_best_of_5(self):
        ms = MatchScore(0, 0, BEST_OF_5)
        paths = MatchPath.generateAllPaths(ms)

        # Should generate more paths than best-of-3
        paths_bo3 = MatchPath.generateAllPaths(MatchScore(0, 0, BEST_OF_3))
        assert len(paths) > len(paths_bo3)

    def test_generate_from_1_0(self):
        ms = MatchScore(1, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        # Fewer paths than from 0-0
        assert len(paths) > 0
        # First path should end with P1 winning 2-0
        first_path = paths[0]
        assert first_path.scoreHistory[-1].sets(pov=1) == (2, 0)

    def test_generate_from_final_score(self):
        ms = MatchScore(2, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        # Only one path - the match is already over
        assert len(paths) == 1
        assert len(paths[0].scoreHistory) == 1

    def test_all_paths_start_with_initial_score(self):
        ms = MatchScore(1, 1, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        for path in paths:
            assert path.scoreHistory[0].sets(pov=1) == (1, 1)

    def test_all_paths_end_in_final(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        for path in paths:
            last_score = path.scoreHistory[-1]
            assert last_score.isFinal


class TestMatchPathStr:
    """Tests for __str__ method."""

    def test_str_single_score(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        path = MatchPath(ms)
        result = str(path)

        assert result == "[(0, 0)]"

    def test_str_multiple_scores(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        path = MatchPath(ms)
        path1, _ = path.increment()
        result = str(path1)

        assert result == "[(0, 0), (1, 0)]"

    def test_str_format(self):
        ms = MatchScore(1, 0, BEST_OF_3)
        path = MatchPath(ms)
        result = str(path)

        assert result.startswith("[")
        assert result.endswith("]")
        assert "(1, 0)" in result


class TestMatchPathWinnerDistribution:
    """Tests verifying correct distribution of winning paths."""

    def test_p1_and_p2_win_paths_exist(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        p1_wins = [p for p in paths if p.scoreHistory[-1].winner == 1]
        p2_wins = [p for p in paths if p.scoreHistory[-1].winner == 2]

        assert len(p1_wins) > 0
        assert len(p2_wins) > 0

    def test_symmetric_paths_from_blank(self):
        ms = MatchScore(0, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        p1_wins = len([p for p in paths if p.scoreHistory[-1].winner == 1])
        p2_wins = len([p for p in paths if p.scoreHistory[-1].winner == 2])

        # From 0-0, the number of P1 and P2 winning paths should be equal
        assert p1_wins == p2_wins

    def test_asymmetric_paths_from_lead(self):
        ms = MatchScore(1, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        p1_wins = len([p for p in paths if p.scoreHistory[-1].winner == 1])
        p2_wins = len([p for p in paths if p.scoreHistory[-1].winner == 2])

        # From 1-0, P1 should have more winning paths
        assert p1_wins > p2_wins


class TestMatchPathSpecificScenarios:
    """Tests for specific match scenarios."""

    def test_straight_sets_path_bo3(self):
        """Test the path where P1 wins 2-0."""
        ms = MatchScore(0, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        # Find the straight sets path (all P1 wins)
        straight_paths = [p for p in paths
                         if p.scoreHistory[-1].sets(pov=1) == (2, 0)]

        assert len(straight_paths) == 1
        straight_path = straight_paths[0]

        # Should be 3 scores: 0-0, 1-0, 2-0
        assert len(straight_path.scoreHistory) == 3

        expected = [(0, 0), (1, 0), (2, 0)]
        for i, score in enumerate(straight_path.scoreHistory):
            assert score.sets(pov=1) == expected[i]

    def test_straight_sets_path_bo5(self):
        """Test the path where P1 wins 3-0."""
        ms = MatchScore(0, 0, BEST_OF_5)
        paths = MatchPath.generateAllPaths(ms)

        # Find the straight sets path
        straight_paths = [p for p in paths
                         if p.scoreHistory[-1].sets(pov=1) == (3, 0)]

        assert len(straight_paths) == 1
        straight_path = straight_paths[0]

        # Should be 4 scores: 0-0, 1-0, 2-0, 3-0
        assert len(straight_path.scoreHistory) == 4

    def test_full_distance_path_bo3(self):
        """Test paths that go the full distance (2-1)."""
        ms = MatchScore(0, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        # Find paths ending in 2-1
        full_paths = [p for p in paths
                      if p.scoreHistory[-1].sets(pov=1) == (2, 1)]

        assert len(full_paths) > 0

        # Each full distance path should have 4 scores (0-0, then 3 more)
        for path in full_paths:
            assert len(path.scoreHistory) == 4

    def test_full_distance_path_bo5(self):
        """Test paths that go the full distance (3-2)."""
        ms = MatchScore(0, 0, BEST_OF_5)
        paths = MatchPath.generateAllPaths(ms)

        # Find paths ending in 3-2
        full_paths = [p for p in paths
                      if p.scoreHistory[-1].sets(pov=1) == (3, 2)]

        assert len(full_paths) > 0

        # Each full distance path should have 6 scores (0-0, then 5 more)
        for path in full_paths:
            assert len(path.scoreHistory) == 6


class TestMatchPathEdgeCases:
    """Tests for edge cases."""

    def test_generate_from_match_point_p1(self):
        """P1 at 1-0 in best-of-3 (one set from winning)."""
        ms = MatchScore(1, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        # Multiple paths possible
        assert len(paths) > 1

        # Shortest path: P1 wins next set
        shortest = min(paths, key=lambda p: len(p.scoreHistory))
        assert len(shortest.scoreHistory) == 2
        assert shortest.scoreHistory[-1].sets(pov=1) == (2, 0)

    def test_generate_from_match_point_p2(self):
        """P2 at 0-1 in best-of-3 (one set from winning)."""
        ms = MatchScore(0, 1, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        # Multiple paths possible
        assert len(paths) > 1

        # Check that both 0-2 (P2 wins) and 1-1 paths exist
        end_scores = {p.scoreHistory[-1].sets(pov=1) for p in paths}
        # 0-2 is a final score (P2 wins), 2-1 and 1-2 are also possible finals
        assert (0, 2) in end_scores or (1, 2) in end_scores or (2, 1) in end_scores

    def test_path_lengths_vary(self):
        """Paths from same start should have varying lengths."""
        ms = MatchScore(0, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        lengths = set(len(p.scoreHistory) for p in paths)

        # Should have multiple different lengths
        assert len(lengths) > 1

        # Shortest possible: 2 sets to win (3 scores including start)
        assert min(lengths) == 3

        # Longest: full 3 sets played (4 scores including start)
        assert max(lengths) == 4

    def test_path_lengths_best_of_5(self):
        """Test path lengths for best-of-5."""
        ms = MatchScore(0, 0, BEST_OF_5)
        paths = MatchPath.generateAllPaths(ms)

        lengths = set(len(p.scoreHistory) for p in paths)

        # Shortest: 3 sets to win (4 scores)
        assert min(lengths) == 4

        # Longest: full 5 sets (6 scores)
        assert max(lengths) == 6

    def test_path_count_best_of_3(self):
        """Verify total number of paths in best-of-3."""
        ms = MatchScore(0, 0, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        # From 0-0 in best-of-3:
        # P1 wins 2-0: 1 path
        # P1 wins 2-1: 2 paths (lose first or second set)
        # P2 wins 0-2: 1 path
        # P2 wins 1-2: 2 paths (win first or second set)
        # Total: 6 paths
        assert len(paths) == 6

    def test_path_count_best_of_5(self):
        """Verify total number of paths in best-of-5."""
        ms = MatchScore(0, 0, BEST_OF_5)
        paths = MatchPath.generateAllPaths(ms)

        # From 0-0 in best-of-5:
        # P1 wins 3-0: 1 path
        # P1 wins 3-1: C(3,1) = 3 paths
        # P1 wins 3-2: C(4,2) = 6 paths
        # P2 wins 0-3: 1 path
        # P2 wins 1-3: C(3,1) = 3 paths
        # P2 wins 2-3: C(4,2) = 6 paths
        # Total: 2 * (1 + 3 + 6) = 20 paths
        assert len(paths) == 20

    def test_from_1_1_best_of_3(self):
        """Test from 1-1 in best-of-3 (deciding set)."""
        ms = MatchScore(1, 1, BEST_OF_3)
        paths = MatchPath.generateAllPaths(ms)

        # Only 2 paths: P1 wins 2-1 or P2 wins 1-2
        assert len(paths) == 2

        winners = {p.scoreHistory[-1].winner for p in paths}
        assert winners == {1, 2}

    def test_from_2_2_best_of_5(self):
        """Test from 2-2 in best-of-5 (deciding set)."""
        ms = MatchScore(2, 2, BEST_OF_5)
        paths = MatchPath.generateAllPaths(ms)

        # Only 2 paths: P1 wins 3-2 or P2 wins 2-3
        assert len(paths) == 2

        winners = {p.scoreHistory[-1].winner for p in paths}
        assert winners == {1, 2}
