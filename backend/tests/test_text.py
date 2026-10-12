import pytest

from app.core.text import keywords, normalize_topic, stem


def test_same_topic_different_wording_gets_same_key():
    a = normalize_topic("Should AI tutors replace homework help?")
    b = normalize_topic("  ai TUTORS replace   homework help ")
    assert a.key == b.key == "ai tutors replace homework help"


def test_title_is_tidied_but_keeps_wording():
    assert normalize_topic("  should   we ban cars? ").title == "Should we ban cars?"


def test_punctuation_and_apostrophes_are_ignored():
    assert normalize_topic("Is it worth it? (Space exploration!)").key == "worth space exploration"
    assert normalize_topic("Children's screen time").key == "childrens screen time"


def test_filler_only_text_is_rejected():
    with pytest.raises(ValueError):
        normalize_topic("Should we? Is it?")


def test_stem_matches_related_forms():
    assert stem("tutors") == stem("tutor")
    assert stem("policies") == stem("policy")
    assert stem("gaming") == stem("game") == stem("games")
    assert stem("banning") == stem("ban")
    assert stem("tutoring") == stem("tutor")
    assert stem("glass") == "glass"
    assert stem("bus") == "bus"


def test_keywords_drop_stopwords_but_keep_acronyms():
    assert keywords("The impact of remote work on the office") == {
        stem(w) for w in ("impact", "remote", "work", "office")
    }
    assert stem("ai") in keywords("Should AI tutors help?")


def test_judgement_words_are_filler():
    assert normalize_topic("Is video gaming good for kids?").key == "video gaming kids"
