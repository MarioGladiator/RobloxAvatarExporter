# RobloxAvatarExporter

Standalone Avatar Exporter + Batch Exporter

Exports Roblox avatars to FBX with R15 bone hierarchy, rigid attachment markers, textures, and bundle `WrapTarget` body cages so the exported FBX stays compatible with Roblox avatar auto-setup/import workflows.

## Prerequisites

### Required
- **Python 3.x**
- **Roblox Studio**

### For Blender Compatibility (Recommended)
- **Autodesk FBX Converter** - Required to convert ASCII FBX to Binary FBX for Blender
  - Download from: [Autodesk FBX Converter Archives](https://www.autodesk.com/developer-network/platform-technologies/fbx-converter-archives)
  - After installation, add `FbxConverter.exe` to your system PATH
  - See [FBX Converter CLI Documentation](https://download.autodesk.com/us/fbx/2013/FBXconverter/index.html?url=files/GUID-AAE019B0-8216-4574-BD41-546EFA372706.htm,topicNumber=d30e3370)

# How to use (single avatar export)

1. Clone repo
2. Install **Autodesk FBX Converter** and add it to PATH (see Prerequisites above)
3. Install the following plugin (or create a local plugin using source code from this repo)  
   https://www.roblox.com/library/6506050633/AvatarExporter  
   ![alt tag](https://raw.githubusercontent.com/SergeyMakeev/RobloxAvatarExporter/master/pics/plugin.png)
4. Run `python FbxExporterServer.py`
   - To resolve `rbxassetid://` meshes, textures, and bundle cage assets through Roblox's current Open Cloud asset delivery API, set `ROBLOX_ASSET_DELIVERY_API_KEY` in the environment before starting the server.
5. Open Roblox Studio and select an avatar you need to export  
   ![alt tag](https://raw.githubusercontent.com/SergeyMakeev/RobloxAvatarExporter/master/pics/select_avatar.png)
6. Click `Avatar Exporter` button
7. Find the resulting `.FBX` files in the `Avatars` folder
   - `<AvatarName>.fbx` - ASCII FBX (compatible with most tools)
   - `<AvatarName>_binary.fbx` - Binary FBX (compatible with Blender)

# How to use (batch export)

1. Clone repo
2. Install the following plugin (or create a local plugin using source code from this repo)  
   https://www.roblox.com/library/6506050633/AvatarExporter
3. Open `bundles.txt` (or `accessories.txt`) and type a list of avatar bundles you want to export
4. Run `python FbxExporterServer.py`
   - Batch bundle exports also use `ROBLOX_ASSET_DELIVERY_API_KEY` for Roblox's Open Cloud asset delivery endpoint when resolving asset IDs.
5. Open Roblox Studio and create an empty base plate
6. Click `Batch Export` button
7. Find the resulting avatar bundles exported to `.FBX` files in the `Avatars` folder
   - `<AvatarName>.fbx` - ASCII FBX (compatible with most tools)
   - `<AvatarName>_binary.fbx` - Binary FBX (compatible with Blender)
   ![alt tag](https://raw.githubusercontent.com/SergeyMakeev/RobloxAvatarExporter/master/pics/fbx_avatar.png)

# Blender Compatibility

Blender only supports **Binary FBX** files. This exporter automatically creates both formats using Autodesk FBX Converter:

- **ASCII FBX** (`*.fbx`) - Compatible with Maya, 3ds Max, Unity, Unreal Engine, etc.
- **Binary FBX** (`*_binary.fbx`) - **Use this for Blender!**

## Manual Conversion

If you need to convert an existing ASCII FBX to Binary:

```bash
# Convert single file
python ascii_to_binary_fbx.py <input.fbx> [output.fbx]

# Convert all FBX files in a directory
python ascii_to_binary_fbx.py Avatars/
```

**Note:** Autodesk FBX Converter must be installed and in your PATH for automatic conversion to work.

## Troubleshooting

### Asset delivery / missing meshes or textures

If `rbxassetid://` content fails to resolve, make sure you started the exporter with a valid Roblox Open Cloud API key:

```bash
export ROBLOX_ASSET_DELIVERY_API_KEY="your-api-key"
python FbxExporterServer.py
```

The exporter now uses `https://apis.roblox.com/asset-delivery-api/v1/assetId/{assetId}` and then downloads the temporary CDN URL returned by that API.

### "FBX Converter not found in PATH"

1. Download and install [Autodesk FBX Converter](https://www.autodesk.com/developer-network/platform-technologies/fbx-converter-archives)
2. Add the installation directory to your system PATH:
   - **Windows:** Add `C:\Program Files\Autodesk\FBX\FBX Converter\2013.3\bin\` (or similar) to PATH
   - **Mac/Linux:** Add the converter binary location to PATH
3. Restart your terminal/command prompt
4. Test by running: `FbxConverter` or `fbxconverter`

### Binary FBX not being created

If the automatic conversion fails, you can:
1. Use the ASCII FBX with other 3D software (Maya, 3ds Max, etc.)
2. Manually convert using FBX Converter GUI
3. Import to another tool first, then re-export as binary FBX for Blender
   
