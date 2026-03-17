import logging

logger = logging.getLogger("thumbnail_engine")


def generate_ai_thumbnail(title: str, output_path: str):
    """
    Placeholder AI thumbnail generator.

    Currently disabled because THUMBNAIL_AI_ENABLED=false.
    This will be replaced later with Flux / API generator.
    """

    logger.info("[ai-thumbnail] AI thumbnail generation currently disabled")

    return None