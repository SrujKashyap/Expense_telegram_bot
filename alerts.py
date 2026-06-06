from db import get_monthly_total, get_budget


def check_budget_alerts(user_id):
    """
    Check overall budget after every expense log.
    Returns a warning string if threshold crossed, None if all clear.
    """
    budget = get_budget(user_id, "overall")
    if not budget:
        return None

    total = get_monthly_total(user_id)
    pct = (total / budget) * 100

    if pct >= 100:
        return (
            f"🚨 You've exceeded your monthly budget!\n"
            f"Spent ₹{total:,.0f} of ₹{budget:,.0f}"
        )
    elif pct >= 80:
        return (
            f"⚠️ You've used {pct:.0f}% of your monthly budget\n"
            f"₹{total:,.0f} of ₹{budget:,.0f} spent"
        )

    return None