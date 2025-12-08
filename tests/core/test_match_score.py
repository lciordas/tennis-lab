"""Tests for MatchScore class."""

import pytest
from src.core.match_score import MatchScore
from src.core.set_score import SetScore
from src.core.game_score import GameScore
from src.core.tiebreak_score import TiebreakScore
from src.core.match_format import MatchFormat, SetEnding


# Common match formats for testing
BEST_OF_3 = MatchFormat(bestOfSets=3)
BEST_OF_5 = MatchFormat(bestOfSets=5)
BEST_OF_3_FINAL_TB = MatchFormat(bestOfSets=3, setEnding=SetEnding.TIEBREAK, finalSetEnding=SetEnding.SUPERTIEBREAK)
BEST_OF_3_FINAL_ADV = MatchFormat(bestOfSets=3, setEnding=SetEnding.TIEBREAK, finalSetEnding=SetEnding.ADVANTAGE)


def win_game(score: MatchScore, player: int):
    """Helper to have a player win a game (4 points)."""
    for _ in range(4):
        score.recordPoint(player)


def win_set(score: MatchScore, player: int):
    """Helper to have a player win a set 6-0."""
    for _ in range(6):
        win_game(score, player)


def win_tiebreak(score: MatchScore, player: int):
    """Helper to have a player win a tiebreak 7-0."""
    for _ in range(7):
        score.recordPoint(player)


class TestMatchScoreInit:
    """Tests for MatchScore initialization."""

    def test_init_blank_score(self):
        score = MatchScore(0, 0, BEST_OF_3)
        assert score.setsPlayer1 == 0
        assert score.setsPlayer2 == 0
        assert score.isBlank
        assert score.currSetScore is not None

    def test_init_with_sets(self):
        score = MatchScore(1, 0, BEST_OF_3)
        assert score.setsPlayer1 == 1
        assert score.setsPlayer2 == 0
        assert not score.isBlank
        assert score.currSetScore is not None
        assert score.currSetScore.isBlank

    def test_init_with_set_score(self):
        set_score = SetScore(3, 2, False, BEST_OF_3)
        score = MatchScore(1, 0, BEST_OF_3, setScore=set_score)
        assert score.setsPlayer1 == 1
        assert score.setsPlayer2 == 0
        assert score.currSetScore.gamesPlayer1 == 3
        assert score.currSetScore.gamesPlayer2 == 2

    def test_init_final_match(self):
        score = MatchScore(2, 0, BEST_OF_3)
        assert score.isFinal
        assert score.winner == 1
        assert score.currSetScore is None

    def test_init_invalid_sets_negative(self):
        with pytest.raises(ValueError):
            MatchScore(-1, 0, BEST_OF_3)

    def test_init_invalid_sets_too_many(self):
        with pytest.raises(ValueError):
            MatchScore(3, 0, BEST_OF_3)  # Can't win 3 sets in best of 3

    def test_init_invalid_sets_not_int(self):
        with pytest.raises(ValueError):
            MatchScore(1.5, 0, BEST_OF_3)

    def test_init_invalid_match_format(self):
        with pytest.raises(ValueError):
            MatchScore(0, 0, "not a match format")

    def test_init_invalid_set_score_type(self):
        with pytest.raises(ValueError):
            MatchScore(0, 0, BEST_OF_3, setScore="not a set score")

    def test_init_invalid_set_score_final(self):
        final_set = SetScore(6, 0, False, BEST_OF_3)
        with pytest.raises(ValueError):
            MatchScore(0, 0, BEST_OF_3, setScore=final_set)

    def test_init_invalid_set_score_mismatched_format(self):
        set_score = SetScore(3, 2, False, BEST_OF_5)
        with pytest.raises(ValueError):
            MatchScore(0, 0, BEST_OF_3, setScore=set_score)

    def test_init_invalid_set_score_when_match_final(self):
        set_score = SetScore(3, 2, False, BEST_OF_3)
        with pytest.raises(ValueError):
            MatchScore(2, 0, BEST_OF_3, setScore=set_score)

    def test_init_deep_copies_set_score(self):
        set_score = SetScore(3, 2, False, BEST_OF_3)
        score = MatchScore(0, 0, BEST_OF_3, setScore=set_score)
        # Mutate original
        set_score.recordPoint(1)
        # MatchScore should be unaffected
        assert score.currSetScore.currGameScore.isBlank


class TestMatchScoreProperties:
    """Tests for MatchScore properties."""

    def test_sets_player1(self):
        score = MatchScore(1, 0, BEST_OF_3)
        assert score.setsPlayer1 == 1

    def test_sets_player2(self):
        score = MatchScore(0, 1, BEST_OF_3)
        assert score.setsPlayer2 == 1

    def test_is_blank_true(self):
        score = MatchScore(0, 0, BEST_OF_3)
        assert score.isBlank

    def test_is_blank_false_after_point(self):
        score = MatchScore(0, 0, BEST_OF_3)
        score.recordPoint(1)
        assert not score.isBlank

    def test_is_blank_false_with_sets(self):
        score = MatchScore(1, 0, BEST_OF_3)
        assert not score.isBlank

    def test_is_final_false(self):
        score = MatchScore(1, 1, BEST_OF_3)
        assert not score.isFinal

    def test_is_final_true_p1_wins(self):
        score = MatchScore(2, 0, BEST_OF_3)
        assert score.isFinal

    def test_is_final_true_p2_wins(self):
        score = MatchScore(0, 2, BEST_OF_3)
        assert score.isFinal

    def test_winner_none(self):
        score = MatchScore(1, 1, BEST_OF_3)
        assert score.winner is None

    def test_winner_p1(self):
        score = MatchScore(2, 0, BEST_OF_3)
        assert score.winner == 1

    def test_winner_p2(self):
        score = MatchScore(1, 2, BEST_OF_3)
        assert score.winner == 2

    def test_set_in_progress_false_at_start(self):
        score = MatchScore(0, 0, BEST_OF_3)
        assert not score.setInProgress

    def test_set_in_progress_true_after_point(self):
        score = MatchScore(0, 0, BEST_OF_3)
        score.recordPoint(1)
        assert score.setInProgress

    def test_set_in_progress_false_when_final(self):
        score = MatchScore(2, 0, BEST_OF_3)
        assert not score.setInProgress


class TestSetsMethod:
    """Tests for sets() method."""

    def test_sets_pov_1(self):
        score = MatchScore(1, 2, BEST_OF_5)
        assert score.sets(pov=1) == (1, 2)

    def test_sets_pov_2(self):
        score = MatchScore(1, 2, BEST_OF_5)
        assert score.sets(pov=2) == (2, 1)

    def test_sets_invalid_pov(self):
        score = MatchScore(1, 1, BEST_OF_3)
        with pytest.raises(ValueError):
            score.sets(pov=3)


class TestRecordPoint:
    """Tests for recordPoint method."""

    def test_record_point_invalid_winner(self):
        score = MatchScore(0, 0, BEST_OF_3)
        with pytest.raises(ValueError):
            score.recordPoint(3)

    def test_record_point_match_already_over(self):
        score = MatchScore(2, 0, BEST_OF_3)
        with pytest.raises(ValueError):
            score.recordPoint(1)

    def test_record_point_updates_set_score(self):
        score = MatchScore(0, 0, BEST_OF_3)
        score.recordPoint(1)
        assert score.currSetScore.currGameScore.asPoints(1) == (1, 0)

    def test_record_point_completes_game(self):
        score = MatchScore(0, 0, BEST_OF_3)
        win_game(score, 1)
        assert score.currSetScore.gamesPlayer1 == 1
        assert score.currSetScore.gamesPlayer2 == 0

    def test_record_point_completes_set(self):
        score = MatchScore(0, 0, BEST_OF_3)
        win_set(score, 1)
        assert score.setsPlayer1 == 1
        assert score.setsPlayer2 == 0
        assert score.currSetScore.isBlank

    def test_record_point_completes_match(self):
        score = MatchScore(1, 0, BEST_OF_3)
        win_set(score, 1)
        assert score.isFinal
        assert score.winner == 1
        assert score.currSetScore is None


class TestNextSetScores:
    """Tests for nextSetScores method."""

    def test_next_set_scores_basic(self):
        score = MatchScore(1, 0, BEST_OF_3)
        next_p1, next_p2 = score.nextSetScores()
        assert next_p1.setsPlayer1 == 2
        assert next_p1.setsPlayer2 == 0
        assert next_p2.setsPlayer1 == 1
        assert next_p2.setsPlayer2 == 1

    def test_next_set_scores_returns_none_when_final(self):
        score = MatchScore(2, 0, BEST_OF_3)
        assert score.nextSetScores() is None

    def test_next_set_scores_raises_when_set_in_progress(self):
        score = MatchScore(1, 0, BEST_OF_3)
        score.recordPoint(1)
        with pytest.raises(ValueError):
            score.nextSetScores()


class TestEquality:
    """Tests for __eq__ and __hash__."""

    def test_equal_scores(self):
        assert MatchScore(1, 0, BEST_OF_3) == MatchScore(1, 0, BEST_OF_3)

    def test_not_equal_different_sets(self):
        assert MatchScore(1, 0, BEST_OF_3) != MatchScore(0, 1, BEST_OF_3)

    def test_not_equal_different_format(self):
        assert MatchScore(1, 0, BEST_OF_3) != MatchScore(1, 0, BEST_OF_5)

    def test_not_equal_different_set_score(self):
        score1 = MatchScore(0, 0, BEST_OF_3)
        score2 = MatchScore(0, 0, BEST_OF_3)
        score1.recordPoint(1)
        assert score1 != score2

    def test_hash_equal_scores(self):
        assert hash(MatchScore(1, 0, BEST_OF_3)) == hash(MatchScore(1, 0, BEST_OF_3))

    def test_hash_different_scores(self):
        # Different scores should (usually) have different hashes
        assert hash(MatchScore(1, 0, BEST_OF_3)) != hash(MatchScore(0, 1, BEST_OF_3))

    def test_usable_in_set(self):
        s = {MatchScore(1, 0, BEST_OF_3), MatchScore(0, 1, BEST_OF_3)}
        assert len(s) == 2
        assert MatchScore(1, 0, BEST_OF_3) in s


class TestReprAndStr:
    """Tests for __repr__ and __str__."""

    def test_repr_contains_key_info(self):
        score = MatchScore(1, 0, BEST_OF_3)
        repr_str = repr(score)
        assert "MatchScore" in repr_str
        assert "setsP1=1" in repr_str
        assert "setsP2=0" in repr_str
        assert "matchFormat=" in repr_str

    def test_repr_eval(self):
        score = MatchScore(1, 0, BEST_OF_3)
        recreated = eval(repr(score))
        assert recreated.setsPlayer1 == 1
        assert recreated.setsPlayer2 == 0

    def test_str_basic(self):
        assert str(MatchScore(1, 0, BEST_OF_3)) == "1-0, 0-0, 0-0"

    def test_str_final(self):
        assert str(MatchScore(2, 0, BEST_OF_3)) == "2-0"

    def test_str_with_set_progress(self):
        score = MatchScore(1, 0, BEST_OF_3)
        win_game(score, 1)
        s = str(score)
        assert s.startswith("1-0")
        assert "1-0" in s  # set score


class TestPlayFullMatch:
    """Tests that play through complete matches."""

    def test_p1_wins_best_of_3_straight_sets(self):
        score = MatchScore(0, 0, BEST_OF_3)
        # P1 wins first set 6-0
        win_set(score, 1)
        assert score.setsPlayer1 == 1
        assert not score.isFinal
        # P1 wins second set 6-0
        win_set(score, 1)
        assert score.setsPlayer1 == 2
        assert score.isFinal
        assert score.winner == 1

    def test_p2_wins_best_of_3_in_three_sets(self):
        score = MatchScore(0, 0, BEST_OF_3)
        # P1 wins first set
        win_set(score, 1)
        assert score.sets(1) == (1, 0)
        # P2 wins second set
        win_set(score, 2)
        assert score.sets(1) == (1, 1)
        # P2 wins third set
        win_set(score, 2)
        assert score.isFinal
        assert score.winner == 2

    def test_best_of_5_match(self):
        score = MatchScore(0, 0, BEST_OF_5)
        # P1 wins two sets
        win_set(score, 1)
        win_set(score, 1)
        assert score.sets(1) == (2, 0)
        assert not score.isFinal
        # P2 wins two sets
        win_set(score, 2)
        win_set(score, 2)
        assert score.sets(1) == (2, 2)
        assert not score.isFinal
        # P1 wins fifth set
        win_set(score, 1)
        assert score.isFinal
        assert score.winner == 1

    def test_match_with_tiebreak_set(self):
        score = MatchScore(0, 0, BEST_OF_3)
        # Play to 6-6 in first set
        for _ in range(6):
            win_game(score, 1)
            win_game(score, 2)
        assert score.currSetScore.gamesPlayer1 == 6
        assert score.currSetScore.gamesPlayer2 == 6
        assert score.currSetScore.tiebreakScore is not None
        # P1 wins tiebreak
        win_tiebreak(score, 1)
        assert score.setsPlayer1 == 1
        assert not score.isFinal

    def test_final_set_with_advantage(self):
        score = MatchScore(1, 1, BEST_OF_3_FINAL_ADV)
        # Play to 6-6 in final set
        for _ in range(6):
            win_game(score, 1)
            win_game(score, 2)
        assert score.currSetScore.gamesPlayer1 == 6
        assert score.currSetScore.gamesPlayer2 == 6
        # No tiebreak - continue with advantage
        assert score.currSetScore.tiebreakScore is None
        # Play to 7-7
        win_game(score, 1)
        win_game(score, 2)
        assert score.currSetScore.gamesPlayer1 == 7
        assert score.currSetScore.gamesPlayer2 == 7
        assert not score.isFinal
        # P1 wins two games to win 9-7
        win_game(score, 1)
        win_game(score, 1)
        assert score.isFinal
        assert score.winner == 1

    def test_final_set_with_supertiebreak(self):
        score = MatchScore(1, 1, BEST_OF_3_FINAL_TB)
        # Play to 6-6 in final set
        for _ in range(6):
            win_game(score, 1)
            win_game(score, 2)
        assert score.currSetScore.tiebreakScore is not None
        # Super tiebreak: first to 10
        for _ in range(10):
            score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1


class TestFinalSetDetection:
    """Tests for _isFinalSet detection."""

    def test_not_final_set_at_start(self):
        score = MatchScore(0, 0, BEST_OF_3)
        # First set is not a final set
        assert not score._isFinalSet()

    def test_final_set_when_1_1(self):
        score = MatchScore(1, 1, BEST_OF_3)
        assert score._isFinalSet()

    def test_final_set_when_p1_needs_one(self):
        score = MatchScore(1, 0, BEST_OF_3)
        assert score._isFinalSet()

    def test_final_set_when_p2_needs_one(self):
        score = MatchScore(0, 1, BEST_OF_3)
        assert score._isFinalSet()

    def test_best_of_5_final_set(self):
        score = MatchScore(2, 2, BEST_OF_5)
        assert score._isFinalSet()

    def test_best_of_5_not_final_set(self):
        score = MatchScore(1, 1, BEST_OF_5)
        assert not score._isFinalSet()
