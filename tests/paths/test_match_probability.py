"""Tests for match probability functions."""

import pytest
import numpy as np
from tennis_lab.paths.match_path import MatchPath
from tennis_lab.paths.match_probability import (
    pathProbability,
    probabilityP1WinsMatch,
    _probabilityP1WinsMatchFromSetBoundary,
    _loadCachedFunction
)
from tennis_lab.core.match_score import MatchScore
from tennis_lab.core.set_score import SetScore
from tennis_lab.core.match_format import MatchFormat

# Default match formats for tests
BO3_FORMAT = MatchFormat(bestOfSets=3)
BO5_FORMAT = MatchFormat(bestOfSets=5)

# Helper to create MatchScore with default args
def make_match_score(setsP1: int, setsP2: int, bestOf: int = 3):
    mf = MatchFormat(bestOfSets=bestOf)
    return MatchScore(setsP1, setsP2, mf)


# =============================================================================
# Tests for pathProbability input validation
# =============================================================================

class TestPathProbabilityValidation:
    """Tests for pathProbability input validation."""

    def test_invalid_path_type_string(self):
        with pytest.raises(ValueError, match="path must be a MatchPath"):
            pathProbability("not a path", 0.6, 0.6)

    def test_invalid_path_type_none(self):
        with pytest.raises(ValueError, match="path must be a MatchPath"):
            pathProbability(None, 0.6, 0.6)

    def test_invalid_prob_p1_negative(self):
        ms = make_match_score(0, 0)
        path = MatchPath(ms)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            pathProbability(path, -0.1, 0.6)

    def test_invalid_prob_p1_greater_than_one(self):
        ms = make_match_score(0, 0)
        path = MatchPath(ms)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            pathProbability(path, 1.1, 0.6)

    def test_invalid_prob_p2_negative(self):
        ms = make_match_score(0, 0)
        path = MatchPath(ms)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            pathProbability(path, 0.6, -0.1)

    def test_invalid_prob_p2_greater_than_one(self):
        ms = make_match_score(0, 0)
        path = MatchPath(ms)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            pathProbability(path, 0.6, 1.1)

    def test_invalid_prob_p1_string(self):
        ms = make_match_score(0, 0)
        path = MatchPath(ms)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            pathProbability(path, "0.6", 0.6)

    def test_invalid_prob_p2_string(self):
        ms = make_match_score(0, 0)
        path = MatchPath(ms)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            pathProbability(path, 0.6, "0.6")

    def test_valid_prob_zero(self):
        ms = make_match_score(0, 0)
        path = MatchPath(ms)
        # Should not raise - zero is a valid probability
        result = pathProbability(path, 0.0, 0.6)
        assert result == 1.0  # Single score, no transitions

    def test_valid_prob_one(self):
        ms = make_match_score(0, 0)
        path = MatchPath(ms)
        result = pathProbability(path, 1.0, 1.0)
        assert result == 1.0

    def test_valid_prob_integer(self):
        ms = make_match_score(0, 0)
        path = MatchPath(ms)
        # Integer 0 and 1 should be accepted
        result = pathProbability(path, 0, 1)
        assert result == 1.0


# =============================================================================
# Tests for single-score paths (no transitions)
# =============================================================================

class TestPathProbabilitySingleScore:
    """Tests for paths with a single score (no transitions)."""

    def test_single_score_returns_one(self):
        ms = make_match_score(0, 0)
        path = MatchPath(ms)
        assert pathProbability(path, 0.6, 0.6) == 1.0

    def test_single_score_with_different_probs(self):
        ms = make_match_score(1, 0)
        path = MatchPath(ms)
        # No transitions means probability is 1 regardless of prob values
        assert pathProbability(path, 0.3, 0.9) == 1.0


# =============================================================================
# Tests for path probability calculations
# =============================================================================

class TestPathProbabilityCalculations:
    """Tests for path probability calculations with multiple transitions."""

    def test_all_paths_sum_to_one_bo3(self):
        """All possible paths from 0-0 should sum to 1."""
        ms = make_match_score(0, 0, bestOf=3)
        paths = MatchPath.generateAllPaths(ms)
        total = sum(pathProbability(p, 0.65, 0.60) for p in paths)
        assert abs(total - 1.0) < 1e-10

    def test_all_paths_sum_to_one_bo5(self):
        """All possible paths from 0-0 in best-of-5 should sum to 1."""
        ms = make_match_score(0, 0, bestOf=5)
        paths = MatchPath.generateAllPaths(ms)
        total = sum(pathProbability(p, 0.65, 0.60) for p in paths)
        assert abs(total - 1.0) < 1e-10

    def test_all_paths_sum_to_one_from_1_0(self):
        """All possible paths from 1-0 should sum to 1."""
        ms = make_match_score(1, 0, bestOf=3)
        paths = MatchPath.generateAllPaths(ms)
        total = sum(pathProbability(p, 0.65, 0.60) for p in paths)
        assert abs(total - 1.0) < 1e-10

    def test_all_paths_sum_to_one_equal_probs(self):
        """All paths sum to 1 when both players have equal probabilities."""
        ms = make_match_score(0, 0, bestOf=3)
        paths = MatchPath.generateAllPaths(ms)
        total = sum(pathProbability(p, 0.5, 0.5) for p in paths)
        assert abs(total - 1.0) < 1e-10

    def test_path_probability_positive(self):
        """All path probabilities should be positive."""
        ms = make_match_score(0, 0, bestOf=3)
        paths = MatchPath.generateAllPaths(ms)
        for path in paths:
            prob = pathProbability(path, 0.65, 0.60)
            assert prob > 0


# =============================================================================
# Tests for path probability monotonicity
# =============================================================================

class TestPathProbabilityMonotonicity:
    """Tests for monotonicity properties of path probabilities."""

    def test_p1_winning_path_increases_with_p1_serve_prob(self):
        """P1 winning paths should be more likely as P1's serve probability increases."""
        ms = make_match_score(0, 0, bestOf=3)
        paths = MatchPath.generateAllPaths(ms)
        # Find a path where P1 wins (2-0 or 2-1)
        p1_win_paths = [p for p in paths if p.scoreHistory[-1].winner == 1]

        for path in p1_win_paths:
            prob_low = pathProbability(path, 0.55, 0.60)
            prob_high = pathProbability(path, 0.75, 0.60)
            assert prob_high > prob_low

    def test_p2_winning_path_decreases_with_p1_serve_prob(self):
        """P2 winning paths should be less likely as P1's serve probability increases."""
        ms = make_match_score(0, 0, bestOf=3)
        paths = MatchPath.generateAllPaths(ms)
        # Find a path where P2 wins (0-2 or 1-2)
        p2_win_paths = [p for p in paths if p.scoreHistory[-1].winner == 2]

        for path in p2_win_paths:
            prob_low = pathProbability(path, 0.55, 0.60)
            prob_high = pathProbability(path, 0.75, 0.60)
            assert prob_high < prob_low


# =============================================================================
# Tests for path probability bounds
# =============================================================================

class TestPathProbabilityBounds:
    """Tests for bounds on path probabilities."""

    def test_probability_between_0_and_1(self):
        """Path probability should always be between 0 and 1."""
        ms = make_match_score(0, 0, bestOf=3)
        paths = MatchPath.generateAllPaths(ms)
        for path in paths:
            prob = pathProbability(path, 0.65, 0.60)
            assert 0 <= prob <= 1

    def test_extreme_probs_still_valid(self):
        """Even with extreme probabilities, results should be valid."""
        ms = make_match_score(0, 0, bestOf=3)
        paths = MatchPath.generateAllPaths(ms)
        for path in paths:
            prob = pathProbability(path, 0.99, 0.01)
            assert 0 <= prob <= 1


# =============================================================================
# Tests for _loadCachedFunction validation
# =============================================================================

class TestLoadCachedFunctionValidation:
    """Tests for _loadCachedFunction input validation."""

    def test_invalid_init_score_type_string(self):
        with pytest.raises(ValueError, match="initScore must be a MatchScore"):
            _loadCachedFunction("not a score")

    def test_invalid_init_score_type_none(self):
        with pytest.raises(ValueError, match="initScore must be a MatchScore"):
            _loadCachedFunction(None)

    def test_set_in_progress_raises_error(self):
        """Should raise error if set is in progress."""
        mf = MatchFormat(bestOfSets=3)
        set_score = SetScore(3, 2, False, mf)
        ms = MatchScore(0, 0, mf, setScore=set_score)
        with pytest.raises(ValueError, match="initScore cannot have a set in progress"):
            _loadCachedFunction(ms)


# =============================================================================
# Tests for _loadCachedFunction behavior
# =============================================================================

class TestLoadCachedFunctionBehavior:
    """Tests for _loadCachedFunction behavior."""

    def test_returns_none_or_callable(self):
        """Should return None or a callable."""
        ms = make_match_score(0, 0, bestOf=3)
        result = _loadCachedFunction(ms)
        assert result is None or callable(result)

    def test_different_scores_may_have_different_caches(self):
        """Different scores might have different cache availability."""
        ms1 = make_match_score(0, 0, bestOf=3)
        ms2 = make_match_score(1, 0, bestOf=3)
        # Just check they don't raise
        _loadCachedFunction(ms1)
        _loadCachedFunction(ms2)


# =============================================================================
# Tests for _probabilityP1WinsMatchFromSetBoundary validation
# =============================================================================

class TestProbabilityP1WinsMatchFromSetBoundaryValidation:
    """Tests for _probabilityP1WinsMatchFromSetBoundary input validation."""

    def test_invalid_init_score_type_string(self):
        with pytest.raises(ValueError, match="initScore must be a MatchScore"):
            _probabilityP1WinsMatchFromSetBoundary("not a score", 0.6, 0.6)

    def test_invalid_init_score_type_none(self):
        with pytest.raises(ValueError, match="initScore must be a MatchScore"):
            _probabilityP1WinsMatchFromSetBoundary(None, 0.6, 0.6)

    def test_set_in_progress_raises_error(self):
        """Should raise error if set is in progress."""
        mf = MatchFormat(bestOfSets=3)
        set_score = SetScore(3, 2, False, mf)
        ms = MatchScore(0, 0, mf, setScore=set_score)
        with pytest.raises(ValueError, match="initScore cannot have a set in progress"):
            _probabilityP1WinsMatchFromSetBoundary(ms, 0.6, 0.6)

    def test_invalid_prob_p1_negative(self):
        ms = make_match_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            _probabilityP1WinsMatchFromSetBoundary(ms, -0.1, 0.6)

    def test_invalid_prob_p1_greater_than_one(self):
        ms = make_match_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            _probabilityP1WinsMatchFromSetBoundary(ms, 1.1, 0.6)

    def test_invalid_prob_p2_negative(self):
        ms = make_match_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            _probabilityP1WinsMatchFromSetBoundary(ms, 0.6, -0.1)

    def test_invalid_prob_p2_greater_than_one(self):
        ms = make_match_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            _probabilityP1WinsMatchFromSetBoundary(ms, 0.6, 1.1)

    def test_paths_must_start_with_init_score(self):
        """Provided paths must start with initScore."""
        ms1 = make_match_score(0, 0, bestOf=3)
        ms2 = make_match_score(1, 0, bestOf=3)
        paths = MatchPath.generateAllPaths(ms2)  # paths starting from 1-0
        with pytest.raises(ValueError, match="all paths must start with"):
            _probabilityP1WinsMatchFromSetBoundary(ms1, 0.6, 0.6, paths=paths)


# =============================================================================
# Tests for _probabilityP1WinsMatchFromSetBoundary behavior
# =============================================================================

class TestProbabilityP1WinsMatchFromSetBoundaryBehavior:
    """Tests for _probabilityP1WinsMatchFromSetBoundary behavior."""

    def test_returns_float(self):
        ms = make_match_score(0, 0, bestOf=3)
        result = _probabilityP1WinsMatchFromSetBoundary(ms, 0.65, 0.60)
        assert isinstance(result, float)

    def test_returns_between_0_and_1(self):
        ms = make_match_score(0, 0, bestOf=3)
        result = _probabilityP1WinsMatchFromSetBoundary(ms, 0.65, 0.60)
        assert 0 <= result <= 1

    def test_equal_probs_returns_half(self):
        """With equal serve probabilities, P1 should have ~50% chance."""
        ms = make_match_score(0, 0, bestOf=3)
        result = _probabilityP1WinsMatchFromSetBoundary(ms, 0.5, 0.5)
        assert abs(result - 0.5) < 0.01

    def test_from_0_0_with_advantage(self):
        """P1 with serve advantage should have >50% chance from 0-0."""
        ms = make_match_score(0, 0, bestOf=3)
        result = _probabilityP1WinsMatchFromSetBoundary(ms, 0.65, 0.60)
        assert result > 0.5

    def test_from_1_0_higher_than_0_0(self):
        """Being ahead 1-0 should give higher win probability than 0-0."""
        ms_0_0 = make_match_score(0, 0, bestOf=3)
        ms_1_0 = make_match_score(1, 0, bestOf=3)
        prob_0_0 = _probabilityP1WinsMatchFromSetBoundary(ms_0_0, 0.65, 0.60)
        prob_1_0 = _probabilityP1WinsMatchFromSetBoundary(ms_1_0, 0.65, 0.60)
        assert prob_1_0 > prob_0_0

    def test_from_0_1_lower_than_0_0(self):
        """Being behind 0-1 should give lower win probability than 0-0."""
        ms_0_0 = make_match_score(0, 0, bestOf=3)
        ms_0_1 = make_match_score(0, 1, bestOf=3)
        prob_0_0 = _probabilityP1WinsMatchFromSetBoundary(ms_0_0, 0.65, 0.60)
        prob_0_1 = _probabilityP1WinsMatchFromSetBoundary(ms_0_1, 0.65, 0.60)
        assert prob_0_1 < prob_0_0

    def test_with_provided_paths(self):
        """Should give same result with pre-generated paths."""
        ms = make_match_score(0, 0, bestOf=3)
        paths = MatchPath.generateAllPaths(ms)
        result_with_paths = _probabilityP1WinsMatchFromSetBoundary(ms, 0.65, 0.60, paths=paths)
        result_without_paths = _probabilityP1WinsMatchFromSetBoundary(ms, 0.65, 0.60)
        assert abs(result_with_paths - result_without_paths) < 1e-10


# =============================================================================
# Tests for _probabilityP1WinsMatchFromSetBoundary monotonicity
# =============================================================================

class TestProbabilityP1WinsMatchFromSetBoundaryMonotonicity:
    """Tests for monotonicity of _probabilityP1WinsMatchFromSetBoundary."""

    def test_increases_with_p1_serve_prob(self):
        """Win probability should increase with P1's serve probability."""
        ms = make_match_score(0, 0, bestOf=3)
        prob_low = _probabilityP1WinsMatchFromSetBoundary(ms, 0.55, 0.60)
        prob_mid = _probabilityP1WinsMatchFromSetBoundary(ms, 0.65, 0.60)
        prob_high = _probabilityP1WinsMatchFromSetBoundary(ms, 0.75, 0.60)
        assert prob_low < prob_mid < prob_high

    def test_decreases_with_p2_serve_prob(self):
        """Win probability should decrease with P2's serve probability."""
        ms = make_match_score(0, 0, bestOf=3)
        prob_low = _probabilityP1WinsMatchFromSetBoundary(ms, 0.65, 0.55)
        prob_mid = _probabilityP1WinsMatchFromSetBoundary(ms, 0.65, 0.65)
        prob_high = _probabilityP1WinsMatchFromSetBoundary(ms, 0.65, 0.75)
        assert prob_low > prob_mid > prob_high


# =============================================================================
# Tests for probabilityP1WinsMatch validation
# =============================================================================

class TestProbabilityP1WinsMatchValidation:
    """Tests for probabilityP1WinsMatch input validation."""

    def test_invalid_init_score_type_string(self):
        with pytest.raises(ValueError, match="initScore must be a MatchScore"):
            probabilityP1WinsMatch("not a score", 1, [0.6], 0.6)

    def test_invalid_init_score_type_none(self):
        with pytest.raises(ValueError, match="initScore must be a MatchScore"):
            probabilityP1WinsMatch(None, 1, [0.6], 0.6)

    def test_invalid_player_serving_zero(self):
        ms = make_match_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            probabilityP1WinsMatch(ms, 0, [0.6], 0.6)

    def test_invalid_player_serving_three(self):
        ms = make_match_score(0, 0)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            probabilityP1WinsMatch(ms, 3, [0.6], 0.6)

    def test_invalid_prob_p1s_negative(self):
        ms = make_match_score(0, 0)
        with pytest.raises(ValueError, match="all probWinPointP1s must be numbers"):
            probabilityP1WinsMatch(ms, 1, [-0.1], 0.6)

    def test_invalid_prob_p1s_greater_than_one(self):
        ms = make_match_score(0, 0)
        with pytest.raises(ValueError, match="all probWinPointP1s must be numbers"):
            probabilityP1WinsMatch(ms, 1, [1.1], 0.6)

    def test_invalid_prob_p2_negative(self):
        ms = make_match_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            probabilityP1WinsMatch(ms, 1, [0.6], -0.1)

    def test_invalid_prob_p2_greater_than_one(self):
        ms = make_match_score(0, 0)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            probabilityP1WinsMatch(ms, 1, [0.6], 1.1)


# =============================================================================
# Tests for probabilityP1WinsMatch return type
# =============================================================================

class TestProbabilityP1WinsMatchReturnType:
    """Tests for probabilityP1WinsMatch return type."""

    def test_returns_numpy_array(self):
        ms = make_match_score(0, 0)
        result = probabilityP1WinsMatch(ms, 1, [0.6], 0.6)
        assert isinstance(result, np.ndarray)

    def test_returns_correct_length(self):
        ms = make_match_score(0, 0)
        result = probabilityP1WinsMatch(ms, 1, [0.5, 0.6, 0.7], 0.6)
        assert len(result) == 3

    def test_accepts_iterator(self):
        """Should accept any iterator, not just list."""
        ms = make_match_score(0, 0)
        result = probabilityP1WinsMatch(ms, 1, iter([0.5, 0.6, 0.7]), 0.6)
        assert len(result) == 3


# =============================================================================
# Tests for probabilityP1WinsMatch at set boundary (Case 2)
# =============================================================================

class TestProbabilityP1WinsMatchSetBoundary:
    """Tests for probabilityP1WinsMatch at set boundary (no set in progress)."""

    def test_at_0_0(self):
        ms = make_match_score(0, 0)
        result = probabilityP1WinsMatch(ms, 1, [0.65], 0.60)
        assert 0 < result[0] < 1

    def test_at_1_0(self):
        ms = make_match_score(1, 0)
        result = probabilityP1WinsMatch(ms, 1, [0.65], 0.60)
        assert 0 < result[0] < 1

    def test_at_1_1(self):
        ms = make_match_score(1, 1)
        result = probabilityP1WinsMatch(ms, 1, [0.65], 0.60)
        assert 0 < result[0] < 1

    def test_multiple_probs(self):
        ms = make_match_score(0, 0)
        probs = [0.5, 0.6, 0.7]
        result = probabilityP1WinsMatch(ms, 1, probs, 0.6)
        assert len(result) == 3
        # Should be monotonically increasing
        assert result[0] < result[1] < result[2]

    def test_equal_probs_gives_half(self):
        """With equal serve probabilities, P1 should have ~50% chance."""
        ms = make_match_score(0, 0)
        result = probabilityP1WinsMatch(ms, 1, [0.5], 0.5)
        assert abs(result[0] - 0.5) < 0.01


# =============================================================================
# Tests for probabilityP1WinsMatch with set in progress (Case 1)
# =============================================================================

class TestProbabilityP1WinsMatchSetInProgress:
    """Tests for probabilityP1WinsMatch when a set is in progress."""

    def test_with_set_in_progress(self):
        """Should work when a set is in progress."""
        mf = MatchFormat(bestOfSets=3)
        set_score = SetScore(3, 2, False, mf)
        ms = MatchScore(0, 0, mf, setScore=set_score)
        result = probabilityP1WinsMatch(ms, 1, [0.65], 0.60)
        assert 0 < result[0] < 1

    def test_leading_in_set_higher_prob(self):
        """Leading in set should give higher prob than trailing."""
        mf = MatchFormat(bestOfSets=3)
        set_score_leading = SetScore(4, 2, False, mf)
        set_score_trailing = SetScore(2, 4, False, mf)
        ms_leading = MatchScore(0, 0, mf, setScore=set_score_leading)
        ms_trailing = MatchScore(0, 0, mf, setScore=set_score_trailing)

        prob_leading = probabilityP1WinsMatch(ms_leading, 1, [0.65], 0.60)[0]
        prob_trailing = probabilityP1WinsMatch(ms_trailing, 1, [0.65], 0.60)[0]
        assert prob_leading > prob_trailing


# =============================================================================
# Tests for probabilityP1WinsMatch consistency
# =============================================================================

class TestProbabilityP1WinsMatchConsistency:
    """Tests for consistency of probabilityP1WinsMatch."""

    def test_consistent_with_set_boundary_func(self):
        """At set boundary, should be consistent with _probabilityP1WinsMatchFromSetBoundary."""
        ms = make_match_score(0, 0)
        result_main = probabilityP1WinsMatch(ms, 1, [0.65], 0.60)[0]
        result_boundary = _probabilityP1WinsMatchFromSetBoundary(ms, 0.65, 0.60)
        assert abs(result_main - result_boundary) < 1e-6

    def test_player_serving_doesnt_matter_at_set_boundary(self):
        """At set boundary (0-0 games), player serving shouldn't change match probability."""
        ms = make_match_score(0, 0)
        result_p1_serves = probabilityP1WinsMatch(ms, 1, [0.65], 0.60)[0]
        result_p2_serves = probabilityP1WinsMatch(ms, 2, [0.65], 0.60)[0]
        # At set boundary (0-0 in games), it shouldn't matter who serves
        assert abs(result_p1_serves - result_p2_serves) < 1e-6


# =============================================================================
# Tests for best-of-5 matches
# =============================================================================

class TestBestOfFiveMatches:
    """Tests specific to best-of-5 matches."""

    def test_bo5_from_0_0(self):
        ms = make_match_score(0, 0, bestOf=5)
        result = probabilityP1WinsMatch(ms, 1, [0.65], 0.60)
        assert 0 < result[0] < 1

    def test_bo5_from_2_1(self):
        ms = make_match_score(2, 1, bestOf=5)
        result = probabilityP1WinsMatch(ms, 1, [0.65], 0.60)
        assert 0 < result[0] < 1

    def test_bo5_all_paths_sum_to_one(self):
        """All possible paths from 0-0 in best-of-5 should sum to 1."""
        ms = make_match_score(0, 0, bestOf=5)
        paths = MatchPath.generateAllPaths(ms)
        total = sum(pathProbability(p, 0.65, 0.60) for p in paths)
        assert abs(total - 1.0) < 1e-10

    def test_bo5_harder_to_upset(self):
        """Favorite should be more likely to win in best-of-5 than best-of-3."""
        ms_bo3 = make_match_score(0, 0, bestOf=3)
        ms_bo5 = make_match_score(0, 0, bestOf=5)
        # Strong favorite
        prob_bo3 = probabilityP1WinsMatch(ms_bo3, 1, [0.70], 0.55)[0]
        prob_bo5 = probabilityP1WinsMatch(ms_bo5, 1, [0.70], 0.55)[0]
        # Favorite should be more likely to win in longer format
        assert prob_bo5 > prob_bo3


# =============================================================================
# Tests for edge cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_high_p1_probability(self):
        """P1 with very high serve probability should have high win probability."""
        ms = make_match_score(0, 0)
        result = probabilityP1WinsMatch(ms, 1, [0.99], 0.50)
        assert result[0] > 0.99

    def test_very_low_p1_probability(self):
        """P1 with very low serve probability should have low win probability."""
        ms = make_match_score(0, 0)
        result = probabilityP1WinsMatch(ms, 1, [0.30], 0.70)
        assert result[0] < 0.1

    def test_empty_prob_list(self):
        """Empty probability list should return empty array."""
        ms = make_match_score(0, 0)
        result = probabilityP1WinsMatch(ms, 1, [], 0.60)
        assert len(result) == 0

    def test_single_prob(self):
        """Single probability value should work."""
        ms = make_match_score(0, 0)
        result = probabilityP1WinsMatch(ms, 1, [0.65], 0.60)
        assert len(result) == 1
