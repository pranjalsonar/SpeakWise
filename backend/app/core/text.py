"""Text helpers shared by topics and reading material. Pure functions, no I/O."""
import re
from dataclasses import dataclass

# Words that don't change what a topic is about: "Should AI tutors replace homework?"
# and "AI tutors replace homework" are the same topic.
FILLER_WORDS = frozenset(
    """
    a an the and or but nor of to in on at for from by with about into over under as
    is are was were be been being am do does did doing have has had can could will would
    shall should may might must ought let lets let's
    i me my we us our you your he she it its they them their this that these those
    what which who whom whose why how when where whether
    vs versus really very just also than then so such
    good bad better best worse worst right wrong ever still actually truly
    exist exists allowed okay fine
    """.split()
)

# Extra words ignored when scoring relevance (on top of FILLER_WORDS).
_STOPWORDS = FILLER_WORDS | frozenset(
    """
    not no yes all any each every some more most many much other another same own
    one two first new also there here out up down off again further once only both
    few nor too s t like make made use used using said says say get got if go oh ok
    """.split()
)

_TOKEN = re.compile(r"[a-z0-9]+")
_SPACES = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalizedTopic:
    title: str           # tidy display title: "Should AI tutors replace homework help?"
    key: str             # dedupe key: "ai tutors replace homework help"
    search_query: str    # what we send to Wikipedia search


def tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower().replace("'", ""))


def normalize_topic(raw: str) -> NormalizedTopic:
    """Raises ValueError if the text has no meaningful words."""
    title = _SPACES.sub(" ", raw).strip()
    if title:
        title = title[0].upper() + title[1:]

    meaningful = [t for t in tokens(title) if t not in FILLER_WORDS]
    if not meaningful:
        raise ValueError("Topic has no meaningful words")

    key = " ".join(meaningful)[:255]
    return NormalizedTopic(title=title, key=key, search_query=" ".join(meaningful))


def stem(word: str) -> str:
    """Very light stemming so related forms match: tutors/tutor, policies/policy,
    gaming/game/games, banning/ban. Only used to compare words, never shown."""
    if len(word) > 4 and word.endswith("ies"):
        word = word[:-3] + "y"
    elif len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        word = word[:-1]
    if len(word) > 5 and word.endswith("ing"):
        word = word[:-3]
        if len(word) >= 3 and word[-1] == word[-2] and word[-1] not in "aeiouls":
            word = word[:-1]  # banning -> bann -> ban
    if len(word) > 3 and word.endswith("e"):
        word = word[:-1]
    return word


def keywords(text: str) -> set[str]:
    """Stemmed content words (2+ characters so acronyms like "AI" count; no stopwords)."""
    return set(keyword_list(text))


def keyword_list(text: str) -> list[str]:
    """Like keywords() but keeps duplicates/order (for frequency counts)."""
    return [stem(t) for t in tokens(text) if len(t) >= 2 and t not in _STOPWORDS]
