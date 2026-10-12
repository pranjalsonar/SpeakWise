from app.integrations.wikipedia.parser import clean_paragraph, parse_extract, total_words

EXTRACT = """Remote work is the practice of working from home.[citation needed] It grew in the 2020s.
Many companies adopted it.

== History ==
Working at home has been documented for centuries ( ).

=== Early years ===
In the 1970s, satellite offices linked to mainframes.

== Potential benefits ==

=== Cost reduction ===
Companies save on office space , and workers save on commuting.

== See also ==
Telecommuting
Digital nomad

== Empty section ==
"""


def test_lead_and_sections_are_split_with_heading_paths():
    sections = parse_extract(EXTRACT)
    headings = [s["heading"] for s in sections]
    assert headings == [None, "History", "Early years", "Cost reduction", "See also"]

    early = sections[2]
    assert early["path"] == ["History", "Early years"]
    assert early["level"] == 3

    cost = sections[3]
    assert cost["path"] == ["Potential benefits", "Cost reduction"]


def test_headings_without_text_are_dropped():
    headings = [s["heading"] for s in parse_extract(EXTRACT)]
    assert "Potential benefits" not in headings  # only has a subsection
    assert "Empty section" not in headings


def test_paragraphs_are_cleaned():
    lead = parse_extract(EXTRACT)[0]
    assert lead["paragraphs"][0] == "Remote work is the practice of working from home. It grew in the 2020s."
    history = parse_extract(EXTRACT)[1]
    assert history["paragraphs"] == ["Working at home has been documented for centuries."]
    cost = parse_extract(EXTRACT)[3]
    assert "space, and" in cost["paragraphs"][0]


def test_list_like_sections_are_flagged():
    see_also = parse_extract(EXTRACT)[4]
    assert see_also["list_ratio"] == 1.0


def test_word_counts():
    sections = parse_extract(EXTRACT)
    assert sections[0]["words"] == len(" ".join(sections[0]["paragraphs"]).split())
    assert total_words(sections) == sum(s["words"] for s in sections)


def test_clean_paragraph_removes_reference_markers():
    assert clean_paragraph("A claim.[12] Another.[dubious – discuss]") == "A claim. Another."
