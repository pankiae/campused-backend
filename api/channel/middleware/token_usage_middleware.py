import logging

from django.db import transaction
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from api.user.models import UserCredit
from utils.openai_logic import token_calculation

logger = logging.getLogger(__name__)


class TokenUsageMiddleware(MiddlewareMixin):
    """
    Middleware to handle token usage per request.
    """

    def process_request(self, request):
        # Only process authenticated users
        if not request.user.is_authenticated:
            return None
        logger.info("user: %s", request.user)
        # Skip admin or non-chat routes if needed
        if not request.path.startswith("/api/channel"):
            return None

        # Get or create credit record
        credit, _ = UserCredit.objects.get_or_create(user=request.user)
        logger.info("remaining token: %s", credit.remaining_tokens)
        # Check if user still has tokens
        if credit.remaining_tokens <= 0:
            return JsonResponse(
                {
                    "error": "Insufficient tokens. Please upgrade your plan.",
                    "remaining_tokens": credit.remaining_tokens,
                },
                status=402,  # Payment Required
            )

        # Store credit object for later use in response
        request.user_credit = credit
        return None

    def process_response(self, request, response):
        """
        Update token usage after successful response and attach remaining tokens.
        """
        try:
            # Skip if no user or no token data was set
            if not hasattr(request, "user") or not hasattr(request, "user_credit"):
                return response

            credit = request.user_credit

            # --- Example: get token data from channel context ---
            if hasattr(request, "gather_tokens"):  # if you attach it in the chat logic
                gather_tokens = request.gather_tokens
                token_summary = token_calculation.sum_input_output_token_cost(
                    model=gather_tokens["model"],
                    input_tokens=gather_tokens["input"],
                    output_tokens=gather_tokens["output"],
                    tier="Standard",
                )

                total_used = gather_tokens["input"] + gather_tokens["output"]

                # Safe update
                with transaction.atomic():
                    credit.used_tokens += total_used
                    credit.remaining_tokens = max(
                        credit.total_tokens - credit.used_tokens, 0
                    )
                    credit.save()

                # Add updated tokens to response headers
                response["X-User-Remaining-Tokens"] = credit.remaining_tokens

            return response

        except Exception as e:
            print(f"[TokenUsageMiddleware] Error: {e}")
            return response
