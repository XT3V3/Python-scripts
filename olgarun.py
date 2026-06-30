# -*- coding: utf-8 -*-
"""
Run OLGA genkey files in sequence.

Created by XT3V3, supported by Claude Code.

Add the files you want to simulate to the "input_files" list at the bottom of
the script, then run it. You may list ".opi" files, ".genkey" files, or a
mix of both:
  - ".opi"   files are first converted to ".genkey" files using opi.exe,
    then the resulting genkey files are run.
  - ".genkey" files are run directly.

Each simulation's full output is written to "<genkey>.log" (open it in
Notepad++ and use the Tail plugin to follow along). Each opi conversion's
output is written to "<opi>.log".

Behaviour:
  - All listed ".opi" files are converted to genkey files first, then every
    genkey file is run in series.
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
# Full path to the opi executable used to convert .opi files into .genkey
# files. Update this when OLGA is upgraded.
OPI_EXE = r"C:\Program Files\Schlumberger\Olga 2025.2.0\opi.exe"
# File OLGA creates when it cannot obtain a license.
LICENSE_FAIL_LOG = "olgalicensefail.log"
# How long to wait (seconds) before retrying after a license failure.
RETRY_WAIT_SECONDS = 10


def run_opi(opi_filename):
    """Convert a single .opi file into a .genkey file using opi.exe.

    Runs the equivalent of:
        & "...\\opi.exe" /c <opi_filename>

    Returns the name of the generated genkey file on success, or None if the
    conversion failed (missing file, opi.exe error, no genkey produced).
    """
    if not os.path.isfile(OPI_EXE):
        print(f"*** opi executable not found:\n    {OPI_EXE}\n"
              f"    Edit OPI_EXE at the top of this script.")
        return None

    if not os.path.isfile(opi_filename):
        print(f"*** opi file '{opi_filename}' not found "
              f"(looked in {os.getcwd()}).")
        return None

    genkey_name = os.path.splitext(opi_filename)[0] + ".genkey"
    log_name = opi_filename + ".log"

    print(f"Generating genkey from '{opi_filename}' on {time.asctime()}.")

    # Run opi.exe, sending stdout and stderr to a per-file log. opi.exe blocks
    # until it has finished writing the genkey file.
    with open(log_name, "w") as log_file:
        result = subprocess.run(
            [OPI_EXE, "/c", opi_filename],
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

    if result.returncode != 0:
        print(f"*** Conversion of '{opi_filename}' FAILED "
              f"(exit code {result.returncode}) on {time.asctime()}.")
        print(f"    See '{log_name}' for the reason.")
        return None

    if not os.path.isfile(genkey_name):
        print(f"*** Conversion of '{opi_filename}' did not produce "
              f"'{genkey_name}'.")
        print(f"    See '{log_name}' for details.")
        return None

    print(f"Generated '{genkey_name}' on {time.asctime()}.")
    return genkey_name


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
    # List the files to simulate below (uncomment / edit as needed). You may
    # list .opi files, .genkey files, or a mix of both.
    #   - .opi   files are converted to .genkey first, then run.
    #   - .genkey files are run directly.
    input_files = [
        # "model.opi",
        # "Year1_Pres176bara_1xR_IniCond_CGR30.genkey",
        # "Year1_Pres176bara_1xR_IniCond_CGR90.genkey",
        # "Year5_Pres95bara_1xR_IniCond_CGR30.genkey",
        # "Year5_Pres95bara_1xR_IniCond_CGR90.genkey",
    ]

    if not input_files:
        print("No files listed. Add .opi or .genkey files to "
              "'input_files' and rerun.")
        raise SystemExit

    # --- Phase 1: convert every listed .opi file into a genkey file ---------
    # Maps each genkey file to run -> the original entry it came from (used for
    # the summary). .opi files that fail to convert are recorded as failures.
    genkeys_to_run = {}
    results = {}
    for filename in input_files:
        extension = os.path.splitext(filename)[1].lower()
        if extension == ".opi":
            genkey = run_opi(filename)
            if genkey is None:
                results[filename] = False
            else:
                genkeys_to_run[genkey] = filename
        elif extension == ".genkey":
            genkeys_to_run[filename] = filename
        else:
            print(f"*** Skipping '{filename}': not a .opi or .genkey file.")
            results[filename] = False

    # --- Phase 2: run every genkey file in series ---------------------------
    for genkey, source in genkeys_to_run.items():
        results[source] = run_olga(genkey)

    print("--- Batch summary ------------------------------------------")
    for source in input_files:
        ok = results.get(source)
        print(f"  {'OK    ' if ok else 'FAILED'}  {source}")
