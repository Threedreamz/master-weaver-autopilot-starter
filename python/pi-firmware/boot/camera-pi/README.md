# Kamera-Pi — Flashen & Inbetriebnahme

Anleitung fuer den Kamera-Pi (Pi 5), der **im CT-Scanner auf einer Powerbank** laeuft und sich als WiFi-Client mit dem Haupt-Pi verbindet.

## Architektur

```
                    WiFi "AutoPilot-CT"
  [Haupt-Pi]  ←─────────────────────────→  [Kamera-Pi]
  192.168.4.1                               192.168.4.x (DHCP)
  AP-Modus                                  Client-Modus
  Port 4800 (iPad)                          Port 4811 (Kamera)
  Port 4801 (Kamera lokal)
  Port 4804 (Setup Portal)
```

## SD-Karte flashen

### 1. Pi OS Lite flashen

Mit dem [Raspberry Pi Imager](https://www.raspberrypi.com/software/):

- **OS**: Raspberry Pi OS Lite (64-bit) — kein Desktop noetig
- **Speicher**: microSD (mindestens 16 GB, Class 10)
- **Einstellungen** (Zahnrad-Icon im Imager):
  - Hostname: `autopilot-cam`
  - SSH aktivieren: Ja (Passwort-Authentifizierung)
  - Benutzername: `pi`
  - Passwort: (eigenes Passwort waehlen)
  - WiFi NICHT konfigurieren (macht firstrun.sh)
  - Locale: `Europe/Berlin`, Tastatur: `de`

### 2. Boot-Dateien kopieren

Nach dem Flashen die SD-Karte nochmal einlegen. Die `boot`-Partition erscheint als Laufwerk.

```bash
# Alle Dateien aus camera-pi/ auf die Boot-Partition kopieren
cp firstrun.sh  /Volumes/bootfs/
cp setup.sh     /Volumes/bootfs/
cp power-save.sh /Volumes/bootfs/
cp autopilot-cam.service /Volumes/bootfs/
```

> **macOS**: Die Boot-Partition heisst `bootfs`
> **Windows**: Erscheint als eigenes Laufwerk (z.B. `D:\`)
> **Linux**: Mounten mit `mount /dev/sdX1 /mnt/boot`

### 3. Firstrun in cmdline.txt eintragen

Die Datei `cmdline.txt` auf der Boot-Partition editieren. Am **Ende der ersten Zeile** (es ist alles eine Zeile!) anfuegen:

```
systemd.run=/boot/firmware/firstrun.sh systemd.run_success_action=reboot
```

> **Wichtig**: Die gesamte cmdline.txt muss EINE Zeile bleiben. Kein Zeilenumbruch!

Alternativ (wenn systemd.run nicht funktioniert) — einen `rc.local`-Eintrag erstellen:

```bash
# In /etc/rc.local vor "exit 0" einfuegen:
if [ -f /boot/firmware/firstrun.sh ]; then
  bash /boot/firmware/firstrun.sh
  mv /boot/firmware/firstrun.sh /boot/firmware/firstrun.sh.done
fi
```

## Erststart-Ablauf

1. **SD-Karte einlegen** und Pi 5 mit Strom verbinden
2. Pi bootet, fuehrt `firstrun.sh` aus:
   - Setzt Hostname auf `autopilot-cam`
   - Aktiviert SSH
   - Verbindet sich mit WiFi "AutoPilot-CT"
   - Erstellt Konfiguration in `/opt/autopilot-cam/config/`
   - Registriert sich beim Haupt-Pi (192.168.4.1)
3. Pi startet neu

## Setup ausfuehren

Per SSH verbinden (Haupt-Pi muss bereits laufen):

```bash
# Vom Haupt-Pi aus:
ssh pi@autopilot-cam.local

# Oder mit IP (der Haupt-Pi vergibt IPs ab 192.168.4.10):
ssh pi@192.168.4.10

# Setup ausfuehren:
sudo bash /boot/firmware/setup.sh

# Optional — Stromsparmodus:
sudo bash /boot/firmware/power-save.sh

# Neustart:
sudo reboot
```

## Nach dem Setup

Der Kamera-Server laeuft automatisch:

```bash
# Status pruefen
systemctl status autopilot-cam

# Logs anzeigen
journalctl -u autopilot-cam -f

# Health-Check
curl http://autopilot-cam.local:4811/health

# Vom Haupt-Pi aus:
curl http://192.168.4.x:4811/health
```

## Powerbank-Tipps

### Empfohlene Powerbanks

| Powerbank | Kapazitaet | Erwartete Laufzeit | Hinweise |
|-----------|------------|-------------------|----------|
| Anker PowerCore 10000 | 10.000 mAh | ~6-8 Std. | Kompakt, passt gut in Scanner |
| Anker PowerCore 20000 | 20.000 mAh | ~12-16 Std. | Empfehlung fuer Tagesbetrieb |
| Anker PowerCore III Elite 26800 | 26.800 mAh | ~16-20 Std. | Maximale Laufzeit |

### Wichtige Anforderungen

- **USB-C Power Delivery**: Pi 5 braucht 5V/5A (25W) — Powerbank muss PD unterstuetzen
- **Kein Auto-Off**: Manche Powerbanks schalten bei geringem Stromverbrauch ab. Pi 5 zieht im Leerlauf ~3-4W, das reicht normalerweise
- **Pass-Through Charging**: Falls die Powerbank waehrend des Ladens Strom liefern kann, laesst sich der Pi auch ohne Unterbrechung betreiben
- **Kapazitaet**: Mit `power-save.sh` verbraucht der Pi ~3-5W. Faustformel: `(mAh * 3.7V / 1000) / 5W * 0.85 = Stunden`

### Problembehebung

| Problem | Loesung |
|---------|---------|
| Pi startet nicht | Powerbank liefert nicht genug Strom — PD-faehige Powerbank verwenden |
| Powerbank schaltet ab | Pi verbraucht zu wenig — `power-save.sh` NICHT ausfuehren oder Powerbank mit niedrigem Mindestverbrauch waehlen |
| WiFi-Verbindung bricht ab | Signal zu schwach im Scanner — Antenne/Position anpassen |
| Kamera nicht erkannt | `libcamera-hello --list-cameras` ausfuehren, Flachbandkabel pruefen |
| Kamera-Server startet nicht | `journalctl -u autopilot-cam -n 50` fuer Fehlermeldungen |

## Dateien in diesem Verzeichnis

| Datei | Zweck |
|-------|-------|
| `firstrun.sh` | Erststart: WiFi-Client, Hostname, SSH, Haupt-Pi-Registrierung |
| `setup.sh` | Node.js + Kamera-Server installieren und starten |
| `power-save.sh` | Bluetooth/HDMI/LEDs aus, GPU-RAM minimal, CPU ondemand |
| `autopilot-cam.service` | Systemd-Unit fuer den Kamera-Server auf Port 4811 |
| `README.md` | Diese Anleitung |

## Unterschied zum Haupt-Pi

| | Haupt-Pi | Kamera-Pi |
|-|----------|-----------|
| WiFi | Access Point (AP) | Client |
| IP | 192.168.4.1 (statisch) | DHCP (192.168.4.x) |
| Hostname | autopilot-pi | autopilot-cam |
| Services | Nginx + PM2 + iPad + Setup + Kamera | Nur Kamera-Server |
| Port | 4800, 4801, 4804 | 4811 |
| Strom | Netzteil (permanent) | Powerbank (mobil) |
| Speicher-Limit | 1 GB | 512 MB |
