# bpy-helper

A lightweight alternative to BlenderProc

[![PyPI version](https://badge.fury.io/py/bpy-helper.svg)](https://pypi.org/project/bpy-helper/) [![Upload Python Package](https://github.com/iamNCJ/bpy-helper/actions/workflows/python-publish.yml/badge.svg)](https://github.com/iamNCJ/bpy-helper/actions/workflows/python-publish.yml)

## Why bpy-helper instead of BlenderProc?

BlenderProc needs a separate blender installation, and a lot of restrictions when using with other pypi packages. Debugging a BlenderProc script is also painful especially when you are using a headless environment. Hence I decide to build my own blender wrapper using `bpy`.

## Installation

```bash
pip install bpy-helper
```

## Projects using bpy-helper

- [NRHints: Relighting Neural Radiance Fields with Shadow and Highlight Hints](https://nrhints.github.io/): bpy-helper is derived from the data rendering scripts of NRHints.
- [DiLightNet: Fine-grained Lighting Control for Diffusion-based Image Generation](https://dilightnet.github.io/): bpy-helper is used to render the training data and radiance hints for DiLightNet.
- [GS^3: Efficient Relighting with Triple Gaussian Splatting](https://gsrelight.github.io/): bpy-helper is used to render the training data for GS^3.
- [RenderFormer: Transformer-based Neural Rendering of Triangle Meshes with Global Illumination](https://microsoft.github.io/renderformer/): bpy-helper is used to render the training data and reference images for RenderFormer.
