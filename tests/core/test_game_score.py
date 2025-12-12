"""Tests for the GameScore class."""

import pytest
from tennis_lab.core.game_score   import GameScore
from tennis_lab.core.match_format import MatchFormat, SetEnding

# Default match format for most tests (capPoints=True is the default)
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)
NO_AD_FORMAT   = MatchFormat(bestOfSets=3, noAdRule=True)
CAP_FORMAT     = MatchFormat(bestOfSets=3, capPoints=True)
NO_CAP_FORMAT  = MatchFormat(bestOfSets=3, capPoints=False)


class TestGameScoreInit:
    """Tests for GameScore initialization."""

    def test_init_blank_score(self):
        score = GameScore(0, 0, DEFAULT_FORMAT)
        assert score.asPoints(1) == (0, 0)
        assert score.isBlank

    def test_init_valid_scores(self):
        # Standard scores
        assert GameScore(0, 0, DEFAULT_FORMAT).asPoints(1) == (0, 0)
        assert GameScore(1, 0, DEFAULT_FORMAT).asPoints(1) == (1, 0)
        assert GameScore(2, 1, DEFAULT_FORMAT).asPoints(1) == (2, 1)
        assert GameScore(3, 3, DEFAULT_FORMAT).asPoints(1) == (3, 3)

    def test_init_invalid_negative(self):
        with pytest.raises(ValueError):
            GameScore(-1, 0, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            GameScore(0, -1, DEFAULT_FORMAT)

    def test_init_invalid_impossible_score(self):
        # Can't have 5-0 (game would end at 4-0)
        with pytest.raises(ValueError):
            GameScore(5, 0, DEFAULT_FORMAT)
        # Can't have 5-1 (game would end at 4-1)
        with pytest.raises(ValueError):
            GameScore(5, 1, DEFAULT_FORMAT)
        # Can't have 6-3 (too far apart after deuce)
        with pytest.raises(ValueError):
            GameScore(6, 3, DEFAULT_FORMAT)

    def test_init_valid_deuce_scores(self):
        # Valid deuce and advantage scores
        GameScore(3, 3, DEFAULT_FORMAT)  # deuce
        GameScore(4, 3, DEFAULT_FORMAT)  # ad P1
        GameScore(3, 4, DEFAULT_FORMAT)  # ad P2
        GameScore(4, 4, DEFAULT_FORMAT)  # deuce again
        GameScore(5, 4, DEFAULT_FORMAT)  # ad P1
        GameScore(5, 5, DEFAULT_FORMAT)  # deuce again

    def test_init_with_capPoints(self):
        # When capPoints=True, extended deuce should collapse to 3-3
        score = GameScore(5, 5, CAP_FORMAT)
        assert score.asPoints(1) == (3, 3)

        # Extended advantage should collapse to 4-3 or 3-4
        score = GameScore(6, 5, CAP_FORMAT)
        assert score.asPoints(1) == (4, 3)

        score = GameScore(5, 6, CAP_FORMAT)
        assert score.asPoints(1) == (3, 4)


class TestGameScoreProperties:
    """Tests for GameScore properties."""

    def test_is_blank(self):
        assert GameScore(0, 0, DEFAULT_FORMAT).isBlank
        assert not GameScore(1, 0, DEFAULT_FORMAT).isBlank
        assert not GameScore(0, 1, DEFAULT_FORMAT).isBlank

    def test_is_deuce(self):
        assert not GameScore(0, 0, DEFAULT_FORMAT).isDeuce
        assert not GameScore(2, 2, DEFAULT_FORMAT).isDeuce  # 30-30 is not deuce
        assert GameScore(3, 3, DEFAULT_FORMAT).isDeuce
        assert GameScore(4, 4, DEFAULT_FORMAT).isDeuce
        assert GameScore(5, 5, DEFAULT_FORMAT).isDeuce

    def test_is_final(self):
        # Not final
        assert not GameScore(0, 0, DEFAULT_FORMAT).isFinal
        assert not GameScore(3, 3, DEFAULT_FORMAT).isFinal
        assert not GameScore(4, 3, DEFAULT_FORMAT).isFinal  # advantage, not win

        # Final - standard rules
        assert GameScore(4, 0, DEFAULT_FORMAT).isFinal
        assert GameScore(4, 1, DEFAULT_FORMAT).isFinal
        assert GameScore(4, 2, DEFAULT_FORMAT).isFinal
        assert GameScore(0, 4, DEFAULT_FORMAT).isFinal
        assert GameScore(5, 3, DEFAULT_FORMAT).isFinal  # win after deuce
        assert GameScore(3, 5, DEFAULT_FORMAT).isFinal

    def test_player_with_advantage(self):
        assert GameScore(0, 0, DEFAULT_FORMAT).playerWithAdvantage is None
        assert GameScore(3, 3, DEFAULT_FORMAT).playerWithAdvantage is None  # deuce
        assert GameScore(4, 3, DEFAULT_FORMAT).playerWithAdvantage == 1
        assert GameScore(3, 4, DEFAULT_FORMAT).playerWithAdvantage == 2
        assert GameScore(5, 4, DEFAULT_FORMAT).playerWithAdvantage == 1
        assert GameScore(4, 5, DEFAULT_FORMAT).playerWithAdvantage == 2

    def test_winner(self):
        assert GameScore(0, 0, DEFAULT_FORMAT).winner is None
        assert GameScore(3, 3, DEFAULT_FORMAT).winner is None
        assert GameScore(4, 3, DEFAULT_FORMAT).winner is None  # advantage, not win
        assert GameScore(4, 0, DEFAULT_FORMAT).winner == 1
        assert GameScore(4, 2, DEFAULT_FORMAT).winner == 1
        assert GameScore(0, 4, DEFAULT_FORMAT).winner == 2
        assert GameScore(5, 3, DEFAULT_FORMAT).winner == 1
        assert GameScore(3, 5, DEFAULT_FORMAT).winner == 2


class TestGameScoreNoAdRule:
    """Tests for no-ad rule games."""

    def test_no_ad_win_at_4(self):
        # In no-ad, first to 4 wins (at deuce, deciding point)
        score = GameScore(4, 3, NO_AD_FORMAT)
        assert score.isFinal
        assert score.winner == 1

        score = GameScore(3, 4, NO_AD_FORMAT)
        assert score.isFinal
        assert score.winner == 2

    def test_no_ad_not_final_before_4(self):
        score = GameScore(3, 3, NO_AD_FORMAT)
        assert not score.isFinal
        assert score.winner is None

    def test_no_ad_standard_wins(self):
        # Standard wins still work
        score = GameScore(4, 0, NO_AD_FORMAT)
        assert score.isFinal
        assert score.winner == 1


class TestRecordPoint:
    """Tests for recordPoint method."""

    def test_record_point_basic(self):
        score = GameScore(0, 0, DEFAULT_FORMAT)
        score.recordPoint(1)
        assert score.asPoints(1) == (1, 0)

        score.recordPoint(2)
        assert score.asPoints(1) == (1, 1)

    def test_record_point_invalid(self):
        score = GameScore(0, 0, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            score.recordPoint(0)
        with pytest.raises(ValueError):
            score.recordPoint(3)

    def test_record_point_with_capPoints(self):
        score = GameScore(3, 3, CAP_FORMAT)
        score.recordPoint(1)  # Should be 4-3 (ad)
        assert score.asPoints(1) == (4, 3)

        score.recordPoint(2)  # Back to deuce, capped to 3-3
        assert score.asPoints(1) == (3, 3)

    def test_record_point_without_capPoints(self):
        score = GameScore(3, 3, NO_CAP_FORMAT)
        score.recordPoint(1)
        assert score.asPoints(1) == (4, 3)

        score.recordPoint(2)  # Back to deuce, but NOT capped
        assert score.asPoints(1) == (4, 4)


class TestAsPoints:
    """Tests for asPoints method."""

    def test_as_points_pov1(self):
        score = GameScore(2, 1, DEFAULT_FORMAT)
        assert score.asPoints(1) == (2, 1)

    def test_as_points_pov2(self):
        score = GameScore(2, 1, DEFAULT_FORMAT)
        assert score.asPoints(2) == (1, 2)

    def test_as_points_invalid_pov(self):
        score = GameScore(0, 0, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            score.asPoints(0)
        with pytest.raises(ValueError):
            score.asPoints(3)


class TestAsTraditional:
    """Tests for asTraditional method."""

    def test_standard_scores(self):
        assert GameScore(0, 0, DEFAULT_FORMAT).asTraditional(1) == "0-0"
        assert GameScore(1, 0, DEFAULT_FORMAT).asTraditional(1) == "15-0"
        assert GameScore(2, 0, DEFAULT_FORMAT).asTraditional(1) == "30-0"
        assert GameScore(3, 0, DEFAULT_FORMAT).asTraditional(1) == "40-0"
        assert GameScore(2, 1, DEFAULT_FORMAT).asTraditional(1) == "30-15"
        assert GameScore(3, 2, DEFAULT_FORMAT).asTraditional(1) == "40-30"

    def test_deuce(self):
        # 3-3 is 40-40, only 4-4+ is displayed as "deuce" (requires capPoints=False)
        assert GameScore(3, 3, DEFAULT_FORMAT).asTraditional(1) == "40-40"
        assert GameScore(4, 4, NO_CAP_FORMAT).asTraditional(1) == "deuce"

    def test_advantage(self):
        assert GameScore(4, 3, DEFAULT_FORMAT).asTraditional(1) == "ad-40"
        assert GameScore(3, 4, DEFAULT_FORMAT).asTraditional(1) == "40-ad"

    def test_win(self):
        assert GameScore(4, 0, DEFAULT_FORMAT).asTraditional(1) == "win-0"
        assert GameScore(4, 2, DEFAULT_FORMAT).asTraditional(1) == "win-30"
        assert GameScore(0, 4, DEFAULT_FORMAT).asTraditional(1) == "0-win"
        assert GameScore(5, 3, DEFAULT_FORMAT).asTraditional(1) == "win-40"
        assert GameScore(3, 5, DEFAULT_FORMAT).asTraditional(1) == "40-win"

    def test_pov2(self):
        assert GameScore(2, 1, DEFAULT_FORMAT).asTraditional(2) == "15-30"
        assert GameScore(4, 3, DEFAULT_FORMAT).asTraditional(2) == "40-ad"


class TestNextScores:
    """Tests for nextScores method."""

    def test_next_scores_basic(self):
        score = GameScore(1, 1, DEFAULT_FORMAT)
        next_p1, next_p2 = score.nextScores()
        assert next_p1.asPoints(1) == (2, 1)
        assert next_p2.asPoints(1) == (1, 2)

    def test_next_scores_final(self):
        score = GameScore(4, 0, DEFAULT_FORMAT)
        assert score.nextScores() is None

    def test_next_scores_propagates_capPoints(self):
        score = GameScore(3, 3, CAP_FORMAT)
        next_p1, next_p2 = score.nextScores()

        # Both should have capPoints=True
        # P1 wins point: 4-3 (ad), stays as 4-3
        assert next_p1.asPoints(1) == (4, 3)

        # Simulate another deuce from next_p1
        next_p1.recordPoint(2)  # Should cap back to 3-3
        assert next_p1.asPoints(1) == (3, 3)

    def test_next_scores_propagates_no_ad_rule(self):
        score = GameScore(3, 3, NO_AD_FORMAT)
        next_p1, next_p2 = score.nextScores()

        # In no-ad, 4-3 is a win
        assert next_p1.isFinal
        assert next_p1.winner == 1
        assert next_p2.isFinal
        assert next_p2.winner == 2


class TestEquality:
    """Tests for __eq__ and __hash__."""

    def test_equal_scores(self):
        assert GameScore(2, 1, DEFAULT_FORMAT) == GameScore(2, 1, DEFAULT_FORMAT)
        assert GameScore(3, 3, DEFAULT_FORMAT) == GameScore(3, 3, DEFAULT_FORMAT)

    def test_unequal_scores(self):
        assert GameScore(2, 1, DEFAULT_FORMAT) != GameScore(1, 2, DEFAULT_FORMAT)
        assert GameScore(2, 1, DEFAULT_FORMAT) != GameScore(2, 2, DEFAULT_FORMAT)

    def test_no_ad_rule_affects_equality(self):
        assert GameScore(3, 3, DEFAULT_FORMAT) != GameScore(3, 3, NO_AD_FORMAT)

    def test_capPoints_does_not_affect_equality(self):
        # Two scores with same points but different capPoints flags should be equal
        assert GameScore(3, 3, DEFAULT_FORMAT) == GameScore(3, 3, CAP_FORMAT)

    def test_hash_consistency(self):
        s1 = GameScore(2, 1, DEFAULT_FORMAT)
        s2 = GameScore(2, 1, DEFAULT_FORMAT)
        assert hash(s1) == hash(s2)

        # Can use in sets/dicts
        score_set = {s1, s2}
        assert len(score_set) == 1


class TestReprAndStr:
    """Tests for __repr__ and __str__."""

    def test_repr(self):
        score = GameScore(2, 1, CAP_FORMAT)
        repr_str = repr(score)
        assert "GameScore" in repr_str
        assert "pointsP1=2" in repr_str
        assert "pointsP2=1" in repr_str
        assert "matchFormat=" in repr_str

    def test_repr_eval(self):
        # repr should produce valid Python
        score = GameScore(3, 2, NO_AD_FORMAT)
        recreated = eval(repr(score))
        assert recreated.asPoints(1) == (3, 2)

    def test_str(self):
        assert str(GameScore(0, 0, DEFAULT_FORMAT)) == "0-0"
        assert str(GameScore(2, 1, DEFAULT_FORMAT)) == "30-15"
        assert str(GameScore(3, 3, DEFAULT_FORMAT)) == "40-40"
        assert str(GameScore(4, 4, NO_CAP_FORMAT)) == "deuce"
        assert str(GameScore(4, 3, DEFAULT_FORMAT)) == "ad-40"


class TestCapPoints:
    """Tests for capPoints behavior."""

    def test_capPoints_deuce(self):
        score = GameScore(5, 5, CAP_FORMAT)
        assert score.asPoints(1) == (3, 3)

    def test_capPoints_advantage_p1(self):
        score = GameScore(6, 5, CAP_FORMAT)
        assert score.asPoints(1) == (4, 3)

    def test_capPoints_advantage_p2(self):
        score = GameScore(5, 6, CAP_FORMAT)
        assert score.asPoints(1) == (3, 4)

    def test_capPoints_no_effect_on_regular_scores(self):
        # capPoints shouldn't affect non-deuce scores
        score = GameScore(2, 1, CAP_FORMAT)
        assert score.asPoints(1) == (2, 1)

        score = GameScore(4, 0, CAP_FORMAT)
        assert score.asPoints(1) == (4, 0)
