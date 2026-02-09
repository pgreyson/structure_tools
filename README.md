# Structure Tools

Tools for working with the [Erogenous Tones Structure](https://www.erogenous-tones.com/modules/structure/) Eurorack video synthesis module.

## Project Structure

```
structure_tools/
  exporter/       Video clip exporter GUI (select ranges, export to Structure format)
  glsl/           GLSL shaders (mirrors Structure SD card layout)
    fx/           Effect shaders (process input video)
```

## exporter/

GUI application for selecting video ranges from 3D SBS segments and exporting clips to Structure's MJPEG format. Includes Syphon output for stereo glasses preview.

See [exporter/README.md](exporter/README.md) for details.

## glsl/

Custom GLSL shaders for Structure. The directory layout mirrors the SD card (`/Volumes/STRUCT_SD/glsl/`) so shaders can be copied directly.

See [glsl/README.md](glsl/README.md) for the shader development workflow.
