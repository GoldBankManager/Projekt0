# Regeln für dieses Projekt

## Geld und Guthaben (gilt immer, für alle Dienste: vast.ai, fal.ai und jeden anderen bezahlten Anbieter)

- **Niemals Guthaben aufladen**, keine Zahlungsmethode hinzufügen, kein Auto-Aufladen einrichten. Auch nicht, wenn das Guthaben leer ist. Dann stoppen und Bescheid sagen.
- **Alles, was Geld kostet, nur mit ausdrücklichem OK des Nutzers für genau diese Aktion**: GPU mieten (`vast.py start`), bezahlte API-Aufrufe (z. B. `car_swap.py`), Speicher, Bandbreite usw. Vorher Preis pro Stunde bzw. pro Aufruf und das geschätzte Gesamtbudget nennen.
- Ein OK gilt nur für die genannte Aktion, nicht für spätere.
- `vast.py start -y` und `car_swap.py -y` nie ohne dieses OK benutzen.
- Laufende vast.ai-Instanzen nicht vergessen: nach der Arbeit den Status zeigen und das Zerstören anbieten.
