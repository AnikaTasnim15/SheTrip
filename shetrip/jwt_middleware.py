from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class JWTRefreshMiddleware(MiddlewareMixin):
    """Auto-refresh JWT access token if it's about to expire."""

    REFRESH_MARGIN = timedelta(minutes=5)  # refresh when less than this remains

    def process_request(self, request):
        access_token = request.COOKIES.get('shetrip-auth')
        refresh_token = request.COOKIES.get('shetrip-refresh')

        if not access_token or not refresh_token:
            return None

        try:
            token = AccessToken(access_token)
        except (TokenError, InvalidToken) as exc:
            # Access token invalid/expired — can't inspect expiry reliably
            logger.debug("Access token invalid when checking expiry: %s", exc)
            return None

        exp = token.payload.get('exp')
        if not exp:
            return None

        try:
            # Make timezone-aware datetime in UTC for comparison
            exp_dt = datetime.fromtimestamp(int(exp), tz=timezone.utc)
        except Exception as exc:
            logger.debug("Failed to parse token exp claim: %s", exc)
            return None

        now = timezone.now()
        # If token is due to expire soon, attempt to refresh access token
        if (exp_dt - now) <= self.REFRESH_MARGIN:
            try:
                refresh = RefreshToken(refresh_token)
                new_access = str(refresh.access_token)
                request.new_jwt_token = new_access

                # Optionally, if you want to rotate refresh tokens and return a new refresh
                # token as well, implement that explicitly here and set request.new_refresh_token.
                # Be careful: rotating requires handling blacklisting depending on your SIMPLE_JWT settings.

            except (TokenError, InvalidToken) as exc:
                logger.info("Refresh token invalid or expired; cannot refresh access token: %s", exc)
                # Don't raise — client will handle auth failure on next request
                return None

        return None

    def process_response(self, request, response):
        if hasattr(request, 'new_jwt_token'):
            jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
            secure = jwt_settings.get('AUTH_COOKIE_SECURE', False)
            samesite = jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax')
            max_age = jwt_settings.get('ACCESS_TOKEN_LIFETIME', None)
            # If max_age is a timedelta, convert to seconds; otherwise fall back to 3600
            try:
                if hasattr(max_age, 'total_seconds'):
                    max_age_seconds = int(max_age.total_seconds())
                else:
                    max_age_seconds = int(max_age) if max_age else 3600
            except Exception:
                max_age_seconds = 3600

            response.set_cookie(
                key='shetrip-auth',
                value=request.new_jwt_token,
                httponly=True,
                secure=secure,
                samesite=samesite,
                max_age=max_age_seconds,
                path='/',
            )

        return response