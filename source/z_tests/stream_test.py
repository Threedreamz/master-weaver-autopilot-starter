from app.runner import start_stream, end_stream, getMin, resetMin






# 1) Blockierend starten (wie früher run_app):
start_stream(block=True)
# -> Mit 'q' oder ESC beenden

# 2) Alternativ: nicht-blockierend starten
start_stream()
# ... eigene Logik ...
print(getMin())   # {'top': 12, 'bottom': 45, 'left': 23, 'right': 31} (Beispiel)
resetMin()        # Session-Minima zurücksetzen
end_stream()      # sauber stoppen
