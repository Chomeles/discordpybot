Hier ist eine Beispiel-README-Datei für GitHub, die die Installation, Einrichtung und Nutzung deines Discord-Bots beschreibt:

```markdown
# Discord Bot

Ein einfacher Discord-Bot, der verschiedene Befehle wie `!join`, `!work`, `!steal`, `!wheel`, `!daily`, `!balance`, `!levelup` und `!level` bietet. Dieser Bot nutzt `discord.py` und `aiosqlite` zur Interaktion mit Discord und zur Speicherung von Daten in einer SQLite-Datenbank.

## Voraussetzungen

Stelle sicher, dass die folgenden Anforderungen erfüllt sind, bevor du den Bot installierst:

- Python 3.7 oder höher
- Git (für das Klonen des Repositories)
- Ein aktiver Discord-Account und ein erstellter Bot über das [Discord Developer Portal](https://discord.com/developers/applications)

## Installation

1. **Klone das Repository:**

   ```bash
   git clone https://github.com/deinbenutzername/dein-repo-name.git
   cd dein-repo-name
   ```

2. **Erstelle ein virtuelles Environment:**

   ```bash
   python3 -m venv discord-bot-env
   ```

3. **Aktiviere das virtuelle Environment:**

   - **Auf macOS/Linux:**

     ```bash
     source discord-bot-env/bin/activate
     ```

   - **Auf Windows:**

     ```bash
     discord-bot-env\Scripts\activate
     ```

4. **Installiere die Abhängigkeiten:**

   ```bash
   pip install -r requirements.txt
   ```

   Falls die `requirements.txt` nicht vorhanden ist, kannst du die benötigten Pakete manuell installieren:

   ```bash
   pip install aiosqlite discord.py
   ```

5. **Bot-Token einfügen:**

   Öffne die Datei `bot2.py` und füge deinen Discord-Bot-Token im `bot.run()`-Befehl ein:

   ```python
   bot.run('DEIN_DISCORD_BOT_TOKEN')
   ```

   **Sicherheitshinweis:** Es wird empfohlen, den Token in einer Umgebungsvariable zu speichern und aus dieser im Code zu laden, um ihn nicht im Quellcode zu veröffentlichen.

## Nutzung

1. **Starte den Bot:**

   Stelle sicher, dass du im Verzeichnis deines Bots bist und das virtuelle Environment aktiviert ist.

   ```bash
   python bot2.py
   ```

2. **Verfügbare Befehle:**

   - `!join`: Tritt dem Spiel bei.
   - `!work`: Arbeite, um Geld zu verdienen.
   - `!steal @Benutzer`: Versuche, von einem anderen Spieler zu stehlen.
   - `!wheel <Einsatz>`: Drehe das Glücksrad mit einem Einsatz für eine Chance auf einen Gewinn.
   - `!daily`: Erhalte deine tägliche Belohnung (einmal alle 24 Stunden).
   - `!balance` oder `!bal`: Zeigt dein aktuelles Guthaben an.
   - `!levelup`: Lerne, um XP zu verdienen und im Level aufzusteigen.
   - `!level`: Zeigt dein aktuelles Level und deine XP an.

3. **Bot auf einem Server hinzufügen:**

   Erstelle eine Einladung für deinen Bot, indem du die Client-ID des Bots in die folgende URL einfügst:

   ```
   https://discord.com/oauth2/authorize?client_id=DEINE_CLIENT_ID&scope=bot&permissions=8
   ```

   Ersetze `DEINE_CLIENT_ID` durch die tatsächliche Client-ID deines Bots.

## Fehlersuche

### Häufige Fehler:

- **ModuleNotFoundError**: Wenn ein Modul wie `aiosqlite` oder `discord.py` nicht gefunden wird, stelle sicher, dass du das virtuelle Environment aktiviert und alle Abhängigkeiten installiert hast.

- **Bot startet nicht**: Überprüfe, ob der Bot-Token korrekt eingefügt wurde und der Bot die erforderlichen Berechtigungen auf dem Discord-Server hat.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Weitere Informationen findest du in der `LICENSE`-Datei.

---

Erstellt von [deinbenutzername](https://github.com/deinbenutzername)
```

### Schritte zur Verwendung der README

1. **Anpassen der Platzhalter:**
   - Ersetze `deinbenutzername`, `dein-repo-name`, `DEIN_DISCORD_BOT_TOKEN`, und `DEINE_CLIENT_ID` durch die tatsächlichen Werte.
   
2. **`requirements.txt` erstellen (optional):**
   - Falls noch nicht vorhanden, erstelle eine `requirements.txt`, indem du die installierten Pakete in deinem virtuellen Environment speicherst:
     ```bash
     pip freeze > requirements.txt
     ```

3. **Hochladen auf GitHub:**
   - Lade die README-Datei zusammen mit deinem Code in dein GitHub-Repository hoch.

Damit hast du eine gut strukturierte Anleitung zur Installation und Nutzung deines Discord-Bots auf GitHub. Wenn du weitere Anpassungen benötigst, lass es mich wissen!
