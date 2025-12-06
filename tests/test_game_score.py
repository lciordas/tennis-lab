"""Tests for the GameScore class."""

import pytest
from src.core.game_score import GameScore


class TestGameScoreInit:
    """Tests for GameScore initialization."""

    def test_init_blank_score(self):
        score = GameScore(0, 0)
        assert score.asPoints(1) == (0, 0)
        assert score.isBlank

    def test_init_valid_scores(self):
        # Standard scores
        assert GameScore(0, 0).asPoints(1) == (0, 0)
        assert GameScore(1, 0).asPoints(1) == (1, 0)
        assert GameScore(2, 1).asPoints(1) == (2, 1)
        assert GameScore(3, 3).asPoints(1) == (3, 3)

    def test_init_invalid_negative(self):
        with pytest.raises(ValueError):
            GameScore(-1, 0)
        with pytest.raises(ValueError):
            GameScore(0, -1)

    def test_init_invalid_impossible_score(self):
        # Can't have 5-0 (game would end at 4-0)
        with pytest.raises(ValueError):
            GameScore(5, 0)
        # Can't have 5-1 (game would end at 4-1)
        with pytest.raises(ValueError):
            GameScore(5, 1)
        # Can't have 6-3 (too far apart after deuce)
        with pytest.raises(ValueError):
            GameScore(6, 3)

    def test_init_valid_deuce_scores(self):
        # Valid deuce and advantage scores
        GameScore(3, 3)  # deuce
        GameScore(4, 3)  # ad P1
        GameScore(3, 4)  # ad P2
        GameScore(4, 4)  # deuce again
        GameScore(5, 4)  # ad P1
        GameScore(5, 5)  # deuce again

    def test_init_with_normalize(self):
        # When normalize=True, extended deuce should collapse to 3-3
        score = GameScore(5, 5, normalize=True)
        assert score.asPoints(1) == (3, 3)

        # Extended advantage should collapse to 4-3 or 3-4
        score = GameScore(6, 5, normalize=True)
        assert score.asPoints(1) == (4, 3)

        score = GameScore(5, 6, normalize=True)
        assert score.asPoints(1) == (3, 4)


class TestGameScoreProperties:
    """Tests for GameScore properties."""

    def test_is_blank(self):
        assert GameScore(0, 0).isBlank
        assert not GameScore(1, 0).isBlank
        assert not GameScore(0, 1).isBlank

    def test_is_deuce(self):
        assert not GameScore(0, 0).isDeuce
        assert not GameScore(2, 2).isDeuce  # 30-30 is not deuce
        assert GameScore(3, 3).isDeuce
        assert GameScore(4, 4).isDeuce
        assert GameScore(5, 5).isDeuce

    def test_is_final(self):
        # Not final
        assert not GameScore(0, 0).isFinal
        assert not GameScore(3, 3).isFinal
        assert not GameScore(4, 3).isFinal  # advantage, not win

        # Final - standard rules
        assert GameScore(4, 0).isFinal
        assert GameScore(4, 1).isFinal
        assert GameScore(4, 2).isFinal
        assert GameScore(0, 4).isFinal
        assert GameScore(5, 3).isFinal  # win after deuce
        assert GameScore(3, 5).isFinal

    def test_player_with_advantage(self):
        assert GameScore(0, 0).playerWithAdvantage is None
        assert GameScore(3, 3).playerWithAdvantage is None  # deuce
        assert GameScore(4, 3).playerWithAdvantage == 1
        assert GameScore(3, 4).playerWithAdvantage == 2
        assert GameScore(5, 4).playerWithAdvantage == 1
        assert GameScore(4, 5).playerWithAdvantage == 2

    def test_winner(self):
        assert GameScore(0, 0).winner is None
        assert GameScore(3, 3).winner is None
        assert GameScore(4, 3).winner is None  # advantage, not win
        assert GameScore(4, 0).winner == 1
        assert GameScore(4, 2).winner == 1
        assert GameScore(0, 4).winner == 2
        assert GameScore(5, 3).winner == 1
        assert GameScore(3, 5).winner == 2


class TestGameScoreNoAdRule:
    """Tests for no-ad rule games."""

    def test_no_ad_win_at_4(self):
        # In no-ad, first to 4 wins (at deuce, deciding point)
        score = GameScore(4, 3, noAdRule=True)
        assert score.isFinal
        assert score.winner == 1

        score = GameScore(3, 4, noAdRule=True)
        assert score.isFinal
        assert score.winner == 2

    def test_no_ad_not_final_before_4(self):
        score = GameScore(3, 3, noAdRule=True)
        assert not score.isFinal
        assert score.winner is None

    def test_no_ad_standard_wins(self):
        # Standard wins still work
        score = GameScore(4, 0, noAdRule=True)
        assert score.isFinal
        assert score.winner == 1


class TestRecordPoint:
    """Tests for recordPoint method."""

    def test_record_point_basic(self):
        score = GameScore(0, 0)
        score.recordPoint(1)
        assert score.asPoints(1) == (1, 0)

        score.recordPoint(2)
        assert score.asPoints(1) == (1, 1)

    def test_record_point_invalid(self):
        score = GameScore(0, 0)
        with pytest.raises(ValueError):
            score.recordPoint(0)
        with pytest.raises(ValueError):
            score.recordPoint(3)

    def test_record_point_with_normalize(self):
        score = GameScore(3, 3, normalize=True)
        score.recordPoint(1)  # Should be 4-3 (ad)
        assert score.asPoints(1) == (4, 3)

        score.recordPoint(2)  # Back to deuce, normalized to 3-3
        assert score.asPoints(1) == (3, 3)

    def test_record_point_without_normalize(self):
        score = GameScore(3, 3, normalize=False)
        score.recordPoint(1)
        assert score.asPoints(1) == (4, 3)

        score.recordPoint(2)  # Back to deuce, but NOT normalized
        assert score.asPoints(1) == (4, 4)


class TestAsPoints:
    """Tests for asPoints method."""

    def test_as_points_pov1(self):
        score = GameScore(2, 1)
        assert score.asPoints(1) == (2, 1)

    def test_as_points_pov2(self):
        score = GameScore(2, 1)
        assert score.asPoints(2) == (1, 2)

    def test_as_points_invalid_pov(self):
        score = GameScore(0, 0)
        with pytest.raises(ValueError):
            score.asPoints(0)
        with pytest.raises(ValueError):
            score.asPoints(3)


class TestAsTraditional:
    """Tests for asTraditional method."""

    def test_standard_scores(self):
        assert GameScore(0, 0).asTraditional(1) == "0-0"
        assert GameScore(1, 0).asTraditional(1) == "15-0"
        assert GameScore(2, 0).asTraditional(1) == "30-0"
        assert GameScore(3, 0).asTraditional(1) == "40-0"
        assert GameScore(2, 1).asTraditional(1) == "30-15"
        assert GameScore(3, 2).asTraditional(1) == "40-30"

    def test_deuce(self):
        # 3-3 is 40-40, only 4-4+ is displayed as "deuce"
        assert GameScore(3, 3).asTraditional(1) == "40-40"
        assert GameScore(4, 4).asTraditional(1) == "deuce"

    def test_advantage(self):
        assert GameScore(4, 3).asTraditional(1) == "ad-40"
        assert GameScore(3, 4).asTraditional(1) == "40-ad"

    def test_win(self):
        assert GameScore(4, 0).asTraditional(1) == "win-0"
        assert GameScore(4, 2).asTraditional(1) == "win-30"
        assert GameScore(0, 4).asTraditional(1) == "0-win"
        assert GameScore(5, 3).asTraditional(1) == "win-40"
        assert GameScore(3, 5).asTraditional(1) == "40-win"

    def test_pov2(self):
        assert GameScore(2, 1).asTraditional(2) == "15-30"
        assert GameScore(4, 3).asTraditional(2) == "40-ad"


class TestNextScores:
    """Tests for nextScores method."""

    def test_next_scores_basic(self):
        score = GameScore(1, 1)
        next_p1, next_p2 = score.nextScores()
        assert next_p1.asPoints(1) == (2, 1)
        assert next_p2.asPoints(1) == (1, 2)

    def test_next_scores_final(self):
        score = GameScore(4, 0)
        assert score.nextScores() is None

    def test_next_scores_propagates_normalize(self):
        score = GameScore(3, 3, normalize=True)
        next_p1, next_p2 = score.nextScores()

        # Both should have normalize=True
        # P1 wins point: 4-3 (ad), stays as 4-3
        assert next_p1.asPoints(1) == (4, 3)

        # Simulate another deuce from next_p1
        next_p1.recordPoint(2)  # Should normalize back to 3-3
        assert next_p1.asPoints(1) == (3, 3)

    def test_next_scores_propagates_no_ad_rule(self):
        score = GameScore(3, 3, noAdRule=True)
        next_p1, next_p2 = score.nextScores()

        # In no-ad, 4-3 is a win
        assert next_p1.isFinal
        assert next_p1.winner == 1
        assert next_p2.isFinal
        assert next_p2.winner == 2


class TestEquality:
    """Tests for __eq__ and __hash__."""

    def test_equal_scores(self):
        assert GameScore(2, 1) == GameScore(2, 1)
        assert GameScore(3, 3) == GameScore(3, 3)

    def test_unequal_scores(self):
        assert GameScore(2, 1) != GameScore(1, 2)
        assert GameScore(2, 1) != GameScore(2, 2)

    def test_no_ad_rule_affects_equality(self):
        assert GameScore(3, 3, noAdRule=False) != GameScore(3, 3, noAdRule=True)

    def test_normalize_does_not_affect_equality(self):
        # Two scores with same points but different normalize flags should be equal
        assert GameScore(3, 3, normalize=False) == GameScore(3, 3, normalize=True)

    def test_hash_consistency(self):
        s1 = GameScore(2, 1)
        s2 = GameScore(2, 1)
        assert hash(s1) == hash(s2)

        # Can use in sets/dicts
        score_set = {s1, s2}
        assert len(score_set) == 1


class TestReprAndStr:
    """Tests for __repr__ and __str__."""

    def test_repr(self):
        score = GameScore(2, 1, noAdRule=False, normalize=True)
        repr_str = repr(score)
        assert "GameScore" in repr_str
        assert "pointsP1=2" in repr_str
        assert "pointsP2=1" in repr_str
        assert "noAdRule=False" in repr_str
        assert "normalize=True" in repr_str

    def test_repr_eval(self):
        # repr should produce valid Python
        score = GameScore(3, 2, noAdRule=True, normalize=False)
        recreated = eval(repr(score))
        assert recreated.asPoints(1) == (3, 2)

    def test_str(self):
        assert str(GameScore(0, 0)) == "0-0"
        assert str(GameScore(2, 1)) == "30-15"
        assert str(GameScore(3, 3)) == "40-40"
        assert str(GameScore(4, 4)) == "deuce"
        assert str(GameScore(4, 3)) == "ad-40"


class TestNormalize:
    """Tests for normalization behavior."""

    def test_normalize_deuce(self):
        score = GameScore(5, 5, normalize=True)
        assert score.asPoints(1) == (3, 3)

    def test_normalize_advantage_p1(self):
        score = GameScore(6, 5, normalize=True)
        assert score.asPoints(1) == (4, 3)

    def test_normalize_advantage_p2(self):
        score = GameScore(5, 6, normalize=True)
        assert score.asPoints(1) == (3, 4)

    def test_normalize_no_effect_on_regular_scores(self):
        # Normalization shouldn't affect non-deuce scores
        score = GameScore(2, 1, normalize=True)
        assert score.asPoints(1) == (2, 1)

        score = GameScore(4, 0, normalize=True)
        assert score.asPoints(1) == (4, 0)
