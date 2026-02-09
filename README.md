# Structure Tools

Tools for working with the [Erogenous Tones Structure](https://www.erogenous-tones.com/modules/structure/) Eurorack video synthesis module.

## Project Structure

```
structure_tools/
  exporter/       Video clip exporter GUI (select ranges, export to Structure format)
  glsl/           GLSL shaders (mirrors Structure SD card layout)
    fx/           Effect shaders (process input video)
  monitoring/     OBS setup for monitoring Structure output on Viture glasses
```

## exporter/

GUI application for selecting video ranges from 3D SBS segments and exporting clips to Structure's MJPEG format. Includes Syphon output for stereo glasses preview.

See [exporter/README.md](exporter/README.md) for details.

## glsl/

Custom GLSL shaders for Structure. The directory layout mirrors the SD card (`/Volumes/STRUCT_SD/glsl/`) so shaders can be copied directly.

See [glsl/README.md](glsl/README.md) for the shader development workflow.

## monitoring/

Capture Structure's composite SD output via Elgato and display as full SBS stereo on Viture XR glasses using OBS, with simultaneous passthrough to a 3D projector.

See [monitoring/README.md](monitoring/README.md) for signal flow and OBS settings.
