"""Tests for the GamePath class."""

import pytest
from tennis_lab.paths.game_path import GamePath
from tennis_lab.core.game_score     import GameScore
from tennis_lab.core.match_format   import MatchFormat

# Default match formats for tests
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)
NO_AD_FORMAT   = MatchFormat(bestOfSets=3, noAdRule=True)


class TestGamePathInit:
    """Tests for GamePath initialization."""

    def test_init_with_blank_score(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].asPoints(1) == (0, 0)

    def test_init_with_non_zero_score(self):
        gs = GameScore(2, 1, DEFAULT_FORMAT)
        path = GamePath(gs)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].asPoints(1) == (2, 1)

    def test_init_with_final_score(self):
        gs = GameScore(4, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].isFinal

    def test_init_invalid_score_type(self):
        with pytest.raises(ValueError):
            GamePath("invalid")
        with pytest.raises(ValueError):
            GamePath(None)
        with pytest.raises(ValueError):
            GamePath(42)


class TestGamePathScoreHistory:
    """Tests for scoreHistory property."""

    def test_score_history_returns_scores(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        assert path.scoreHistory is path._scores

    def test_score_history_initial_length(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        assert len(path.scoreHistory) == 1


class TestGamePathIncrement:
    """Tests for increment method."""

    def test_increment_from_blank(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        result = path.increment()

        assert isinstance(result, tuple)
        assert len(result) == 2

        path1, path2 = result
        assert len(path1.scoreHistory) == 2
        assert len(path2.scoreHistory) == 2
        assert path1.scoreHistory[-1].asPoints(1) == (1, 0)
        assert path2.scoreHistory[-1].asPoints(1) == (0, 1)

    def test_increment_from_mid_game(self):
        gs = GameScore(2, 1, DEFAULT_FORMAT)
        path = GamePath(gs)
        result = path.increment()

        assert isinstance(result, tuple)
        path1, path2 = result
        assert path1.scoreHistory[-1].asPoints(1) == (3, 1)
        assert path2.scoreHistory[-1].asPoints(1) == (2, 2)

    def test_increment_from_final_score(self):
        gs = GameScore(4, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        result = path.increment()

        # Should return a copy of self, not a tuple
        assert isinstance(result, GamePath)
        assert result is not path  # deepcopy
        assert len(result.scoreHistory) == 1
        assert result.scoreHistory[0].asPoints(1) == (4, 0)

    def test_increment_preserves_original(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        original_len = len(path.scoreHistory)

        path.increment()

        # Original path should be unchanged
        assert len(path.scoreHistory) == original_len

    def test_increment_creates_independent_copies(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        path1, path2 = path.increment()

        # Modifying one shouldn't affect the other
        path1._scores.append(GameScore(2, 0, DEFAULT_FORMAT))
        assert len(path2.scoreHistory) == 2


class TestGamePathGenerateAllPaths:
    """Tests for generateAllPaths static method."""

    def test_generate_from_blank_standard_scoring(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # From 0-0, there are 50 possible paths (to win or deuce)
        # This includes paths ending in deuce (3-3)
        assert len(paths) == 50

    def test_generate_from_blank_no_ad(self):
        gs = GameScore(0, 0, NO_AD_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # With no-ad rule, deuce (3-3) decides on next point
        # So we get more complete paths
        assert len(paths) > 0
        # All paths should end in a final score
        for path in paths:
            assert path.scoreHistory[-1].isFinal

    def test_generate_from_30_30(self):
        gs = GameScore(2, 2, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # From 30-30, there are fewer paths
        assert len(paths) > 0
        assert len(paths) < 50  # Fewer than from 0-0

    def test_generate_from_40_0(self):
        gs = GameScore(3, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # From 40-0, paths are shorter
        assert len(paths) > 0
        # First path should be P1 winning on next point
        first_path = paths[0]
        assert first_path.scoreHistory[-1].asPoints(1) == (4, 0)

    def test_generate_from_final_score(self):
        gs = GameScore(4, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Only one path - the game is already over
        assert len(paths) == 1
        assert len(paths[0].scoreHistory) == 1

    def test_all_paths_start_with_initial_score(self):
        gs = GameScore(1, 1, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        for path in paths:
            assert path.scoreHistory[0].asPoints(1) == (1, 1)

    def test_all_paths_end_in_final_or_deuce(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        for path in paths:
            last_score = path.scoreHistory[-1]
            # Either game is over or it's deuce (with standard scoring)
            assert last_score.isFinal or last_score.isDeuce


class TestGamePathStr:
    """Tests for __str__ method."""

    def test_str_single_score(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        result = str(path)

        assert result == "[(0, 0)]"

    def test_str_multiple_scores(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        path1, _ = path.increment()
        result = str(path1)

        assert result == "[(0, 0), (1, 0)]"

    def test_str_format(self):
        gs = GameScore(2, 1, DEFAULT_FORMAT)
        path = GamePath(gs)
        result = str(path)

        assert result.startswith("[")
        assert result.endswith("]")
        assert "(2, 1)" in result


class TestGamePathDeuceBehavior:
    """Tests for deuce handling in path generation."""

    def test_paths_stop_at_deuce_standard_scoring(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Find paths that end in deuce
        deuce_paths = [p for p in paths if p.scoreHistory[-1].isDeuce]

        # There should be some paths ending in deuce
        assert len(deuce_paths) > 0

        # These paths should not continue beyond deuce
        for path in deuce_paths:
            assert path.scoreHistory[-1].asPoints(1) == (3, 3)

    def test_paths_continue_past_deuce_no_ad(self):
        gs = GameScore(0, 0, NO_AD_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # No paths should end in deuce with no-ad rule
        deuce_paths = [p for p in paths if p.scoreHistory[-1].isDeuce]
        assert len(deuce_paths) == 0

        # All paths should end with a winner
        for path in paths:
            assert path.scoreHistory[-1].isFinal


class TestGamePathWinnerDistribution:
    """Tests verifying correct distribution of winning paths."""

    def test_p1_and_p2_win_paths_exist(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Filter for complete paths (not ending in deuce)
        complete_paths = [p for p in paths if p.scoreHistory[-1].isFinal]

        p1_wins = [p for p in complete_paths if p.scoreHistory[-1].winner == 1]
        p2_wins = [p for p in complete_paths if p.scoreHistory[-1].winner == 2]

        assert len(p1_wins) > 0
        assert len(p2_wins) > 0

    def test_symmetric_paths_from_blank(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        complete_paths = [p for p in paths if p.scoreHistory[-1].isFinal]

        p1_wins = len([p for p in complete_paths if p.scoreHistory[-1].winner == 1])
        p2_wins = len([p for p in complete_paths if p.scoreHistory[-1].winner == 2])

        # From 0-0, the number of P1 and P2 winning paths should be equal
        assert p1_wins == p2_wins

    def test_asymmetric_paths_from_lead(self):
        gs = GameScore(2, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        complete_paths = [p for p in paths if p.scoreHistory[-1].isFinal]

        p1_wins = len([p for p in complete_paths if p.scoreHistory[-1].winner == 1])
        p2_wins = len([p for p in complete_paths if p.scoreHistory[-1].winner == 2])

        # From 30-0 (2-0), P1 should have more winning paths
        assert p1_wins > p2_wins


class TestGamePathSpecificScenarios:
    """Tests for specific game scenarios."""

    def test_love_game_path(self):
        """Test the path where server wins 4-0."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Find the love game path (all P1 wins)
        love_paths = [p for p in paths
                      if p.scoreHistory[-1].asPoints(1) == (4, 0)]

        assert len(love_paths) == 1
        love_path = love_paths[0]

        # Should be 5 scores: 0-0, 1-0, 2-0, 3-0, 4-0
        assert len(love_path.scoreHistory) == 5

        expected = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
        for i, score in enumerate(love_path.scoreHistory):
            assert score.asPoints(1) == expected[i]

    def test_deuce_path(self):
        """Test a path that reaches deuce."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Find a path ending in deuce
        deuce_paths = [p for p in paths if p.scoreHistory[-1].isDeuce]
        assert len(deuce_paths) > 0

        # One such path: alternating wins
        # 0-0 -> 1-0 -> 1-1 -> 2-1 -> 2-2 -> 3-2 -> 3-3
        alternating_path = None
        for path in deuce_paths:
            scores = [s.asPoints(1) for s in path.scoreHistory]
            if scores == [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)]:
                alternating_path = path
                break

        assert alternating_path is not None

    def test_no_ad_deuce_resolution(self):
        """Test that no-ad games resolve deuce in one point."""
        gs = GameScore(3, 3, NO_AD_FORMAT)  # Deuce with no-ad
        paths = GamePath.generateAllPaths(gs)

        # Should be exactly 2 paths: P1 wins or P2 wins
        assert len(paths) == 2

        winners = {paths[0].scoreHistory[-1].winner, paths[1].scoreHistory[-1].winner}
        assert winners == {1, 2}


class TestGamePathEdgeCases:
    """Tests for edge cases."""

    def test_generate_from_game_point_p1(self):
        """P1 at 40-0 (game point)."""
        gs = GameScore(3, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Multiple paths possible
        assert len(paths) > 1

        # Shortest path: P1 wins next point
        shortest = min(paths, key=lambda p: len(p.scoreHistory))
        assert len(shortest.scoreHistory) == 2
        assert shortest.scoreHistory[-1].asPoints(1) == (4, 0)

    def test_generate_from_game_point_p2(self):
        """P2 at 0-40 (game point)."""
        gs = GameScore(0, 3, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Multiple paths possible
        assert len(paths) > 1

        # Shortest path: P2 wins next point
        shortest = min(paths, key=lambda p: len(p.scoreHistory))
        assert len(shortest.scoreHistory) == 2
        assert shortest.scoreHistory[-1].asPoints(1) == (0, 4)

    def test_path_lengths_vary(self):
        """Paths from same start should have varying lengths."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        lengths = set(len(p.scoreHistory) for p in paths)

        # Should have multiple different lengths
        assert len(lengths) > 1

        # Shortest possible: 4 points to win (5 scores including start)
        assert min(lengths) == 5

        # Longest without deuce continuation: 7 scores (to reach deuce)
        # 0-0, then 6 more to reach 3-3
        assert 7 in lengths
