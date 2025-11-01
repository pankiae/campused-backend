import logging

from api.user.models import UserCredit

logger = logging.getLogger(__name__)


def activate_subscription(order):
    """
    Credit tokens to user after successful payment.
    Add tokens cumulatively if user already has credits.
    """
    plan = order.plan
    if not plan:
        logger.warning("Order %s has no plan linked", order.id)
        return None

    user_credit, _ = UserCredit.objects.get_or_create(user=order.user)

    user_credit.total_tokens += plan.token_limit
    user_credit.remaining_tokens += plan.token_limit
    user_credit.save()

    logger.info("Added %s tokens to user %s", plan.token_limit, order.user.username)
    return user_credit


def check_and_deduct_tokens(user, tokens_to_consume: int):
    """
    Check user has enough tokens and deduct the used ones.
    Raise an error if the balance is insufficient.
    """
    user_credit = UserCredit.objects.select_for_update().get(user=user)

    if user_credit.remaining_tokens < tokens_to_consume:
        raise PermissionError("Insufficient token balance. Please upgrade your plan.")

    user_credit.used_tokens += tokens_to_consume
    user_credit.remaining_tokens -= tokens_to_consume
    user_credit.save()

    return user_credit
