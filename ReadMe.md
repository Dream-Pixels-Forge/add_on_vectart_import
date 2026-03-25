# VectArt - Vector-to-3D Procedural Pipeline for Blender 5.1

![vectart_import_logo](https://github.com/user-attachments/assets/1e0ec924-6cad-40f1-8a41-c623b9232046)

## Overview
VectArt is a professional-grade Blender extension that transforms static SVG files into dynamic, procedural 3D environments. Built for the modern Blender 5.1 API, it bridges the gap between vector design and 3D modeling with high-performance engines.

## Key Features

### 1. Procedural Geometry Nodes Engine
- **Non-Destructive Extrusion:** Change depth, bevel, and offsets without affecting original path data.
- **Dynamic Beveling:** Integrated procedural beveling powered by Blender's latest GN nodes.
- **Global & Layer Controls:** Mix standard curve properties with advanced procedural modifiers.

### 2. Grease Pencil v3 (GPv3) Bridge
- **High-Performance Viewport:** Import complex SVGs as GPv3 objects for massive performance gains.
- **Artistic Control:** Sculpt, build, and animate vector paths using Grease Pencil's specialized toolset.
- **Auto-Conversion:** One-click conversion from imported curves to GPv3 layers and strokes.

### 3. Real-Time "Live Link" Sync
- **Background Watcher:** Monitors your SVG files for changes on disk.
- **Auto-Update:** Save in Illustrator, Affinity, or Inkscape and watch your 3D model update instantly in Blender.
- **Material Preservation:** Intelligent round-trip system preserves your custom Blender shaders during reimports.

### 4. Advanced Layer Management
- **Automated Depth Mapping:** Layers are automatically spaced and organized based on SVG structure.
- **Smart Grouping:** Create empty parents and bounding-box based hierarchies with one click.

## Requirements
- **Blender 5.1 or newer** (Extension format)
- Supported Editors: Adobe Illustrator, Affinity Designer, Inkscape, or any SVG editor.

## Installation
1. Pack the folder as a `.zip` or install via the Blender Preferences > Extensions > Install from Disk.
2. Set your **Library Path** in the Add-on Preferences to point to your SVG folder.

## Usage
- **Import:** Use the N-panel (VectArt tab) to browse your library and import SVGs.
- **Engine Selection:** Choose between `Standard`, `Procedural` (GN), or `Grease Pencil` in the Layer Tools.
- **Edit SVG:** Select an object and click "Edit Selection" to launch your external editor with a live sync connection.

## License
SPDX:GPL-3.0-or-later

## Credits
Created by **Dimona Patrick** (Dream-Pixels-Forge)
