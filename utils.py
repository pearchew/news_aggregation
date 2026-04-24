import logging
import requests

logger = logging.getLogger(__name__)

def send_to_discord(webhook_url: str, content: str, username: str = "Digest Bot", avatar_url: str = None) -> None:
    """
    Sends a message to a Discord channel via webhook.
    """
    if webhook_url == "YOUR_DISCORD_WEBHOOK_URL_HERE" or not webhook_url:
        logger.warning("Skipping Discord notification (no valid webhook URL provided).")
        return

    logger.info(f"Sending summary to Discord as '{username}'...")

    # Discord has a 2000 character limit for the 'content' field.
    if len(content) > 2000:
        logger.warning("Digest exceeds 2000 characters. Truncating for Discord limit...")
        content = content[:1993] + "..."

    payload = {
        "content": content,
        "username": username,
    }
    
    if avatar_url:
        payload["avatar_url"] = avatar_url

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        logger.info("✅ Successfully posted to Discord!")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to send to Discord: {e}")
        # If the response exists, it might contain helpful error info from Discord
        if hasattr(e, 'response') and e.response is not None:
             logger.error(f"Response content: {e.response.text}")