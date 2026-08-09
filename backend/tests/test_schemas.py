import pytest
from pydantic import ValidationError

from app.schemas import build_chat_reply_model
from app.templates import DOCUMENT_IDS


def test_build_chat_reply_model_accepts_known_field_keys():
    Reply = build_chat_reply_model(["purpose", "governingLaw"])

    instance = Reply(reply="hi", field_updates={"purpose": "evaluating a deal"})

    assert instance.field_updates.purpose == "evaluating a deal"
    assert instance.field_updates.governingLaw is None


def test_build_chat_reply_model_rejects_unknown_field_keys():
    Reply = build_chat_reply_model(["purpose"])

    with pytest.raises(ValidationError):
        Reply(reply="hi", field_updates={"notARealField": "x"})


def test_build_chat_reply_model_document_id_accepts_any_catalog_id():
    Reply = build_chat_reply_model([])

    for document_id in DOCUMENT_IDS:
        instance = Reply(reply="hi", document_id=document_id)
        assert instance.document_id == document_id


def test_build_chat_reply_model_document_id_rejects_unknown_id():
    Reply = build_chat_reply_model([])

    with pytest.raises(ValidationError):
        Reply(reply="hi", document_id="not-a-real-document")


def test_build_chat_reply_model_with_no_fields_still_allows_omitting_field_updates():
    Reply = build_chat_reply_model([])

    instance = Reply(reply="hi")

    assert instance.field_updates.model_dump() == {}
