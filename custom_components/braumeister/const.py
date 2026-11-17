"""Konstanten der Braumeister-Integration."""

DOMAIN = "braumeister"
DEFAULT_PORT = 8080
SCAN_INTERVAL_SECONDS = 5
PLATFORMS = ["sensor", "binary_sensor", "switch", "number", "button", "camera"]

# Zustandsnamen des Braumeisters (wie server/device/states.js)
DEVICE_STATES = [
    "Disconnected", "Idle", "Finished", "Completed", "AboutToBrewStart", "AboutToStartBrewing",
    "PumpVentilation", "HeatingUpMashing", "HeatedUpMashing", "MaltInsertBreak", "HeatingUpRest",
    "HeatedUpRest", "Resting", "RestFinished", "TakeOutMalt", "HeatingUpHop", "HeatedUpHop",
    "HopCooking", "AddHop", "Cooling", "Mashing", "Lautering", "Boiling", "AboutToAbort",
    "Manual", "Fermenting",
]
