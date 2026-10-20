"""
protocol.py - the final Phase-1 class set, intent map and scripts.

One place that defines every label, so the cue logger, the plotter and the
paper tables all use exactly the same names.  Edit here, nowhere else.
"""

# ---------------------------------------------------------------------------
# Intent categories (what the home should do)
# ---------------------------------------------------------------------------
INTENTS = {
    "I0": "No command (routine activity or idle) - the home must NOT act",
    "I1": "Device control",
    "I2": "Personal need / comfort",
    "I3": "Alert / assistance",
    "I4": "Interaction (wake / confirm)",
}

# ---------------------------------------------------------------------------
# Routine atomic actions (isolated trials).  dur = seconds between GO and STOP.
# ---------------------------------------------------------------------------
ACTIONS = {
    #  label        dur  reps  source              look-alike sign
    "walk":        (6, 10, "UT-HAR",            "-"),
    "sitstand":    (6, 10, "UT-HAR",            "PAIN"),
    "pickup":      (6, 10, "UT-HAR",            "HELP"),
    "lightswitch": (4, 10, "OPPORTUNITY",       "LAMP"),
    "drink":       (6, 10, "OPPORTUNITY",       "WATER"),
    "answerphone": (6, 10, "CASAS / Lawton",    "CALL"),
    "eat":         (6, 10, "CASAS / Katz ADL",  "HOT, THANK YOU"),
    "wipetable":   (6, 10, "CASAS / OPPORTUNITY", "FAN, HELLO"),
    "tvremote":    (5, 10, "CASAS",             "TELEVISION"),
    "fall":        (6, 5,  "UT-HAR / XRF55",    "ACCIDENT"),
}

# ---------------------------------------------------------------------------
# ISL signs (isolated trials, 5 standing + 5 seated per person)
# intent = default intent; ctx = context-dependent intents
# Final 14-sign set agreed by the team on 2 Oct 2026 (TOILET, COOK, HUNGRY added).
# ---------------------------------------------------------------------------
SIGNS = {
    #  label        dur intent  home action           source
    "HELLO":      (4, "I4", "wake_system",          "INCLUDE-50"),
    "THANKYOU":   (4, "I4", "confirm_close",        "INCLUDE (verify)"),
    "LAMP":       (4, "I1", "toggle_light",         "INCLUDE-50"),
    "FAN":        (4, "I1", "toggle_fan",           "INCLUDE-50"),
    "TELEVISION": (4, "I1", "toggle_tv",            "INCLUDE (verify)"),
    "COOK":       (4, "I1", "cooking_mode",         "ISLRTC dictionary (verify)"),  # exhaust + light + visual timer
    "WATER":      (4, "I2", "bring_water_reminder", "ISLRTC dictionary (verify)"),
    "HOT":        (4, "I2", "cool_room",            "ISL emergency set"),
    "HUNGRY":     (4, "I2", "food_request",         "ISLRTC dictionary (verify)"),
    "TOILET":     (4, "I2", "toilet_assist",        "ISLRTC dictionary (verify)"),  # bathroom light on, tell caregiver
    "CALL":       (4, "I3", "call_caregiver",       "ISL emergency set"),
    "HELP":       (4, "I3", "notify_caregiver",     "ISL emergency set"),
    "PAIN":       (4, "I3", "health_alert",         "ISL emergency set"),
    "ACCIDENT":   (4, "I3", "emergency_alert",      "ISL emergency set"),
}

# Context changes the intent for these signs (this is the paper's intent test):
#   HOT  while eating / at the table  -> I3 kitchen_hazard_alert  (burn / stove)
#   HOT  while seated watching TV     -> I2 cool_room             (fan on)
#   HELP during cleaning              -> I3 notify_caregiver      (assistance)
#   HELP after a fall                 -> I3 emergency_alert       (urgent)
CONTEXT_INTENT = {
    ("HOT", "meal"): ("I3", "kitchen_hazard_alert"),
    ("HOT", "tv"): ("I2", "cool_room"),
    ("HELP", "cleaning"): ("I3", "notify_caregiver"),
    ("HELP", "after_fall"): ("I3", "emergency_alert"),
}

BASELINES = {"stand_still": 60, "sit_still": 60}   # seconds, per participant
# empty_room (120 s) is recorded by the operator at the start and end of each day.

# ---------------------------------------------------------------------------
# Scripts: 3 sequential stories (SEQ): the activities first, then the signs as a block.
# 2 Oct: the guide said interleaved (INT) stories are not required, so they were removed
# before any script was recorded.
# Each step: (label, type, context)   type in {activity, sign, idle, sync}
# ---------------------------------------------------------------------------
def _a(label, ctx):
    return (label, "activity", ctx)


def _s(label, ctx):
    return (label, "sign", ctx)


SYNC = ("clap_x3", "sync", "-")

SCRIPTS = {
    # Meal (complex activity C1: have a meal) - HOT means kitchen hazard here.
    # 2 Oct: HUNGRY and COOK added (kitchen signs).
    "M-SEQ": [SYNC, _a("walk", "meal"), _a("lightswitch", "meal"), _a("sitstand", "meal"),
              _a("eat", "meal"), _a("drink", "meal"),
              _s("HELLO", "meal"), _s("HUNGRY", "meal"), _s("COOK", "meal"), _s("HOT", "meal"),
              _s("WATER", "meal"), _s("THANKYOU", "meal"),
              _a("sitstand", "meal"), _a("walk", "meal"), SYNC],
    # TV (complex activity C2: watch TV + C4 phone conversation) - HOT means "cool the room".
    # 2 Oct: TOILET added (signed just before getting up to leave).
    "T-SEQ": [SYNC, _a("walk", "tv"), _a("sitstand", "tv"), _a("tvremote", "tv"),
              _a("answerphone", "tv"),
              _s("HELLO", "tv"), _s("TELEVISION", "tv"), _s("HOT", "tv"), _s("LAMP", "tv"), _s("CALL", "tv"),
              _s("TOILET", "tv"),
              _a("sitstand", "tv"), _a("walk", "tv"), SYNC],
    # Cleaning -> fall (complex activity C3: clean up) - HELP changes meaning after the fall
    "C-SEQ": [SYNC, _a("walk", "cleaning"), _a("wipetable", "cleaning"), _a("pickup", "cleaning"),
              _s("FAN", "cleaning"), _s("HELP", "cleaning"),
              _a("walk", "cleaning"), _a("fall", "after_fall"),
              _s("HELP", "after_fall"), _s("PAIN", "after_fall"), _s("ACCIDENT", "after_fall"), _s("CALL", "after_fall"),
              SYNC],
}


def intent_of(label, typ, ctx):
    """Return (intent_category, home_action) for one labelled segment."""
    if typ != "sign":
        return ("I0", "none")
    if (label, ctx) in CONTEXT_INTENT:
        return CONTEXT_INTENT[(label, ctx)]
    _, cat, action, _ = SIGNS[label]
    return (cat, action)
