import random
import os
import logging

# ---------------------------------------------------------
# LOGGER
# ---------------------------------------------------------
logger = logging.getLogger("image_motion_engine")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler(
        "logs/image_motion_engine.log",
        encoding="utf-8"
    )
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


# ---------------------------------------------------------
# MOTION TRAIT REGISTRY
# ---------------------------------------------------------
MOTION_TRAITS = {

    "shake": {
        "strength": (2, 6),
        "speed": (6, 12),
    },

    "micro_jitter": {
        "strength": (1, 2),
        "speed": (10, 18),
    },

    "slow_zoom": {
        "zoom_start": 1.0,
        "zoom_end": (1.05, 1.15),
    },

    "push_in": {
        "zoom_start": 1.0,
        "zoom_end": (1.15, 1.35),
    },

    "pull_out": {
        "zoom_start": (1.1, 1.2),
        "zoom_end": 1.0,
    },

    "pulse_zoom": {
        "zoom_start": 1.0,
        "zoom_end": (1.08, 1.15),
        "pulse": True,
    },

    "float": {
        "drift": (5, 20),
    },

    "drift": {
        "drift": (10, 40),
    },

    "parallax": {
        "depth": (10, 40),
    },

    "tilt_pan": {
        "angle": (-6, 6),
    },
}


# ---------------------------------------------------------
# MOTION WEIGHTS (controls randomness)
# ---------------------------------------------------------
MOTION_WEIGHTS = {
    "slow_zoom": 5,
    "push_in": 4,
    "parallax": 3,
    "drift": 3,
    "float": 2,
    "shake": 2,
    "micro_jitter": 2,
    "pulse_zoom": 2,
    "tilt_pan": 1,
    "pull_out": 1,
}


# ---------------------------------------------------------
# EMOTION → MOTION MAP
# ---------------------------------------------------------
EMOTION_MOTION_MAP = {

    "fear": ["micro_jitter", "pulse_zoom", "slow_zoom"],

    "horror": ["pulse_zoom", "micro_jitter", "push_in"],

    "suspense": ["slow_zoom", "push_in"],

    "dramatic": ["push_in", "parallax"],

    "action": ["shake", "tilt_pan"],

    "calm": ["drift", "float"],

    "dream": ["float", "drift", "slow_zoom"],

    "neutral": ["slow_zoom"],
}


# ---------------------------------------------------------
# SCENE TYPE → MOTION MAP
# ---------------------------------------------------------
SCENE_TYPE_MOTION = {

    "horror": ["pulse_zoom", "micro_jitter", "push_in"],

    "action": ["shake", "tilt_pan"],

    "dialog": ["slow_zoom"],

    "dramatic": ["push_in", "pull_out"],

    "establishing": ["drift", "parallax"],

    "asmr": ["float", "drift"],
}


# ---------------------------------------------------------
# RANDOM VALUE RESOLUTION
# ---------------------------------------------------------
def _resolve_value(value):

    if isinstance(value, tuple):
        return random.uniform(value[0], value[1])

    return value


def resolve_motion_parameters(trait_name: str):

    config = MOTION_TRAITS.get(trait_name, {})

    params = {}
    for key, value in config.items():
        params[key] = _resolve_value(value)

    return params


# ---------------------------------------------------------
# WEIGHTED RANDOM SELECTION
# ---------------------------------------------------------
def _weighted_choice(options):

    weights = [MOTION_WEIGHTS.get(o, 1) for o in options]

    return random.choices(
        options,
        weights=weights,
        k=1
    )[0]


# ---------------------------------------------------------
# OPTIONAL MOTION LAYERING
# ---------------------------------------------------------
def _maybe_add_secondary_motion(primary):

    possible_secondary = {
        "slow_zoom": ["micro_jitter", "drift"],
        "push_in": ["micro_jitter"],
        "parallax": ["drift"],
    }

    if primary not in possible_secondary:
        return None

    if random.random() < 0.35:  # 35% chance
        return random.choice(possible_secondary[primary])

    return None


# ---------------------------------------------------------
# MAIN TRAIT SELECTOR
# ---------------------------------------------------------
def select_motion_trait(
    emotion: str = "neutral",
    scene_type: str = "normal",
    pacing: str = "normal",
    narration: str = "",
    seed: int | None = None,
):
    """
    Dynamically select motion strategy.
    """

    if seed is not None:
        random.seed(seed)

    emotion = (emotion or "neutral").lower()
    scene_type = (scene_type or "normal").lower()

    motion_pool = []

    if emotion in EMOTION_MOTION_MAP:
        motion_pool.extend(EMOTION_MOTION_MAP[emotion])

    if scene_type in SCENE_TYPE_MOTION:
        motion_pool.extend(SCENE_TYPE_MOTION[scene_type])

    if not motion_pool:
        motion_pool = ["slow_zoom"]

    trait = _weighted_choice(motion_pool)

    secondary = _maybe_add_secondary_motion(trait)

    params = resolve_motion_parameters(trait)

    if secondary:
        params["secondary"] = {
            "trait": secondary,
            "params": resolve_motion_parameters(secondary),
        }

    logger.info(
        "🎬 Motion Selected | emotion=%s scene=%s pacing=%s trait=%s secondary=%s params=%s",
        emotion,
        scene_type,
        pacing,
        trait,
        secondary,
        params,
    )

    return {
        "trait": trait,
        "params": params,
    }