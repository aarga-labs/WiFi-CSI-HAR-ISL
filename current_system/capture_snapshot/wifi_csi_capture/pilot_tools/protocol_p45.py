"""P04/P05 additions. The original protocol.py remains the P01-P03 definition."""
from protocol import (ACTIONS as ORIGINAL_ACTIONS, BASELINES, CONTEXT_INTENT,
                      INTENTS, SIGNS, SCRIPTS as ORIGINAL_SCRIPTS, SYNC,
                      intent_of)

VERSION = "p45-v1"

# Cold props at the existing table. Both actions remain I0 (no home command).
COOKING_ACTIONS = {
    "chop_food": (6, 10, "FYP protocol addition", "COOK, HUNGRY"),
    "stir_pot": (6, 10, "FYP protocol addition", "COOK, HOT, WATER"),
}
ACTIONS = {**ORIGINAL_ACTIONS, **COOKING_ACTIONS}
SEATED_ACTIONS = {
    label: ACTIONS[label]
    for label in ("drink", "eat", "answerphone", "tvremote", "wipetable",
                  "chop_food", "stir_pot")
}

ACTION_INSTRUCTIONS = {
    "chop_food": "repeat chopping motions with a blunt prop on a board; cold setup",
    "stir_pot": "stir a spoon in an empty/cold pot; keep the same pot and spoon",
}

SCRIPTS = {name: list(steps) for name, steps in ORIGINAL_SCRIPTS.items()}
# Keep the original meal order, inserting two cooking actions before sitting.
SCRIPTS["M-SEQ"][3:3] = [
    ("chop_food", "activity", "meal"),
    ("stir_pot", "activity", "meal"),
]
# All movements in this additional story are performed seated at the table.
# Activities remain a block followed by a sign block, as in the original protocol.
SCRIPTS["S-SEQ"] = [
    SYNC,
    ("wipetable", "activity", "meal"),
    ("chop_food", "activity", "meal"),
    ("stir_pot", "activity", "meal"),
    ("eat", "activity", "meal"),
    ("drink", "activity", "meal"),
    ("HELLO", "sign", "meal"),
    ("HUNGRY", "sign", "meal"),
    ("COOK", "sign", "meal"),
    ("HOT", "sign", "meal"),
    ("WATER", "sign", "meal"),
    ("HELP", "sign", "meal"),
    ("THANKYOU", "sign", "meal"),
    SYNC,
]
SCRIPT_START_POSTURE = {"S-SEQ": "seated"}


def script_postures(name):
    """Posture during each step, including transitions and mattress signs."""
    state = SCRIPT_START_POSTURE.get(name, "standing")
    result = []
    for label, typ, _ in SCRIPTS[name]:
        if typ == "activity" and label == "sitstand":
            result.append("transition")
            state = "standing" if state == "seated" else "seated"
        elif typ == "activity" and label == "fall":
            result.append("transition")
            state = "mattress"
        else:
            result.append("moving" if typ == "activity" and label == "walk" else state)
    return result
