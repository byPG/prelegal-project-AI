"""Chat system-prompt building for the AI-driven document flow.

Generalizes what PREL-5 built as Mutual-NDA-only prompt building across
every document in templates.py's catalog (PREL-6).
"""

from .templates import ALL_DOCUMENTS, get_document

GREETING = (
    "Hi! I can help you put together a legal agreement — NDAs, service "
    "agreements, data processing agreements, and more. What kind of "
    "document do you need, and what's it for?"
)

_BASE_INSTRUCTIONS = (
    "You are a friendly, concise legal-intake assistant helping a user create a "
    "legal agreement through natural conversation. Do not give legal advice or "
    "invent values the user hasn't provided or confirmed. Always end your reply "
    "with a question — either to gather the next missing piece of information, to "
    "confirm something ambiguous, or (once everything needed is filled in) to "
    "confirm the document is ready to download. Never end your reply with a plain "
    "statement that leaves the user with nothing to respond to."
)


def _catalog_listing() -> str:
    return "\n".join(f"- {document.id}: {document.name} — {document.description}" for document in ALL_DOCUMENTS)


def build_system_prompt(document_id: str | None, known_fields: dict[str, str | None]) -> str:
    if document_id is None:
        return (
            f"{_BASE_INSTRUCTIONS}\n\n"
            "We only generate the following document types:\n"
            f"{_catalog_listing()}\n\n"
            "Figure out from the conversation which one (if any) the user needs, and "
            "set document_id once you're confident. If the user describes something "
            "we don't support, clearly say we can't generate that specific document, "
            "then suggest the closest match from the list above and explain briefly "
            "why it's the closest fit. Don't set document_id until the user has "
            "confirmed a specific supported type — a suggestion alone isn't a "
            "confirmation."
        )

    document = get_document(document_id)
    field_lines = "\n".join(f"- {field.key}: {field.label}" for field in document.fields)
    known_lines = (
        "\n".join(f"- {key}: {value!r}" for key, value in known_fields.items() if value) or "(none yet)"
    )

    return (
        f"{_BASE_INSTRUCTIONS}\n\n"
        f"The user is creating a {document.name} ({document.description}).\n\n"
        f"Fields to fill in:\n{field_lines}\n\n"
        f"Already known:\n{known_lines}\n\n"
        "Ask about one or two missing fields at a time rather than listing all of "
        "them at once. Reply with a natural-language message continuing the "
        "conversation, plus any field values you can newly infer or confirm from the "
        "user's latest message. Leave a field's update empty if the user's latest "
        "message gave no new information about it — don't repeat back values you "
        "already have unless the user is changing them."
    )
