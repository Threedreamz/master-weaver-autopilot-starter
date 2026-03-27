# Leitfaden CT — WinWerth Scan Workflow

> Source: Leitfaden CT.pdf (internal Werth documentation)
> This is the primary workflow AutoPilot must automate end-to-end.

## Overview: 7-Step CT Scan Pipeline

```
1. Sensor Selection → 2. Size Profile → 3. CT Tab Parameters →
4. Tube On → 5. Position Check → 6. Scan (Messen) →
7. STL Export (Kontur → VxVol → Speichern)
```

---

## Step 1: CT-Sensor Auswahl (Sensor Selection)

- Select the **CT-Sensor** from the sensor toolbar (top icons)
- Click the button again to open **"Vergrößerungseinstellungen"** (magnification settings) window

### Size Profiles (Startsize)
| Profile | Use Case |
|---------|----------|
| **Size_120_L** | Large parts |
| **Size_100_L** | Medium parts (default) |
| **Size_50_L** | Small/detailed parts |

Other available: Size_025_L_Ref, Size_016_L, Size_010_L, Size_090_L_Wrm, Size_120_XL, Size_100_XL, Size_050_XL, Size_025_XL, Size_016_XL, Size_010_XL, Size_090_XL_Wrm

### Magnification Window Fields
- Durchmesser (mm): e.g. 99.2
- Höhe (mm): e.g. 77.8
- Voxelgröße (µm): e.g. 69.8
- Fokus-Detektor Abstand (mm): e.g. 521.9
- Kegelstrahlwinkel (°): e.g. 15.0
- Intensitätsfaktor: e.g. 1.0
- Binning / Stufe: L
- Stufenlos checkbox
- "aus Position berechnen" checkbox

Click **"Schließen"** to close.

---

## Step 2: CT-Reiter öffnen (Switch to CT Tab)

After magnification selection, click the **CT** tab in the Status panel.

Status panel shows:
- Röhrenbe... (Tube status)
- Bilddynamik (Image dynamics)
- CT-Durchmesser
- Voxelgröße (µm)
- Interlock (green = OK)
- Vakuum (green = OK)

---

## Step 3: Scan-Parameter einstellen (Configure Parameters)

### 3.1 Default values for plastic parts (Kunststoffteile)

| Parameter | Default Value |
|-----------|---------------|
| Spannung (kV) | Soll **120** |
| Generatorstrom (µA) | Soll **200** |
| Generatorleistung (W) | 32.0 / 0.0 |
| Integrationszeit (ms) | **150** |
| Bildqualität | **3** |
| Bilder Ignorieren | 0 |
| Drehschritte | **400** / Auto |
| Tomografieoptionen | Volle Umdrehung |

### 3.2 "On the Fly" aktivieren
- Check **"On the Fly"** checkbox (under Tomografieoptionen)
- Only disable if Y-axis rastering is needed

### 3.3 Hell-/Dunkelkorrektur
- Set to **"Letzte verwenden"** (use last)
- If needed, perform a fresh Hell-/Dunkelabgleich first

### 3.4 Additional settings
- Ausschnitt-Tomografie (ROI): aktiv checkbox
- Exzentrische Tomografie: aktiv checkbox + Mittelpunkt
- Aufwärmphase / Abschnittstomografie / Driftkorrektur: as needed
- Detektorbereich: **voll**
- Fokusgröße: **Minimal** (default) or Automatisch
- Rekonstruktion Ausgabe: **Standard**
- Pfad: `F:\21-00364\TomoScope`
- Projektionsbilder sichern: checked
- Offline: unchecked
- Messzeitschätzung: shows estimated time (e.g. 00h 04m)

### 3.5 Actions
- Aktion bei Einlernen: **tomografieren**
- Aktion bei Abarbeitung: **tomografieren**

---

## Step 4: Röhre aktivieren (Activate Tube)

1. **Position workpiece** on turntable (Drehteller)
2. **Adjust height** roughly
3. **Verify door is closed** (Interlock must be green)
4. Click **"Röhre an"** button
5. Workpiece should appear on image processor

---

## Step 5: Positionierung prüfen (Check Position)

1. Fine-tune workpiece position (X-axis / height)
2. Use **Joystick for rotation axis (A)** to verify:
   - Workpiece stays in frame during full rotation
   - **Bilddynamik between 20 and 220** (critical!)
3. Adjust Spannung/Strom if dynamics out of range

---

## Step 6: Scan starten (Start Scan)

1. Click **"Messen"** button (top-right of measurement toolbar)
2. Scan runs automatically
3. Wait for completion (time shown in Messzeitschätzung)

### Measurement Toolbar
```
Datei: C:\Werth\User\DMIS\new program.dms
[Play] [Pause] [Stop] [Hand] [Forward] [Forward+] [Return]
Löschen | Papierkorb | D/R | Kreispunkt | 1. Ergebnis | ... | [Messen]
Name | SYM | Istwert | Sollwert | OTol | UTol | Abweich | Grafik | Bezeichnung
```

---

## Step 7: STL Export

### 7.1 Switch to Rechensensor (Computation Sensor)
- Click the computation sensor icon in toolbar

### 7.2 Create STL Contour
1. Click **"KONTUR"** button
2. Select **"STL aus Voxelvolumen"** (STL from voxel volume)
3. In **Merkmalsbaum** (feature tree), select **VxVol** entry (e.g. VxVol_2)
4. Click **"Messen"** → STL contour is generated

### 7.3 Save STL File
1. Select the STL contour in feature tree (e.g. R_Kont_2)
2. Menu: **Grafik3D → Speichern unter**
3. Set **Dateityp**: "STL Dateien (*.stl)"
4. Enter **Dateiname** (e.g. "Scan")
5. Set **Dateimodus**: überschreiben (overwrite)
6. Choose **Speicherort** (save location)
7. Current default path: `Y:\3D-Druck_CT\Auftäge-2023`

---

## AutoPilot Automation Mapping

| Step | WinWerth UI Action | AutoPilot Module | Status |
|------|-------------------|------------------|--------|
| 1 | Sensor selection + Size profile | `source/libs/pywinauto/profile/` | Exists |
| 2 | CT tab click | `source/libs/pywinauto/tabcontrol/` | Exists |
| 3.1 | Parameter entry | `source/libs/pywinauto/textbox/` + `combobox/` | Exists |
| 3.2 | On the Fly checkbox | `source/libs/pywinauto/checkbox/` | Exists |
| 3.3 | Hell/Dunkelkorrektur dropdown | `source/libs/pywinauto/combobox/` | Exists |
| 4 | Röhre an button | `source/libs/pywinauto/rohr/` | Exists |
| 5 | Rotation check + dynamics | `source/libs/drehen/` + `monitor/` | Exists |
| 6 | Messen button | `source/libs/pywinauto/button/` | Exists |
| 7.1 | Sensor switch | `source/libs/pywinauto/button/` | Exists |
| 7.2 | Kontur + VxVol + Messen | `source/libs/pywinauto/treeview/` + `button/` | Exists |
| 7.3 | Grafik3D → Save STL | `source/libs/pywinauto/topMenu/` + `childWindow/SaveFileDialog/` | Exists |

**All 7 steps have corresponding pywinauto modules in the trello_era source.**
