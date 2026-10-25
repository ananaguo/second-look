"""Historical one-calendar-year downside estimates; no AI or network calls."""
import math


def calculate_risk(history, series, amount=10000, confidence=0.95):
    """Nearest-rank historical VaR and exact empirical tail-average ES.

    Annual returns are percentages. Losses are floored at zero: gains are not
    reported as negative risk. Drawdown uses compounded year-end wealth only.
    Require >=40 consecutive annual observations for at least two tail years.
    """
    if not math.isfinite(amount) or amount <= 0 or not 0 < confidence < 1:
        raise ValueError("Amount and confidence must be valid positive inputs.")
    rows = sorted(history, key=lambda row: row['year'])
    if len(rows) < 40:
        raise ValueError("At least 40 annual observations are needed for these estimates.")
    years = [row['year'] for row in rows]
    if any(b != a + 1 for a, b in zip(years, years[1:])):
        raise ValueError("Historical years must be consecutive, without duplicates.")
    returns = [float(row[series]) for row in rows]
    if any(not math.isfinite(r) or r < -100 for r in returns):
        raise ValueError("Returns must be finite percentages, no lower than -100%.")
    losses = sorted(max(0.0, -r) for r in returns)
    n = len(losses)
    var = losses[math.ceil(confidence * n) - 1]
    # Average exactly the worst (1-confidence) share of the empirical sample.
    tail_mass = n * (1 - confidence)
    whole = int(math.floor(tail_mass + 1e-12))
    fraction = max(0.0, tail_mass - whole)
    descending = list(reversed(losses))
    es = (sum(descending[:whole]) + (fraction * descending[whole] if fraction > 1e-12 else 0)) / tail_mass
    wealth = peak = 1.0
    drawdown = 0.0
    for r in returns:
        wealth *= 1 + r / 100
        peak = max(peak, wealth)
        drawdown = max(drawdown, (peak - wealth) / peak * 100)
    return dict(var_pct=var, es_pct=es, drawdown_pct=drawdown,
                loss_frequency_pct=100 * sum(r < 0 for r in returns) / n,
                losing_years=sum(r < 0 for r in returns), observations=n,
                start=years[0], end=years[-1], confidence=confidence, amount=amount,
                var_dollars=amount * var / 100, es_dollars=amount * es / 100,
                drawdown_dollars=amount * drawdown / 100)
