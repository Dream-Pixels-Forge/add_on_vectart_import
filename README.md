# VectArt - SVG Import & Layer Management for Blender

## Overview
VectArt is a powerful Blender addon that enhances SVG file management and curve manipulation. It provides an intuitive interface for importing SVG files, organizing them in layers, and managing curve properties with real-time updates.


## Demos
https://www.youtube.com/playlist?list=PLLZMHnPcqlHTAODP3zuduqjbHuwzJzBqu

## Features

### SVG Library Management
- Organized SVG file browser with thumbnails
- Quick import of SVG files from library
- Custom library path configuration
- Library refresh functionality
- SVG preview system
- 
![Screenshot 2025-04-23 232158](https://github.com/user-attachments/assets/65f84ca3-566b-4a61-b1a3-fde2b181de8e)

- 
![Screenshot 2025-04-23 232212](https://github.com/user-attachments/assets/23ad56d7-b9e1-402d-82cb-5d69617b0d74)

### Layer Management
- Create and manage multiple layers for curves
- Individual layer settings for:
  - Scale
  - Extrude height
  - Z-offset
- Layer visibility toggles
- Layer reordering
- Batch operations on layers

### Selection Tools
Right-click menu provides quick access to:
- Select all curves in active collection
- Select curves in specific layers
- Select all meshes in scene
- Select meshes in active collection
- Focus view on selected objects

### Curve Properties
- Global settings for all curves:
  - Base height
  - Layer spacing
  - Bevel depth
  - Bevel resolution
  - Cyclic option
- Live update support for real-time property changes

### Grouping Tools
- Create empty parent objects
- Customizable empty types
- Automatic naming system
- Size control for empty objects

## Installation

1. Download the `vectart_import.zip` file
2. Open Blender and go to Edit > Preferences
3. Click on the "Add-ons" tab
4. Click "Install" and select the downloaded zip file
5. Enable the addon by checking the checkbox

## Initial Setup

1. Set your SVG library path in the addon preferences
2. Configure default settings if needed
3. Refresh the library to load your SVG files

## Usage

### Importing SVG Files
1. Open the VectArt panel in the 3D View sidebar (N-panel)
2. Browse your SVG library using the preview thumbnails
3. Select an SVG file and click "Import Selected SVG"
4. Adjust import settings as needed

### Layer Management
1. Create new layers using the "Add Layer" button
2. Assign curves to layers
3. Adjust layer properties:
   - Scale
   - Extrude height
   - Z-offset
4. Toggle layer visibility
5. Reorder layers using up/down arrows

### Selection Tools
1. Right-click in the 3D viewport
2. Choose VectArt Selection from the menu
3. Select desired selection operation

### Converting to Mesh
1. Select the layers you want to convert
2. Click "Convert to Mesh"
3. Confirm the operation

## Global Settings

### Layer Settings
- Base Height: Sets the starting Z position for layers
- Layer Gap: Defines spacing between layers
- Bevel Depth: Controls curve bevel depth
- Bevel Resolution: Sets bevel quality
- Use Cyclic: Toggles closed/open curves

### Empty Object Settings
- Empty Type: Choose type of empty object
- Empty Name: Set naming convention
- Empty Size: Control display size

## Tips & Tricks

1. Use live updates for real-time preview of changes
2. Group related curves using empty objects
3. Organize SVGs in collections for better management:

  - Create main folder named SVGs Collections
  - Create subfolder named from your collection category: Company Logo Collection, Social Media Collection.
  - In the preferences on the addon choose your main collections
  - Click on refresh, dropdown menu now show your collection subfolders.
  - Choose SVG in Preview Panel, and voila!

4. Use layer system for complex designs
5. Convert to mesh only when final result is achieved

## Requirements
- Blender 4.0 or newer
- Supported operating systems:
  - Windows
  - macOS
  - Linux

## Known Issues
- Large SVG files may take longer to generate previews
- Live updates might slow down with many curves

## Support
For issues and feature requests, please use the GitHub issue tracker.

## License
["SPDX:GPL-3.0-or-later",]

## Credits
Created by [Dream-Pixels-Forge, Dimona Patrick]
