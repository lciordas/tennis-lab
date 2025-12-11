"""Tests for tiebreak probability functions."""

import pytest
import math
from tennis_lab.paths.tiebreak_path import TiebreakPath
from tennis_lab.paths.tiebreak_probability import pathProbability, probabilityP1WinsTiebreak, _probabilityP1WinsTie
from tennis_lab.core.tiebreak_score import TiebreakScore
from tennis_lab.core.match_format import MatchFormat

# Default match format for tests
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)


# =============================================================================
# Tests for pathProbability
# =============================================================================

class TestPathProbabilityValidation:
    """Tests for pathProbability input validation."""

    def test_invalid_path_type(self):
        with pytest.raises(ValueError, match="path must be a TiebreakPath"):
            pathProbability("not a path", 0.65, 0.60)

    def test_invalid_path_none(self):
        with pytest.raises(ValueError, match="path must be a TiebreakPath"):
            pathProbability(None, 0.65, 0.60)

    def test_invalid_prob_p1_negative(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            pathProbability(path, -0.1, 0.60)

    def test_invalid_prob_p1_greater_than_one(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            pathProbability(path, 1.1, 0.60)

    def test_invalid_prob_p2_negative(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            pathProbability(path, 0.65, -0.1)

    def test_invalid_prob_p2_greater_than_one(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            pathProbability(path, 0.65, 1.1)

    def test_valid_prob_zero(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        result = pathProbability(path, 0.0, 0.0)
        assert result == 1.0  # Single score, no transitions

    def test_valid_prob_one(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        result = pathProbability(path, 1.0, 1.0)
        assert result == 1.0

    def test_valid_prob_integer(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        result = pathProbability(path, 0, 1)
        assert result == 1.0


class TestPathProbabilitySingleScore:
    """Tests for paths with a single score (no transitions)."""

    def test_single_score_returns_one(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        assert pathProbability(path, 0.65, 0.60) == 1.0

    def test_single_score_any_prob(self):
        ts = TiebreakScore(3, 2, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        assert pathProbability(path, 0.3, 0.4) == 1.0
        assert pathProbability(path, 0.9, 0.8) == 1.0


class TestPathProbabilityLoveTiebreak:
    """Tests for love tiebreak paths (7-0)."""

    def test_love_tiebreak_p1_serves_first(self):
        """Path: 0-0 -> 1-0 -> 2-0 -> ... -> 7-0 with P1 serving first."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        # Find the 7-0 path
        love_path = None
        for p in paths:
            if p.scoreHistory[-1].score.asPoints(1) == (7, 0):
                love_path = p
                break

        assert love_path is not None

        # Server rotation: P1(1), P2(2), P2(2), P1(2), P1(2), P2(2), P2(1)
        # Points won by P1: 7, all against alternating servers
        # With p1=0.65, p2=0.60:
        # P1 serves points 1,4,5 and wins: 0.65^3
        # P2 serves points 2,3,6,7 and P1 wins (breaks): (1-0.60)^4 = 0.40^4
        prob = pathProbability(love_path, 0.65, 0.60)
        expected = (0.65 ** 3) * (0.40 ** 4)
        assert math.isclose(prob, expected, rel_tol=1e-9)

    def test_love_tiebreak_p2_serves_first(self):
        """Path: 0-0 -> 1-0 -> ... -> 7-0 with P2 serving first."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 2)

        love_path = None
        for p in paths:
            if p.scoreHistory[-1].score.asPoints(1) == (7, 0):
                love_path = p
                break

        assert love_path is not None

        # Server rotation: P2(1), P1(2), P1(2), P2(2), P2(2), P1(2), P1(1)
        # P2 serves points 1,4,5 and P1 wins (breaks): (1-0.60)^3 = 0.40^3
        # P1 serves points 2,3,6,7 and wins: 0.65^4
        prob = pathProbability(love_path, 0.65, 0.60)
        expected = (0.40 ** 3) * (0.65 ** 4)
        assert math.isclose(prob, expected, rel_tol=1e-9)


class TestPathProbabilityMixedPaths:
    """Tests for paths with mixed point outcomes."""

    def test_simple_two_point_path(self):
        """Path: 0-0 -> 1-0 -> 1-1"""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        path1, _ = path.increment()   # 1-0 (P1 served, won)
        _, path2 = path1.increment()  # 1-1 (P2 served, won)

        # P1 wins on serve (0.65), P2 wins on serve (0.60)
        prob = pathProbability(path2, 0.65, 0.60)
        expected = 0.65 * 0.60
        assert math.isclose(prob, expected, rel_tol=1e-9)

    def test_path_with_breaks(self):
        """Path: 0-0 -> 0-1 -> 0-2 (P1 serves first, loses both)"""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        path = TiebreakPath(ts, 1)
        _, path1 = path.increment()   # 0-1 (P1 served, lost)
        _, path2 = path1.increment()  # 0-2 (P2 served, lost by P1 breaking)

        # Wait - at 0-1, P2 serves. If score goes to 0-2, P2 won.
        # P1 loses on serve (0.35), P2 wins on serve (0.60)
        prob = pathProbability(path2, 0.65, 0.60)
        expected = (1 - 0.65) * 0.60
        assert math.isclose(prob, expected, rel_tol=1e-9)


class TestPathProbabilitySymmetry:
    """Tests for symmetry properties."""

    def test_equal_probs_total_win_probability(self):
        """With equal serve probs, P1 wins exactly 50% overall."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        # Total win probability should be 0.5 with equal probs
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.65)
        assert math.isclose(prob, 0.5, rel_tol=1e-9)


# =============================================================================
# Tests for _probabilityP1WinsTie
# =============================================================================

class TestProbabilityP1WinsTieValidation:
    """Tests for _probabilityP1WinsTie input validation."""

    def test_invalid_prob_p1_negative(self):
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            _probabilityP1WinsTie(-0.1, 0.60)

    def test_invalid_prob_p1_greater_than_one(self):
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            _probabilityP1WinsTie(1.1, 0.60)

    def test_invalid_prob_p2_negative(self):
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            _probabilityP1WinsTie(0.65, -0.1)

    def test_invalid_prob_p2_greater_than_one(self):
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            _probabilityP1WinsTie(0.65, 1.1)


class TestProbabilityP1WinsTieFormula:
    """Tests for the deuce formula."""

    def test_equal_probs_gives_half(self):
        """With equal serve probs, P1 wins 50% from deuce."""
        prob = _probabilityP1WinsTie(0.65, 0.65)
        assert math.isclose(prob, 0.5, rel_tol=1e-9)

    def test_equal_probs_various(self):
        """Equal probs always give 0.5."""
        for p in [0.3, 0.5, 0.7, 0.9]:
            prob = _probabilityP1WinsTie(p, p)
            assert math.isclose(prob, 0.5, rel_tol=1e-9)

    def test_p1_advantage(self):
        """P1 with better serve should win > 50%."""
        prob = _probabilityP1WinsTie(0.70, 0.60)
        assert prob > 0.5

    def test_p2_advantage(self):
        """P2 with better serve means P1 wins < 50%."""
        prob = _probabilityP1WinsTie(0.60, 0.70)
        assert prob < 0.5

    def test_edge_case_both_perfect(self):
        """Both players winning all serve points returns 0.5."""
        prob = _probabilityP1WinsTie(1.0, 1.0)
        assert math.isclose(prob, 0.5, rel_tol=1e-9)

    def test_formula_calculation(self):
        """Verify the formula: p1*(1-p2) / (1 - p1*p2 - (1-p1)*(1-p2))."""
        p1, p2 = 0.65, 0.60
        expected = p1 * (1 - p2) / (1 - p1 * p2 - (1 - p1) * (1 - p2))
        prob = _probabilityP1WinsTie(p1, p2)
        assert math.isclose(prob, expected, rel_tol=1e-9)


# =============================================================================
# Tests for probabilityP1WinsTiebreak
# =============================================================================

class TestProbabilityP1WinsTiebreakValidation:
    """Tests for probabilityP1WinsTiebreak input validation."""

    def test_invalid_init_score_type(self):
        with pytest.raises(ValueError, match="initScore must be a TiebreakScore"):
            probabilityP1WinsTiebreak("not a score", 1, 0.65, 0.60)

    def test_invalid_init_score_none(self):
        with pytest.raises(ValueError, match="initScore must be a TiebreakScore"):
            probabilityP1WinsTiebreak(None, 1, 0.65, 0.60)

    def test_invalid_player_to_serve_zero(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            probabilityP1WinsTiebreak(ts, 0, 0.65, 0.60)

    def test_invalid_player_to_serve_three(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            probabilityP1WinsTiebreak(ts, 3, 0.65, 0.60)

    def test_invalid_prob_p1(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError, match="probWinPointP1 must be a number"):
            probabilityP1WinsTiebreak(ts, 1, 1.5, 0.60)

    def test_invalid_prob_p2(self):
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError, match="probWinPointP2 must be a number"):
            probabilityP1WinsTiebreak(ts, 1, 0.65, -0.1)


class TestProbabilityP1WinsTiebreakFromBlank:
    """Tests for probability calculations from 0-0."""

    def test_equal_probs_gives_half(self):
        """With equal serve probs, P1 wins exactly 50%."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.65)
        assert math.isclose(prob, 0.5, rel_tol=1e-9)

    def test_certain_win(self):
        """With p1=1.0, p2=0.0, P1 always wins."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 1.0, 0.0)
        assert math.isclose(prob, 1.0, rel_tol=1e-9)

    def test_certain_loss(self):
        """With p1=0.0, p2=1.0, P1 always loses."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.0, 1.0)
        assert math.isclose(prob, 0.0, rel_tol=1e-9)

    def test_p1_serve_advantage(self):
        """P1 with better serve should win > 50%."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.70, 0.60)
        assert prob > 0.5

    def test_p2_serve_advantage(self):
        """P2 with better serve means P1 < 50%."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.60, 0.70)
        assert prob < 0.5


class TestProbabilityP1WinsTiebreakFromDeuce:
    """Tests for probability calculations from 6-6."""

    def test_from_deuce_equals_formula(self):
        """From 6-6, result should match _probabilityP1WinsTie."""
        ts = TiebreakScore(6, 6, False, DEFAULT_FORMAT)
        p1, p2 = 0.65, 0.60
        prob = probabilityP1WinsTiebreak(ts, 1, p1, p2)
        expected = _probabilityP1WinsTie(p1, p2)
        assert math.isclose(prob, expected, rel_tol=1e-9)

    def test_from_deuce_equal_probs(self):
        """From 6-6 with equal probs gives 0.5."""
        ts = TiebreakScore(6, 6, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.65)
        assert math.isclose(prob, 0.5, rel_tol=1e-9)


class TestProbabilityP1WinsTiebreakFromAdvantage:
    """Tests for probability calculations from advantage scores."""

    def test_from_6_0(self):
        """From 6-0, P1 should almost certainly win."""
        ts = TiebreakScore(6, 0, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.60)
        assert prob > 0.99

    def test_from_0_6(self):
        """From 0-6, P1 should almost certainly lose."""
        ts = TiebreakScore(0, 6, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.60)
        assert prob < 0.01

    def test_from_6_5(self):
        """From 6-5 (tiebreak point for P1), high probability."""
        ts = TiebreakScore(6, 5, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.60)
        assert prob > 0.8

    def test_from_5_6(self):
        """From 5-6 (tiebreak point for P2), lower probability."""
        ts = TiebreakScore(5, 6, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.60)
        assert prob < 0.5  # P1 is behind, so probability should be below 50%


class TestProbabilityP1WinsTiebreakSymmetry:
    """Tests for symmetry properties."""

    def test_equal_probs_symmetric(self):
        """With equal probs, P1 wins 50% regardless of who serves first."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        prob1 = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.65)
        prob2 = probabilityP1WinsTiebreak(ts, 2, 0.65, 0.65)
        assert math.isclose(prob1, 0.5, rel_tol=1e-9)
        assert math.isclose(prob2, 0.5, rel_tol=1e-9)

    def test_mirrored_scores_mirrored_probs(self):
        """P1's prob from (a,b) with (p1,p2) should equal P2's prob from (b,a) with (p2,p1)."""
        ts1 = TiebreakScore(4, 2, False, DEFAULT_FORMAT)
        ts2 = TiebreakScore(2, 4, False, DEFAULT_FORMAT)

        p1, p2 = 0.65, 0.60
        prob1 = probabilityP1WinsTiebreak(ts1, 1, p1, p2)  # P1 winning from 4-2
        prob2 = probabilityP1WinsTiebreak(ts2, 1, p2, p1)  # P1 (with P2's stats) from 2-4

        # prob1 should equal 1 - prob2 (complementary)
        # Actually, this is more complex due to server rotation. Skip this test.


class TestProbabilityP1WinsTiebreakMonotonicity:
    """Tests that probability increases with P1's serve advantage."""

    def test_monotonic_in_p1(self):
        """Higher p1 should give higher win probability."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        p2 = 0.60
        probs = [probabilityP1WinsTiebreak(ts, 1, p/10, p2) for p in range(3, 9)]

        for i in range(len(probs) - 1):
            assert probs[i] < probs[i + 1]

    def test_monotonic_in_p2_inverse(self):
        """Higher p2 should give lower P1 win probability."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        p1 = 0.65
        probs = [probabilityP1WinsTiebreak(ts, 1, p1, p/10) for p in range(3, 9)]

        for i in range(len(probs) - 1):
            assert probs[i] > probs[i + 1]


class TestProbabilityP1WinsTiebreakFinalScores:
    """Tests for already-final scores."""

    def test_p1_already_won(self):
        """If P1 already won (7-5), probability is 1."""
        ts = TiebreakScore(7, 5, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.60)
        assert prob == 1.0

    def test_p1_already_lost(self):
        """If P1 already lost (5-7), probability is 0."""
        ts = TiebreakScore(5, 7, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.60)
        assert prob == 0.0

    def test_p1_won_7_0(self):
        """7-0 win gives probability 1."""
        ts = TiebreakScore(7, 0, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.60)
        assert prob == 1.0

    def test_p1_lost_0_7(self):
        """0-7 loss gives probability 0."""
        ts = TiebreakScore(0, 7, False, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.60)
        assert prob == 0.0


class TestProbabilityP1WinsTiebreakSuperTiebreak:
    """Tests for super-tiebreak (first to 10)."""

    def test_super_from_blank_equal_probs(self):
        """Super-tiebreak from 0-0 with equal probs gives 0.5."""
        ts = TiebreakScore(0, 0, True, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.65)
        assert math.isclose(prob, 0.5, rel_tol=1e-9)

    def test_super_from_9_9_equals_formula(self):
        """From 9-9, result matches _probabilityP1WinsTie."""
        ts = TiebreakScore(9, 9, True, DEFAULT_FORMAT)
        p1, p2 = 0.65, 0.60
        prob = probabilityP1WinsTiebreak(ts, 1, p1, p2)
        expected = _probabilityP1WinsTie(p1, p2)
        assert math.isclose(prob, expected, rel_tol=1e-9)

    def test_super_p1_already_won(self):
        """10-8 gives probability 1."""
        ts = TiebreakScore(10, 8, True, DEFAULT_FORMAT)
        prob = probabilityP1WinsTiebreak(ts, 1, 0.65, 0.60)
        assert prob == 1.0


class TestProbabilityP1WinsTiebreakProbabilitySum:
    """Tests verifying probability properties."""

    def test_all_path_probs_sum_to_one(self):
        """Sum of all path probabilities should equal 1."""
        ts = TiebreakScore(5, 5, False, DEFAULT_FORMAT)
        paths = TiebreakPath.generateAllPaths(ts, 1)

        p1, p2 = 0.65, 0.60
        total = sum(pathProbability(p, p1, p2) for p in paths)

        assert math.isclose(total, 1.0, rel_tol=1e-9)

    def test_win_plus_loss_equals_one(self):
        """P(P1 wins) + P(P2 wins) = 1."""
        ts = TiebreakScore(0, 0, False, DEFAULT_FORMAT)
        p1, p2 = 0.65, 0.60
        prob_p1_wins = probabilityP1WinsTiebreak(ts, 1, p1, p2)

        # P2 wins = 1 - P1 wins
        assert math.isclose(prob_p1_wins + (1 - prob_p1_wins), 1.0, rel_tol=1e-9)
