"""
Baut die statischen RSL-Ranglisten für die Website.

Lädt zwei Jahre Wochenkurse von Yahoo Finance, berechnet RSL = Kurs / SMA(26 Wochen)
und die Ränge für JEDE Woche und schreibt pro Index eine JSON-Datei nach docs/data/.

Zusaetzlich wird docs/data/prices.json geschrieben: der letzte Tagesschlusskurs
je Aktie. Dieser Wert dient NUR der Anzeige - die RSL-Berechnung und alle
Raenge bleiben unveraendert auf Wochenbasis (Levy).

Aufruf:
  python scripts/build_rankings.py                 # alle Indizes, volle Rechnung
  python scripts/build_rankings.py --index DAX     # nur einer
  python scripts/build_rankings.py --weeks 78      # mehr Historie behalten
  python scripts/build_rankings.py --prices-only   # nur Tagesschlusskurse auffrischen

Schlägt ein Index fehl (Yahoo blockt, Netzwerk weg), bleibt seine bisherige
JSON-Datei unverändert stehen. Die Seite zeigt dann die Daten der Vorwoche.
"""

import sys, json, time, argparse, unicodedata, re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import rsl_core as core
from rsl_core import SMA_PERIOD, MIN_PERIODS, TOP_PCT, INDEX_DEFS, fetch_index_tickers

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'data'
WEEKS_DEFAULT = 78          # rund 1,5 Jahre Historie in der JSON-Datei
RETRIES = 3


def slug(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def download(tickers):
    """Wochenkurse laden, mit Wiederholung bei Fehlern von Yahoo."""
    import yfinance as yf
    last = None
    for n in range(1, RETRIES + 1):
        try:
            d = yf.download(tickers, period="2y", interval="1wk", auto_adjust=True,
                            progress=False, threads=True, timeout=60)
            if d is not None and not d.empty:
                return d
            last = "Leere Antwort von Yahoo."
        except Exception as e:
            last = str(e)
        if n < RETRIES:
            print(f"    Versuch {n} fehlgeschlagen ({last}) — neuer Versuch in 20s")
            time.sleep(20)
    raise RuntimeError(last or "Download fehlgeschlagen.")


def download_daily(tickers):
    """Letzte Tageskurse laden (nur fuer die Anzeige des aktuellen Kurses)."""
    import yfinance as yf
    last = None
    for n in range(1, RETRIES + 1):
        try:
            d = yf.download(tickers, period="10d", interval="1d", auto_adjust=True,
                            progress=False, threads=True, timeout=60)
            if d is not None and not d.empty:
                return d
            last = "Leere Antwort von Yahoo."
        except Exception as e:
            last = str(e)
        if n < RETRIES:
            print(f"    Versuch {n} fehlgeschlagen ({last}) - neuer Versuch in 20s")
            time.sleep(20)
    raise RuntimeError(last or "Download fehlgeschlagen.")


def close_frame(data, tickers, fill=True):
    """Close-Spalten aus der yfinance-Antwort holen (wie in rsl_core).

    fill=True fuellt Luecken vorwaerts - richtig fuer die Wochenreihe der
    RSL-Rechnung. fill=False laesst Luecken stehen, damit ein Tageskurs nicht
    faelschlich das Datum eines Tages bekommt, an dem er gar nicht gehandelt wurde.
    """
    if isinstance(data.columns, pd.MultiIndex):
        if 'Close' not in data.columns.get_level_values(0):
            raise RuntimeError("Keine Close-Daten in der Antwort.")
        c = data['Close'].dropna(axis=1, how='all')
        return c.ffill() if fill else c
    if 'Close' not in data.columns:
        raise RuntimeError("Keine Close-Daten.")
    c = data[['Close']]
    if fill:
        c = c.ffill()
    c.columns = tickers[:1]
    return c


def build_index(index_name, weeks):
    print(f"\n[{index_name}]")
    tickers, sector_info = fetch_index_tickers(index_name)
    if not tickers:
        raise RuntimeError("Keine Ticker gefunden.")
    print(f"  {len(tickers)} Ticker, lade Kursdaten...")

    close = close_frame(download(tickers), tickers)
    if close.empty or len(close.columns) < 3:
        raise RuntimeError(f"Nur {0 if close.empty else len(close.columns)} Aktien mit Daten.")

    sma = close.rolling(window=SMA_PERIOD, min_periods=MIN_PERIODS).mean()
    rsl = close / sma

    # Wochen ohne ausreichende Abdeckung verwerfen (wie in rsl_core)
    vi = rsl.notna().sum(axis=1)
    keep = vi[vi >= len(close.columns) * 0.5].index
    rsl, close, sma = rsl.loc[keep], close.loc[keep], sma.loc[keep]
    if rsl.empty:
        raise RuntimeError("Keine gültigen RSL-Werte berechnet.")

    rsl, close, sma = rsl.tail(weeks), close.tail(weeks), sma.tail(weeks)
    dates = [d.strftime('%Y-%m-%d') for d in rsl.index]
    out = {t: {'n': core.ticker_name(t, sector_info),
               's': (sector_info.get(t) or {}).get('sector', ''),
               'r': [], 'c': [], 'v': []} for t in close.columns}
    totals = []

    for d in rsl.index:
        rv, cv, sv = rsl.loc[d], close.loc[d], sma.loc[d]
        valid = rv.notna() & (rv > 0) & (rv < 10)
        ranked = rv[valid].sort_values(ascending=False)
        totals.append(len(ranked))
        ranks = {t: i for i, t in enumerate(ranked.index, 1)}
        for t in out:
            r = ranks.get(t)
            out[t]['r'].append(r)
            out[t]['c'].append(round(float(cv[t]), 4) if r else None)
            out[t]['v'].append(round(float(rv[t]), 4) if r else None)

    # Aktien ohne jeden Rang weglassen
    out = {t: v for t, v in out.items() if any(x is not None for x in v['r'])}
    print(f"  {len(out)} Aktien · {len(dates)} Wochen · letzter Stand {dates[-1]}")

    return {
        'index': index_name,
        'slug': slug(index_name),
        'description': INDEX_DEFS[index_name].get('description', ''),
        'generated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'dates': dates,
        'totals': totals,
        'sma_period': SMA_PERIOD,
        'top_pct': TOP_PCT,
        'tickers': out,
    }


def build_prices(names):
    """Schreibt docs/data/prices.json mit dem letzten Tagesschlusskurs je Aktie.

    Reine Anzeigegroesse. Schlaegt ein Index fehl, bleiben seine bisherigen
    Kurse aus der alten Datei erhalten.
    """
    path = OUT / 'prices.json'
    prices = {}
    if path.exists():
        try:
            prices = json.loads(path.read_text(encoding='utf-8')).get('prices', {})
        except Exception:
            prices = {}

    ok, failed = [], []
    for name in names:
        if name not in INDEX_DEFS:
            continue
        print(f"\n[Kurse {name}]")
        try:
            tickers, _ = fetch_index_tickers(name)
            if not tickers:
                raise RuntimeError("Keine Ticker gefunden.")
            # fill=False: jeder Kurs behaelt das Datum, an dem er wirklich entstand
            close = close_frame(download_daily(tickers), tickers, fill=False)
            n, tage = 0, set()
            for t in close.columns:
                col = close[t].dropna()
                if col.empty:
                    continue
                prices[t] = [round(float(col.iloc[-1]), 4), col.index[-1].strftime('%Y-%m-%d')]
                tage.add(prices[t][1])
                n += 1
            if n == 0:
                raise RuntimeError("Keine Kurse in der Antwort.")
            print(f"  {n} Kurse, letzter Handelstag {max(tage)}"
                  + (f" (abweichend bei einzelnen Werten, frueheste: {min(tage)})" if len(tage) > 1 else ""))
            ok.append(name)
        except Exception as e:
            print(f"  FEHLER: {e}")
            failed.append(name)

    if not prices:
        print("\nKeine Kurse erhalten - prices.json bleibt unveraendert.")
        return 1

    path.write_text(json.dumps({
        'generated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'prices': prices,
    }, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
    print(f"\nKurse geschrieben: {len(prices)} Aktien ({path.stat().st_size / 1024:.0f} KB)"
          + (f", fehlgeschlagen: {', '.join(failed)}" if failed else "."))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', action='append', help="nur diese Indizes (mehrfach möglich)")
    ap.add_argument('--weeks', type=int, default=WEEKS_DEFAULT)
    ap.add_argument('--prices-only', action='store_true',
                    help="nur die Tagesschlusskurse auffrischen, Raenge unveraendert lassen")
    args = ap.parse_args()

    names = args.index or list(INDEX_DEFS.keys())
    OUT.mkdir(parents=True, exist_ok=True)

    if args.prices_only:
        return build_prices(names)

    entries, failed = [], []

    for name in names:
        if name not in INDEX_DEFS:
            print(f"Unbekannter Index: {name}"); failed.append(name); continue
        path = OUT / f"{slug(name)}.json"
        try:
            data = build_index(name, args.weeks)
            path.write_text(json.dumps(data, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
            print(f"  geschrieben: {path.name} ({path.stat().st_size / 1024:.0f} KB)")
        except Exception as e:
            print(f"  FEHLER: {e}")
            failed.append(name)
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding='utf-8'))   # alte Daten behalten
            print("  behalte die bisherige Datei")
        entries.append({'name': data['index'], 'slug': data['slug'], 'description': data['description'],
                        'date': data['dates'][-1], 'stocks': data['totals'][-1],
                        'weeks': len(data['dates']), 'generated': data['generated']})

    if not entries:
        print("\nKeine Daten erzeugt — Manifest bleibt unverändert.")
        return 1

    (OUT / 'manifest.json').write_text(json.dumps({
        'generated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'sma_period': SMA_PERIOD, 'top_pct': TOP_PCT, 'indices': entries,
    }, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')

    print(f"\nFertig. {len(entries)} Indizes im Manifest" + (f", fehlgeschlagen: {', '.join(failed)}" if failed else "."))

    # Aktuelle Tagesschlusskurse gleich mitnehmen (reine Anzeige)
    try:
        build_prices(names)
    except Exception as e:
        print(f"Kurse konnten nicht aktualisiert werden: {e}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
