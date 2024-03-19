# bpy-helper

A lightweight alternative to BlenderProc

## Why bpy-helper instead of BlenderProc?

BlenderProc needs a separate blender installation, and a lot of restrictions when using with other pypi packages. Debugging a BlenderProc script is also painful especially when you are using a headless environment. Hence I decide to build my own blender wrapper using `bpy`.

## Installation

```bash
pip install git+https://github.com/iamNCJ/bpy-helper.git
```

## Projects using bpy-helper

- [NRHints: Relighting Neural Radiance Fields with Shadow and Highlight Hints](https://nrhints.github.io/): bpy-helper is derived from the data rendering scripts of NRHints.
