"""Tests for the SetPath class."""

import pytest
from tennis_lab.paths.set_path import SetPath
from tennis_lab.core.set_score import SetScore
from tennis_lab.core.game_score import GameScore
from tennis_lab.core.match_format import MatchFormat

# Default match format for tests
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)


class TestSetPathInit:
    """Tests for SetPath initialization."""

    def test_init_with_blank_score(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].score.games(pov=1) == (0, 0)
        assert path.scoreHistory[0].playerServing == 1

    def test_init_with_non_zero_score(self):
        ss = SetScore(3, 2, False, DEFAULT_FORMAT)
        path = SetPath(ss, 2)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].score.games(pov=1) == (3, 2)
        assert path.scoreHistory[0].playerServing == 2

    def test_init_with_final_score(self):
        ss = SetScore(6, 4, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].score.isFinal

    def test_init_player1_serving(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        assert path.scoreHistory[0].playerServing == 1

    def test_init_player2_serving(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 2)
        assert path.scoreHistory[0].playerServing == 2

    def test_init_invalid_score_type(self):
        with pytest.raises(ValueError, match="initialScore must be a SetScore"):
            SetPath("invalid", 1)
        with pytest.raises(ValueError, match="initialScore must be a SetScore"):
            SetPath(None, 1)
        with pytest.raises(ValueError, match="initialScore must be a SetScore"):
            SetPath(42, 1)

    def test_init_invalid_player_to_serve(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            SetPath(ss, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            SetPath(ss, 3)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            SetPath(ss, "1")

    def test_init_with_game_in_progress_raises(self):
        """Cannot create SetPath with a game in progress."""
        gs = GameScore(1, 0, DEFAULT_FORMAT)  # 15-0
        ss = SetScore(2, 2, False, DEFAULT_FORMAT, gameScore=gs)
        with pytest.raises(ValueError, match="cannot have a game or tiebreak in progress"):
            SetPath(ss, 1)

    def test_init_with_tiebreak_in_progress_raises(self):
        """Cannot create SetPath with a tiebreak in progress."""
        from tennis_lab.core.tiebreak_score import TiebreakScore
        ts = TiebreakScore(3, 2, False, DEFAULT_FORMAT)
        ss = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=ts)
        with pytest.raises(ValueError, match="cannot have a game or tiebreak in progress"):
            SetPath(ss, 1)


class TestSetPathScoreHistory:
    """Tests for scoreHistory property."""

    def test_score_history_returns_entries(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        assert path.scoreHistory is path._entries

    def test_score_history_initial_length(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        assert len(path.scoreHistory) == 1

    def test_score_history_entry_is_path_entry(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        entry = path.scoreHistory[0]
        assert hasattr(entry, 'score')
        assert hasattr(entry, 'playerServing')


class TestSetPathIncrement:
    """Tests for increment method."""

    def test_increment_from_blank(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        result = path.increment()

        assert isinstance(result, tuple)
        assert len(result) == 2

        path1, path2 = result
        assert len(path1.scoreHistory) == 2
        assert len(path2.scoreHistory) == 2
        assert path1.scoreHistory[-1].score.games(pov=1) == (1, 0)
        assert path2.scoreHistory[-1].score.games(pov=1) == (0, 1)

    def test_increment_from_mid_set(self):
        ss = SetScore(3, 2, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        result = path.increment()

        assert isinstance(result, tuple)
        path1, path2 = result
        assert path1.scoreHistory[-1].score.games(pov=1) == (4, 2)
        assert path2.scoreHistory[-1].score.games(pov=1) == (3, 3)

    def test_increment_from_final_score(self):
        ss = SetScore(6, 4, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        result = path.increment()

        # Should return a copy of self, not a tuple
        assert isinstance(result, SetPath)
        assert result is not path  # deepcopy
        assert len(result.scoreHistory) == 1
        assert result.scoreHistory[0].score.games(pov=1) == (6, 4)

    def test_increment_preserves_original(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        original_len = len(path.scoreHistory)

        path.increment()

        # Original path should be unchanged
        assert len(path.scoreHistory) == original_len

    def test_increment_creates_independent_copies(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        path1, path2 = path.increment()

        # Modifying one shouldn't affect the other
        path1._entries.append(SetPath.PathEntry(score=SetScore(2, 0, False, DEFAULT_FORMAT), playerServing=1))
        assert len(path2.scoreHistory) == 2

    def test_increment_alternates_server(self):
        """Server should alternate after each game."""
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        path1, path2 = path.increment()

        # After first game, server should switch to player 2
        assert path1.scoreHistory[-1].playerServing == 2
        assert path2.scoreHistory[-1].playerServing == 2

        # After second game, server should switch back to player 1
        path1a, _ = path1.increment()
        assert path1a.scoreHistory[-1].playerServing == 1


class TestSetPathGenerateAllPaths:
    """Tests for generateAllPaths static method."""

    def test_generate_from_blank(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        # Should generate many paths
        assert len(paths) > 0

    def test_generate_from_5_4(self):
        ss = SetScore(5, 4, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        # Fewer paths than from 0-0
        assert len(paths) > 0
        # First path should end with P1 winning 6-4
        first_path = paths[0]
        assert first_path.scoreHistory[-1].score.games(pov=1) == (6, 4)

    def test_generate_from_final_score(self):
        ss = SetScore(6, 4, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        # Only one path - the set is already over
        assert len(paths) == 1
        assert len(paths[0].scoreHistory) == 1

    def test_all_paths_start_with_initial_score(self):
        ss = SetScore(2, 2, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        for path in paths:
            assert path.scoreHistory[0].score.games(pov=1) == (2, 2)

    def test_all_paths_end_in_final_or_tied(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        for path in paths:
            last_score = path.scoreHistory[-1].score
            # Either set is over or it's tied (e.g., 6-6)
            assert last_score.isFinal or last_score.isTied


class TestSetPathStr:
    """Tests for __str__ method."""

    def test_str_single_score(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        result = str(path)

        assert result == "[(0, 0, 1)]"

    def test_str_multiple_scores(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        path1, _ = path.increment()
        result = str(path1)

        assert result == "[(0, 0, 1), (1, 0, 2)]"

    def test_str_format(self):
        ss = SetScore(3, 2, False, DEFAULT_FORMAT)
        path = SetPath(ss, 1)
        result = str(path)

        assert result.startswith("[")
        assert result.endswith("]")
        assert "(3, 2, 1)" in result


class TestSetPathTiedBehavior:
    """Tests for tied score (6-6) handling in path generation."""

    def test_paths_stop_at_tied(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        # Find paths that end in tied score (6-6)
        tied_paths = [p for p in paths if p.scoreHistory[-1].score.isTied]

        # There should be some paths ending in tied score
        assert len(tied_paths) > 0

        # These paths should end at 6-6
        for path in tied_paths:
            assert path.scoreHistory[-1].score.games(pov=1) == (6, 6)


class TestSetPathWinnerDistribution:
    """Tests verifying correct distribution of winning paths."""

    def test_p1_and_p2_win_paths_exist(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        # Filter for complete paths (not ending in tied)
        complete_paths = [p for p in paths if p.scoreHistory[-1].score.isFinal]

        p1_wins = [p for p in complete_paths if p.scoreHistory[-1].score.winner == 1]
        p2_wins = [p for p in complete_paths if p.scoreHistory[-1].score.winner == 2]

        assert len(p1_wins) > 0
        assert len(p2_wins) > 0

    def test_symmetric_paths_from_blank(self):
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        complete_paths = [p for p in paths if p.scoreHistory[-1].score.isFinal]

        p1_wins = len([p for p in complete_paths if p.scoreHistory[-1].score.winner == 1])
        p2_wins = len([p for p in complete_paths if p.scoreHistory[-1].score.winner == 2])

        # From 0-0, the number of P1 and P2 winning paths should be equal
        assert p1_wins == p2_wins

    def test_asymmetric_paths_from_lead(self):
        ss = SetScore(4, 2, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        complete_paths = [p for p in paths if p.scoreHistory[-1].score.isFinal]

        p1_wins = len([p for p in complete_paths if p.scoreHistory[-1].score.winner == 1])
        p2_wins = len([p for p in complete_paths if p.scoreHistory[-1].score.winner == 2])

        # From 4-2, P1 should have more winning paths
        assert p1_wins > p2_wins


class TestSetPathSpecificScenarios:
    """Tests for specific set scenarios."""

    def test_love_set_path(self):
        """Test the path where P1 wins 6-0."""
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        # Find the love set path (all P1 wins)
        love_paths = [p for p in paths
                      if p.scoreHistory[-1].score.games(pov=1) == (6, 0)]

        assert len(love_paths) == 1
        love_path = love_paths[0]

        # Should be 7 scores: 0-0, 1-0, 2-0, 3-0, 4-0, 5-0, 6-0
        assert len(love_path.scoreHistory) == 7

        expected = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0)]
        for i, entry in enumerate(love_path.scoreHistory):
            assert entry.score.games(pov=1) == expected[i]

    def test_tied_path(self):
        """Test a path that reaches 6-6."""
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        # Find paths ending in tied score
        tied_paths = [p for p in paths if p.scoreHistory[-1].score.isTied]
        assert len(tied_paths) > 0

        # One such path: alternating wins to 6-6
        # 0-0 -> 1-0 -> 1-1 -> 2-1 -> 2-2 -> ... -> 6-6
        alternating_path = None
        for path in tied_paths:
            scores = [e.score.games(pov=1) for e in path.scoreHistory]
            expected = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3),
                        (4, 3), (4, 4), (5, 4), (5, 5), (6, 5), (6, 6)]
            if scores == expected:
                alternating_path = path
                break

        assert alternating_path is not None


class TestSetPathEdgeCases:
    """Tests for edge cases."""

    def test_generate_from_set_point_p1(self):
        """P1 at 5-4 (set point)."""
        ss = SetScore(5, 4, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        # Multiple paths possible
        assert len(paths) > 1

        # Shortest path: P1 wins next game
        shortest = min(paths, key=lambda p: len(p.scoreHistory))
        assert len(shortest.scoreHistory) == 2
        assert shortest.scoreHistory[-1].score.games(pov=1) == (6, 4)

    def test_generate_from_set_point_p2(self):
        """P2 at 4-5 (set point)."""
        ss = SetScore(4, 5, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        # Multiple paths possible
        assert len(paths) > 1

        # Check that both 4-6 (P2 wins) and 5-5 paths exist
        end_scores = {p.scoreHistory[-1].score.games(pov=1) for p in paths if len(p.scoreHistory) == 2}
        assert (4, 6) in end_scores or (5, 5) in end_scores

    def test_path_lengths_vary(self):
        """Paths from same start should have varying lengths."""
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        lengths = set(len(p.scoreHistory) for p in paths)

        # Should have multiple different lengths
        assert len(lengths) > 1

        # Shortest possible: 6 games to win (7 scores including start)
        assert min(lengths) == 7

        # Longest without tied continuation: 13 scores (to reach 6-6)
        # 0-0, then 12 more to reach 6-6
        assert 13 in lengths

    def test_server_rotation_throughout_set(self):
        """Verify server alternates correctly throughout a full path."""
        ss = SetScore(0, 0, False, DEFAULT_FORMAT)
        paths = SetPath.generateAllPaths(ss, 1)

        # Take the love set path (6-0)
        love_path = [p for p in paths if p.scoreHistory[-1].score.games(pov=1) == (6, 0)][0]

        # Server should alternate: 1, 2, 1, 2, 1, 2, 1
        expected_servers = [1, 2, 1, 2, 1, 2, 1]
        for i, entry in enumerate(love_path.scoreHistory):
            assert entry.playerServing == expected_servers[i]
