import random
import sys
import time
from pathlib import Path
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.android import adb, device_is_connected, find, tap, ui_nodes
from src.contacts import load_contacts

# ---------------- SETTINGS ----------------
# International format: country code, no "+" and no leading 0
# (Pakistan: 0336xxxxxxx -> 92336xxxxxxx)
CONTACTS_FILE = PROJECT_ROOT / "data/contacts.csv"

# {name} is replaced with each contact's name. Urdu, emoji and new lines work.
MESSAGE = "Assalam o Alaikum {name}, yeh ek test message hai."

PKG = "com.whatsapp"         # use "com.whatsapp.w4b" for WhatsApp Business
SEND_BTN = r"^send$"         # label of the send button on your phone
DELAY_MIN, DELAY_MAX = 3, 10 # random pause between messages (seconds)
# ------------------------------------------

def tap_label(pattern, tries=5, delay=1.5):
    for _ in range(tries):
        n = find(ui_nodes(), pattern)
        if n:
            tap(n)
            return True
        time.sleep(delay)
    return False


def main():
    # helper mode: print everything on the phone screen
    if len(sys.argv) > 1 and sys.argv[1] == "labels":
        for n in ui_nodes():
            if n["text"] or n["desc"]:
                print(f'text="{n["text"]}"  desc="{n["desc"]}"  at ({n["x"]},{n["y"]})')
        return

    if not device_is_connected():
        print("Phone not connected. Run 'adb devices' and allow USB debugging.")
        sys.exit(1)

    try:
        contacts = load_contacts(CONTACTS_FILE)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(error)
        sys.exit(1)

    adb("input", "keyevent", "KEYCODE_WAKEUP")
    adb("svc", "power", "stayon", "usb")      # keep the screen on while plugged in

    results = []
    try:
        for i, contact in enumerate(contacts, 1):
            number = contact.number
            name = contact.name or number
            print(f"[{i}/{len(contacts)}] Messaging {name} ({number})...")
            text = MESSAGE.format(name=name)
            url = f"whatsapp://send?phone={number}&text={quote(text, safe='')}"
            adb("am", "start", "-a", "android.intent.action.VIEW",
                "-d", f"'{url}'", "-p", PKG)
            time.sleep(3)

            if tap_label(SEND_BTN):
                print("  sent")
                results.append((number, "sent"))
                time.sleep(2)
            else:
                print("  could not find the Send button (number not on WhatsApp?)")
                results.append((number, "failed"))
                adb("input", "keyevent", "KEYCODE_BACK")

            if i < len(contacts):
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    except KeyboardInterrupt:
        print("\nStopped by user.")

    print("\nSummary:")
    for number, r in results:
        print(f"  {number}: {r}")
    print("All done.")


if __name__ == "__main__":
    main()
    sys.exit(0)
