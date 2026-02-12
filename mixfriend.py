#!/usr/bin/env python3
"""Generate Logic Pro X Channel EQ preset files (.pst) for device speaker simulation."""

import argparse
import json
import struct
import os
import sys

# --- Binary format constants ---

HEADER = struct.pack(
    "<III8sI",
    240,            # file size
    1,              # version
    52,             # unknown field
    b"GAMETSPP",    # magic
    236,            # data size
)

# 88-byte footer (analyzer settings, output gain, etc.)
# Extracted from existing Logic Pro Channel EQ presets — identical across all.
FOOTER = bytes.fromhex(
    "8fc2353f00000000000000003333434100000000000000000000000000000040"
    "00000000000020410000803f000000bf000000000000803f000000000000803f"
    "0000704200000000000070420000803f7838504c08000000"
)

# Band field order: change this tuple to reorder if presets load with wrong values.
# Current order: [Q, enabled, frequency, gain]
BAND_FIELD_ORDER = ("q", "enabled", "frequency", "gain")

DEFAULT_Q = 0.71


def pack_band(q, enabled, frequency, gain):
    """Pack a single EQ band as 16 bytes (4 little-endian floats)."""
    fields = {"q": q, "enabled": enabled, "frequency": frequency, "gain": gain}
    values = [fields[name] for name in BAND_FIELD_ORDER]
    return struct.pack("<ffff", *values)


def build_preset(bands_config):
    """Build a complete 240-byte .pst file from a list of 8 band dicts."""
    band_data = b""
    for band in bands_config:
        q = float(band.get("q", DEFAULT_Q))
        enabled = 0.0 if band.get("enabled") is False else 1.0
        frequency = float(band["frequency"])
        gain = float(band.get("gain", 0.0))
        band_data += pack_band(q, enabled, frequency, gain)

    preset = HEADER + band_data + FOOTER
    assert len(preset) == 240, f"Preset size mismatch: {len(preset)} != 240"
    return preset


def load_devices(config_path):
    """Load device profiles from JSON config."""
    with open(config_path, "r") as f:
        return json.load(f)["devices"]


def generate_preset(device, output_dir):
    """Generate a single .pst file for a device profile. Returns output path."""
    preset_data = build_preset(device["bands"])
    filename = device.get("filename", device["name"].replace(" ", "_") + ".pst")
    output_path = os.path.join(output_dir, filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(preset_data)
    return output_path


def list_devices(devices):
    """Print available device profiles."""
    print(f"Available devices ({len(devices)}):\n")
    for d in devices:
        bands = d["bands"]
        active = sum(1 for b in bands if b.get("enabled") is not False)
        print(f"  {d['name']:<22} {active}/8 bands active  ->  {d.get('filename', '?')}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate Logic Pro X Channel EQ presets for device speaker simulation."
    )
    parser.add_argument(
        "--config", default=os.path.join(os.path.dirname(__file__), "devices.json"),
        help="Path to device profiles JSON (default: devices.json alongside script)",
    )
    parser.add_argument(
        "--output", "-o", default=".",
        help="Output directory for .pst files (default: current directory)",
    )
    parser.add_argument(
        "--list", action="store_true", dest="list_devices",
        help="List available device profiles and exit",
    )
    parser.add_argument(
        "--device", "-d", type=str, default=None,
        help="Generate preset for a single device (case-insensitive substring match)",
    )
    args = parser.parse_args()

    devices = load_devices(args.config)

    if args.list_devices:
        list_devices(devices)
        return

    os.makedirs(args.output, exist_ok=True)

    # Filter to single device if requested
    if args.device:
        query = args.device.lower()
        matches = [d for d in devices if query in d["name"].lower()]
        if not matches:
            print(f"No device matching '{args.device}'. Use --list to see options.", file=sys.stderr)
            sys.exit(1)
        targets = matches
    else:
        targets = devices

    # Generate
    print(f"Generating {len(targets)} preset(s) -> {os.path.abspath(args.output)}/\n")
    for device in targets:
        path = generate_preset(device, args.output)
        bands = device["bands"]
        active = sum(1 for b in bands if b.get("enabled") is not False)
        hp_freq = bands[0]["frequency"]
        lp_freq = bands[7]["frequency"]
        print(f"  {device['name']:<22} {active}/8 bands  HP={hp_freq}Hz  LP={lp_freq}Hz  ->  {os.path.basename(path)}")

    print(f"\nDone. {len(targets)} preset(s) written.")


if __name__ == "__main__":
    main()
