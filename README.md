# RSL Ranking — Anleitung für GitHub

Die Seite besteht aus drei Teilen: einem Python-Skript, das die Ranglisten berechnet, einem Zeitplan bei GitHub, der es jeden Montag startet, und einer HTML-Seite, die die Ergebnisse anzeigt. Es läuft kein Server, und es fallen keine Kosten an.

## Was in das Projekt gehört

```
requirements.txt
.github/workflows/rsl.yml      Zeitplan: montags automatisch
scripts/build_rankings.py      berechnet die Ranglisten
scripts/rsl_core.py            Indexlisten und RSL-Logik
docs/index.html                die Website
docs/robots.txt                hält Suchmaschinen fern
docs/data/                     hier landen die Ranglisten (anfangs leer)
```

---

## Schritt 1: GitHub-Konto

Falls noch nicht vorhanden, auf `github.com` registrieren. Kostenlos, es reicht eine E-Mail-Adresse.

## Schritt 2: Repository anlegen

Oben rechts auf **+** → **New repository**.

- **Repository name:** zum Beispiel `rsl-ranking`. Der Name steht später in der Adresse.
- **Public** auswählen. Bei privaten Projekten kostet GitHub Pages Geld. Deine Trades kommen hier ohnehin nicht hinein.
- Bei „Initialize this repository" nichts anhaken.
- **Create repository**.

## Schritt 3: Dateien hochladen

Im neuen Repository auf **Add file** → **Upload files**.

Ziehe die Ordner `docs` und `scripts` sowie die Datei `requirements.txt` in das Browserfenster. Die Ordnerstruktur bleibt dabei erhalten. Unten auf **Commit changes**.

Den Ordner `.github` lädst du besser von Hand an, weil Ordner mit einem Punkt am Anfang je nach System ausgeblendet werden:

1. **Add file** → **Create new file**.
2. Als Dateinamen exakt `.github/workflows/rsl.yml` eintippen. Sobald du die Schrägstriche tippst, legt GitHub die Ordner automatisch an.
3. Den Inhalt aus der mitgelieferten `rsl.yml` hineinkopieren.
4. **Commit changes**.

## Schritt 4: Schreibrechte für den Automatismus

Der Zeitplan muss die berechneten Ranglisten ins Projekt zurückschreiben dürfen.

**Settings** → links **Actions** → **General** → nach unten scrollen zu **Workflow permissions** → **Read and write permissions** auswählen → **Save**.

Ohne diesen Schritt läuft die Berechnung durch, das Speichern schlägt aber mit einem Berechtigungsfehler fehl.

## Schritt 5: Website aktivieren

**Settings** → links **Pages**.

- **Source:** „Deploy from a branch"
- **Branch:** `main`, Ordner **`/docs`**
- **Save**

Oben erscheint danach deine Adresse, etwa `https://deinname.github.io/rsl-ranking/`.

## Schritt 6: Ersten Lauf starten

Reiter **Actions**. Falls GitHub fragt, ob Workflows aktiviert werden sollen, bestätigen.

Links **RSL Ranglisten** anklicken → rechts **Run workflow** → grünen Knopf **Run workflow** drücken.

Der Lauf dauert je nach Index 3 bis 10 Minuten, der S&P 500 am längsten. Ein grüner Haken bedeutet: fertig. Danach liegen in `docs/data` die JSON-Dateien.

## Schritt 7: Seite öffnen

Rufe `https://deinname.github.io/rsl-ranking/` auf. Nach dem allerersten Aktivieren von Pages kann es ein paar Minuten dauern, bis die Adresse antwortet.

Am Handy im Browser öffnen und **Zum Startbildschirm hinzufügen** wählen. Die Seite verhält sich dann wie eine App und lädt die Daten beim Öffnen neu.

Ab jetzt läuft alles von allein: Jeden Montag um 06:00 UTC, also 08:00 deutscher Sommerzeit und 07:00 im Winter, rechnet GitHub neu und aktualisiert die Seite.

---

## Wenn etwas nicht klappt

**Roter Punkt im Actions-Tab.** Lauf anklicken, dann den fehlgeschlagenen Schritt aufklappen. Die letzten Zeilen nennen den Grund. Bei einem Berechtigungsfehler fehlt Schritt 4.

**Yahoo blockt den Lauf.** Das Skript versucht es dreimal. Scheitert ein Index trotzdem, bleiben seine Daten aus der Vorwoche stehen, und die anderen Indizes werden normal aktualisiert. Ein manueller Neustart über **Run workflow** hilft meist.

**Seite zeigt „Keine Daten gefunden".** Dann war noch kein erfolgreicher Lauf da. Prüfe, ob in `docs/data` JSON-Dateien liegen.

**404 auf der Adresse.** In Settings → Pages prüfen, ob Branch `main` und Ordner `/docs` eingestellt sind.

**GitHub schickt eine E-Mail bei Fehlern.** Schlägt ein Lauf fehl, wirst du automatisch benachrichtigt.

---

## Gut zu wissen

- **Kosten:** Für öffentliche Projekte sind GitHub Actions und Pages unbegrenzt kostenlos.
- **Ruhende Projekte:** Geplante Abläufe werden nach 60 Tagen ohne Aktivität abgeschaltet. Da jeder Montagslauf etwas speichert, passiert das hier nicht.
- **Verzögerung:** Der Startzeitpunkt kann sich bei GitHub um einige Minuten bis Stunden verschieben. Für Wochendaten ist das ohne Bedeutung.
- **Sichtbarkeit:** Die Seite ist für jeden erreichbar, der die Adresse kennt. Suchmaschinen werden durch `robots.txt` und ein `noindex` ferngehalten, ein Schutz gegen gezielte Zugriffe ist das aber nicht.

## Anpassen

- **Andere Indizes:** In `scripts/rsl_core.py` stehen die Ticker-Listen und `INDEX_DEFS`.
- **Kaufzone:** `TOP_PCT` in `scripts/rsl_core.py`, aktuell 0.25 für die oberen 25 %.
- **Mehr Historie:** In `.github/workflows/rsl.yml` den Aufruf zu `python scripts/build_rankings.py --weeks 104` ändern. Zwei Jahre sind das Maximum, weil so viel von Yahoo geladen wird.
- **Lokal testen:** `pip install -r requirements.txt`, dann `python scripts/build_rankings.py --index DAX`. Danach im Ordner `docs` ein `python -m http.server 8000` starten und `http://localhost:8000` öffnen.
