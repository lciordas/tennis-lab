"""Tests for the TiebreakerScore class."""

import pytest
from src.core.tiebreaker_score import TiebreakerScore


class TestTiebreakerScoreInit:
    """Tests for TiebreakerScore initialization."""

    def test_init_blank_score(self):
        score = TiebreakerScore(0, 0, isSuper=False)
        assert score.asPoints(1) == (0, 0)
        assert score.isBlank

    def test_init_blank_score_super(self):
        score = TiebreakerScore(0, 0, isSuper=True)
        assert score.asPoints(1) == (0, 0)
        assert score.isBlank

    def test_init_valid_scores(self):
        # Standard tiebreaker scores
        assert TiebreakerScore(0, 0, isSuper=False).asPoints(1) == (0, 0)
        assert TiebreakerScore(3, 2, isSuper=False).asPoints(1) == (3, 2)
        assert TiebreakerScore(6, 6, isSuper=False).asPoints(1) == (6, 6)
        assert TiebreakerScore(7, 5, isSuper=False).asPoints(1) == (7, 5)

    def test_init_valid_scores_super(self):
        # Super-tiebreaker scores
        assert TiebreakerScore(0, 0, isSuper=True).asPoints(1) == (0, 0)
        assert TiebreakerScore(5, 3, isSuper=True).asPoints(1) == (5, 3)
        assert TiebreakerScore(9, 9, isSuper=True).asPoints(1) == (9, 9)
        assert TiebreakerScore(10, 8, isSuper=True).asPoints(1) == (10, 8)

    def test_init_invalid_negative(self):
        with pytest.raises(ValueError):
            TiebreakerScore(-1, 0, isSuper=False)
        with pytest.raises(ValueError):
            TiebreakerScore(0, -1, isSuper=False)

    def test_init_invalid_isSuper_type(self):
        with pytest.raises(ValueError):
            TiebreakerScore(0, 0, isSuper="False")
        with pytest.raises(ValueError):
            TiebreakerScore(0, 0, isSuper=1)
        with pytest.raises(ValueError):
            TiebreakerScore(0, 0, isSuper=None)

    def test_init_invalid_too_far_apart(self):
        # Can't be more than 2 apart after reaching pointsToWin
        with pytest.raises(ValueError):
            TiebreakerScore(9, 6, isSuper=False)
        with pytest.raises(ValueError):
            TiebreakerScore(12, 9, isSuper=True)

    def test_init_valid_extended_tiebreaker(self):
        # Extended tiebreaker scores (beyond pointsToWin)
        TiebreakerScore(8, 6, isSuper=False)  # valid win
        TiebreakerScore(7, 7, isSuper=False)  # deuce at 7-7
        TiebreakerScore(8, 7, isSuper=False)  # advantage
        TiebreakerScore(11, 9, isSuper=True)  # valid super win
        TiebreakerScore(10, 10, isSuper=True)  # deuce at 10-10

    def test_init_with_normalize(self):
        # When normalize=True, extended deuce should collapse to 6-6 (9-9 if super)
        score = TiebreakerScore(8, 8, isSuper=False, normalize=True)
        assert score.asPoints(1) == (6, 6)

        score = TiebreakerScore(11, 11, isSuper=True, normalize=True)
        assert score.asPoints(1) == (9, 9)

        # Extended advantage should collapse to 7-6 or 6-7 (10-9 or 9-10 if super)
        score = TiebreakerScore(9, 8, isSuper=False, normalize=True)
        assert score.asPoints(1) == (7, 6)

        score = TiebreakerScore(8, 9, isSuper=False, normalize=True)
        assert score.asPoints(1) == (6, 7)


class TestTiebreakerScoreProperties:
    """Tests for TiebreakerScore properties."""

    def test_is_blank(self):
        assert TiebreakerScore(0, 0, isSuper=False).isBlank
        assert not TiebreakerScore(1, 0, isSuper=False).isBlank
        assert not TiebreakerScore(0, 1, isSuper=False).isBlank

    def test_is_deuce(self):
        # Standard tiebreaker - deuce at 6-6 and above
        assert not TiebreakerScore(0, 0, isSuper=False).isDeuce
        assert not TiebreakerScore(5, 5, isSuper=False).isDeuce
        assert TiebreakerScore(6, 6, isSuper=False).isDeuce
        assert TiebreakerScore(7, 7, isSuper=False).isDeuce

    def test_is_deuce_super(self):
        # Super-tiebreaker - deuce at 9-9 and above
        assert not TiebreakerScore(0, 0, isSuper=True).isDeuce
        assert not TiebreakerScore(8, 8, isSuper=True).isDeuce
        assert TiebreakerScore(9, 9, isSuper=True).isDeuce
        assert TiebreakerScore(10, 10, isSuper=True).isDeuce

    def test_is_final(self):
        # Not final
        assert not TiebreakerScore(0, 0, isSuper=False).isFinal
        assert not TiebreakerScore(6, 6, isSuper=False).isFinal
        assert not TiebreakerScore(7, 6, isSuper=False).isFinal  # advantage, not win

        # Final - standard tiebreaker
        assert TiebreakerScore(7, 0, isSuper=False).isFinal
        assert TiebreakerScore(7, 5, isSuper=False).isFinal
        assert TiebreakerScore(8, 6, isSuper=False).isFinal

    def test_is_final_super(self):
        # Not final
        assert not TiebreakerScore(9, 9, isSuper=True).isFinal
        assert not TiebreakerScore(10, 9, isSuper=True).isFinal  # advantage, not win

        # Final - super-tiebreaker
        assert TiebreakerScore(10, 0, isSuper=True).isFinal
        assert TiebreakerScore(10, 8, isSuper=True).isFinal
        assert TiebreakerScore(11, 9, isSuper=True).isFinal

    def test_player_with_advantage(self):
        assert TiebreakerScore(0, 0, isSuper=False).playerWithAdvantage is None
        assert TiebreakerScore(6, 6, isSuper=False).playerWithAdvantage is None  # deuce
        assert TiebreakerScore(7, 6, isSuper=False).playerWithAdvantage == 1
        assert TiebreakerScore(6, 7, isSuper=False).playerWithAdvantage == 2
        assert TiebreakerScore(8, 7, isSuper=False).playerWithAdvantage == 1

    def test_player_with_advantage_super(self):
        assert TiebreakerScore(9, 9, isSuper=True).playerWithAdvantage is None  # deuce
        assert TiebreakerScore(10, 9, isSuper=True).playerWithAdvantage == 1
        assert TiebreakerScore(9, 10, isSuper=True).playerWithAdvantage == 2
        assert TiebreakerScore(11, 10, isSuper=True).playerWithAdvantage == 1

    def test_winner(self):
        assert TiebreakerScore(0, 0, isSuper=False).winner is None
        assert TiebreakerScore(6, 6, isSuper=False).winner is None
        assert TiebreakerScore(7, 6, isSuper=False).winner is None  # advantage, not win
        assert TiebreakerScore(7, 0, isSuper=False).winner == 1
        assert TiebreakerScore(7, 5, isSuper=False).winner == 1
        assert TiebreakerScore(0, 7, isSuper=False).winner == 2
        assert TiebreakerScore(8, 6, isSuper=False).winner == 1
        assert TiebreakerScore(6, 8, isSuper=False).winner == 2

    def test_winner_super(self):
        assert TiebreakerScore(9, 9, isSuper=True).winner is None
        assert TiebreakerScore(10, 9, isSuper=True).winner is None  # advantage, not win
        assert TiebreakerScore(10, 0, isSuper=True).winner == 1
        assert TiebreakerScore(10, 8, isSuper=True).winner == 1
        assert TiebreakerScore(0, 10, isSuper=True).winner == 2
        assert TiebreakerScore(11, 9, isSuper=True).winner == 1

    def test_points_to_win(self):
        assert TiebreakerScore(0, 0, isSuper=False).pointsToWin == 7
        assert TiebreakerScore(0, 0, isSuper=True).pointsToWin == 10


class TestRecordPoint:
    """Tests for recordPoint method."""

    def test_record_point_basic(self):
        score = TiebreakerScore(0, 0, isSuper=False)
        score.recordPoint(1)
        assert score.asPoints(1) == (1, 0)

        score.recordPoint(2)
        assert score.asPoints(1) == (1, 1)

    def test_record_point_invalid(self):
        score = TiebreakerScore(0, 0, isSuper=False)
        with pytest.raises(ValueError):
            score.recordPoint(0)
        with pytest.raises(ValueError):
            score.recordPoint(3)

    def test_record_point_with_normalize(self):
        score = TiebreakerScore(6, 6, isSuper=False, normalize=True)
        score.recordPoint(1)  # Should be 7-6 (advantage)
        assert score.asPoints(1) == (7, 6)

        score.recordPoint(2)  # Back to deuce, normalized to 6-6
        assert score.asPoints(1) == (6, 6)

    def test_record_point_without_normalize(self):
        score = TiebreakerScore(6, 6, isSuper=False, normalize=False)
        score.recordPoint(1)
        assert score.asPoints(1) == (7, 6)

        score.recordPoint(2)  # Back to deuce, but NOT normalized
        assert score.asPoints(1) == (7, 7)


class TestAsPoints:
    """Tests for asPoints method."""

    def test_as_points_pov1(self):
        score = TiebreakerScore(5, 3, isSuper=False)
        assert score.asPoints(1) == (5, 3)

    def test_as_points_pov2(self):
        score = TiebreakerScore(5, 3, isSuper=False)
        assert score.asPoints(2) == (3, 5)

    def test_as_points_invalid_pov(self):
        score = TiebreakerScore(0, 0, isSuper=False)
        with pytest.raises(ValueError):
            score.asPoints(0)
        with pytest.raises(ValueError):
            score.asPoints(3)


class TestNextScores:
    """Tests for nextScores method."""

    def test_next_scores_basic(self):
        score = TiebreakerScore(3, 2, isSuper=False)
        next_p1, next_p2 = score.nextScores()
        assert next_p1.asPoints(1) == (4, 2)
        assert next_p2.asPoints(1) == (3, 3)

    def test_next_scores_final(self):
        score = TiebreakerScore(7, 5, isSuper=False)
        assert score.nextScores() is None

    def test_next_scores_propagates_normalize(self):
        score = TiebreakerScore(6, 6, isSuper=False, normalize=True)
        next_p1, next_p2 = score.nextScores()

        # Both should have normalize=True
        # P1 wins point: 7-6 (advantage)
        assert next_p1.asPoints(1) == (7, 6)

        # Simulate another deuce from next_p1
        next_p1.recordPoint(2)  # Should normalize back to 6-6
        assert next_p1.asPoints(1) == (6, 6)

    def test_next_scores_propagates_is_super(self):
        score = TiebreakerScore(9, 9, isSuper=True)
        next_p1, next_p2 = score.nextScores()

        # In super-tiebreaker, 10-9 is advantage, not win
        assert not next_p1.isFinal
        assert next_p1.playerWithAdvantage == 1
        assert not next_p2.isFinal
        assert next_p2.playerWithAdvantage == 2


class TestEquality:
    """Tests for __eq__ and __hash__."""

    def test_equal_scores(self):
        assert TiebreakerScore(5, 3, isSuper=False) == TiebreakerScore(5, 3, isSuper=False)
        assert TiebreakerScore(6, 6, isSuper=True) == TiebreakerScore(6, 6, isSuper=True)

    def test_unequal_scores(self):
        assert TiebreakerScore(5, 3, isSuper=False) != TiebreakerScore(3, 5, isSuper=False)
        assert TiebreakerScore(5, 3, isSuper=False) != TiebreakerScore(5, 4, isSuper=False)

    def test_is_super_affects_equality(self):
        assert TiebreakerScore(5, 3, isSuper=False) != TiebreakerScore(5, 3, isSuper=True)

    def test_normalize_does_not_affect_equality(self):
        # Two scores with same points but different normalize flags should be equal
        assert TiebreakerScore(6, 6, isSuper=False, normalize=False) == TiebreakerScore(6, 6, isSuper=False, normalize=True)

    def test_hash_consistency(self):
        s1 = TiebreakerScore(5, 3, isSuper=False)
        s2 = TiebreakerScore(5, 3, isSuper=False)
        assert hash(s1) == hash(s2)

        # Can use in sets/dicts
        score_set = {s1, s2}
        assert len(score_set) == 1


class TestReprAndStr:
    """Tests for __repr__ and __str__."""

    def test_repr(self):
        score = TiebreakerScore(5, 3, isSuper=False, normalize=True)
        repr_str = repr(score)
        assert "TiebreakerScore" in repr_str
        assert "pointsP1=5" in repr_str
        assert "pointsP2=3" in repr_str
        assert "isSuper=False" in repr_str
        assert "normalize=True" in repr_str

    def test_repr_eval(self):
        # repr should produce valid Python
        score = TiebreakerScore(5, 3, isSuper=True, normalize=False)
        recreated = eval(repr(score))
        assert recreated.asPoints(1) == (5, 3)

    def test_str(self):
        assert str(TiebreakerScore(0, 0, isSuper=False)) == "0-0"
        assert str(TiebreakerScore(5, 3, isSuper=False)) == "5-3"
        assert str(TiebreakerScore(7, 6, isSuper=False)) == "7-6"
        assert str(TiebreakerScore(10, 8, isSuper=True)) == "10-8"


class TestNormalize:
    """Tests for normalization behavior."""

    def test_normalize_deuce(self):
        score = TiebreakerScore(8, 8, isSuper=False, normalize=True)
        assert score.asPoints(1) == (6, 6)

    def test_normalize_deuce_super(self):
        score = TiebreakerScore(11, 11, isSuper=True, normalize=True)
        assert score.asPoints(1) == (9, 9)

    def test_normalize_advantage_p1(self):
        score = TiebreakerScore(9, 8, isSuper=False, normalize=True)
        assert score.asPoints(1) == (7, 6)

    def test_normalize_advantage_p2(self):
        score = TiebreakerScore(8, 9, isSuper=False, normalize=True)
        assert score.asPoints(1) == (6, 7)

    def test_normalize_advantage_p1_super(self):
        score = TiebreakerScore(12, 11, isSuper=True, normalize=True)
        assert score.asPoints(1) == (10, 9)

    def test_normalize_advantage_p2_super(self):
        score = TiebreakerScore(11, 12, isSuper=True, normalize=True)
        assert score.asPoints(1) == (9, 10)

    def test_normalize_no_effect_on_regular_scores(self):
        # Normalization shouldn't affect non-deuce scores
        score = TiebreakerScore(3, 2, isSuper=False, normalize=True)
        assert score.asPoints(1) == (3, 2)

        score = TiebreakerScore(7, 5, isSuper=False, normalize=True)
        assert score.asPoints(1) == (7, 5)


class TestClassConstants:
    """Tests for class constants."""

    def test_points_to_win_tiebreaker(self):
        assert TiebreakerScore.POINTS_TO_WIN_TIEBREAKER == 7

    def test_points_to_win_super_tiebreaker(self):
        assert TiebreakerScore.POINTS_TO_WIN_SUPER_TIEBREAKER == 10


class TestTiebreakerScenarios:
    """Tests for realistic tiebreaker scenarios."""

    def test_standard_tiebreaker_p1_wins_7_0(self):
        score = TiebreakerScore(0, 0, isSuper=False)
        for _ in range(7):
            score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1
        assert score.asPoints(1) == (7, 0)

    def test_standard_tiebreaker_p2_wins_7_5(self):
        score = TiebreakerScore(0, 0, isSuper=False)
        # Alternate until 5-5, then P2 wins 2 straight
        for i in range(10):
            score.recordPoint((i % 2) + 1)
        assert score.asPoints(1) == (5, 5)
        score.recordPoint(2)
        score.recordPoint(2)
        assert score.isFinal
        assert score.winner == 2
        assert score.asPoints(1) == (5, 7)

    def test_extended_tiebreaker_with_multiple_deuces(self):
        score = TiebreakerScore(6, 6, isSuper=False)

        # P1 advantage
        score.recordPoint(1)
        assert score.playerWithAdvantage == 1

        # Back to deuce
        score.recordPoint(2)
        assert score.isDeuce

        # P2 advantage
        score.recordPoint(2)
        assert score.playerWithAdvantage == 2

        # Back to deuce
        score.recordPoint(1)
        assert score.isDeuce

        # P1 wins
        score.recordPoint(1)
        score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1

    def test_super_tiebreaker_p1_wins_10_8(self):
        score = TiebreakerScore(0, 0, isSuper=True)
        # P1 gets to 10-8
        for _ in range(10):
            score.recordPoint(1)
        for _ in range(8):
            score.recordPoint(2)
        # Wait, that's wrong order - let me redo

        score = TiebreakerScore(0, 0, isSuper=True)
        # Simulate a 10-8 win for P1
        points = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 1]  # 10-8
        for p in points:
            score.recordPoint(p)
        assert score.isFinal
        assert score.winner == 1
        assert score.asPoints(1) == (10, 8)

    def test_super_tiebreaker_extended(self):
        score = TiebreakerScore(9, 9, isSuper=True)

        # P1 advantage
        score.recordPoint(1)
        assert score.playerWithAdvantage == 1
        assert not score.isFinal

        # P1 wins
        score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1
        assert score.asPoints(1) == (11, 9)
