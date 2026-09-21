import os
import re
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.android import adb, device_is_connected
from src.contacts import load_contacts

# ---------------- SETTINGS ----------------
CONTACTS_FILE = PROJECT_ROOT / "data/contacts.csv"

AUDIO = PROJECT_ROOT / "assets/audio/voice.mp3"  # file on your laptop
PHONE_AUDIO = "/sdcard/Music/voice.mp3" # where it is copied on the phone

PLAY_ON_PHONE = True    # True  = play from phone (needs speakerphone ON)
                        # False = play from laptop speakers

SPEAKER_TAP = None      # optional, e.g. (540, 1500) to tap the speaker button
                        # find coordinates with: adb shell uiautomator dump

RING_TIMEOUT = 45       # max seconds to wait for the person to answer
MAX_PLAY = 30           # audio duration cap in seconds
GAP_BETWEEN_CALLS = 3   # seconds between calls
# ------------------------------------------

def call_state():
    """Returns 'ACTIVE' (answered), 'DIALING' (ringing) or 'IDLE' (no call)."""
    if "state=ACTIVE" in adb("dumpsys", "telecom"):
        return "ACTIVE"
    states = re.findall(r"mCallState=(\d)", adb("dumpsys", "telephony.registry"))
    if states and all(s == "0" for s in states):
        return "IDLE"
    return "DIALING"


def wait_for_answer():
    """True if answered, False if rejected / failed / timed out."""
    start = time.time()
    while time.time() - start < RING_TIMEOUT:
        s = call_state()
        if s == "ACTIVE":
            return True
        if s == "IDLE" and time.time() - start > 4:
            return False
        time.sleep(1)
    return False


def play_from_phone():
    adb("am", "start", "-a", "android.intent.action.VIEW",
        "-d", f"file://{PHONE_AUDIO}", "-t", "audio/mpeg")
    t0 = time.time()
    while time.time() - t0 < MAX_PLAY:
        if call_state() == "IDLE":
            print("  they hung up early")
            break
        time.sleep(1)
    adb("input", "keyevent", "KEYCODE_MEDIA_STOP")


def play_from_laptop():
    player = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
         "-t", str(MAX_PLAY), AUDIO])
    while player.poll() is None:
        if call_state() == "IDLE":
            player.terminate()
            print("  they hung up early")
            break
        time.sleep(1)


def hang_up():
    adb("input", "keyevent", "KEYCODE_ENDCALL")


def tap_speaker():
    """Find the 'Speaker' button on the in-call screen and tap it.
    Only call this once per call, because tapping again turns it off."""
    adb("uiautomator", "dump", "/sdcard/ui.xml")
    xml = adb("cat", "/sdcard/ui.xml")
    for node in re.findall(r"<node [^>]*>", xml):
        if re.search(r'(text|content-desc)="[^"]*speaker[^"]*"', node, re.I):
            m = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
            if m:
                x1, y1, x2, y2 = map(int, m.groups())
                adb("input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
                return True
    return False


def main():
    # check that the phone is connected
    if not device_is_connected():
        print("Phone not connected. Run 'adb devices' and allow USB debugging.")
        sys.exit(1)

    if not os.path.exists(AUDIO):
        print(f"Audio file '{AUDIO}' not found. Check the AUDIO setting.")
        sys.exit(1)

    try:
        numbers = [contact.number for contact in load_contacts(CONTACTS_FILE)]
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(error)
        sys.exit(1)

    if PLAY_ON_PHONE:
        print("Copying audio to phone...")
        r = subprocess.run(["adb", "push", AUDIO, PHONE_AUDIO],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("Could not copy audio to phone:", r.stderr.strip())
            sys.exit(1)

    results = []
    try:
        for i, n in enumerate(numbers, 1):
            print(f"[{i}/{len(numbers)}] Calling {n}...")
            adb("am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{n}")
            time.sleep(2)

            if wait_for_answer():
                print("  answered, playing audio")
                time.sleep(1)
                if SPEAKER_TAP:
                    adb("input", "tap", str(SPEAKER_TAP[0]), str(SPEAKER_TAP[1]))
                elif not tap_speaker():
                    print("  could not find the speaker button, turn it on manually")
                time.sleep(1)
                if PLAY_ON_PHONE:
                    play_from_phone()
                else:
                    play_from_laptop()
                results.append((n, "answered"))
            else:
                print("  not answered, skipping")
                results.append((n, "not answered"))

            hang_up()
            time.sleep(GAP_BETWEEN_CALLS)

    except KeyboardInterrupt:
        print("\nStopped by user.")
        hang_up()

    print("\nSummary:")
    for n, r in results:
        print(f"  {n}: {r}")
    print("All done.")


if __name__ == "__main__":
    main()
    sys.exit(0)
