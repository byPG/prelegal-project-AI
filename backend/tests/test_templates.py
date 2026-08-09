from app.templates import ALL_DOCUMENTS, DOCUMENT_IDS, get_document


def test_all_eleven_catalog_documents_parsed():
    assert len(ALL_DOCUMENTS) == 11
    assert len(DOCUMENT_IDS) == 11
    assert len(set(DOCUMENT_IDS)) == 11  # no id collisions


def test_every_document_has_party_fields_and_body():
    for document in ALL_DOCUMENTS:
        field_keys = {field.key for field in document.fields}
        assert {"partyOneName", "partyOneAddress", "partyTwoName", "partyTwoAddress"} <= field_keys
        assert len(document.body) > 0


def test_get_document_returns_none_for_unknown_id():
    assert get_document("not-a-real-document") is None


def test_get_document_returns_match_for_known_id():
    document = get_document("mutual-nda")
    assert document is not None
    assert document.name == "Mutual Non-Disclosure Agreement"


def test_mutual_nda_fields_match_known_set():
    # Regression check: this is exactly the field set the original
    # hand-crafted Mutual NDA prototype used, so migrating it onto the
    # generic parser shouldn't change what the user is asked to fill in.
    document = get_document("mutual-nda")
    field_keys = {field.key for field in document.fields}
    assert field_keys == {
        "partyOneName",
        "partyOneAddress",
        "partyTwoName",
        "partyTwoAddress",
        "purpose",
        "effectiveDate",
        "mndaTerm",
        "termOfConfidentiality",
        "governingLaw",
        "jurisdiction",
    }


def test_mutual_nda_field_referenced_twice_in_body_is_a_single_field():
    # "Governing Law" appears twice in the Mutual NDA body text but must
    # dedupe to one field, not two.
    document = get_document("mutual-nda")
    matching = [field for field in document.fields if field.key == "governingLaw"]
    assert len(matching) == 1


def test_only_mutual_nda_has_a_trailing_attribution_line():
    for document in ALL_DOCUMENTS:
        if document.id == "mutual-nda":
            assert document.attribution and "Common Paper" in document.attribution
        else:
            assert document.attribution is None


def test_field_placeholder_segments_reference_a_declared_field_key():
    for document in ALL_DOCUMENTS:
        declared_keys = {field.key for field in document.fields}
        for item in document.body:
            for segment in item.inline:
                if segment.type == "field":
                    assert segment.field_key in declared_keys


def test_malformed_html_in_source_does_not_leak_into_rendered_text():
    # DPA and CSA/SLA have real quirks in the source markdown (a stray
    # extra </span>, and a <span id="..."> that wraps bold text instead of
    # being empty) — the parser must swallow the tags, not the text.
    dpa = get_document("dpa")
    all_text = " ".join(
        segment.text for item in dpa.body for segment in item.inline if segment.text
    )
    assert "<span" not in all_text
    assert "</span>" not in all_text

    sla = get_document("sla")
    link_items = [item for item in sla.body if any(s.type == "link" for s in item.inline)]
    assert link_items, "expected the SLA definitions to include a bare-URL reference"
    link_segment = next(s for s in link_items[0].inline if s.type == "link")
    assert link_segment.href == "https://commonpaper.com/standards/service-level-agreement/2.0/"


def test_header_spans_produce_header_variant_segments():
    dpa = get_document("dpa")
    header_variants = {
        segment.variant
        for item in dpa.body
        for segment in item.inline
        if segment.type == "text" and segment.variant in ("header2", "header3")
    }
    assert header_variants == {"header2", "header3"}


def test_a_space_survives_between_a_header_span_and_the_following_prose():
    # Regression check: DPA.md's header_3 items put two spaces between
    # "</span>" and the prose that follows (e.g. "...Provider as
    # Processor.</span>  In situations where..."). A naive .strip() on
    # each inline-text run swallows that gap entirely, gluing the header
    # onto the next word with no space at all once rendered as adjacent
    # elements ("Provider as Processor.In situations...").
    dpa = get_document("dpa")
    header_item = next(
        item
        for item in dpa.body
        if any(s.type == "text" and s.variant == "header3" for s in item.inline)
    )
    header_index = next(
        i for i, s in enumerate(header_item.inline) if s.type == "text" and s.variant == "header3"
    )
    following = header_item.inline[header_index + 1]
    assert following.type == "text"
    assert following.text.startswith(" "), (
        f"expected a leading space to survive after the header span, got {following.text!r}"
    )
