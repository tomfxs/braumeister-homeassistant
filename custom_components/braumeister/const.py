"""Konstanten der Braumeister-Integration."""

DOMAIN = "braumeister"
DEFAULT_PORT = 8080

CONF_MODE = "mode"
CONF_DEVICE = "device"
MODE_DASHBOARD = "dashboard"      # über das lokale Braumeister-Dashboard
MODE_DIRECT = "direct"            # direkt über My-Speidel, ohne Dashboard
SCAN_INTERVAL_SECONDS = 5
PLATFORMS = ["sensor", "binary_sensor", "switch", "number", "button"]

# Zustandsnamen des Braumeisters (wie server/device/states.js)
DEVICE_STATES = [
    "Disconnected", "Idle", "Finished", "Completed", "AboutToBrewStart", "AboutToStartBrewing",
    "PumpVentilation", "HeatingUpMashing", "HeatedUpMashing", "MaltInsertBreak", "HeatingUpRest",
    "HeatedUpRest", "Resting", "RestFinished", "TakeOutMalt", "HeatingUpHop", "HeatedUpHop",
    "HopCooking", "AddHop", "Cooling", "Mashing", "Lautering", "Boiling", "AboutToAbort",
    "Manual", "Fermenting",
]
