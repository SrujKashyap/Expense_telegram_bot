from datetime import datetime
from db import (
    get_monthly_total, get_category_breakdown, get_budget,
    set_budget, get_last_expense, delete_expense, get_recent_expenses
)


def handle_total(user_id):
    total = get_monthly_total(user_id)
    budget = get_budget(user_id, "overall")
    month = datetime.now().strftime("%B %Y")

    lines = [f"📊 *{month}*", f"Total: ₹{total:,.0f}"]

    if budget:
        remaining = budget - total
        pct = (total / budget) * 100
        lines.append(f"Budget: ₹{budget:,.0f}")
        if remaining >= 0:
            lines.append(f"Remaining: ₹{remaining:,.0f} ({100 - pct:.0f}% left) ✅")
        else:
            lines.append(f"Over by: ₹{abs(remaining):,.0f} ⚠️")
    else:
        lines.append("Tip: set a budget with /budget 20000")

    return "\n".join(lines)


def handle_summary(user_id, last_month=False):
    now = datetime.now()
    if last_month:
        month = now.month - 1 if now.month > 1 else 12
        year = now.year if now.month > 1 else now.year - 1
    else:
        month = now.month
        year = now.year

    month_name = datetime(year, month, 1).strftime("%B %Y")
    breakdown = get_category_breakdown(user_id, year, month)
    total = get_monthly_total(user_id, year, month)
    budget = get_budget(user_id, "overall")

    if not breakdown:
        return f"No expenses recorded for {month_name}."

    lines = [f"📊 *{month_name} Summary*\n"]
    for row in breakdown:
        lines.append(f"  {row['category']:<15} ₹{row['total']:>8,.0f}")

    lines.append(f"\n{'─' * 26}")
    lines.append(f"  {'Total':<15} ₹{total:>8,.0f}")

    if budget:
        lines.append(f"  {'Budget':<15} ₹{budget:>8,.0f}")
        diff = total - budget
        if diff > 0:
            lines.append(f"\n  Over by ₹{diff:,.0f} ⚠️")
        else:
            lines.append(f"\n  Under by ₹{abs(diff):,.0f} ✅")

    return "\n".join(lines)


def handle_budget_set(user_id, args):
    """
    /budget 20000        -> set overall budget
    /budget food 5000    -> set category budget
    """
    if not args:
        budget = get_budget(user_id, "overall")
        if budget:
            return f"Current budget: ₹{budget:,.0f}\nTo change: /budget 20000"
        return "No budget set.\nUsage: /budget 20000 or /budget food 5000"

    try:
        if len(args) == 1:
            amount = float(args[0])
            set_budget(user_id, amount, "overall")
            return f"✅ Monthly budget set to ₹{amount:,.0f}"
        elif len(args) == 2:
            category = args[0].lower()
            amount = float(args[1])
            set_budget(user_id, amount, category)
            return f"✅ Budget for '{category}' set to ₹{amount:,.0f}"
        else:
            return "Usage: /budget 20000 or /budget food 5000"
    except ValueError:
        return "Invalid amount.\nUsage: /budget 20000 or /budget food 5000"


def handle_undo(user_id):
    last = get_last_expense(user_id)
    if not last:
        return "No expenses to undo."

    delete_expense(last["id"])
    msg = f"↩️ Deleted: ₹{last['amount']:,.0f} — {last['category']}"
    if last["note"]:
        msg += f" ({last['note']})"
    return msg


def handle_expenses(user_id, args):
    category = args[0].lower() if args else None
    rows = get_recent_expenses(user_id, category=category, limit=10)

    if not rows:
        label = f"in '{category}'" if category else ""
        return f"No expenses found {label}".strip()

    header = f"Last {len(rows)} expenses"
    if category:
        header += f" in '{category}'"
    lines = [f"📋 *{header}*\n"]

    for row in rows:
        date = row["created_at"][:10]
        line = f"  {date}  ₹{row['amount']:>8,.0f}  {row['category']}"
        if row["note"]:
            line += f"  ({row['note']})"
        lines.append(line)

    return "\n".join(lines)