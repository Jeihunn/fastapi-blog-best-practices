from httpx_oauth.clients.google import GoogleOAuth2

from src.core.config import settings

google_oauth_client = GoogleOAuth2(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
)
