import pandas as pd
import numpy as np
from quantlab.quant.annualization import resolve_annualization

def compute_metrics(bt: pd.DataFrame, interval: str | None = None) -> dict:
    equity = bt["equity"]
    total_return = float(equity.iloc[-1] - 1.0)

    # Drawdown
    peak = equity.cummax()
    dd = (equity / peak) - 1.0
    max_dd = float(dd.min())

    # Winrate (por días positivos con posición)
    active = bt["position"].shift(1).fillna(0) == 1
    wins = (bt.loc[active, "strategy_ret_net"] > 0).sum()
    total = active.sum()
    winrate = float(wins / total) if total > 0 else 0.0

    # Sharpe simple por periodo, sin tasa libre
    r = bt["strategy_ret_net"]
    context = resolve_annualization(bt.index, interval)
    factor = context.periods_per_year
    sharpe = float(np.sqrt(factor) * (r.mean() / (r.std() + 1e-12))) if factor else None

    return {
        "total_return": total_return,
        "max_drawdown": max_dd,
        "winrate_active_days": winrate,
        "sharpe_simple": sharpe,
        "interval": interval,
        "periods_per_year": factor,
        "annualization_status": context.annualization_status,
        "annualization_reason": context.reason,
        "days": int(len(bt)),
        "trades": int((bt["trade"].abs() > 0).sum())
    }
