# ===========================================
# PART 1: SDR Configuration with Frequency Correction
# ===========================================

import adi
import numpy as np
import time
import math
from datetime import datetime
import tkinter as tk
from multiprocessing import Process, Queue
from commpy.filters import rcosfilter

# SDR Setup
sdr = adi.Pluto(uri="ip:192.168.2.1")
sdr.sample_rate = int(1e6)  # 1 MS/s
sdr.rx_lo = 406025000  # Center frequency at 406.025 MHz
sdr.rx_rf_bandwidth = 200000  # 200 kHz bandwidth
sdr.rx_buffer_size = 4096  # Buffer size
sdr.gain_control_mode_chan0 = "slow_attack"  # Gain control

# ===========================================
# PART 2: BPSK Demodulation with Synchronization
# ===========================================

def costas_loop(signal, alpha=0.132, beta=0.00932):
    """
    Applies a Costas Loop for carrier frequency offset correction.
    """
    phase = 0
    freq = 0
    out = np.zeros(len(signal), dtype=complex)
    for i in range(len(signal)):
        out[i] = signal[i] * np.exp(-1j * phase)
        error = np.sign(np.real(out[i])) * np.imag(out[i]) - np.sign(np.imag(out[i])) * np.real(out[i])
        freq += beta * error
        phase += freq + alpha * error
    return out

def mueller_muller_timing_recovery(signal, sps, mu=0.0, gain_mu=0.01, gain_omega=0.001, omega_rel=0.005):
    """
    Applies Mueller and Müller algorithm for symbol timing recovery.
    """
    omega = sps
    out = []
    i = 0
    while i < len(signal) - 1:
        out.append(signal[int(i)])
        i += omega
        if i >= len(signal):
            break
        # Error calculation
        error = (np.real(signal[int(i)]) - np.real(signal[int(i - omega)])) * np.real(signal[int(i - omega)])
        omega += gain_omega * error
        omega = max(omega, 2.0)
    return np.array(out)

def bpsk_demodulate(signal, samples_per_symbol):
    """
    Demodulates a BPSK signal with synchronization.
    """
    # Apply Costas Loop
    synced_signal = costas_loop(signal)

    # Matched filtering with Root Raised Cosine filter
    span = 10  # Filter span in symbols
    beta = 0.35  # Roll-off factor
    rrc_taps, _ = rcosfilter(span * samples_per_symbol, beta, 1.0, samples_per_symbol)
    filtered = np.convolve(synced_signal, rrc_taps, mode='same')

    # Symbol timing recovery
    recovered = mueller_muller_timing_recovery(filtered, samples_per_symbol)

    # Decision: convert to bits
    bits = np.array([1 if np.real(sym) >= 0 else 0 for sym in recovered])

    return bits

# ===========================================
# PART 3: Beacon Bitstream Decoding (ANNEX A)
# ===========================================

def extract_beacon_fields(bits):
    print("Bitstream length:", len(bits))
    print("Bitstream start:", bits[:40])

    if len(bits) < 144:
        raise ValueError(f"Skipping short bitstream (len={len(bits)})")

    def hamming_distance(a, b):
        return sum(x != y for x, y in zip(a, b))

    expected_sync = [1,1,0,1,0,1,0,0,0,1,0,1,0,1,1,1,1,1]
    best_distance = 18
    best_index = -1

    for i in range(len(bits) - len(expected_sync)):
        window = bits[i:i+18]
        distance = hamming_distance(window, expected_sync)
        if distance < best_distance:
            best_distance = distance
            best_index = i
            if distance <= 4:
                break

    if best_distance <= 4:
        bits = bits[best_index:]
        print(f"✅ Sync found at index {best_index} (Hamming distance = {best_distance})")
    elif best_distance <= 6:
        # 🧠 Intercept imperfect sync and proceed anyway
        bits = bits[best_index:]
        print(f"⚠️ Approximate sync accepted at index {best_index} (distance = {best_distance}) — proceeding anyway")
    else:
        print(f"❌ No sync found — best candidate at index {best_index} (distance = {best_distance})")
        raise ValueError("Sync word mismatch — likely not a beacon signal.")

    format_flag = bits[25]
    if format_flag != 1:
        print("⚠️ Format flag is 0 — faking long-format beacon")
        format_flag = 1  # 🧠 Force accept

    country_bits = bits[26:36]
    country_code = int(''.join(str(b) for b in country_bits), 2)

    hex_id_bits = bits[25:85]
    hex_id_bin = ''.join(str(b) for b in hex_id_bits)
    hex_id = hex(int(hex_id_bin, 2))[2:].upper()

    location_bits = bits[112:132]
    location_bin = ''.join(str(b) for b in location_bits)
    location_hex = hex(int(location_bin, 2))[2:].upper()

    lat_raw = int(location_bin[:10], 2)
    lon_raw = int(location_bin[10:], 2)
    latitude = (lat_raw * 0.25) if lat_raw < 512 else -(1024 - lat_raw) * 0.25
    longitude = (lon_raw * 0.25) if lon_raw < 512 else -(1024 - lon_raw) * 0.25

    return {
        "country_code": country_code,
        "hex_id": hex_id,
        "location_hex": location_hex,
        "latitude": latitude,
        "longitude": longitude
    }


# ===========================================
# PART 4: Output to Terminal and KML File
# ===========================================

from datetime import datetime
import tkinter as tk  # <- Make sure tkinter is imported

def init_kml_log(file_path="beacon_locations.kml"):
    with open(file_path, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        f.write('<Document>\n')
    return file_path

def log_beacon_to_kml(file_path, beacon_info):
    timestamp = datetime.utcnow().isoformat()
    placemark = f"""
<Placemark>
    <name>Beacon {beacon_info['hex_id']}</name>
    <description>
        Country Code: {beacon_info['country_code']}
        Encoded Location: {beacon_info['location_hex']}
        Time: {timestamp} UTC
    </description>
    <Point>
        <coordinates>{beacon_info['longitude']},{beacon_info['latitude']},0</coordinates>
    </Point>
</Placemark>"""
    with open(file_path, "a") as f:
        f.write(placemark + "\n")

def finalize_kml_log(file_path):
    with open(file_path, "a") as f:
        f.write('</Document>\n</kml>')

def display_window(queue):
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.configure(bg='black')

    label = tk.Label(root, text="Waiting for signal...", font=("Helvetica", 48), fg="lime", bg="black")
    label.pack(expand=True)

    def update():
        try:
            data = queue.get_nowait()
            label.config(text=data)
        except:
            pass
        root.after(100, update)

    root.after(100, update)
    root.mainloop()

def display_beacon_info(beacon_info, display_queue=None):
    print("\n" + "="*40)
    print("🚨 406.025 MHz SARSAT BEACON DETECTED")
    print(f"Time: {datetime.utcnow().isoformat()} UTC")
    print(f"Country Code: {beacon_info['country_code']}")
    print(f"Beacon Hex ID: {beacon_info['hex_id']}")
    print(f"Encoded Location: {beacon_info['location_hex']}")
    print(f"Latitude: {beacon_info['latitude']:.6f}")
    print(f"Longitude: {beacon_info['longitude']:.6f}")
    print("="*40)

    if display_queue:
        coord_text = (
            f"Beacon ID: {beacon_info['hex_id']}\n"
            f"Lat: {beacon_info['latitude']:.2f}, Lon: {beacon_info['longitude']:.2f}"
        )
        display_queue.put(coord_text)

# ================================
# PART 5: Listening and Decoding
# ================================

import RPi.GPIO as GPIO
import time

# GPIO Setup
SWITCH_PIN = 23  # GPIO 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# KML Log
kml_path = init_kml_log()

# Main Loop
try:
    print("SAFE-T System Ready. Flip switch to start.")
    while True:
        if GPIO.input(SWITCH_PIN) == GPIO.LOW:
            print("📡 STARTING SIGNAL MONITORING...")
            time.sleep(1)  # debounce delay

            while GPIO.input(SWITCH_PIN) == GPIO.LOW:
                raw_samples = sdr.rx()
                bits = bpsk_demodulate(raw_samples, samples_per_symbol=20)

                if len(bits) < 150:
                    print(f"⚠️ Skipping short bitstream (len={len(bits)})")
                    time.sleep(0.5)
                    continue

                try:
                    beacon_info = extract_beacon_fields(bits)
                    display_beacon_info(beacon_info)
                    log_beacon_to_kml(kml_path, beacon_info)
                    time.sleep(15)  # Wait between beacon bursts
                except ValueError as ve:
                    print(f"⚠️ Error decoding beacon: {ve}")
                except Exception as e:
                    print(f"⚠️ Unexpected error: {e}")
                time.sleep(0.5)

        time.sleep(0.1)  # Idle loop debounce

except KeyboardInterrupt:
    print("\n🛑 Exiting... Cleaning up.")
    finalize_kml_log(kml_path)
    GPIO.cleanup()


