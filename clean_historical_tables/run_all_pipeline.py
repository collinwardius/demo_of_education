#!/usr/bin/env python3
"""
Master script to run the complete data processing pipeline.

This script runs:
1. All Stata .do files for data cleaning (in chronological order)
2. combine_datasets.py to merge all cleaned datasets
3. extract_unique_colleges.py to create college summaries

Author: Generated for demo of education project
"""

import subprocess
import os
import sys
from pathlib import Path
import time

def run_command(command, description, working_dir=None):
    """
    Run a shell command and handle errors.
    
    Args:
        command: List of command parts or string command
        description: Description of what the command does
        working_dir: Directory to run the command in
    
    Returns:
        bool: True if successful, False if failed
    """
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"COMMAND: {' '.join(command) if isinstance(command, list) else command}")
    print(f"{'='*60}")
    
    try:
        if working_dir:
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True,
                cwd=working_dir
            )
        else:
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True
            )
        
        print("✅ SUCCESS")
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED with return code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    """Main function to run the complete pipeline."""
    
    print("🚀 STARTING COMPLETE DATA PROCESSING PIPELINE")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define base directory
    base_dir = "/Users/cjwardius/Documents/GitHub/demo_of_education/clean_historical_tables"
    
    # Check if base directory exists
    if not os.path.exists(base_dir):
        print(f"❌ ERROR: Base directory not found: {base_dir}")
        sys.exit(1)
    
    # Find all .do files in the directory (sorted for consistent order)
    do_files = sorted([f for f in os.listdir(base_dir) if f.endswith('.do')])

    # Define Python scripts in specific order
    python_scripts = ["combine_datasets.py"]

    # Find remaining Python scripts (excluding specific ones and this script)
    remaining_python_scripts = sorted([f for f in os.listdir(base_dir)
                                     if f.endswith('.py') and f != 'run_all_pipeline.py' and f not in python_scripts])

    # Special Stata script to run after combine_datasets.py
    post_combine_do_script = "clean_appended_dataset.do"
    
    # Track success/failure
    results = {
        "stata_cleaning": [],
        "python_processing": [],
        "post_combine_cleaning": [],
        "final_python_processing": []
    }
    
    # Remove post_combine_do_script from do_files to avoid running it twice
    do_files = [f for f in do_files if f != post_combine_do_script]

    print(f"\n📁 Working directory: {base_dir}")
    print(f"📋 Found {len(do_files)} Stata cleaning scripts")
    print(f"🐍 Found {len(python_scripts)} initial Python processing scripts")
    print(f"🔧 Found post-combine cleaning script: {post_combine_do_script}")
    print(f"🐍 Found {len(remaining_python_scripts)} final Python processing scripts")
    
    # Step 1: Run all Stata .do files for data cleaning
    print(f"\n{'🔄 PHASE 1: STATA DATA CLEANING':^60}")
    
    for do_file in do_files:
        do_file_path = os.path.join(base_dir, do_file)
        
        # Check if file exists
        if not os.path.exists(do_file_path):
            print(f"⚠️  WARNING: {do_file} not found, skipping...")
            results["stata_cleaning"].append((do_file, False, "File not found"))
            continue
        
        # Run the Stata .do file
        command = ["/Applications/StataNow/StataSE.app/Contents/MacOS/StataSE", "-b", "-e", "do", do_file]
        description = f"Stata cleaning script: {do_file}"
        
        success = run_command(command, description, working_dir=base_dir)
        results["stata_cleaning"].append((do_file, success, ""))
        
        if not success:
            print(f"⚠️  WARNING: {do_file} failed, but continuing with pipeline...")
            
        # Small delay between Stata runs
        time.sleep(2)
    
    # Step 2: Run initial Python data processing scripts (combine_datasets.py)
    print(f"\n{'🐍 PHASE 2: INITIAL PYTHON DATA PROCESSING':^60}")

    for py_script in python_scripts:
        py_script_path = os.path.join(base_dir, py_script)

        # Check if file exists
        if not os.path.exists(py_script_path):
            print(f"⚠️  WARNING: {py_script} not found, skipping...")
            results["python_processing"].append((py_script, False, "File not found"))
            continue

        # Run the Python script
        command = ["python3", py_script]
        description = f"Python processing script: {py_script}"

        success = run_command(command, description, working_dir=base_dir)
        results["python_processing"].append((py_script, success, ""))

        if not success:
            print(f"⚠️  WARNING: {py_script} failed, but continuing with pipeline...")

    # Step 3: Run post-combine Stata cleaning script
    print(f"\n{'🔧 PHASE 3: POST-COMBINE DATA CLEANING':^60}")

    post_combine_path = os.path.join(base_dir, post_combine_do_script)

    # Check if file exists
    if not os.path.exists(post_combine_path):
        print(f"⚠️  WARNING: {post_combine_do_script} not found, skipping...")
        results["post_combine_cleaning"].append((post_combine_do_script, False, "File not found"))
    else:
        # Run the post-combine Stata .do file
        command = ["/Applications/StataNow/StataSE.app/Contents/MacOS/StataSE", "-b", "-e", "do", post_combine_do_script]
        description = f"Post-combine cleaning script: {post_combine_do_script}"

        success = run_command(command, description, working_dir=base_dir)
        results["post_combine_cleaning"].append((post_combine_do_script, success, ""))

        if not success:
            print(f"⚠️  WARNING: {post_combine_do_script} failed, but continuing with pipeline...")

        # Small delay after Stata run
        time.sleep(2)

    # Step 4: Run final Python data processing scripts
    print(f"\n{'🐍 PHASE 4: FINAL PYTHON DATA PROCESSING':^60}")

    for py_script in remaining_python_scripts:
        py_script_path = os.path.join(base_dir, py_script)

        # Check if file exists
        if not os.path.exists(py_script_path):
            print(f"⚠️  WARNING: {py_script} not found, skipping...")
            results["final_python_processing"].append((py_script, False, "File not found"))
            continue

        # Run the Python script
        command = ["python3", py_script]
        description = f"Final Python processing script: {py_script}"

        success = run_command(command, description, working_dir=base_dir)
        results["final_python_processing"].append((py_script, success, ""))

        if not success:
            print(f"⚠️  WARNING: {py_script} failed, but continuing with pipeline...")
    
    # Step 5: Print final summary
    print(f"\n{'📊 PIPELINE SUMMARY':^60}")
    print(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n🔄 STATA CLEANING RESULTS:")
    for script, success, error in results["stata_cleaning"]:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {script}: {status}")
        if error:
            print(f"    Error: {error}")

    print(f"\n🐍 INITIAL PYTHON PROCESSING RESULTS:")
    for script, success, error in results["python_processing"]:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {script}: {status}")
        if error:
            print(f"    Error: {error}")

    print(f"\n🔧 POST-COMBINE CLEANING RESULTS:")
    for script, success, error in results["post_combine_cleaning"]:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {script}: {status}")
        if error:
            print(f"    Error: {error}")

    print(f"\n🐍 FINAL PYTHON PROCESSING RESULTS:")
    for script, success, error in results["final_python_processing"]:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {script}: {status}")
        if error:
            print(f"    Error: {error}")

    # Calculate overall success rate
    stata_successes = sum(1 for _, success, _ in results["stata_cleaning"] if success)
    initial_python_successes = sum(1 for _, success, _ in results["python_processing"] if success)
    post_combine_successes = sum(1 for _, success, _ in results["post_combine_cleaning"] if success)
    final_python_successes = sum(1 for _, success, _ in results["final_python_processing"] if success)

    total_scripts = (len(results["stata_cleaning"]) + len(results["python_processing"]) +
                    len(results["post_combine_cleaning"]) + len(results["final_python_processing"]))
    total_successes = stata_successes + initial_python_successes + post_combine_successes + final_python_successes
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"  Total scripts: {total_scripts}")
    print(f"  Successful: {total_successes}")
    print(f"  Failed: {total_scripts - total_successes}")
    print(f"  Success rate: {(total_successes/total_scripts)*100:.1f}%")
    
    if total_successes == total_scripts:
        print(f"\n🎉 PIPELINE COMPLETED SUCCESSFULLY! 🎉")
        return 0
    else:
        print(f"\n⚠️  PIPELINE COMPLETED WITH SOME FAILURES")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)