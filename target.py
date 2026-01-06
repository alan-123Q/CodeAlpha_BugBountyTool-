debug = False
import os

PASSWORD = os.getenv("APP_PASSWORD")

if PASSWORD is None:
    raise RuntimeError("Password not set in environment variables")

ALLOWED_COMMANDS = {
    "hello": lambda: print("Hello, user!"),
    "status": lambda: print("System is running securely"),
    "exit": lambda: print("Exiting program")
}

user_input = input("Enter command: ").strip().lower()

if user_input in ALLOWED_COMMANDS:
    ALLOWED_COMMANDS[user_input]()
else:
    print("Invalid command")