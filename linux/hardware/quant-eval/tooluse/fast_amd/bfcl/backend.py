"""Backend registry for the eight environments in the source snapshot."""

CLASS_FILES = {
    "GorillaFileSystem": "gorilla_file_system",
    "MathAPI": "math_api",
    "MessageAPI": "message_api",
    "TwitterAPI": "posting_api",
    "TicketAPI": "ticket_api",
    "TradingBot": "trading_bot",
    "TravelAPI": "travel_booking",
    "VehicleControlAPI": "vehicle_control",
}
CLASS_FILE_PATH_MAPPING = {
    name: f"fast_amd.bfcl.environments.{module}" for name, module in CLASS_FILES.items()
}
STATELESS_CLASSES = {"MathAPI"}
