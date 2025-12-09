"""Tests for the TiebreakPath class."""

import pytest
from src.paths.tiebreak_path import TiebreakPath
from src.core.tiebreak_score import TiebreakScore
from src.core.match_format   import MatchFormat

# Default match formats for tests
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)


class TestTiebreakPathInit:
    """Tests for TiebreakPath initialization."""

    def test_init_with_blank_score(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].score.asPoints(1) == (0, 0)
        assert path.scoreHistory[0].playerToServe == 1

    def test_init_with_non_zero_score(self):
        ts = TiebreakScore(3, 2, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 2)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].score.asPoints(1) == (3, 2)
        assert path.scoreHistory[0].playerToServe == 2

    def test_init_with_final_score(self):
        ts = TiebreakScore(7, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        assert len(path.scoreHistory) == 1
        assert path.scoreHistory[0].score.isFinal

    def test_init_player1_serving(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        assert path.scoreHistory[0].playerToServe == 1

    def test_init_player2_serving(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 2)
        assert path.scoreHistory[0].playerToServe == 2

    def test_init_invalid_score_type(self):
        with pytest.raises(ValueError):
            TiebreakPath("invalid", 1)
        with pytest.raises(ValueError):
            TiebreakPath(None, 1)
        with pytest.raises(ValueError):
            TiebreakPath(42, 1)

    def test_init_invalid_player_to_serve(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            TiebreakPath(ts, 0)
        with pytest.raises(ValueError):
            TiebreakPath(ts, 3)
        with pytest.raises(ValueError):
            TiebreakPath(ts, "1")


class TestTiebreakPathScoreHistory:
    """Tests for scoreHistory property."""

    def test_score_history_returns_entries(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        assert path.scoreHistory is path._entries

    def test_score_history_initial_length(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        assert len(path.scoreHistory) == 1

    def test_score_history_entry_is_path_entry(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        entry = path.scoreHistory[0]
        assert hasattr(entry, 'score')
        assert hasattr(entry, 'playerToServe')


class TestTiebreakPathIncrement:
    """Tests for increment method."""

    def test_increment_from_blank(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        result = path.increment()

        assert isinstance(result, tuple)
        assert len(result) == 2

        path1, path2 = result
        assert len(path1.scoreHistory) == 2
        assert len(path2.scoreHistory) == 2
        assert path1.scoreHistory[-1].score.asPoints(1) == (1, 0)
        assert path2.scoreHistory[-1].score.asPoints(1) == (0, 1)

    def test_increment_from_mid_tiebreak(self):
        ts = TiebreakScore(3, 2, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        result = path.increment()

        assert isinstance(result, tuple)
        path1, path2 = result
        assert path1.scoreHistory[-1].score.asPoints(1) == (4, 2)
        assert path2.scoreHistory[-1].score.asPoints(1) == (3, 3)

    def test_increment_from_final_score(self):
        ts = TiebreakScore(7, 5, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        result = path.increment()

        # Should return a copy of self, not a tuple
        assert isinstance(result, TiebreakPath)
        assert result is not path  # deepcopy
        assert len(result.scoreHistory) == 1
        assert result.scoreHistory[0].score.asPoints(1) == (7, 5)

    def test_increment_preserves_original(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        original_len = len(path.scoreHistory)

        path.increment()

        # Original path should be unchanged
        assert len(path.scoreHistory) == original_len

    def test_increment_creates_independent_copies(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        path1, path2 = path.increment()

        # Modifying one shouldn't affect the other
        path1._entries.append(TiebreakPath.PathEntry(
            score=TiebreakScore(2, 0, False, DEFAULT_FORMAT),
            playerToServe=1
        ))
        assert len(path2.scoreHistory) == 2


class TestTiebreakPathServerRotation:
    """Tests for server rotation logic in tiebreaks."""

    def test_server_switches_after_first_point(self):
        """After 0-0, the serve should switch to the other player."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)  # P1 serves first point
        path1, path2 = path.increment()

        # After the first point, P2 should serve
        assert path1.scoreHistory[-1].playerToServe == 2
        assert path2.scoreHistory[-1].playerToServe == 2

    def test_server_stays_for_two_points_after_switch(self):
        """After switching, the same player serves 2 points."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)

        # Simulate: 0-0 (P1) -> 1-0 (P2) -> 2-0 (P2) -> 3-0 (P1)
        path1, _ = path.increment()      # Now at 1-0, P2 serves
        path2, _ = path1.increment()     # Now at 2-0, P2 serves
        path3, _ = path2.increment()     # Now at 3-0, P1 serves

        assert path1.scoreHistory[-1].playerToServe == 2  # After 1 point
        assert path2.scoreHistory[-1].playerToServe == 2  # After 2 points
        assert path3.scoreHistory[-1].playerToServe == 1  # After 3 points, switch

    def test_full_7_0_path_server_rotation(self):
        """Verify server rotation for a 7-0 tiebreak win."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Find the 7-0 path
        path_7_0 = None
        for path in paths:
            if path.scoreHistory[-1].score.asPoints(1) == (7, 0):
                path_7_0 = path
                break

        assert path_7_0 is not None

        # Extract servers for each point
        servers = [entry.playerToServe for entry in path_7_0.scoreHistory]

        # Expected: P1 serves 1, then P2 serves 2, then P1 serves 2, etc.
        # 0-0(P1), 1-0(P2), 2-0(P2), 3-0(P1), 4-0(P1), 5-0(P2), 6-0(P2), 7-0(P1)
        expected_servers = [1, 2, 2, 1, 1, 2, 2, 1]
        assert servers == expected_servers

    def test_server_rotation_starting_with_p2(self):
        """Verify server rotation when P2 serves first."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 2)  # P2 serves first

        # Find the 7-0 path (P1 wins all)
        path_7_0 = None
        for path in paths:
            if path.scoreHistory[-1].score.asPoints(1) == (7, 0):
                path_7_0 = path
                break

        assert path_7_0 is not None
        servers = [entry.playerToServe for entry in path_7_0.scoreHistory]

        # Expected: P2 serves 1, then P1 serves 2, then P2 serves 2, etc.
        expected_servers = [2, 1, 1, 2, 2, 1, 1, 2]
        assert servers == expected_servers


class TestTiebreakPathGenerateAllPaths:
    """Tests for generateAllPaths static method."""

    def test_generate_from_blank_regular_tiebreak(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # From 0-0, there are 2508 possible paths (to win or 6-6)
        assert len(paths) == 2508

    def test_generate_from_5_5(self):
        ts = TiebreakScore(5, 5, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # From 5-5, fewer paths
        assert len(paths) > 0
        assert len(paths) < 2508

    def test_generate_from_6_0(self):
        ts = TiebreakScore(6, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # From 6-0, P1 needs 1 more point
        assert len(paths) > 0

        # Shortest path should be P1 winning immediately
        shortest = min(paths, key=lambda p: len(p.scoreHistory))
        assert shortest.scoreHistory[-1].score.asPoints(1) == (7, 0)

    def test_generate_from_final_score(self):
        ts = TiebreakScore(7, 5, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Only one path - the tiebreak is already over
        assert len(paths) == 1
        assert len(paths[0].scoreHistory) == 1

    def test_all_paths_start_with_initial_score(self):
        ts = TiebreakScore(2, 2, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        for path in paths:
            assert path.scoreHistory[0].score.asPoints(1) == (2, 2)

    def test_all_paths_end_in_final_or_deuce(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        for path in paths:
            last_score = path.scoreHistory[-1].score
            # Either tiebreak is over or it's at 6-6 (deuce)
            assert last_score.isFinal or last_score.isDeuce


class TestTiebreakPathDeuceBehavior:
    """Tests for deuce (6-6) handling in path generation."""

    def test_paths_stop_at_6_6(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Find paths that end at 6-6
        deuce_paths = [p for p in paths if p.scoreHistory[-1].score.isDeuce]

        # There should be some paths ending at 6-6
        assert len(deuce_paths) > 0

        # These paths should end exactly at 6-6
        for path in deuce_paths:
            assert path.scoreHistory[-1].score.asPoints(1) == (6, 6)

    def test_generate_from_6_6_returns_single_path(self):
        ts = TiebreakScore(6, 6, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Should be exactly 1 path - no extension from 6-6
        assert len(paths) == 1
        assert paths[0].scoreHistory[0].score.asPoints(1) == (6, 6)


class TestTiebreakPathStr:
    """Tests for __str__ method."""

    def test_str_single_score(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        result = str(path)

        assert result == "[(0, 0, 1)]"

    def test_str_multiple_scores(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        path1, _ = path.increment()
        result = str(path1)

        # 0-0 with P1 serving, then 1-0 with P2 serving
        assert result == "[(0, 0, 1), (1, 0, 2)]"

    def test_str_format(self):
        ts = TiebreakScore(3, 2, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 2)
        result = str(path)

        assert result.startswith("[")
        assert result.endswith("]")
        assert "(3, 2, 2)" in result


class TestTiebreakPathSuperTiebreak:
    """Tests for super-tiebreak (first to 10) scenarios."""

    def test_super_tiebreak_from_blank(self):
        ts = TiebreakScore(0, 0, True, DEFAULT_FORMAT)  # isSuper=True
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Super-tiebreaks have more paths than regular tiebreaks
        assert len(paths) > 2508

    def test_super_tiebreak_paths_stop_at_9_9(self):
        ts = TiebreakScore(0, 0, True, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Find paths that end in deuce (9-9)
        deuce_paths = [p for p in paths if p.scoreHistory[-1].score.isDeuce]

        # Should have paths ending at 9-9
        assert len(deuce_paths) > 0
        for path in deuce_paths:
            assert path.scoreHistory[-1].score.asPoints(1) == (9, 9)

    def test_super_tiebreak_generate_from_9_9(self):
        ts = TiebreakScore(9, 9, True, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Should be exactly 1 path - no extension from 9-9
        assert len(paths) == 1
        assert paths[0].scoreHistory[0].score.asPoints(1) == (9, 9)

    def test_super_tiebreak_win_at_10(self):
        ts = TiebreakScore(9, 0, True, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Shortest path should end at 10-0
        shortest = min(paths, key=lambda p: len(p.scoreHistory))
        assert shortest.scoreHistory[-1].score.asPoints(1) == (10, 0)
        assert shortest.scoreHistory[-1].score.isFinal


class TestTiebreakPathWinnerDistribution:
    """Tests verifying correct distribution of winning paths."""

    def test_p1_and_p2_win_paths_exist(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Filter for complete paths (not ending in deuce)
        complete_paths = [p for p in paths if p.scoreHistory[-1].score.isFinal]

        p1_wins = [p for p in complete_paths if p.scoreHistory[-1].score.winner == 1]
        p2_wins = [p for p in complete_paths if p.scoreHistory[-1].score.winner == 2]

        assert len(p1_wins) > 0
        assert len(p2_wins) > 0

    def test_symmetric_paths_from_blank(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        complete_paths = [p for p in paths if p.scoreHistory[-1].score.isFinal]

        p1_wins = len([p for p in complete_paths if p.scoreHistory[-1].score.winner == 1])
        p2_wins = len([p for p in complete_paths if p.scoreHistory[-1].score.winner == 2])

        # From 0-0, the number of P1 and P2 winning paths should be equal
        assert p1_wins == p2_wins

    def test_asymmetric_paths_from_lead(self):
        ts = TiebreakScore(4, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        complete_paths = [p for p in paths if p.scoreHistory[-1].score.isFinal]

        p1_wins = len([p for p in complete_paths if p.scoreHistory[-1].score.winner == 1])
        p2_wins = len([p for p in complete_paths if p.scoreHistory[-1].score.winner == 2])

        # From 4-0, P1 should have more winning paths
        assert p1_wins > p2_wins


class TestTiebreakPathSpecificScenarios:
    """Tests for specific tiebreak scenarios."""

    def test_love_tiebreak_path(self):
        """Test the path where P1 wins 7-0."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Find the 7-0 path
        love_paths = [p for p in paths
                      if p.scoreHistory[-1].score.asPoints(1) == (7, 0)]

        assert len(love_paths) == 1
        love_path = love_paths[0]

        # Should be 8 entries: 0-0 through 7-0
        assert len(love_path.scoreHistory) == 8

        expected = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0)]
        for i, entry in enumerate(love_path.scoreHistory):
            assert entry.score.asPoints(1) == expected[i]

    def test_6_6_path(self):
        """Test a path that reaches 6-6."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Find a path ending at 6-6
        deuce_paths = [p for p in paths if p.scoreHistory[-1].score.isDeuce]
        assert len(deuce_paths) > 0

        # One such path: alternating wins
        # 0-0 -> 1-0 -> 1-1 -> 2-1 -> 2-2 -> ... -> 6-6
        alternating_path = None
        for path in deuce_paths:
            scores = [e.score.asPoints(1) for e in path.scoreHistory]
            expected = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3),
                        (4, 3), (4, 4), (5, 4), (5, 5), (6, 5), (6, 6)]
            if scores == expected:
                alternating_path = path
                break

        assert alternating_path is not None

    def test_minimum_win_7_5(self):
        """Test 7-5 win (minimum margin when one player reaches 6 first)."""
        ts = TiebreakScore(6, 5, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # P1 should be able to win with one more point
        p1_win_paths = [p for p in paths
                        if p.scoreHistory[-1].score.asPoints(1) == (7, 5)]

        assert len(p1_win_paths) > 0


class TestTiebreakPathEdgeCases:
    """Tests for edge cases."""

    def test_generate_from_tiebreak_point_p1(self):
        """P1 at 6-5 (tiebreak point)."""
        ts = TiebreakScore(6, 5, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Multiple paths possible
        assert len(paths) > 1

        # Shortest path: P1 wins next point
        shortest = min(paths, key=lambda p: len(p.scoreHistory))
        assert len(shortest.scoreHistory) == 2
        assert shortest.scoreHistory[-1].score.asPoints(1) == (7, 5)

    def test_generate_from_tiebreak_point_p2(self):
        """P2 at 5-6 (tiebreak point)."""
        ts = TiebreakScore(5, 6, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Multiple paths possible
        assert len(paths) > 1

        # Shortest paths have length 2 (one more point)
        shortest_len = min(len(p.scoreHistory) for p in paths)
        assert shortest_len == 2

        # One path ends at 5-7 (P2 wins), one at 6-6 (deuce)
        end_scores = {p.scoreHistory[-1].score.asPoints(1) for p in paths if len(p.scoreHistory) == 2}
        assert (5, 7) in end_scores or (6, 6) in end_scores

    def test_path_lengths_vary(self):
        """Paths from same start should have varying lengths."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        lengths = set(len(p.scoreHistory) for p in paths)

        # Should have multiple different lengths
        assert len(lengths) > 1

        # Shortest possible: 7 points to win (8 entries including start)
        assert min(lengths) == 8

        # Longest without deuce continuation: 13 entries (to reach 6-6)
        assert 13 in lengths

    def test_path_entry_namedtuple_access(self):
        """Test PathEntry namedtuple attributes."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        entry = path.scoreHistory[0]

        # Test both attribute and index access
        assert entry.score == entry[0]
        assert entry.playerToServe == entry[1]
        assert entry.score.asPoints(1) == (0, 0)
        assert entry.playerToServe == 1
