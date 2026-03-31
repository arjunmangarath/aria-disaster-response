"""
Root-level entry point for Streamlit Cloud.
Delegates to the actual app in the project subfolder.
"""
import os
import runpy
import sys

project_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Connect AI Agents to Real-World Data",
)

os.chdir(project_dir)
sys.path.insert(0, project_dir)

runpy.run_path(os.path.join(project_dir, "main.py"), run_name="__main__")
