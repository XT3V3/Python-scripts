# -*- coding: utf-8 -*-
"""
Run OLGA genkey files in sequence.

Created by XT3V3, 4 Apr 2022. Cleaned up 22 May 2026 by Claude Code.

Add the genkey files you want to simulate to the ``genkey_files`` list at the
bottom of the script, then run it. Each simulation's full output is written to
"<genkey>.log" (open it in Notepad++ and use the Tail plugin to follow along).

Behaviour:
  - If all OLGA licenses are in use, the script waits and retries until one
    frees up.
  - If a simulation fails for any other reason (missing file, bad genkey), a
    clear warning is printed and the reason is recorded in the .log file.
  - A summary of which simulations passed or failed is printed at the end.

If Python is stopped, the simulation already running continues, but queued
simulations will not start. To stop the script, press Ctrl-C in the console.
"""
import os
import subprocess
import time

# --- Configuration ----------------------------------------------------------
# Full path to the OLGA executable. Update this when OLGA is upgraded.
OLGA_EXE = (
    r"C:\Program Files\Schlumberger\Olga 2025.2.0"
    r"\OlgaExecutables\Olga-2025.2.0.exe"
)
# File OLGA creates when it cannot obtain a license.
LICENSE_FAIL_LOG = "olgalicensefail.log"
# How long to wait (seconds) before retrying after a license failure.
RETRY_WAIT_SECONDS = 10


def run_olga(filename):
    """Run a single OLGA genkey file, retrying while licenses are unavailable.

    Returns True if the simulation completed successfully, False if it failed
    for a non-license reason (missing file, bad genkey, etc.).
    """
    if not os.path.isfile(OLGA_EXE):
        print(f"*** OLGA executable not found:\n    {OLGA_EXE}\n"
              f"    Edit OLGA_EXE at the top of this script.")
        return False

    if not os.path.isfile(filename):
        print(f"*** Genkey file '{filename}' not found "
              f"(looked in {os.getcwd()}).")
        return False

    log_name = filename + ".log"

    while True:
        # Clear any stale license-failure flag from a previous attempt.
        if os.path.isfile(LICENSE_FAIL_LOG):
            os.remove(LICENSE_FAIL_LOG)

        print(f"Starting simulation '{filename}' on {time.asctime()}.")

        # Run OLGA, sending stdout and stderr to the per-simulation log file.
        # subprocess.run blocks until OLGA exits.
        with open(log_name, "w") as log_file:
            result = subprocess.run(
                [OLGA_EXE, "./" + filename],
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )

        if os.path.isfile(LICENSE_FAIL_LOG):
            # OLGA could not get a license. Wait, then retry.
            print(f"--> No licenses available {time.asctime()}. "
                  f"Retrying in {RETRY_WAIT_SECONDS} s. Please wait.")
            time.sleep(RETRY_WAIT_SECONDS)
            continue

        if result.returncode != 0:
            # A genuine failure. The reason is recorded in the log file.
            print(f"*** Simulation '{filename}' FAILED "
                  f"(exit code {result.returncode}) on {time.asctime()}.")
            print(f"    See '{log_name}' for the reason.")
            return False

        print(f"Simulation '{filename}' ended on {time.asctime()}.\n")
        return True


if __name__ == "__main__":
    # Add the genkey files to simulate below (uncomment / edit as needed).
    genkey_files = [
        # "Year1_Pres176bara_1xR_IniCond_CGR30.genkey",
        # "Year1_Pres176bara_1xR_IniCond_CGR90.genkey",
        # "Year5_Pres95bara_1xR_IniCond_CGR30.genkey",
        # "Year5_Pres95bara_1xR_IniCond_CGR90.genkey",
    ]

    if not genkey_files:
        print("No genkey files listed. Add them to 'genkey_files' and rerun.")
    else:
        results = {genkey: run_olga(genkey) for genkey in genkey_files}

        print("--- Batch summary ------------------------------------------")
        for genkey, ok in results.items():
            print(f"  {'OK    ' if ok else 'FAILED'}  {genkey}")
