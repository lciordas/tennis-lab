"""Tests for the TiebreakScore class."""

import pytest
from src.core.tiebreak_score import TiebreakScore
from src.core.match_format import MatchFormat, SetEnding, POINTS_TO_WIN_TIEBREAK, POINTS_TO_WIN_SUPERTIEBREAK

# Default match formats for tests
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)
CAP_FORMAT     = MatchFormat(bestOfSets=3, capPoints=True)


class TestTiebreakScoreInit:
    """Tests for TiebreakScore initialization."""

    def test_init_blank_score(self):
        score = TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT)
        assert score.asPoints(1) == (0, 0)
        assert score.isBlank

    def test_init_blank_score_super(self):
        score = TiebreakScore(0, 0, isSuper=True, matchFormat=DEFAULT_FORMAT)
        assert score.asPoints(1) == (0, 0)
        assert score.isBlank

    def test_init_valid_scores(self):
        # Standard tiebreak scores
        assert TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT).asPoints(1) == (0, 0)
        assert TiebreakScore(3, 2, isSuper=False, matchFormat=DEFAULT_FORMAT).asPoints(1) == (3, 2)
        assert TiebreakScore(6, 6, isSuper=False, matchFormat=DEFAULT_FORMAT).asPoints(1) == (6, 6)
        assert TiebreakScore(7, 5, isSuper=False, matchFormat=DEFAULT_FORMAT).asPoints(1) == (7, 5)

    def test_init_valid_scores_super(self):
        # Super-tiebreak scores
        assert TiebreakScore(0, 0, isSuper=True, matchFormat=DEFAULT_FORMAT).asPoints(1) == (0, 0)
        assert TiebreakScore(5, 3, isSuper=True, matchFormat=DEFAULT_FORMAT).asPoints(1) == (5, 3)
        assert TiebreakScore(9, 9, isSuper=True, matchFormat=DEFAULT_FORMAT).asPoints(1) == (9, 9)
        assert TiebreakScore(10, 8, isSuper=True, matchFormat=DEFAULT_FORMAT).asPoints(1) == (10, 8)

    def test_init_invalid_negative(self):
        with pytest.raises(ValueError):
            TiebreakScore(-1, 0, isSuper=False, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            TiebreakScore(0, -1, isSuper=False, matchFormat=DEFAULT_FORMAT)

    def test_init_invalid_isSuper_type(self):
        with pytest.raises(ValueError):
            TiebreakScore(0, 0, isSuper="False", matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            TiebreakScore(0, 0, isSuper=1, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            TiebreakScore(0, 0, isSuper=None, matchFormat=DEFAULT_FORMAT)

    def test_init_invalid_matchFormat_type(self):
        with pytest.raises(ValueError):
            TiebreakScore(0, 0, isSuper=False, matchFormat="invalid")
        with pytest.raises(ValueError):
            TiebreakScore(0, 0, isSuper=False, matchFormat=None)

    def test_init_invalid_too_far_apart(self):
        # Can't be more than 2 apart after reaching pointsToWin
        with pytest.raises(ValueError):
            TiebreakScore(9, 6, isSuper=False, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            TiebreakScore(12, 9, isSuper=True, matchFormat=DEFAULT_FORMAT)

    def test_init_valid_extended_tiebreak(self):
        # Extended tiebreak scores (beyond pointsToWin)
        TiebreakScore(8, 6, isSuper=False, matchFormat=DEFAULT_FORMAT)  # valid win
        TiebreakScore(7, 7, isSuper=False, matchFormat=DEFAULT_FORMAT)  # deuce at 7-7
        TiebreakScore(8, 7, isSuper=False, matchFormat=DEFAULT_FORMAT)  # advantage
        TiebreakScore(11, 9, isSuper=True, matchFormat=DEFAULT_FORMAT)  # valid super win
        TiebreakScore(10, 10, isSuper=True, matchFormat=DEFAULT_FORMAT) # deuce at 10-10

    def test_init_with_capPoints(self):
        # When capPoints=True, extended deuce should collapse to 6-6 (9-9 if super)
        score = TiebreakScore(8, 8, isSuper=False, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (6, 6)

        score = TiebreakScore(11, 11, isSuper=True, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (9, 9)

        # Extended advantage should collapse to 7-6 or 6-7 (10-9 or 9-10 if super)
        score = TiebreakScore(9, 8, isSuper=False, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (7, 6)

        score = TiebreakScore(8, 9, isSuper=False, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (6, 7)


class TestTiebreakScoreProperties:
    """Tests for TiebreakScore properties."""

    def test_is_blank(self):
        assert TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT).isBlank
        assert not TiebreakScore(1, 0, isSuper=False, matchFormat=DEFAULT_FORMAT).isBlank
        assert not TiebreakScore(0, 1, isSuper=False, matchFormat=DEFAULT_FORMAT).isBlank

    def test_is_deuce(self):
        # Standard tiebreak - deuce at 6-6 and above
        assert not TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT).isDeuce
        assert not TiebreakScore(5, 5, isSuper=False, matchFormat=DEFAULT_FORMAT).isDeuce
        assert TiebreakScore(6, 6, isSuper=False, matchFormat=DEFAULT_FORMAT).isDeuce
        assert TiebreakScore(7, 7, isSuper=False, matchFormat=DEFAULT_FORMAT).isDeuce

    def test_is_deuce_super(self):
        # Super-tiebreak - deuce at 9-9 and above
        assert not TiebreakScore(0, 0, isSuper=True, matchFormat=DEFAULT_FORMAT).isDeuce
        assert not TiebreakScore(8, 8, isSuper=True, matchFormat=DEFAULT_FORMAT).isDeuce
        assert TiebreakScore(9, 9, isSuper=True, matchFormat=DEFAULT_FORMAT).isDeuce
        assert TiebreakScore(10, 10, isSuper=True, matchFormat=DEFAULT_FORMAT).isDeuce

    def test_is_final(self):
        # Not final
        assert not TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT).isFinal
        assert not TiebreakScore(6, 6, isSuper=False, matchFormat=DEFAULT_FORMAT).isFinal
        assert not TiebreakScore(7, 6, isSuper=False, matchFormat=DEFAULT_FORMAT).isFinal  # advantage, not win

        # Final - standard tiebreak
        assert TiebreakScore(7, 0, isSuper=False, matchFormat=DEFAULT_FORMAT).isFinal
        assert TiebreakScore(7, 5, isSuper=False, matchFormat=DEFAULT_FORMAT).isFinal
        assert TiebreakScore(8, 6, isSuper=False, matchFormat=DEFAULT_FORMAT).isFinal

    def test_is_final_super(self):
        # Not final
        assert not TiebreakScore(9, 9, isSuper=True, matchFormat=DEFAULT_FORMAT).isFinal
        assert not TiebreakScore(10, 9, isSuper=True, matchFormat=DEFAULT_FORMAT).isFinal  # advantage, not win

        # Final - super-tiebreak
        assert TiebreakScore(10, 0, isSuper=True, matchFormat=DEFAULT_FORMAT).isFinal
        assert TiebreakScore(10, 8, isSuper=True, matchFormat=DEFAULT_FORMAT).isFinal
        assert TiebreakScore(11, 9, isSuper=True, matchFormat=DEFAULT_FORMAT).isFinal

    def test_player_with_advantage(self):
        assert TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT).playerWithAdvantage is None
        assert TiebreakScore(6, 6, isSuper=False, matchFormat=DEFAULT_FORMAT).playerWithAdvantage is None  # deuce
        assert TiebreakScore(7, 6, isSuper=False, matchFormat=DEFAULT_FORMAT).playerWithAdvantage == 1
        assert TiebreakScore(6, 7, isSuper=False, matchFormat=DEFAULT_FORMAT).playerWithAdvantage == 2
        assert TiebreakScore(8, 7, isSuper=False, matchFormat=DEFAULT_FORMAT).playerWithAdvantage == 1

    def test_player_with_advantage_super(self):
        assert TiebreakScore(9, 9, isSuper=True, matchFormat=DEFAULT_FORMAT).playerWithAdvantage is None  # deuce
        assert TiebreakScore(10, 9, isSuper=True, matchFormat=DEFAULT_FORMAT).playerWithAdvantage == 1
        assert TiebreakScore(9, 10, isSuper=True, matchFormat=DEFAULT_FORMAT).playerWithAdvantage == 2
        assert TiebreakScore(11, 10, isSuper=True, matchFormat=DEFAULT_FORMAT).playerWithAdvantage == 1

    def test_winner(self):
        assert TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT).winner is None
        assert TiebreakScore(6, 6, isSuper=False, matchFormat=DEFAULT_FORMAT).winner is None
        assert TiebreakScore(7, 6, isSuper=False, matchFormat=DEFAULT_FORMAT).winner is None  # advantage, not win
        assert TiebreakScore(7, 0, isSuper=False, matchFormat=DEFAULT_FORMAT).winner == 1
        assert TiebreakScore(7, 5, isSuper=False, matchFormat=DEFAULT_FORMAT).winner == 1
        assert TiebreakScore(0, 7, isSuper=False, matchFormat=DEFAULT_FORMAT).winner == 2
        assert TiebreakScore(8, 6, isSuper=False, matchFormat=DEFAULT_FORMAT).winner == 1
        assert TiebreakScore(6, 8, isSuper=False, matchFormat=DEFAULT_FORMAT).winner == 2

    def test_winner_super(self):
        assert TiebreakScore(9, 9, isSuper=True, matchFormat=DEFAULT_FORMAT).winner is None
        assert TiebreakScore(10, 9, isSuper=True, matchFormat=DEFAULT_FORMAT).winner is None  # advantage, not win
        assert TiebreakScore(10, 0, isSuper=True, matchFormat=DEFAULT_FORMAT).winner == 1
        assert TiebreakScore(10, 8, isSuper=True, matchFormat=DEFAULT_FORMAT).winner == 1
        assert TiebreakScore(0, 10, isSuper=True, matchFormat=DEFAULT_FORMAT).winner == 2
        assert TiebreakScore(11, 9, isSuper=True, matchFormat=DEFAULT_FORMAT).winner == 1

    def test_points_to_win(self):
        assert TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT).pointsToWin == 7
        assert TiebreakScore(0, 0, isSuper=True, matchFormat=DEFAULT_FORMAT).pointsToWin == 10


class TestRecordPoint:
    """Tests for recordPoint method."""

    def test_record_point_basic(self):
        score = TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT)
        score.recordPoint(1)
        assert score.asPoints(1) == (1, 0)

        score.recordPoint(2)
        assert score.asPoints(1) == (1, 1)

    def test_record_point_invalid(self):
        score = TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            score.recordPoint(0)
        with pytest.raises(ValueError):
            score.recordPoint(3)

    def test_record_point_with_capPoints(self):
        score = TiebreakScore(6, 6, isSuper=False, matchFormat=CAP_FORMAT)
        score.recordPoint(1)  # Should be 7-6 (advantage)
        assert score.asPoints(1) == (7, 6)

        score.recordPoint(2)  # Back to deuce, capped to 6-6
        assert score.asPoints(1) == (6, 6)

    def test_record_point_without_capPoints(self):
        score = TiebreakScore(6, 6, isSuper=False, matchFormat=DEFAULT_FORMAT)
        score.recordPoint(1)
        assert score.asPoints(1) == (7, 6)

        score.recordPoint(2)  # Back to deuce, but NOT capped
        assert score.asPoints(1) == (7, 7)


class TestAsPoints:
    """Tests for asPoints method."""

    def test_as_points_pov1(self):
        score = TiebreakScore(5, 3, isSuper=False, matchFormat=DEFAULT_FORMAT)
        assert score.asPoints(1) == (5, 3)

    def test_as_points_pov2(self):
        score = TiebreakScore(5, 3, isSuper=False, matchFormat=DEFAULT_FORMAT)
        assert score.asPoints(2) == (3, 5)

    def test_as_points_invalid_pov(self):
        score = TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            score.asPoints(0)
        with pytest.raises(ValueError):
            score.asPoints(3)


class TestNextScores:
    """Tests for nextScores method."""

    def test_next_scores_basic(self):
        score = TiebreakScore(3, 2, isSuper=False, matchFormat=DEFAULT_FORMAT)
        next_p1, next_p2 = score.nextScores()
        assert next_p1.asPoints(1) == (4, 2)
        assert next_p2.asPoints(1) == (3, 3)

    def test_next_scores_final(self):
        score = TiebreakScore(7, 5, isSuper=False, matchFormat=DEFAULT_FORMAT)
        assert score.nextScores() is None

    def test_next_scores_propagates_capPoints(self):
        score = TiebreakScore(6, 6, isSuper=False, matchFormat=CAP_FORMAT)
        next_p1, next_p2 = score.nextScores()

        # Both should have capPoints=True
        # P1 wins point: 7-6 (advantage)
        assert next_p1.asPoints(1) == (7, 6)

        # Simulate another deuce from next_p1
        next_p1.recordPoint(2)  # Should cap back to 6-6
        assert next_p1.asPoints(1) == (6, 6)

    def test_next_scores_propagates_is_super(self):
        score = TiebreakScore(9, 9, isSuper=True, matchFormat=DEFAULT_FORMAT)
        next_p1, next_p2 = score.nextScores()

        # In super-tiebreak, 10-9 is advantage, not win
        assert not next_p1.isFinal
        assert next_p1.playerWithAdvantage == 1
        assert not next_p2.isFinal
        assert next_p2.playerWithAdvantage == 2


class TestEquality:
    """Tests for __eq__ and __hash__."""

    def test_equal_scores(self):
        assert TiebreakScore(5, 3, isSuper=False, matchFormat=DEFAULT_FORMAT) == TiebreakScore(5, 3, isSuper=False, matchFormat=DEFAULT_FORMAT)
        assert TiebreakScore(6, 6, isSuper=True, matchFormat=DEFAULT_FORMAT) == TiebreakScore(6, 6, isSuper=True, matchFormat=DEFAULT_FORMAT)

    def test_unequal_scores(self):
        assert TiebreakScore(5, 3, isSuper=False, matchFormat=DEFAULT_FORMAT) != TiebreakScore(3, 5, isSuper=False, matchFormat=DEFAULT_FORMAT)
        assert TiebreakScore(5, 3, isSuper=False, matchFormat=DEFAULT_FORMAT) != TiebreakScore(5, 4, isSuper=False, matchFormat=DEFAULT_FORMAT)

    def test_is_super_affects_equality(self):
        assert TiebreakScore(5, 3, isSuper=False, matchFormat=DEFAULT_FORMAT) != TiebreakScore(5, 3, isSuper=True, matchFormat=DEFAULT_FORMAT)

    def test_capPoints_does_not_affect_equality(self):
        # Two scores with same points but different capPoints flags should be equal
        assert TiebreakScore(6, 6, isSuper=False, matchFormat=DEFAULT_FORMAT) == TiebreakScore(6, 6, isSuper=False, matchFormat=CAP_FORMAT)

    def test_hash_consistency(self):
        s1 = TiebreakScore(5, 3, isSuper=False, matchFormat=DEFAULT_FORMAT)
        s2 = TiebreakScore(5, 3, isSuper=False, matchFormat=DEFAULT_FORMAT)
        assert hash(s1) == hash(s2)

        # Can use in sets/dicts
        score_set = {s1, s2}
        assert len(score_set) == 1


class TestReprAndStr:
    """Tests for __repr__ and __str__."""

    def test_repr(self):
        score = TiebreakScore(5, 3, isSuper=False, matchFormat=CAP_FORMAT)
        repr_str = repr(score)
        assert "TiebreakScore" in repr_str
        assert "pointsP1=5" in repr_str
        assert "pointsP2=3" in repr_str
        assert "isSuper=False" in repr_str
        assert "matchFormat=" in repr_str

    def test_repr_eval(self):
        # repr should produce valid Python
        score = TiebreakScore(5, 3, isSuper=True, matchFormat=DEFAULT_FORMAT)
        recreated = eval(repr(score))
        assert recreated.asPoints(1) == (5, 3)

    def test_str(self):
        assert str(TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT)) == "0-0"
        assert str(TiebreakScore(5, 3, isSuper=False, matchFormat=DEFAULT_FORMAT)) == "5-3"
        assert str(TiebreakScore(7, 6, isSuper=False, matchFormat=DEFAULT_FORMAT)) == "7-6"
        assert str(TiebreakScore(10, 8, isSuper=True, matchFormat=DEFAULT_FORMAT)) == "10-8"


class TestCapPoints:
    """Tests for capPoints behavior."""

    def test_capPoints_deuce(self):
        score = TiebreakScore(8, 8, isSuper=False, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (6, 6)

    def test_capPoints_deuce_super(self):
        score = TiebreakScore(11, 11, isSuper=True, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (9, 9)

    def test_capPoints_advantage_p1(self):
        score = TiebreakScore(9, 8, isSuper=False, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (7, 6)

    def test_capPoints_advantage_p2(self):
        score = TiebreakScore(8, 9, isSuper=False, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (6, 7)

    def test_capPoints_advantage_p1_super(self):
        score = TiebreakScore(12, 11, isSuper=True, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (10, 9)

    def test_capPoints_advantage_p2_super(self):
        score = TiebreakScore(11, 12, isSuper=True, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (9, 10)

    def test_capPoints_no_effect_on_regular_scores(self):
        # capPoints shouldn't affect non-deuce scores
        score = TiebreakScore(3, 2, isSuper=False, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (3, 2)

        score = TiebreakScore(7, 5, isSuper=False, matchFormat=CAP_FORMAT)
        assert score.asPoints(1) == (7, 5)


class TestModuleConstants:
    """Tests for module-level constants from match_format."""

    def test_points_to_win_tiebreak(self):
        assert POINTS_TO_WIN_TIEBREAK == 7

    def test_points_to_win_super_tiebreak(self):
        assert POINTS_TO_WIN_SUPERTIEBREAK == 10


class TestTiebreakScenarios:
    """Tests for realistic tiebreak scenarios."""

    def test_standard_tiebreak_p1_wins_7_0(self):
        score = TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT)
        for _ in range(7):
            score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1
        assert score.asPoints(1) == (7, 0)

    def test_standard_tiebreak_p2_wins_7_5(self):
        score = TiebreakScore(0, 0, isSuper=False, matchFormat=DEFAULT_FORMAT)
        # Alternate until 5-5, then P2 wins 2 straight
        for i in range(10):
            score.recordPoint((i % 2) + 1)
        assert score.asPoints(1) == (5, 5)
        score.recordPoint(2)
        score.recordPoint(2)
        assert score.isFinal
        assert score.winner == 2
        assert score.asPoints(1) == (5, 7)

    def test_extended_tiebreak_with_multiple_deuces(self):
        score = TiebreakScore(6, 6, isSuper=False, matchFormat=DEFAULT_FORMAT)

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

    def test_super_tiebreak_p1_wins_10_8(self):
        score = TiebreakScore(0, 0, isSuper=True, matchFormat=DEFAULT_FORMAT)
        # Simulate a 10-8 win for P1
        points = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 1]  # 10-8
        for p in points:
            score.recordPoint(p)
        assert score.isFinal
        assert score.winner == 1
        assert score.asPoints(1) == (10, 8)

    def test_super_tiebreak_extended(self):
        score = TiebreakScore(9, 9, isSuper=True, matchFormat=DEFAULT_FORMAT)

        # P1 advantage
        score.recordPoint(1)
        assert score.playerWithAdvantage == 1
        assert not score.isFinal

        # P1 wins
        score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1
        assert score.asPoints(1) == (11, 9)
