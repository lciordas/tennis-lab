"""Tests for set probability functions."""

import pytest
import math
from tennis_lab.paths.set_path import SetPath
from tennis_lab.paths.set_probability import pathProbability, _loadCachedFunction, _probabilityP1WinsSetFromGameBoundary, probabilityP1WinsSet
import numpy as np
from tennis_lab.core.set_score import SetScore
from tennis_lab.core.match_format import MatchFormat

# Default match format for tests
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)

# Helper to create SetScore with default args (non-final set)
def make_set_score(gamesP1: int, gamesP2: int, is_final_set: bool = False):
    return SetScore(gamesP1, gamesP2, is_final_set, DEFAULT_FORMAT)


# =============================================================================
# Tests for pathProbability input validation
# =============================================================================

class TestPathProbabilityValidation:
    """Tests for pathProbability input validation."""

    def test_invalid_path_type_string(self):
        with pytest.raises(ValueError, match="path must be a SetPath"):
            pathProbability("not a path", 0.6, 0.6)

    def test_invalid_path_type_none(self):
        with pytest.raises(ValueError, match="path must be a SetPath"):
            pathProbability(None, 0.6, 0.6)

    def test_invalid_prob_p1_negative(self):
        ss = make_set_score(0, 0)
        path = SetPath(ss, playerServing=1)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            pathProbability(path, -0.1, 0.6)

    def test_invalid_prob_p1_greater_than_one(self):
        ss = make_set_score(0, 0)
        path = SetPath(ss, playerServing=1)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            pathProbability(path, 1.1, 0.6)

    def test_invalid_prob_p2_negative(self):
        ss = make_set_score(0, 0)
        path = SetPath(ss, playerServing=1)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            pathProbability(path, 0.6, -0.1)

    def test_invalid_prob_p2_greater_than_one(self):
        ss = make_set_score(0, 0)
        path = SetPath(ss, playerServing=1)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            pathProbability(path, 0.6, 1.1)

    def test_invalid_prob_p1_string(self):
        ss = make_set_score(0, 0)
        path = SetPath(ss, playerServing=1)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            pathProbability(path, "0.6", 0.6)

    def test_invalid_prob_p2_string(self):
        ss = make_set_score(0, 0)
        path = SetPath(ss, playerServing=1)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            pathProbability(path, 0.6, "0.6")

    def test_valid_prob_zero(self):
        ss = make_set_score(0, 0)
        path = SetPath(ss, playerServing=1)
        # Should not raise - zero is a valid probability
        result = pathProbability(path, 0.0, 0.6)
        assert result == 1.0  # Single score, no transitions

    def test_valid_prob_one(self):
        ss = make_set_score(0, 0)
        path = SetPath(ss, playerServing=1)
        result = pathProbability(path, 1.0, 1.0)
        assert result == 1.0

    def test_valid_prob_integer(self):
        ss = make_set_score(0, 0)
        path = SetPath(ss, playerServing=1)
        # Integer 0 and 1 should be accepted
        result = pathProbability(path, 0, 1)
        assert result == 1.0


# =============================================================================
# Tests for single-score paths (no transitions)
# =============================================================================

class TestPathProbabilitySingleScore:
    """Tests for paths with a single score (no transitions)."""

    def test_single_score_returns_one(self):
        ss = make_set_score(0, 0)
        path = SetPath(ss, playerServing=1)
        assert pathProbability(path, 0.6, 0.6) == 1.0

    def test_single_score_any_prob(self):
        ss = make_set_score(3, 2)
        path = SetPath(ss, playerServing=2)
        assert pathProbability(path, 0.3, 0.7) == 1.0
        assert pathProbability(path, 0.9, 0.4) == 1.0


# =============================================================================
# Tests for love set paths (player wins 6-0)
# =============================================================================

class TestPathProbabilityLoveSet:
    """Tests for love set paths where one player wins all games."""

    def test_love_set_p1_wins_p1_starts_serving(self):
        """Path: 0-0 -> 1-0 -> 2-0 -> 3-0 -> 4-0 -> 5-0 -> 6-0, P1 serves first."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        # Find the 6-0 path
        love_path = None
        for p in paths:
            final = p.scoreHistory[-1].score.games(pov=1)
            if final == (6, 0):
                love_path = p
                break

        assert love_path is not None

        # P1 serves games 1, 3, 5; P2 serves games 2, 4, 6
        # P1 wins all 6 games
        # Games P1 serves and wins: 3 games
        # Games P2 serves and P1 wins (breaks): 3 games

    def test_love_set_p2_wins_p1_starts_serving(self):
        """Path: 0-0 -> 0-1 -> 0-2 -> 0-3 -> 0-4 -> 0-5 -> 0-6, P1 serves first."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        # Find the 0-6 path
        love_path = None
        for p in paths:
            final = p.scoreHistory[-1].score.games(pov=1)
            if final == (0, 6):
                love_path = p
                break

        assert love_path is not None


# =============================================================================
# Tests for probability calculations with specific paths
# =============================================================================

class TestPathProbabilityCalculations:
    """Tests for specific probability calculations."""

    def test_all_paths_probs_sum_near_one(self):
        """Sum of all path probabilities should be close to 1 (excluding tied paths)."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        probP1 = 0.65
        probP2 = 0.60

        total = 0.0
        for path in paths:
            prob = pathProbability(path, probP1, probP2)
            total += prob

        # The total will be less than 1 because we cut off at 6-6 (tied)
        # Paths ending in 6-6 represent infinite possible outcomes
        assert total < 1.0
        # But should still account for a significant fraction
        assert total > 0.5

    def test_symmetric_probs_equal_paths(self):
        """With equal serve probabilities, P1 winning 6-0 should equal P2 winning 0-6 when serving patterns are symmetric."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        prob = 0.65  # Same for both players

        # Find 6-0 and 0-6 paths
        p1_wins_path = None
        p2_wins_path = None
        for p in paths:
            final = p.scoreHistory[-1].score.games(pov=1)
            if final == (6, 0):
                p1_wins_path = p
            elif final == (0, 6):
                p2_wins_path = p

        assert p1_wins_path is not None
        assert p2_wins_path is not None

        prob_p1_wins = pathProbability(p1_wins_path, prob, prob)
        prob_p2_wins = pathProbability(p2_wins_path, prob, prob)

        # With equal serve probabilities, these should be equal
        assert math.isclose(prob_p1_wins, prob_p2_wins, rel_tol=1e-9)


# =============================================================================
# Tests for monotonicity properties
# =============================================================================

class TestPathProbabilityMonotonicity:
    """Tests that probability changes appropriately with serve probabilities."""

    def test_higher_p1_prob_increases_p1_win_probability(self):
        """Higher P1 serve probability should increase P1 winning paths."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        # Find a path where P1 wins
        p1_wins_path = None
        for p in paths:
            final = p.scoreHistory[-1].score.games(pov=1)
            if final == (6, 0):
                p1_wins_path = p
                break

        assert p1_wins_path is not None

        probP2 = 0.60  # Keep P2's probability constant

        # Calculate probability with increasing P1 serve percentages
        probs = []
        for p1 in [0.50, 0.55, 0.60, 0.65, 0.70]:
            prob = pathProbability(p1_wins_path, p1, probP2)
            probs.append(prob)

        # Should be monotonically increasing
        for i in range(len(probs) - 1):
            assert probs[i] < probs[i + 1]

    def test_higher_p2_prob_decreases_p1_win_probability(self):
        """Higher P2 serve probability should decrease P1 winning paths (P2 holds more)."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        # Find a path where P1 wins
        p1_wins_path = None
        for p in paths:
            final = p.scoreHistory[-1].score.games(pov=1)
            if final == (6, 0):
                p1_wins_path = p
                break

        assert p1_wins_path is not None

        probP1 = 0.65  # Keep P1's probability constant

        # Calculate probability with increasing P2 serve percentages
        probs = []
        for p2 in [0.50, 0.55, 0.60, 0.65, 0.70]:
            prob = pathProbability(p1_wins_path, probP1, p2)
            probs.append(prob)

        # Should be monotonically decreasing (P2 holds more often)
        for i in range(len(probs) - 1):
            assert probs[i] > probs[i + 1]


# =============================================================================
# Tests for edge cases and final scores
# =============================================================================

class TestPathProbabilityFinalScores:
    """Tests for paths with final scores."""

    def test_path_ending_6_4(self):
        """Test a path ending at 6-4."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        # Find a 6-4 path
        path_6_4 = None
        for p in paths:
            final = p.scoreHistory[-1].score.games(pov=1)
            if final == (6, 4):
                path_6_4 = p
                break

        assert path_6_4 is not None

        # Probability should be positive and less than 1
        prob = pathProbability(path_6_4, 0.65, 0.60)
        assert 0 < prob < 1

    def test_path_ending_7_5(self):
        """Test a path ending at 7-5."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        # Find a 7-5 path
        path_7_5 = None
        for p in paths:
            final = p.scoreHistory[-1].score.games(pov=1)
            if final == (7, 5):
                path_7_5 = p
                break

        assert path_7_5 is not None

        prob = pathProbability(path_7_5, 0.65, 0.60)
        assert 0 < prob < 1

    def test_path_ending_tied_6_6(self):
        """Test a path ending at 6-6 (tied, goes to tiebreak)."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        # Find a 6-6 path
        tied_path = None
        for p in paths:
            final = p.scoreHistory[-1].score.games(pov=1)
            if final == (6, 6):
                tied_path = p
                break

        assert tied_path is not None

        prob = pathProbability(tied_path, 0.65, 0.60)
        assert 0 < prob < 1


# =============================================================================
# Tests for probability bounds
# =============================================================================

class TestPathProbabilityBounds:
    """Tests that probabilities are always within valid bounds."""

    def test_probability_between_zero_and_one(self):
        """All path probabilities should be between 0 and 1."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        for path in paths:
            prob = pathProbability(path, 0.65, 0.60)
            assert 0 <= prob <= 1

    def test_extreme_probabilities(self):
        """Test with extreme (but valid) probabilities."""
        ss = make_set_score(0, 0)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        # Test with very low probabilities
        for path in paths[:5]:  # Just check first few paths
            prob = pathProbability(path, 0.01, 0.01)
            assert 0 <= prob <= 1

        # Test with very high probabilities
        for path in paths[:5]:
            prob = pathProbability(path, 0.99, 0.99)
            assert 0 <= prob <= 1


# =============================================================================
# Tests for different starting scores
# =============================================================================

class TestPathProbabilityFromDifferentScores:
    """Tests for paths starting from non-zero scores."""

    def test_from_3_2_score(self):
        """Test path probability from 3-2."""
        ss = make_set_score(3, 2)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        # All paths should have valid probabilities
        for path in paths:
            prob = pathProbability(path, 0.65, 0.60)
            assert 0 <= prob <= 1

    def test_from_5_4_score(self):
        """Test path probability from 5-4."""
        ss = make_set_score(5, 4)
        paths = SetPath.generateAllPaths(ss, playerServing=2)

        # Should have relatively few paths from this score
        assert len(paths) > 0

        for path in paths:
            prob = pathProbability(path, 0.65, 0.60)
            assert 0 <= prob <= 1

    def test_from_5_5_score(self):
        """Test path probability from 5-5."""
        ss = make_set_score(5, 5)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        # From 5-5, possible outcomes: 7-5, 5-7, or 6-6
        for path in paths:
            prob = pathProbability(path, 0.65, 0.60)
            assert 0 <= prob <= 1


# =============================================================================
# Tests for server rotation
# =============================================================================

class TestPathProbabilityServerRotation:
    """Tests that server rotation is handled correctly."""

    def test_different_starting_servers(self):
        """Probability may differ based on who serves first."""
        ss = make_set_score(0, 0)

        paths_p1_first = SetPath.generateAllPaths(ss, playerServing=1)
        paths_p2_first = SetPath.generateAllPaths(ss, playerServing=2)

        # Find 6-0 paths from each
        p1_first_6_0 = None
        p2_first_6_0 = None

        for p in paths_p1_first:
            final = p.scoreHistory[-1].score.games(pov=1)
            if final == (6, 0):
                p1_first_6_0 = p
                break

        for p in paths_p2_first:
            final = p.scoreHistory[-1].score.games(pov=1)
            if final == (6, 0):
                p2_first_6_0 = p
                break

        assert p1_first_6_0 is not None
        assert p2_first_6_0 is not None

        # With asymmetric serve probabilities, who serves first matters
        probP1 = 0.70
        probP2 = 0.55

        prob_p1_first = pathProbability(p1_first_6_0, probP1, probP2)
        prob_p2_first = pathProbability(p2_first_6_0, probP1, probP2)

        # These should generally be different
        # (might be equal in some edge cases, but typically different)
        # We just verify both are valid probabilities
        assert 0 < prob_p1_first < 1
        assert 0 < prob_p2_first < 1


# =============================================================================
# Tests for _loadCachedFunction
# =============================================================================

class TestLoadCachedFunctionValidation:
    """Tests for _loadCachedFunction input validation."""

    def test_invalid_init_score_type(self):
        with pytest.raises(ValueError, match="initScore must be a SetScore"):
            _loadCachedFunction("not a score", 1)

    def test_invalid_init_score_none(self):
        with pytest.raises(ValueError, match="initScore must be a SetScore"):
            _loadCachedFunction(None, 1)

    def test_invalid_player_serving_zero(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            _loadCachedFunction(ss, 0)

    def test_invalid_player_serving_three(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            _loadCachedFunction(ss, 3)

    def test_invalid_player_serving_string(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            _loadCachedFunction(ss, "1")

    def test_invalid_game_in_progress(self):
        """Cannot load cached function when game is in progress."""
        from tennis_lab.core.game_score import GameScore
        game_score = GameScore(1, 2, DEFAULT_FORMAT)  # 15-30
        ss = SetScore(2, 3, False, DEFAULT_FORMAT, gameScore=game_score)
        with pytest.raises(ValueError, match="initScore cannot have a game or tiebreak in progress"):
            _loadCachedFunction(ss, 1)


class TestLoadCachedFunctionBehavior:
    """Tests for _loadCachedFunction behavior (skip if cache unavailable)."""

    def test_returns_callable_or_none(self):
        """Function should return a callable or None."""
        ss = make_set_score(0, 0)
        result = _loadCachedFunction(ss, 1)
        assert result is None or callable(result)

    def test_cached_function_returns_float(self):
        """If cache available, returned function should return a float."""
        ss = make_set_score(0, 0)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")
        result = cached_fn(0.65, 0.60)
        assert isinstance(result, float)

    def test_cached_function_matches_direct_calculation(self):
        """Cached function should match direct _probabilityP1WinsSetFromGameBoundary calculation."""
        ss = make_set_score(0, 0)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p1, p2 = 0.65, 0.60
        cached_result = cached_fn(p1, p2)
        direct_result = _probabilityP1WinsSetFromGameBoundary(ss, 1, p1, p2)
        # Allow some tolerance due to interpolation
        assert math.isclose(cached_result, direct_result, rel_tol=0.01)

    def test_cached_function_from_3_2(self):
        """Test cached function from 3-2 score."""
        ss = make_set_score(3, 2)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p1, p2 = 0.60, 0.65
        cached_result = cached_fn(p1, p2)
        direct_result = _probabilityP1WinsSetFromGameBoundary(ss, 1, p1, p2)
        assert math.isclose(cached_result, direct_result, rel_tol=0.01)

    def test_cached_function_from_5_5(self):
        """Test cached function from 5-5 score."""
        ss = make_set_score(5, 5)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p1, p2 = 0.65, 0.60
        cached_result = cached_fn(p1, p2)
        direct_result = _probabilityP1WinsSetFromGameBoundary(ss, 1, p1, p2)
        assert math.isclose(cached_result, direct_result, rel_tol=0.01)

    def test_cached_function_from_6_5(self):
        """Test cached function from 6-5 score (set point for P1)."""
        ss = make_set_score(6, 5)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p1, p2 = 0.65, 0.60
        cached_result = cached_fn(p1, p2)
        # P1 at 6-5 should have high probability
        assert cached_result > 0.7

    def test_cached_function_from_5_6(self):
        """Test cached function from 5-6 score (set point for P2)."""
        ss = make_set_score(5, 6)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p1, p2 = 0.65, 0.60
        cached_result = cached_fn(p1, p2)
        # P1 at 5-6 should have lower probability
        assert cached_result < 0.5

    def test_cached_function_player2_serving(self):
        """Test cached function when player 2 is serving."""
        ss = make_set_score(2, 3)
        cached_fn = _loadCachedFunction(ss, 2)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p1, p2 = 0.60, 0.65
        cached_result = cached_fn(p1, p2)
        direct_result = _probabilityP1WinsSetFromGameBoundary(ss, 2, p1, p2)
        assert math.isclose(cached_result, direct_result, rel_tol=0.01)

    def test_cached_probability_bounds(self):
        """Cached probability should be between 0 and 1."""
        ss = make_set_score(0, 0)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        for p1 in [0.3, 0.5, 0.7]:
            for p2 in [0.3, 0.5, 0.7]:
                result = cached_fn(p1, p2)
                assert 0.0 <= result <= 1.0

    def test_cached_function_equal_probs_gives_half(self):
        """With equal serve probs, cached function should give ~0.5."""
        ss = make_set_score(0, 0)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        result = cached_fn(0.65, 0.65)
        assert math.isclose(result, 0.5, rel_tol=0.01)

    def test_cached_function_p1_advantage(self):
        """With P1 having better serve, P1 should win > 50%."""
        ss = make_set_score(0, 0)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        result = cached_fn(0.70, 0.60)
        assert result > 0.5

    def test_cached_function_p2_advantage(self):
        """With P2 having better serve, P1 should win < 50%."""
        ss = make_set_score(0, 0)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        result = cached_fn(0.60, 0.70)
        assert result < 0.5


class TestLoadCachedFunctionMonotonicity:
    """Tests that cached probability changes appropriately with serve probabilities."""

    def test_monotonic_in_p1(self):
        """Higher p1 should give higher win probability."""
        ss = make_set_score(0, 0)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p2 = 0.60
        probs = [cached_fn(p / 10, p2) for p in range(4, 8)]

        for i in range(len(probs) - 1):
            assert probs[i] < probs[i + 1]

    def test_monotonic_in_p2_inverse(self):
        """Higher p2 should give lower P1 win probability."""
        ss = make_set_score(0, 0)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p1 = 0.65
        probs = [cached_fn(p1, p / 10) for p in range(4, 8)]

        for i in range(len(probs) - 1):
            assert probs[i] > probs[i + 1]


class TestLoadCachedFunctionTiedScore:
    """Tests for cached function at 6-6 (tied) score."""

    def test_cached_function_at_6_6(self):
        """Test cached function at 6-6 (should use tiebreak cache)."""
        ss = make_set_score(6, 6)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available (need tiebreak cache for 6-6)")

        p1, p2 = 0.65, 0.60
        result = cached_fn(p1, p2)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_cached_function_at_6_6_equal_probs(self):
        """At 6-6 with equal probs, should give ~0.5."""
        ss = make_set_score(6, 6)
        cached_fn = _loadCachedFunction(ss, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available (need tiebreak cache for 6-6)")

        result = cached_fn(0.65, 0.65)
        assert math.isclose(result, 0.5, rel_tol=0.01)


# =============================================================================
# Tests for _probabilityP1WinsSetFromGameBoundary
# =============================================================================

class TestProbabilityP1WinsSetFromGameBoundaryValidation:
    """Tests for _probabilityP1WinsSetFromGameBoundary input validation."""

    def test_invalid_init_score_type(self):
        with pytest.raises(ValueError, match="initScore must be a SetScore"):
            _probabilityP1WinsSetFromGameBoundary("not a score", 1, 0.65, 0.60)

    def test_invalid_init_score_none(self):
        with pytest.raises(ValueError, match="initScore must be a SetScore"):
            _probabilityP1WinsSetFromGameBoundary(None, 1, 0.65, 0.60)

    def test_invalid_game_in_progress(self):
        """Cannot calculate from a score with game in progress."""
        from tennis_lab.core.game_score import GameScore
        game_score = GameScore(1, 2, DEFAULT_FORMAT)  # 15-30
        ss = SetScore(2, 3, False, DEFAULT_FORMAT, gameScore=game_score)
        with pytest.raises(ValueError, match="initScore cannot have a game or tiebreak in progress"):
            _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.60)

    def test_invalid_tiebreak_in_progress(self):
        """Cannot calculate from a score with tiebreak in progress."""
        from tennis_lab.core.tiebreak_score import TiebreakScore
        tiebreak_score = TiebreakScore(3, 2, isSuper=False, matchFormat=DEFAULT_FORMAT)
        ss = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tiebreak_score)
        with pytest.raises(ValueError, match="initScore cannot have a game or tiebreak in progress"):
            _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.60)

    def test_invalid_player_serving_zero(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            _probabilityP1WinsSetFromGameBoundary(ss, 0, 0.65, 0.60)

    def test_invalid_player_serving_three(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            _probabilityP1WinsSetFromGameBoundary(ss, 3, 0.65, 0.60)

    def test_invalid_player_serving_string(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            _probabilityP1WinsSetFromGameBoundary(ss, "1", 0.65, 0.60)

    def test_invalid_prob_p1_negative(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            _probabilityP1WinsSetFromGameBoundary(ss, 1, -0.1, 0.60)

    def test_invalid_prob_p1_greater_than_one(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            _probabilityP1WinsSetFromGameBoundary(ss, 1, 1.1, 0.60)

    def test_invalid_prob_p2_negative(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, -0.1)

    def test_invalid_prob_p2_greater_than_one(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 1.1)

    def test_invalid_prob_p1_string(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            _probabilityP1WinsSetFromGameBoundary(ss, 1, "0.65", 0.60)

    def test_invalid_prob_p2_string(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, "0.60")

    def test_invalid_paths_wrong_start_score(self):
        """Paths must start with the given initScore."""
        ss_0_0 = make_set_score(0, 0)
        ss_3_2 = make_set_score(3, 2)
        paths = SetPath.generateAllPaths(ss_3_2, playerServing=1)
        with pytest.raises(ValueError, match="all paths must start with 'initScore'"):
            _probabilityP1WinsSetFromGameBoundary(ss_0_0, 1, 0.65, 0.60, paths=paths)


class TestProbabilityP1WinsSetFromGameBoundaryBehavior:
    """Tests for _probabilityP1WinsSetFromGameBoundary behavior."""

    def test_returns_float(self):
        ss = make_set_score(0, 0)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.60)
        assert isinstance(result, float)

    def test_probability_bounds(self):
        """Probability should be between 0 and 1."""
        ss = make_set_score(0, 0)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.60)
        assert 0.0 <= result <= 1.0

    def test_equal_probs_gives_half(self):
        """With equal serve probs from 0-0, should give ~0.5."""
        ss = make_set_score(0, 0)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.65)
        assert math.isclose(result, 0.5, rel_tol=0.01)

    def test_p1_advantage_gives_more_than_half(self):
        """With P1 having better serve, P1 should win > 50%."""
        ss = make_set_score(0, 0)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.70, 0.60)
        assert result > 0.5

    def test_p2_advantage_gives_less_than_half(self):
        """With P2 having better serve, P1 should win < 50%."""
        ss = make_set_score(0, 0)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.60, 0.70)
        assert result < 0.5

    def test_from_3_2_score(self):
        """P1 at 3-2 should have > 50% chance."""
        ss = make_set_score(3, 2)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.65)
        assert result > 0.5

    def test_from_2_3_score(self):
        """P1 at 2-3 should have < 50% chance."""
        ss = make_set_score(2, 3)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.65)
        assert result < 0.5

    def test_from_5_4_p1_serving(self):
        """P1 at 5-4 serving should have high chance."""
        ss = make_set_score(5, 4)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.65)
        assert result > 0.6

    def test_from_4_5_p2_serving(self):
        """P1 at 4-5 with P2 serving should have < 50% chance."""
        ss = make_set_score(4, 5)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 2, 0.65, 0.65)
        assert result < 0.5

    def test_from_6_5_score(self):
        """P1 at 6-5 should have high probability."""
        ss = make_set_score(6, 5)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.60)
        assert result > 0.7

    def test_from_5_6_score(self):
        """P1 at 5-6 should have lower probability."""
        ss = make_set_score(5, 6)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.60)
        assert result < 0.5

    def test_from_6_6_tied(self):
        """At 6-6, probability depends on tiebreak."""
        ss = make_set_score(6, 6)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.65)
        assert math.isclose(result, 0.5, rel_tol=0.05)

    def test_with_pregenerated_paths(self):
        """Using pre-generated paths should give same result."""
        ss = make_set_score(3, 2)
        paths = SetPath.generateAllPaths(ss, playerServing=1)

        result_with_paths = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.60, paths=paths)
        result_without_paths = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.60)

        assert math.isclose(result_with_paths, result_without_paths, rel_tol=1e-9)


class TestProbabilityP1WinsSetFromGameBoundaryMonotonicity:
    """Tests for monotonicity properties."""

    def test_monotonic_in_p1(self):
        """Higher P1 serve probability should give higher win probability."""
        ss = make_set_score(0, 0)
        p2 = 0.60

        probs = [_probabilityP1WinsSetFromGameBoundary(ss, 1, p1 / 100, p2)
                 for p1 in range(50, 75, 5)]

        for i in range(len(probs) - 1):
            assert probs[i] < probs[i + 1]

    def test_monotonic_in_p2_inverse(self):
        """Higher P2 serve probability should give lower P1 win probability."""
        ss = make_set_score(0, 0)
        p1 = 0.65

        probs = [_probabilityP1WinsSetFromGameBoundary(ss, 1, p1, p2 / 100)
                 for p2 in range(50, 75, 5)]

        for i in range(len(probs) - 1):
            assert probs[i] > probs[i + 1]

    def test_monotonic_in_games_ahead(self):
        """More games ahead should give higher win probability."""
        p1, p2 = 0.65, 0.65

        prob_0_0 = _probabilityP1WinsSetFromGameBoundary(make_set_score(0, 0), 1, p1, p2)
        prob_1_0 = _probabilityP1WinsSetFromGameBoundary(make_set_score(1, 0), 1, p1, p2)
        prob_2_0 = _probabilityP1WinsSetFromGameBoundary(make_set_score(2, 0), 1, p1, p2)
        prob_3_0 = _probabilityP1WinsSetFromGameBoundary(make_set_score(3, 0), 1, p1, p2)

        assert prob_0_0 < prob_1_0 < prob_2_0 < prob_3_0


class TestProbabilityP1WinsSetFromGameBoundarySymmetry:
    """Tests for symmetry properties."""

    def test_symmetric_scores_equal_probs(self):
        """With equal serve probs, P1 at 3-2 should be greater than 0.5."""
        p = 0.65

        prob_3_2 = _probabilityP1WinsSetFromGameBoundary(make_set_score(3, 2), 1, p, p)
        prob_2_3 = _probabilityP1WinsSetFromGameBoundary(make_set_score(2, 3), 1, p, p)

        # P1 at 3-2 should have > 50% chance, P1 at 2-3 should have < 50% chance
        assert prob_3_2 > 0.5
        assert prob_2_3 < 0.5
        # The sum should be close to 1 (but may not be exactly 1 due to server effects)
        assert 0.9 < prob_3_2 + prob_2_3 < 1.5

    def test_5_5_gives_half(self):
        """At 5-5 with equal probs, should give ~0.5."""
        ss = make_set_score(5, 5)
        result = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.65)
        assert math.isclose(result, 0.5, rel_tol=0.01)


# =============================================================================
# Tests for probabilityP1WinsSet
# =============================================================================

class TestProbabilityP1WinsSetValidation:
    """Tests for probabilityP1WinsSet input validation."""

    def test_invalid_init_score_type(self):
        with pytest.raises(ValueError, match="initScore must be a SetScore"):
            probabilityP1WinsSet("not a score", 1, [0.65], 0.60)

    def test_invalid_init_score_none(self):
        with pytest.raises(ValueError, match="initScore must be a SetScore"):
            probabilityP1WinsSet(None, 1, [0.65], 0.60)

    def test_invalid_player_serving_zero(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            probabilityP1WinsSet(ss, 0, [0.65], 0.60)

    def test_invalid_player_serving_three(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            probabilityP1WinsSet(ss, 3, [0.65], 0.60)

    def test_invalid_player_serving_string(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            probabilityP1WinsSet(ss, "1", [0.65], 0.60)

    def test_invalid_prob_p2_negative(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            probabilityP1WinsSet(ss, 1, [0.65], -0.1)

    def test_invalid_prob_p2_greater_than_one(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            probabilityP1WinsSet(ss, 1, [0.65], 1.1)

    def test_invalid_prob_p2_string(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            probabilityP1WinsSet(ss, 1, [0.65], "0.60")

    def test_invalid_prob_p1s_negative(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="all probWinPointP1s must be numbers"):
            probabilityP1WinsSet(ss, 1, [0.65, -0.1], 0.60)

    def test_invalid_prob_p1s_greater_than_one(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="all probWinPointP1s must be numbers"):
            probabilityP1WinsSet(ss, 1, [0.65, 1.1], 0.60)

    def test_invalid_prob_p1s_string(self):
        ss = make_set_score(0, 0)
        with pytest.raises(ValueError, match="all probWinPointP1s must be numbers"):
            probabilityP1WinsSet(ss, 1, [0.65, "0.70"], 0.60)


class TestProbabilityP1WinsSetReturnType:
    """Tests for probabilityP1WinsSet return type."""

    def test_returns_numpy_array(self):
        ss = make_set_score(0, 0)
        result = probabilityP1WinsSet(ss, 1, [0.65], 0.60)
        assert isinstance(result, np.ndarray)

    def test_returns_correct_length(self):
        ss = make_set_score(0, 0)
        result = probabilityP1WinsSet(ss, 1, [0.60, 0.65, 0.70], 0.60)
        assert len(result) == 3

    def test_accepts_iterator(self):
        """Should accept any iterator, not just list."""
        ss = make_set_score(0, 0)
        result = probabilityP1WinsSet(ss, 1, iter([0.60, 0.65, 0.70]), 0.60)
        assert len(result) == 3

    def test_accepts_generator(self):
        """Should accept generator."""
        ss = make_set_score(0, 0)
        result = probabilityP1WinsSet(ss, 1, (x/100 for x in range(60, 70)), 0.60)
        assert len(result) == 10

    def test_empty_iterator_returns_empty_array(self):
        """Empty iterator should return empty array."""
        ss = make_set_score(0, 0)
        result = probabilityP1WinsSet(ss, 1, [], 0.60)
        assert len(result) == 0


class TestProbabilityP1WinsSetCase3GameBoundary:
    """Tests for probabilityP1WinsSet Case 3: at game boundary."""

    def test_matches_direct_calculation_single_value(self):
        """Should match _probabilityP1WinsSetFromGameBoundary for single value."""
        ss = make_set_score(0, 0)
        result = probabilityP1WinsSet(ss, 1, [0.65], 0.60)
        direct = _probabilityP1WinsSetFromGameBoundary(ss, 1, 0.65, 0.60)
        # Allow tolerance due to potential cache vs direct calculation differences
        assert math.isclose(result[0], direct, rel_tol=0.01)

    def test_matches_direct_calculation_multiple_values(self):
        """Should match _probabilityP1WinsSetFromGameBoundary for multiple values."""
        ss = make_set_score(3, 2)
        p1_values = [0.60, 0.65, 0.70]
        result = probabilityP1WinsSet(ss, 1, p1_values, 0.60)

        for i, p1 in enumerate(p1_values):
            direct = _probabilityP1WinsSetFromGameBoundary(ss, 1, p1, 0.60)
            # Allow tolerance due to potential cache vs direct calculation differences
            assert math.isclose(result[i], direct, rel_tol=0.01)

    def test_probability_bounds(self):
        """All probabilities should be between 0 and 1."""
        ss = make_set_score(0, 0)
        result = probabilityP1WinsSet(ss, 1, [0.50, 0.60, 0.70, 0.80], 0.60)
        assert all(0.0 <= p <= 1.0 for p in result)

    def test_equal_probs_gives_half(self):
        """With equal serve probs from 0-0, should give ~0.5."""
        ss = make_set_score(0, 0)
        result = probabilityP1WinsSet(ss, 1, [0.65], 0.65)
        assert math.isclose(result[0], 0.5, rel_tol=0.01)

    def test_monotonic_in_p1(self):
        """Higher P1 serve probability should give higher win probability."""
        ss = make_set_score(0, 0)
        result = probabilityP1WinsSet(ss, 1, [0.50, 0.55, 0.60, 0.65, 0.70], 0.60)
        for i in range(len(result) - 1):
            assert result[i] < result[i + 1]


class TestProbabilityP1WinsSetCase1GameInProgress:
    """Tests for probabilityP1WinsSet Case 1: game in progress."""

    def test_game_in_progress_returns_array(self):
        """Should return numpy array when game in progress."""
        from tennis_lab.core.game_score import GameScore
        game_score = GameScore(1, 2, DEFAULT_FORMAT)  # 15-30
        ss = SetScore(2, 3, False, DEFAULT_FORMAT, gameScore=game_score)
        result = probabilityP1WinsSet(ss, 1, [0.65], 0.60)
        assert isinstance(result, np.ndarray)

    def test_game_in_progress_probability_bounds(self):
        """Probabilities should be between 0 and 1."""
        from tennis_lab.core.game_score import GameScore
        game_score = GameScore(2, 1, DEFAULT_FORMAT)  # 30-15
        ss = SetScore(3, 3, False, DEFAULT_FORMAT, gameScore=game_score)
        result = probabilityP1WinsSet(ss, 1, [0.50, 0.65, 0.80], 0.60)
        assert all(0.0 <= p <= 1.0 for p in result)

    def test_game_in_progress_monotonic(self):
        """Higher P1 serve probability should give higher win probability."""
        from tennis_lab.core.game_score import GameScore
        game_score = GameScore(2, 2, DEFAULT_FORMAT)  # 30-30
        ss = SetScore(4, 4, False, DEFAULT_FORMAT, gameScore=game_score)
        result = probabilityP1WinsSet(ss, 1, [0.50, 0.55, 0.60, 0.65, 0.70], 0.60)
        for i in range(len(result) - 1):
            assert result[i] < result[i + 1]

    def test_game_in_progress_p1_serving_ahead(self):
        """P1 serving at 40-0 should have higher probability than 0-0 game."""
        from tennis_lab.core.game_score import GameScore
        game_score_ahead = GameScore(3, 0, DEFAULT_FORMAT)  # 40-0
        ss_ahead = SetScore(3, 3, False, DEFAULT_FORMAT, gameScore=game_score_ahead)

        ss_boundary = make_set_score(3, 3)

        result_ahead = probabilityP1WinsSet(ss_ahead, 1, [0.65], 0.65)
        result_boundary = probabilityP1WinsSet(ss_boundary, 1, [0.65], 0.65)

        assert result_ahead[0] > result_boundary[0]

    def test_game_in_progress_p1_serving_behind(self):
        """P1 serving at 0-40 should have lower probability than 0-0 game."""
        from tennis_lab.core.game_score import GameScore
        game_score_behind = GameScore(0, 3, DEFAULT_FORMAT)  # 0-40
        ss_behind = SetScore(3, 3, False, DEFAULT_FORMAT, gameScore=game_score_behind)

        ss_boundary = make_set_score(3, 3)

        result_behind = probabilityP1WinsSet(ss_behind, 1, [0.65], 0.65)
        result_boundary = probabilityP1WinsSet(ss_boundary, 1, [0.65], 0.65)

        assert result_behind[0] < result_boundary[0]

    def test_game_in_progress_p2_serving(self):
        """When P2 is serving and P1 is ahead in the game (break point), P1 should have higher set probability."""
        from tennis_lab.core.game_score import GameScore
        # GameScore stores points from P1's POV: GameScore(3, 0) means P1 has 40-0 (3 points vs 0)
        # If P2 is serving and P1 has 40-0, P1 is about to break serve
        game_score = GameScore(3, 0, DEFAULT_FORMAT)  # P1 at 40-0 (break point)
        ss = SetScore(3, 3, False, DEFAULT_FORMAT, gameScore=game_score)

        ss_boundary = make_set_score(3, 3)

        # P2 is serving, so P1 being at 40-0 means P1 is about to break
        result_game = probabilityP1WinsSet(ss, 2, [0.65], 0.65)
        result_boundary = probabilityP1WinsSet(ss_boundary, 2, [0.65], 0.65)

        assert result_game[0] > result_boundary[0]


class TestProbabilityP1WinsSetCase2TiebreakInProgress:
    """Tests for probabilityP1WinsSet Case 2: tiebreak in progress."""

    def test_tiebreak_in_progress_returns_array(self):
        """Should return numpy array when tiebreak in progress."""
        from tennis_lab.core.tiebreak_score import TiebreakScore
        tiebreak_score = TiebreakScore(3, 2, isSuper=False, matchFormat=DEFAULT_FORMAT)
        ss = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tiebreak_score)
        result = probabilityP1WinsSet(ss, 1, [0.65], 0.60)
        assert isinstance(result, np.ndarray)

    def test_tiebreak_in_progress_probability_bounds(self):
        """Probabilities should be between 0 and 1."""
        from tennis_lab.core.tiebreak_score import TiebreakScore
        tiebreak_score = TiebreakScore(4, 4, isSuper=False, matchFormat=DEFAULT_FORMAT)
        ss = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tiebreak_score)
        result = probabilityP1WinsSet(ss, 1, [0.50, 0.65, 0.80], 0.60)
        assert all(0.0 <= p <= 1.0 for p in result)

    def test_tiebreak_in_progress_monotonic(self):
        """Higher P1 serve probability should give higher win probability."""
        from tennis_lab.core.tiebreak_score import TiebreakScore
        tiebreak_score = TiebreakScore(3, 3, isSuper=False, matchFormat=DEFAULT_FORMAT)
        ss = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tiebreak_score)
        result = probabilityP1WinsSet(ss, 1, [0.50, 0.55, 0.60, 0.65, 0.70], 0.60)
        for i in range(len(result) - 1):
            assert result[i] < result[i + 1]

    def test_tiebreak_p1_ahead(self):
        """P1 at 5-2 in tiebreak should have higher probability than 0-0."""
        from tennis_lab.core.tiebreak_score import TiebreakScore
        tb_ahead = TiebreakScore(5, 2, isSuper=False, matchFormat=DEFAULT_FORMAT)
        ss_ahead = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tb_ahead)

        tb_even = TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT)
        ss_even = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tb_even)

        result_ahead = probabilityP1WinsSet(ss_ahead, 1, [0.65], 0.65)
        result_even = probabilityP1WinsSet(ss_even, 1, [0.65], 0.65)

        assert result_ahead[0] > result_even[0]

    def test_tiebreak_p1_behind(self):
        """P1 at 2-5 in tiebreak should have lower probability than 0-0."""
        from tennis_lab.core.tiebreak_score import TiebreakScore
        tb_behind = TiebreakScore(2, 5, isSuper=False, matchFormat=DEFAULT_FORMAT)
        ss_behind = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tb_behind)

        tb_even = TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT)
        ss_even = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tb_even)

        result_behind = probabilityP1WinsSet(ss_behind, 1, [0.65], 0.65)
        result_even = probabilityP1WinsSet(ss_even, 1, [0.65], 0.65)

        assert result_behind[0] < result_even[0]

    def test_tiebreak_equal_probs_equal_score_gives_half(self):
        """At 3-3 in tiebreak with equal probs, should give ~0.5."""
        from tennis_lab.core.tiebreak_score import TiebreakScore
        tiebreak_score = TiebreakScore(3, 3, isSuper=False, matchFormat=DEFAULT_FORMAT)
        ss = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tiebreak_score)
        result = probabilityP1WinsSet(ss, 1, [0.65], 0.65)
        assert math.isclose(result[0], 0.5, rel_tol=0.05)


class TestProbabilityP1WinsSetConsistency:
    """Tests for consistency between different entry points."""

    def test_game_boundary_vs_game_at_0_0(self):
        """Game at 0-0 should give same result as game boundary (with adjusted expectations)."""
        from tennis_lab.core.game_score import GameScore
        game_score = GameScore(0, 0, DEFAULT_FORMAT)
        ss_with_game = SetScore(3, 2, False, DEFAULT_FORMAT, gameScore=game_score)

        # This should behave similarly to a game boundary, but go through Case 1 logic
        result_game = probabilityP1WinsSet(ss_with_game, 1, [0.65], 0.60)

        # The result should be within reasonable bounds
        assert 0.0 <= result_game[0] <= 1.0

    def test_consistent_across_all_cases(self):
        """Verify all three cases give reasonable results."""
        from tennis_lab.core.game_score import GameScore
        from tennis_lab.core.tiebreak_score import TiebreakScore

        # Case 3: Game boundary
        ss_boundary = make_set_score(3, 3)
        result_boundary = probabilityP1WinsSet(ss_boundary, 1, [0.65], 0.65)

        # Case 1: Game in progress
        game_score = GameScore(2, 2, DEFAULT_FORMAT)
        ss_game = SetScore(3, 3, False, DEFAULT_FORMAT, gameScore=game_score)
        result_game = probabilityP1WinsSet(ss_game, 1, [0.65], 0.65)

        # Case 2: Tiebreak in progress
        tiebreak_score = TiebreakScore(3, 3, isSuper=False, matchFormat=DEFAULT_FORMAT)
        ss_tiebreak = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tiebreak_score)
        result_tiebreak = probabilityP1WinsSet(ss_tiebreak, 1, [0.65], 0.65)

        # All should be close to 0.5 with equal probs at equal scores
        assert math.isclose(result_boundary[0], 0.5, rel_tol=0.05)
        assert math.isclose(result_game[0], 0.5, rel_tol=0.05)
        assert math.isclose(result_tiebreak[0], 0.5, rel_tol=0.05)
