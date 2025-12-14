# Game Asset Pipeline

Complete examples of game asset pipeline workflows using ArtReactor.

## Character Export Workflow

A typical character pipeline involves:

1. **Modeling** in Maya/Blender
2. **Validation** of naming, topology, and bone counts
3. **Export** to FBX with correct settings
4. **Version Control** checkout in Perforce/Git
5. **Import** to Unreal/Unity
6. **Auto-Configuration** of materials and settings
7. **Version Control** submit with description

### Example: Maya to Unreal

```python
# Agent command
"Export character 'CHAR_Hero_Male' from Maya and import to Unreal"

# ArtReactor orchestrates:
# 1. validate_character("CHAR_Hero_Male")
# 2. export_character(...) 
# 3. p4_edit(...)
# 4. import_to_unreal(...)
# 5. setup_materials(...)
# 6. p4_submit(...)
```

See the [Architecture Overview](../architecture/overview.md) for how these tools are coordinated.

## Environment Asset Batch Processing

Process hundreds of props efficiently:

- Parallel export from Blender
- Automatic LOD generation
- Texture optimization
- Batch import to engine
- Prefab creation

## Animation Pipeline

Motion capture to game-ready animation:

1. Import mocap data
2. Clean up and retarget
3. Bake to game skeleton
4. Export animation files
5. Import with compression

See [Use Cases Overview](overview.md) for more examples.
