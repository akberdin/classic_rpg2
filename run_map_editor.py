#!/usr/bin/env python3
"""
Launcher script for the Classic RPG Map Editor.
Run this script to start the map editor independently from the game.
"""

import sys
from pathlib import Path

# Ensure we're in the correct directory
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from map_editor.main import main
    main()
