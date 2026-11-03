# RSL-Ranking – Projektkontext

Repo: https://github.com/Montimoor/RSL-Ranking · Website: https://montimoor.github.io/RSL-Ranking/

## Zweck
Öffentliche, kostenlose RSL-Ranglisten-Website (Relative Stärke nach Levy). Sie zeigt nur Ranglisten, kein Portfolio und keine Trades. Es gibt keinen Server: GitHub Actions rechnet, und GitHub Pages zeigt `docs/` an. Einen Besucherzähler soll es nicht geben. Suchmaschinen werden über `robots.txt` und `noindex` ferngehalten.

## Arbeitsweise mit Nico
- Antworten auf Deutsch, knapp und strukturiert.
- **Vor dem Coden offene Punkte als Fragen stellen und nachfragen, ob er bereit ist.** Er will oft noch Ideen ergänzen.
- Änderungen über einen Branch und einen Pull Request, nicht direkt auf `main`.
- Vor jedem Arbeiten zuerst `git pull`: Der Bot committet Mo–Sa neue Daten, sonst gibt es Konflikte.

## Aufbau
| Datei | Inhalt |
|---|---|
| `.github/workflows/rsl.yml` | Zeitplan `cron: '23 4 * * 1-6'` (GitHub startet oft Stunden später). Montags `voll` (neue Wochenrangliste), Di–Sa `kurse` (nur Tagesschlusskurse, `--prices-only`). Manuell startbar mit `auto`/`voll`/`kurse`. Der Bot committet nur `docs/data`. |
| `scripts/build_rankings.py` | Ablauf: Ticker holen → 5 Jahre Wochenkurse von yfinance (`HISTORY_PERIOD = "5y"`) → RSL → Ranglisten-JSON, Markt-RSL, Marktbreite, 5-Jahres-Rendite (`g5`), Wochenenddaten |
| `scripts/rsl_core.py` | Aus der Desktop-Version (`rsl_gui.py`) übernommen. `build_rankings.py` nutzt davon nur `SMA_PERIOD`, `MIN_PERIODS`, `TOP_PCT`, `INDEX_DEFS`, `fetch_index_tickers` (inkl. `_wiki_sp500`) und `ticker_name`. Ungenutzt sind `RSLDatabase` (SQLite/Trades), `calculate_rsl_update`, `generate_html_report`, `SELL_THR`, `C` und `SECTOR_COLORS`. |
| `docs/index.html` | Die Website, ca. 720 Zeilen, eine Datei |
| `docs/data/` | Je Index `<slug>.json` (kurz, wird beim Öffnen geladen) und `<slug>-lang.json` (volle Historie), dazu `manifest.json` und `prices.json` |

## Fachlogik (Ist-Stand)
- Wochenkurse mit `auto_adjust` (dividenden- und splitbereinigt).
- Angefangene Kerzen werden verworfen: Eine Wochenkerze zählt erst ab Samstag 00:00 UTC nach ihrem Montag (`nur_fertige_wochen`, gilt auch für den Markt-RSL), Tageskerzen nur vor dem heutigen UTC-Datum (`nur_fertige_tage`).
- RSL = Kurs / SMA(26 Wochen), `MIN_PERIODS = 21`.
- Wochen, in denen weniger als 50 % der Aktien einen RSL haben, werden verworfen. Gerankt wird nur bei 0 < RSL < 10.
- Kaufzone `TOP_PCT = 0.25` (obere 25 %).
- Yahoo datiert Wochenkerzen auf den Montag. `week_end_dates()` bestimmt über ein Kalendersymbol je Markt den echten letzten Handelstag (`enddates`). Kalendersymbole: `^GSPC`, `^GDAXI` (für DAX, MDAX und TecDAX), `^N225`, `^KS11`.
- Markt-RSL (Index / SMA26) und Marktbreite (Anteil der Aktien mit RSL > 1) dienen nur der Anzeige und fließen nicht ins Ranking ein.
- Ticker-Quellen (`fetch_tickers`): zuerst die Online-Quelle. Liegt das Ergebnis unter `WIKI_MIN` oder tritt ein Fehler auf, greift die feste Liste in `rsl_core.py` (Stand 03.11.2026, alle Ticker bei Yahoo vorhanden).
  - **DAX, MDAX:** englische Wikipedia.
  - **TecDAX:** deutsche Wikipedia (die englische Seite hat keine Mitgliedertabelle mehr).
  - **KOSPI 200:** englische Wikipedia; Codes werden auf sechs Stellen aufgefüllt (`code_digits`).
  - **Nikkei 225:** offizielle Nikkei-Seite (`list_url`, `nikkei_tickers`), da Wikipedia keine Mitglieder mehr führt. Die Seite lehnt Abrufe ohne Zertifikatsprüfung mit 403 ab.
  - **S&P 500:** Es gibt keine feste Liste, nur einen zweiten Wikipedia-Versuch (`_wiki_sp500`). Scheitert auch dieser, bleibt die alte Datei stehen.

## Lokal testen
```
pip install -r requirements.txt
python scripts/build_rankings.py --index DAX
cd docs && python -m http.server 8000   →  http://localhost:8000
```

## Umgebung (Windows-PC)
- Repo liegt in `C:\Trading\RSL-Ranking`. Git 2.56 und GitHub CLI sind installiert, `gh` ist als Montimoor angemeldet (seit 03.11.2026).
- Python 3.12 (`py -3`). Für dieses Projekt gibt es noch keine `.venv`.
- Pushen, PR öffnen (`gh pr create`) und Läufe starten (`gh workflow run rsl.yml -f modus=voll|kurse`) macht Claude selbst.
- **Mergen erst nach Nicos „ok“** (`gh pr merge --merge`). Nach einem Merge, der die Rechnung ändert, einen `voll`-Lauf starten und das Ergebnis prüfen.
- Testläufe nicht auf einem Branch starten: Der Bot committet dann Daten in den Branch, und es gibt Konflikte mit `main`.
