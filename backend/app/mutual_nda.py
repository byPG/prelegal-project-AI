"""Field metadata for the one document type the AI chat currently supports.

Mirrors frontend/types/mutual-nda.ts's MUTUAL_NDA_FIELDS. Kept as a small,
separate Python copy rather than shared codegen since there's exactly one
document type today (PREL-5) — revisit if/when more templates are added.
"""

FIELD_GUIDE: dict[str, str] = {
    "partyOneName": "Legal name of the first party (the one disclosing or receiving confidential information)",
    "partyOneAddress": "Mailing address of the first party",
    "partyTwoName": "Legal name of the second party",
    "partyTwoAddress": "Mailing address of the second party",
    "purpose": "The shared purpose for exchanging confidential information, e.g. 'evaluating a potential business relationship'",
    "effectiveDate": "The date the agreement takes effect",
    "mndaTerm": "How long the agreement itself stays in effect, e.g. '2 years'",
    "termOfConfidentiality": "How long confidentiality obligations survive after the agreement ends, e.g. '3 years'",
    "governingLaw": "The state whose law governs the agreement, e.g. 'Delaware'",
    "jurisdiction": "The courts where disputes must be brought, e.g. 'New Castle County, Delaware'",
}

GREETING = (
    "Hi! I'll help you put together a Mutual NDA. Let's start with the two parties — "
    "what's the legal name and address of the party you represent?"
)


def build_system_prompt(known_fields: dict[str, str | None]) -> str:
    field_lines = "\n".join(f"- {key}: {description}" for key, description in FIELD_GUIDE.items())
    known_lines = "\n".join(
        f"- {key}: {value!r}" for key, value in known_fields.items() if value
    ) or "(none yet)"

    return (
        "You are a friendly, concise legal-intake assistant helping a user fill out a "
        "Common Paper Mutual Non-Disclosure Agreement (Mutual NDA) through natural "
        "conversation. Ask about one or two missing fields at a time rather than "
        "listing all of them at once. Do not give legal advice or invent values the "
        "user hasn't provided or confirmed.\n\n"
        f"Fields to fill in:\n{field_lines}\n\n"
        f"Already known:\n{known_lines}\n\n"
        "Reply with a natural-language message continuing the conversation, plus any "
        "field values you can newly infer or confirm from the user's latest message. "
        "Leave a field's update empty if the user's latest message gave no new "
        "information about it — don't repeat back values you already have unless the "
        "user is changing them."
    )
