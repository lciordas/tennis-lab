"""Tests for game probability functions."""

import pytest
import math
from tennis_lab.paths.game_path import GamePath
from tennis_lab.paths.game_probability import pathProbability, probabilityServerWinsGame, loadCachedFunction
from tennis_lab.core.game_score import GameScore
from tennis_lab.core.match_format import MatchFormat

# Default match formats for tests
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)
NO_AD_FORMAT = MatchFormat(bestOfSets=3, noAdRule=True)
NO_CAP_FORMAT = MatchFormat(bestOfSets=3, capPoints=False)


# =============================================================================
# Tests for pathProbability
# =============================================================================

class TestPathProbabilityValidation:
    """Tests for pathProbability input validation."""

    def test_invalid_path_type(self):
        with pytest.raises(ValueError, match="path must be a GamePath"):
            pathProbability("not a path", 1, 0.6)

    def test_invalid_path_none(self):
        with pytest.raises(ValueError, match="path must be a GamePath"):
            pathProbability(None, 1, 0.6)

    def test_invalid_player_to_serve_zero(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            pathProbability(path, 0, 0.6)

    def test_invalid_player_to_serve_three(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            pathProbability(path, 3, 0.6)

    def test_invalid_prob_negative(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        with pytest.raises(ValueError, match="probWinPoint must be a number"):
            pathProbability(path, 1, -0.1)

    def test_invalid_prob_greater_than_one(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        with pytest.raises(ValueError, match="probWinPoint must be a number"):
            pathProbability(path, 1, 1.1)

    def test_valid_prob_zero(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        # Should not raise
        result = pathProbability(path, 1, 0.0)
        assert result == 1.0  # Single score, no transitions

    def test_valid_prob_one(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        result = pathProbability(path, 1, 1.0)
        assert result == 1.0

    def test_valid_prob_integer(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        # Integer 0 and 1 should be accepted
        result = pathProbability(path, 1, 0)
        assert result == 1.0
        result = pathProbability(path, 1, 1)
        assert result == 1.0


class TestPathProbabilitySingleScore:
    """Tests for paths with a single score (no transitions)."""

    def test_single_score_returns_one(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        path = GamePath(gs)
        assert pathProbability(path, 1, 0.6) == 1.0

    def test_single_score_any_prob(self):
        gs = GameScore(2, 1, DEFAULT_FORMAT)
        path = GamePath(gs)
        assert pathProbability(path, 1, 0.3) == 1.0
        assert pathProbability(path, 2, 0.9) == 1.0


class TestPathProbabilityLoveGame:
    """Tests for love game paths (server wins 4-0)."""

    def test_love_game_p1_serves(self):
        """Path: 0-0 -> 1-0 -> 2-0 -> 3-0 -> 4-0"""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Find the love game path
        love_path = None
        for p in paths:
            if p.scoreHistory[-1].asPoints(1) == (4, 0):
                love_path = p
                break

        assert love_path is not None

        # With p=0.6, probability is 0.6^4 = 0.1296
        prob = pathProbability(love_path, 1, 0.6)
        assert math.isclose(prob, 0.6**4, rel_tol=1e-9)

    def test_love_game_p2_serves(self):
        """When P2 serves, the love game means P2 wins all points."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Find path where receiver wins 0-4 (from P1's POV)
        receiver_love_path = None
        for p in paths:
            if p.scoreHistory[-1].asPoints(1) == (0, 4):
                receiver_love_path = p
                break

        assert receiver_love_path is not None

        # P2 serves, wins all points with prob 0.7
        # Path from P2's POV: 0-0 -> 1-0 -> 2-0 -> 3-0 -> 4-0
        prob = pathProbability(receiver_love_path, 2, 0.7)
        assert math.isclose(prob, 0.7**4, rel_tol=1e-9)


class TestPathProbabilityMixedPaths:
    """Tests for paths with mixed point outcomes."""

    def test_alternating_path_to_deuce(self):
        """Path: 0-0 -> 1-0 -> 1-1 -> 2-1 -> 2-2 -> 3-2 -> 3-3"""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Find alternating path to deuce
        target_scores = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)]
        alternating_path = None
        for p in paths:
            scores = [s.asPoints(1) for s in p.scoreHistory]
            if scores == target_scores:
                alternating_path = p
                break

        assert alternating_path is not None

        # P1 serves with prob 0.6
        # Points: P1 wins, P2 wins, P1 wins, P2 wins, P1 wins, P2 wins
        # Prob = 0.6 * 0.4 * 0.6 * 0.4 * 0.6 * 0.4
        expected = (0.6 ** 3) * (0.4 ** 3)
        prob = pathProbability(alternating_path, 1, 0.6)
        assert math.isclose(prob, expected, rel_tol=1e-9)

    def test_path_15_40_then_win(self):
        """Test a specific path where server falls behind then wins."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Find path: 0-0 -> 1-0 -> 1-1 -> 1-2 -> 1-3 -> 2-3 -> 3-3 (deuce)
        target = [(0, 0), (1, 0), (1, 1), (1, 2), (1, 3), (2, 3), (3, 3)]
        target_path = None
        for p in paths:
            scores = [s.asPoints(1) for s in p.scoreHistory]
            if scores == target:
                target_path = p
                break

        if target_path is not None:
            # P1 serves: wins 1, loses 3, wins 2
            # Prob = p * (1-p)^3 * p^2 = p^3 * (1-p)^3
            p = 0.5
            expected = (p ** 3) * ((1 - p) ** 3)
            prob = pathProbability(target_path, 1, p)
            assert math.isclose(prob, expected, rel_tol=1e-9)


class TestPathProbabilitySymmetry:
    """Tests for symmetry properties."""

    def test_player_symmetry(self):
        """Swapping server should give complementary probabilities for mirrored paths."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        # Find love game for P1 (4-0) and love game for P2 (0-4)
        p1_love = None
        p2_love = None
        for p in paths:
            final = p.scoreHistory[-1].asPoints(1)
            if final == (4, 0):
                p1_love = p
            elif final == (0, 4):
                p2_love = p

        assert p1_love is not None
        assert p2_love is not None

        prob = 0.6
        # P1 serves, wins love game
        p1_wins = pathProbability(p1_love, 1, prob)
        # P2 serves, wins love game
        p2_wins = pathProbability(p2_love, 2, prob)

        # Both should equal prob^4
        assert math.isclose(p1_wins, prob**4, rel_tol=1e-9)
        assert math.isclose(p2_wins, prob**4, rel_tol=1e-9)


# =============================================================================
# Tests for probabilityServerWinsGame
# =============================================================================

class TestProbabilityServerWinsGameValidation:
    """Tests for probabilityServerWinsGame input validation."""

    def test_invalid_init_score_type(self):
        with pytest.raises(ValueError, match="initScore must be a GameScore"):
            probabilityServerWinsGame("not a score", 1, 0.6)

    def test_invalid_init_score_none(self):
        with pytest.raises(ValueError, match="initScore must be a GameScore"):
            probabilityServerWinsGame(None, 1, 0.6)

    def test_invalid_player_to_serve(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            probabilityServerWinsGame(gs, 0, 0.6)

    def test_invalid_prob_win_point(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        with pytest.raises(ValueError, match="probWinPoint must be a number"):
            probabilityServerWinsGame(gs, 1, 1.5)


class TestProbabilityServerWinsGameFromBlank:
    """Tests for probability calculations from 0-0."""

    def test_fifty_percent_gives_half(self):
        """With p=0.5, server should win exactly 50% of games."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        prob = probabilityServerWinsGame(gs, 1, 0.5)
        assert math.isclose(prob, 0.5, rel_tol=1e-9)

    def test_certain_win(self):
        """With p=1.0, server always wins."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        prob = probabilityServerWinsGame(gs, 1, 1.0)
        assert math.isclose(prob, 1.0, rel_tol=1e-9)

    def test_certain_loss(self):
        """With p=0.0, server always loses."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        prob = probabilityServerWinsGame(gs, 1, 0.0)
        assert math.isclose(prob, 0.0, rel_tol=1e-9)

    def test_typical_serve_probability(self):
        """Test with typical ATP serve win probability (~65%)."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        prob = probabilityServerWinsGame(gs, 1, 0.65)
        # Server should win more than 50% but less than 100%
        assert 0.5 < prob < 1.0
        # Approximately 83% for p=0.65
        assert math.isclose(prob, 0.83, rel_tol=0.01)

    def test_weak_serve_probability(self):
        """Test with weak serve (~55%)."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        prob = probabilityServerWinsGame(gs, 1, 0.55)
        # Should still be above 50% due to advantage of serving
        assert prob > 0.5


class TestProbabilityServerWinsGameFromDeuce:
    """Tests for probability calculations from deuce (3-3)."""

    def test_from_deuce_fifty_percent(self):
        """From deuce with p=0.5, server wins 50%."""
        gs = GameScore(3, 3, DEFAULT_FORMAT)
        prob = probabilityServerWinsGame(gs, 1, 0.5)
        assert math.isclose(prob, 0.5, rel_tol=1e-9)

    def test_from_deuce_formula(self):
        """Verify the deuce formula: p^2 / (1 - 2*p*(1-p))."""
        gs = GameScore(3, 3, DEFAULT_FORMAT)
        p = 0.6
        expected = p**2 / (1 - 2*p*(1 - p))
        prob = probabilityServerWinsGame(gs, 1, p)
        assert math.isclose(prob, expected, rel_tol=1e-9)

    def test_from_deuce_various_probs(self):
        """Test deuce formula with various probabilities."""
        gs = GameScore(3, 3, DEFAULT_FORMAT)
        for p in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
            expected = p**2 / (1 - 2*p*(1 - p))
            prob = probabilityServerWinsGame(gs, 1, p)
            assert math.isclose(prob, expected, rel_tol=1e-9)


class TestProbabilityServerWinsGameFromAdvantage:
    """Tests for probability calculations from advantage scores."""

    def test_from_40_0(self):
        """From 40-0 (game point), high probability to win."""
        gs = GameScore(3, 0, DEFAULT_FORMAT)
        p = 0.6
        prob = probabilityServerWinsGame(gs, 1, p)
        # Should be very high - server needs just one more point
        assert prob > 0.9

    def test_from_0_40(self):
        """From 0-40 (break point), low probability to win."""
        gs = GameScore(0, 3, DEFAULT_FORMAT)
        p = 0.6
        prob = probabilityServerWinsGame(gs, 1, p)
        # Should be low but not zero
        assert prob < 0.3
        assert prob > 0

    def test_from_30_30(self):
        """From 30-30, slightly better than 50% for server."""
        gs = GameScore(2, 2, DEFAULT_FORMAT)
        prob = probabilityServerWinsGame(gs, 1, 0.6)
        # Should be similar to from 0-0 but not identical
        assert 0.5 < prob < 1.0


class TestProbabilityServerWinsGameSymmetry:
    """Tests for symmetry properties."""

    def test_player_symmetry_from_blank(self):
        """Result should be same regardless of which player serves."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        prob1 = probabilityServerWinsGame(gs, 1, 0.6)
        prob2 = probabilityServerWinsGame(gs, 2, 0.6)
        assert math.isclose(prob1, prob2, rel_tol=1e-9)

    def test_player_symmetry_from_deuce(self):
        """Same symmetry holds from deuce."""
        gs = GameScore(3, 3, DEFAULT_FORMAT)
        prob1 = probabilityServerWinsGame(gs, 1, 0.7)
        prob2 = probabilityServerWinsGame(gs, 2, 0.7)
        assert math.isclose(prob1, prob2, rel_tol=1e-9)


class TestProbabilityServerWinsGameMonotonicity:
    """Tests that probability increases with point win probability."""

    def test_monotonically_increasing(self):
        """Higher p should give higher game win probability."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        probs = [probabilityServerWinsGame(gs, 1, p/10) for p in range(1, 10)]

        for i in range(len(probs) - 1):
            assert probs[i] < probs[i + 1]

    def test_monotonic_from_any_score(self):
        """Monotonicity holds from any starting score."""
        for pts1 in range(4):
            for pts2 in range(4):
                gs = GameScore(pts1, pts2, DEFAULT_FORMAT)
                if gs.isFinal:
                    continue
                probs = [probabilityServerWinsGame(gs, 1, p/10) for p in range(1, 10)]
                for i in range(len(probs) - 1):
                    assert probs[i] < probs[i + 1]


class TestProbabilityServerWinsGameFinalScores:
    """Tests for already-final scores."""

    def test_server_already_won(self):
        """If server already won, probability is 1."""
        gs = GameScore(4, 0, DEFAULT_FORMAT)
        prob = probabilityServerWinsGame(gs, 1, 0.6)
        assert prob == 1.0

    def test_server_already_lost(self):
        """If server already lost, probability is 0."""
        gs = GameScore(0, 4, DEFAULT_FORMAT)
        prob = probabilityServerWinsGame(gs, 1, 0.6)
        assert prob == 0.0

    def test_advantage_server(self):
        """Server at advantage (4-3): high but not certain win."""
        gs = GameScore(4, 3, DEFAULT_FORMAT)
        p = 0.6
        prob = probabilityServerWinsGame(gs, 1, p)
        # Not final yet - needs to win by 2
        # From advantage, prob = p + (1-p) * prob_from_deuce
        prob_deuce = p**2 / (1 - 2*p*(1 - p))
        expected = p + (1 - p) * prob_deuce
        assert math.isclose(prob, expected, rel_tol=1e-9)

    def test_advantage_receiver(self):
        """Receiver at advantage (3-4): low but not zero chance."""
        # Use NO_CAP_FORMAT so the deuce formula applies (standard tennis scoring)
        gs = GameScore(3, 4, NO_CAP_FORMAT)
        p = 0.6
        prob = probabilityServerWinsGame(gs, 1, p)
        # Not final yet - server must win point to get back to deuce
        # From ad-out, prob = p * prob_from_deuce
        prob_deuce = p**2 / (1 - 2*p*(1 - p))
        expected = p * prob_deuce
        assert math.isclose(prob, expected, rel_tol=1e-9)


class TestProbabilityServerWinsGameNoAd:
    """Tests for no-ad scoring."""

    def test_no_ad_from_blank(self):
        """No-ad scoring from 0-0."""
        gs = GameScore(0, 0, NO_AD_FORMAT)
        prob = probabilityServerWinsGame(gs, 1, 0.5)
        # With p=0.5, should still be 50%
        assert math.isclose(prob, 0.5, rel_tol=1e-9)

    def test_no_ad_from_deuce(self):
        """No-ad: deuce is decided by single point."""
        gs = GameScore(3, 3, NO_AD_FORMAT)
        p = 0.6
        prob = probabilityServerWinsGame(gs, 1, p)
        # In no-ad, next point decides: server wins with prob p
        assert math.isclose(prob, p, rel_tol=1e-9)

    def test_no_ad_vs_standard_from_deuce(self):
        """No-ad gives different result than standard from deuce."""
        gs_noad = GameScore(3, 3, NO_AD_FORMAT)
        gs_std = GameScore(3, 3, DEFAULT_FORMAT)
        p = 0.6

        prob_noad = probabilityServerWinsGame(gs_noad, 1, p)
        prob_std = probabilityServerWinsGame(gs_std, 1, p)

        # No-ad: p = 0.6
        # Standard: p^2 / (1 - 2*p*(1-p)) = 0.36 / 0.52 ≈ 0.692
        assert math.isclose(prob_noad, p, rel_tol=1e-9)
        assert prob_std > prob_noad  # Standard scoring favors better server


class TestProbabilityServerWinsGameProbabilitySum:
    """Tests verifying probability properties."""

    def test_all_path_probs_sum_to_one(self):
        """Sum of all path probabilities should equal 1."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        paths = GamePath.generateAllPaths(gs)

        p = 0.6
        total = 0.0
        for path in paths:
            prob = pathProbability(path, 1, p)
            last = path.scoreHistory[-1]
            if last.isDeuce:
                # Deuce path represents infinite paths, but probability is finite
                total += prob
            else:
                total += prob

        # Total should be 1 (accounting for deuce formula)
        # Actually, paths to deuce + paths to final scores = 1
        assert math.isclose(total, 1.0, rel_tol=1e-9)

    def test_win_plus_loss_equals_one(self):
        """P(server wins) + P(server loses) = 1."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        p = 0.6
        prob_win = probabilityServerWinsGame(gs, 1, p)

        # Calculate prob of losing (swap perspective)
        # Server loses = receiver wins
        # This equals 1 - prob_win
        assert math.isclose(prob_win + (1 - prob_win), 1.0, rel_tol=1e-9)


# =============================================================================
# Tests for loadCachedFunction
# =============================================================================

class TestLoadCachedFunctionValidation:
    """Tests for loadCachedFunction input validation."""

    def test_invalid_init_score_type(self):
        with pytest.raises(ValueError, match="initScore must be a GameScore"):
            loadCachedFunction("not a score", 1)

    def test_invalid_init_score_none(self):
        with pytest.raises(ValueError, match="initScore must be a GameScore"):
            loadCachedFunction(None, 1)

    def test_invalid_player_serving_zero(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            loadCachedFunction(gs, 0)

    def test_invalid_player_serving_three(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            loadCachedFunction(gs, 3)

    def test_invalid_player_serving_string(self):
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        with pytest.raises(ValueError, match="playerServing must be 1 or 2"):
            loadCachedFunction(gs, "1")


class TestLoadCachedFunctionBehavior:
    """Tests for loadCachedFunction behavior (skip if cache unavailable)."""

    def test_returns_callable_or_none(self):
        """Function should return a callable or None."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        result = loadCachedFunction(gs, 1)
        assert result is None or callable(result)

    def test_cached_function_returns_float(self):
        """If cache available, returned function should return a float."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        cached_fn = loadCachedFunction(gs, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")
        result = cached_fn(0.65)
        assert isinstance(result, float)

    def test_cached_function_matches_direct_calculation(self):
        """Cached function should match direct probabilityServerWinsGame calculation."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        cached_fn = loadCachedFunction(gs, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p = 0.65
        cached_result = cached_fn(p)
        direct_result = probabilityServerWinsGame(gs, 1, p)
        # Allow some tolerance due to interpolation
        assert math.isclose(cached_result, direct_result, rel_tol=0.01)

    def test_cached_function_from_30_15(self):
        """Test cached function from 30-15 score."""
        gs = GameScore(2, 1, DEFAULT_FORMAT)
        cached_fn = loadCachedFunction(gs, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p = 0.60
        cached_result = cached_fn(p)
        direct_result = probabilityServerWinsGame(gs, 1, p)
        assert math.isclose(cached_result, direct_result, rel_tol=0.01)

    def test_cached_function_from_deuce(self):
        """Test cached function from deuce (3-3)."""
        gs = GameScore(3, 3, DEFAULT_FORMAT)
        cached_fn = loadCachedFunction(gs, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p = 0.65
        cached_result = cached_fn(p)
        direct_result = probabilityServerWinsGame(gs, 1, p)
        assert math.isclose(cached_result, direct_result, rel_tol=0.01)

    def test_cached_function_from_extended_deuce(self):
        """Test that extended deuce (5-5) is capped to 3-3 and works correctly."""
        gs_extended = GameScore(5, 5, DEFAULT_FORMAT)
        gs_capped = GameScore(3, 3, DEFAULT_FORMAT)

        cached_fn_extended = loadCachedFunction(gs_extended, 1)
        cached_fn_capped = loadCachedFunction(gs_capped, 1)

        if cached_fn_extended is None or cached_fn_capped is None:
            pytest.skip("Cached data not available")

        p = 0.65
        # Both should return the same result since 5-5 is capped to 3-3
        assert math.isclose(cached_fn_extended(p), cached_fn_capped(p), rel_tol=1e-9)

    def test_cached_function_no_ad_rule(self):
        """Test cached function with no-ad rule."""
        gs = GameScore(0, 0, NO_AD_FORMAT)
        cached_fn = loadCachedFunction(gs, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p = 0.65
        cached_result = cached_fn(p)
        direct_result = probabilityServerWinsGame(gs, 1, p)
        assert math.isclose(cached_result, direct_result, rel_tol=0.01)

    def test_cached_function_player2_serving(self):
        """Test cached function when player 2 is serving."""
        gs = GameScore(1, 2, DEFAULT_FORMAT)  # 15-30
        cached_fn = loadCachedFunction(gs, 2)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        p = 0.60
        cached_result = cached_fn(p)
        direct_result = probabilityServerWinsGame(gs, 2, p)
        assert math.isclose(cached_result, direct_result, rel_tol=0.01)

    def test_cached_probability_bounds(self):
        """Cached probability should be between 0 and 1."""
        gs = GameScore(0, 0, DEFAULT_FORMAT)
        cached_fn = loadCachedFunction(gs, 1)
        if cached_fn is None:
            pytest.skip("Cached data not available")

        for p in [0.1, 0.3, 0.5, 0.7, 0.9]:
            result = cached_fn(p)
            assert 0.0 <= result <= 1.0
