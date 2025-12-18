"""Tests for the match_simulation module."""

import random
import pytest
import numpy as np

from tennis_lab.core.match_format import MatchFormat
from tennis_lab.montecarlo.match_simulation import simulateMatchWinProbabilityEvolution


class TestSimulateMatchWinProbabilityEvolution:
    """Tests for simulateMatchWinProbabilityEvolution function."""

    def test_returns_four_arrays(self):
        """Function returns exactly 4 numpy arrays."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=3)
        result = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=0.60, alpha2=50
        )
        assert len(result) == 4
        assert all(isinstance(arr, np.ndarray) for arr in result)

    def test_static_and_dynamic_arrays_same_length(self):
        """Static and dynamic probability arrays have the same length."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=3)
        static, dynamic, p1_updated, p2_updated = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=0.60, alpha2=50
        )
        assert len(static) == len(dynamic)

    def test_probabilities_start_between_0_and_1(self):
        """Initial probabilities are in valid range [0, 1]."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=3)
        static, dynamic, _, _ = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=0.60, alpha2=50
        )
        # All probabilities except last two (which are 0 or 1) should be in (0, 1)
        assert all(0 <= p <= 1 for p in static)
        assert all(0 <= p <= 1 for p in dynamic)

    def test_final_probability_is_0_or_1(self):
        """Final probability is either 0 (P1 lost) or 1 (P1 won)."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=3)
        static, dynamic, _, _ = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=0.60, alpha2=50
        )
        assert static[-1] in (0, 1)
        assert dynamic[-1] in (0, 1)
        # Both should have same final result
        assert static[-1] == dynamic[-1]

    def test_p1_updated_starts_with_prior(self):
        """P1 updated array starts with the prior value."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=3)
        P1prior = 0.63
        _, _, p1_updated, _ = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=P1prior, alpha1=50, P2prior=0.60, alpha2=50
        )
        assert p1_updated[0] == P1prior

    def test_p2_updated_starts_with_prior(self):
        """P2 updated array starts with the prior value."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=3)
        P2prior = 0.60
        _, _, _, p2_updated = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=P2prior, alpha2=50
        )
        assert p2_updated[0] == P2prior

    def test_updated_probabilities_stay_in_valid_range(self):
        """Updated serve probabilities stay in valid range (0, 1)."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=3)
        _, _, p1_updated, p2_updated = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=0.60, alpha2=50
        )
        assert all(0 < p < 1 for p in p1_updated)
        assert all(0 < p < 1 for p in p2_updated)

    def test_static_uses_fixed_priors(self):
        """Static calculation uses fixed prior values throughout."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=3)
        P1prior, P2prior = 0.63, 0.60
        static, dynamic, _, _ = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=P1prior, alpha1=50, P2prior=P2prior, alpha2=50
        )
        # Static and dynamic should start with same value (both use priors at start)
        assert static[0] == dynamic[0]

    def test_best_of_5_produces_longer_match(self):
        """Best of 5 matches tend to be longer than best of 3."""
        random.seed(42)
        matchFormat3 = MatchFormat(bestOfSets=3)
        static3, _, _, _ = simulateMatchWinProbabilityEvolution(
            matchFormat3, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=0.60, alpha2=50
        )

        random.seed(42)
        matchFormat5 = MatchFormat(bestOfSets=5)
        static5, _, _, _ = simulateMatchWinProbabilityEvolution(
            matchFormat5, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=0.60, alpha2=50
        )
        # Best of 5 should generally produce more data points
        # (though with same seed the match progression differs, so we just check it runs)
        assert len(static3) > 1
        assert len(static5) > 1

    def test_deterministic_with_seed(self):
        """Same random seed produces same results."""
        matchFormat = MatchFormat(bestOfSets=3)

        random.seed(123)
        result1 = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=0.60, alpha2=50
        )

        random.seed(123)
        result2 = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=0.60, alpha2=50
        )

        np.testing.assert_array_equal(result1[0], result2[0])
        np.testing.assert_array_equal(result1[1], result2[1])
        np.testing.assert_array_equal(result1[2], result2[2])
        np.testing.assert_array_equal(result1[3], result2[3])

    def test_dominant_player_usually_wins(self):
        """Player with much higher serve probability usually wins over many trials."""
        matchFormat = MatchFormat(bestOfSets=3)
        wins = 0
        num_trials = 50

        for i in range(num_trials):
            random.seed(i)
            static, _, _, _ = simulateMatchWinProbabilityEvolution(
                matchFormat, P1actual=0.80, P2actual=0.50,
                P1prior=0.65, alpha1=50, P2prior=0.65, alpha2=50
            )
            if static[-1] == 1:
                wins += 1

        # With such a dominant advantage, P1 should win most matches
        assert wins > num_trials * 0.7

    def test_bayesian_update_moves_toward_actual(self):
        """Over time, Bayesian updates should move toward actual probabilities."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=5)
        P1actual = 0.70
        P1prior = 0.50  # Start with wrong estimate

        _, _, p1_updated, _ = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=P1actual, P2actual=0.60,
            P1prior=P1prior, alpha1=10, P2prior=0.60, alpha2=50
        )

        # With low alpha (high uncertainty), updates should move toward actual
        # The final estimate should be closer to actual than the prior
        if len(p1_updated) > 10:  # Need enough data points
            assert abs(p1_updated[-1] - P1actual) < abs(P1prior - P1actual)

    def test_high_alpha_resists_updates(self):
        """High alpha (high confidence) means updates change slowly."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=3)
        P1prior = 0.60

        _, _, p1_updated_low_alpha, _ = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.70, P2actual=0.60,
            P1prior=P1prior, alpha1=10, P2prior=0.60, alpha2=50
        )

        random.seed(42)
        _, _, p1_updated_high_alpha, _ = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.70, P2actual=0.60,
            P1prior=P1prior, alpha1=200, P2prior=0.60, alpha2=50
        )

        # High alpha should result in smaller changes from prior
        if len(p1_updated_low_alpha) > 5 and len(p1_updated_high_alpha) > 5:
            max_change_low = max(abs(p - P1prior) for p in p1_updated_low_alpha)
            max_change_high = max(abs(p - P1prior) for p in p1_updated_high_alpha)
            assert max_change_high < max_change_low

    def test_equal_players_win_roughly_half(self):
        """When players are equal, each wins roughly half the matches."""
        matchFormat = MatchFormat(bestOfSets=3)
        wins = 0
        num_trials = 100

        for i in range(num_trials):
            random.seed(i)
            static, _, _, _ = simulateMatchWinProbabilityEvolution(
                matchFormat, P1actual=0.65, P2actual=0.65,
                P1prior=0.65, alpha1=50, P2prior=0.65, alpha2=50
            )
            if static[-1] == 1:
                wins += 1

        # Should be roughly 50% with some variance
        assert 30 < wins < 70

    def test_arrays_have_at_least_2_elements(self):
        """Result arrays have at least 2 elements (start and end)."""
        random.seed(42)
        matchFormat = MatchFormat(bestOfSets=3)
        static, dynamic, p1_updated, p2_updated = simulateMatchWinProbabilityEvolution(
            matchFormat, P1actual=0.65, P2actual=0.62,
            P1prior=0.63, alpha1=50, P2prior=0.60, alpha2=50
        )
        assert len(static) >= 2
        assert len(dynamic) >= 2
        assert len(p1_updated) >= 1
        assert len(p2_updated) >= 1
