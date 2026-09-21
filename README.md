# Android call and WhatsApp helpers

Small Python scripts for making Android phone calls, placing WhatsApp voice calls, and sending WhatsApp messages through a USB-debugged Android device.

Use these tools only for people who have agreed to receive your calls or messages. Check local rules and WhatsApp's terms before sending anything in bulk.

## Project layout

```text
assets/audio/              Audio clips used by the call scripts
scripts/android_call.py    Regular cellular-call automation
scripts/whatsapp_call.py   WhatsApp voice-call automation
scripts/whatsapp_text.py   WhatsApp message automation
src/android.py             Shared ADB and screen/UI helpers
src/contacts.py            CSV/XLSX contact-file loader
data/contacts.example.csv  Contact-file template
```

## Requirements

- Python 3.9 or newer
- Android Platform Tools (`adb`) on your `PATH`
- An Android phone with USB debugging enabled and the debugging prompt approved
- `ffplay` on your `PATH` when playing audio from the computer
- WhatsApp installed on the phone for the WhatsApp scripts
- `openpyxl` only if using an Excel (`.xlsx`) contact file

Confirm the connection before running a script:

```bash
adb devices
```

The device must appear as `device`, not `unauthorized`.

## Configure and run

Copy the contact template, then add only contacts who expect this communication:

```bash
cp data/contacts.example.csv data/contacts.csv
```

The contact file must have a `number` column. A `name` column is optional and is used by the WhatsApp text-message template.

```csv
number,name
923001234567,Example Contact
```

All scripts read `data/contacts.csv` by default. To use an Excel file, save the same columns as `data/contacts.xlsx`, install its reader, and change `CONTACTS_FILE` in the script:

```bash
python3 -m pip install openpyxl
```

Format phone-number cells as **Text** in Excel so leading zeroes are preserved. Edit each script's settings to choose its contact file, adjust timeouts, message text, or button-label patterns for your phone.

```bash
# Standard phone call
python3 scripts/android_call.py

# WhatsApp voice call
python3 scripts/whatsapp_call.py

# WhatsApp text message
python3 scripts/whatsapp_text.py
```

Phone numbers in the WhatsApp scripts use international format without `+` or a leading zero; for example, `923001234567`.

## WhatsApp button labels

The WhatsApp scripts identify on-screen controls by their visible label. If WhatsApp has a different language, layout, or label on your device, open the relevant screen on the phone and run:

```bash
python3 scripts/whatsapp_call.py labels
python3 scripts/whatsapp_text.py labels
```

Update `VOICE_CALL_BTN`, `IN_CALL_BTN`, or `SEND_BTN` in the corresponding script with the labels printed by that command.

## Audio files

Put audio clips in [`assets/audio`](assets/audio). The included scripts now default to `voice.mp3`; change their `AUDIO` setting to use another file. `android_call.py` can either copy and play audio on the phone (`PLAY_ON_PHONE = True`) or play it through the computer with `ffplay`.

## Notes

- Keep the phone unlocked while testing; the scripts wake the screen but cannot bypass a lock screen.
- UI automation can break when Android or WhatsApp changes its interface. Use `labels` mode to recalibrate it.
- Stop a running script with `Ctrl+C`; the call scripts then try to end the active call.
