# Structure Tools

Tools for working with the [Erogenous Tones Structure](https://www.erogenous-tones.com/modules/structure/) Eurorack video synthesis module.

## Background

I've always loved 3D and thought it is magical — from Viewmasters to cross-eyed 3D-ification of repeating patterns (chainlink fence, tile floors) to scribbled stereoscopic sketches to the first Avatar (!) to Blade Runner 2049 (which I thought quite beautiful) to creating my own stereoscopic video and now to integrating it into my modular video synthesis pipeline.

This project sits at the intersection of two things: stereoscopic imagery and analog/digital video synthesis. The combination turns out to be more than the sum of its parts. Once your eyes accept they are viewing an image of depth, non-stereoscopic video synthesis elements — generated patterns, feedback, color manipulation — take on stereoscopic quality. Your visual system extends the 3D interpretation to everything in the frame.

Going the other direction is equally interesting: applying synthesis effects to stereoscopic footage sometimes violates the laws of parallax (e.g. zooming both eyes to center), but rather than breaking the illusion, it gives the video a physical texture — making it a sculptural medium rather than a photographic one.

The work produced with these tools is part of [sublingualism.com](https://sublingualism.com), built from the [sublinguist](https://github.com/pgreyson/sublinguist) repo.

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
