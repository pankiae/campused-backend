from api.subscriptions.models import UserCredit


def activate_subscription(order):
    """
    Add tokens to user's balance when a plan is purchased successfully.
    If user already has tokens, sum them up.
    """
    plan = order.plan
    user_credit, _ = UserCredit.objects.get_or_create(user=order.user)

    # Add new plan tokens to the user's existing balance
    user_credit.total_tokens += plan.token_limit
    user_credit.remaining_tokens += plan.token_limit
    user_credit.save()

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
