import json

from app.agent.client import get_client, get_model
from app.agent.prompts import (
    CLASSIFY_AND_EXTRACT_PROMPT,
    CONFIRM_BLOCKED_TEMPLATE,
    CONFIRM_REPLY_TEMPLATE,
    INVALID_ITEMS_NOTE_TEMPLATE,
    MENU_CONTEXT_TEMPLATE,
    REPLY_SYSTEM_PROMPT,
)
from app.agent.state import AgentState, InvalidOrderItem, OrderItem
from app.repositories import menu_repository

_VALID_INTENTS = {"ORDER", "MODIFY_ORDER", "QUESTION", "CONFIRM", "CHITCHAT"}
_SUGGESTION_COUNT = 3


def _chat(
    system_prompt: str,
    conversation: list[dict[str, str]],
    temperature: float | None = None,
    json_mode: bool = False,
) -> str:
    response = get_client().chat.completions.create(
        model=get_model(),
        messages=[{"role": "system", "content": system_prompt}, *conversation],
        temperature=temperature,
        response_format={"type": "json_object"} if json_mode else None,
    )
    return response.choices[0].message.content or ""


async def _menu_context() -> str:
    items = await menu_repository.search_items("", limit=100)
    lines = [f"- {item.name} (${item.price:.2f})" for item in items if item.available]
    return MENU_CONTEXT_TEMPLATE.format(menu_lines="\n".join(lines))


def classify_and_extract(state: AgentState) -> dict:
    # Merged from two separate LLM calls (classify_intent + extract_order_items) into one - each
    # round trip to the local model costs ~4-7s here (qwen2.5:7b only partially fits this GPU's
    # VRAM, see CLAUDE_1.md latency notes), so cutting a whole call matters more than keeping the
    # two concerns in separate functions.
    #
    # temperature=0: structured-extraction task, not a creative one - left at default sampling
    # temperature, this was non-deterministic (observed ~50-80% failure rate on identical inputs).
    # json_mode=True: forces syntactically valid JSON. Without it, the model would sometimes
    # produce malformed/double-encoded output (a JSON array containing an unescaped or
    # re-stringified object instead of the object itself) that failed to parse at all, silently
    # dropping the whole order - json_object mode eliminates that failure class at the source.
    raw = _chat(CLASSIFY_AND_EXTRACT_PROMPT, state["conversation"], temperature=0, json_mode=True)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    intent = str(parsed.get("intent", "")).strip().upper()
    if intent not in _VALID_INTENTS:
        intent = "ORDER"

    entries = parsed.get("items", [])
    if not isinstance(entries, list):
        entries = []

    items: list[OrderItem] = []
    for entry in entries:
        # Belt-and-suspenders: still unwrap a string-wrapped object if the model nests one
        # despite JSON mode.
        if isinstance(entry, str):
            try:
                entry = json.loads(entry)
            except json.JSONDecodeError:
                continue

        if not isinstance(entry, dict) or not entry.get("name"):
            continue

        items.append(
            {
                "name": str(entry.get("name", "")),
                "quantity": int(entry.get("quantity", 1)),
                "notes": str(entry.get("notes", "")),
                "item_id": None,
                "price": None,
            }
        )

    return {"intent": intent, "order_items": items}


async def validate_order_items(state: AgentState) -> dict:
    """Confirms every extracted item against the real menu DB - never trusts the LLM's free-text
    name or a price it might have hallucinated. Unmatched items get "did you mean" suggestions
    pulled from a fuzzy search, so the agent can ask a clarifying question instead of guessing.
    """
    valid_items: list[OrderItem] = []
    invalid_items: list[InvalidOrderItem] = []

    for item in state.get("order_items", []):
        # Extraction sometimes splits a size/variant word into "notes" instead of keeping it in
        # "name" (e.g. name="كشري", notes="وسط") - since this menu has no variant system (each size
        # is its own SKU: كشري صغير/وسط/كبير/سوبريم are 4 separate menu_items rows), matching on
        # name alone silently resolves to the wrong SKU regardless of the size actually asked for.
        # Search the combined text first, and only fall back to name-alone if that finds nothing
        # (covers notes holding something unrelated, e.g. "no onions", that would corrupt the query).
        combined_query = f"{item['name']} {item['notes']}".strip()
        match = await menu_repository.get_item_by_name(combined_query)
        if match is None and combined_query != item["name"]:
            match = await menu_repository.get_item_by_name(item["name"])

        if match is None:
            suggestions = await menu_repository.search_items(combined_query, limit=_SUGGESTION_COUNT)
            if suggestions:
                names = ", ".join(s.name for s in suggestions)
                reason = f"not found on the menu, closest items: {names}"
            else:
                reason = "not on the menu"
            invalid_items.append({"name": item["name"], "reason": reason})
            continue

        if not await menu_repository.check_availability(match.id):
            invalid_items.append({"name": match.name, "reason": "currently unavailable"})
            continue

        valid_items.append(
            {
                "name": match.name,
                "quantity": item["quantity"],
                "notes": item["notes"],
                "item_id": str(match.id),
                "price": match.price,
            }
        )

    return {"order_items": valid_items, "invalid_items": invalid_items}


async def generate_reply(state: AgentState) -> dict:
    system_prompt = REPLY_SYSTEM_PROMPT + await _menu_context()

    invalid_items = state.get("invalid_items", [])
    if invalid_items:
        names = ", ".join(f"{item['name']} ({item['reason']})" for item in invalid_items)
        system_prompt += INVALID_ITEMS_NOTE_TEMPLATE.format(items=names)

    # Low, non-zero temperature: default sampling temperature produced garbled output on this
    # model (stray Latin/Thai-script fragments mixed into Arabic replies) - 0-0.3 was clean in
    # testing. Some variation is fine here (unlike the structured-extraction nodes above), this
    # is just conversational reply text.
    reply_text = _chat(system_prompt, state["conversation"], temperature=0.3)
    return {"reply_text": reply_text}


def confirm_order(state: AgentState) -> dict:
    invalid_items = state.get("invalid_items", [])
    if invalid_items:
        names = ", ".join(item["name"] for item in invalid_items)
        reply_text = _chat(CONFIRM_BLOCKED_TEMPLATE.format(items=names), state["conversation"], temperature=0.3)
        return {"reply_text": reply_text, "order_confirmed": False}

    items = state.get("order_items", [])
    if not items:
        return {
            "reply_text": "I don't have any items on your order yet — what would you like?",
            "order_confirmed": False,
        }

    items_summary = ", ".join(f"{item['quantity']}x {item['name']}" for item in items)
    reply_text = _chat(CONFIRM_REPLY_TEMPLATE.format(items=items_summary), state["conversation"], temperature=0.3)
    return {"reply_text": reply_text, "order_confirmed": True}
