# Structure GLSL Shaders

Custom GLSL shaders for the Erogenous Tones Structure module. The directory layout mirrors the SD card so shaders can be copied directly to `/Volumes/STRUCT_SD/glsl/`.

## Shader Categories

Structure organizes shaders by type:

| Directory | Purpose |
|-----------|---------|
| `gen/`    | Generators (create visuals from scratch) |
| `fx/`     | Effects (process input video/texture) |
| `mix/`    | Mix/blend between sources |
| `fb/`     | Feedback effects |
| `wipe/`   | Wipe transitions |
| ... | See SD card for full list |

## Shaders

### fx/stereo_zoom.glsl

Centered zoom on left and right sides of a side-by-side stereo image. Each eye is zoomed independently around its own center, with black fill outside bounds.

- **f0**: zoom level (center = no zoom, right = zoom in, left = zoom out)

## Stereo-Aware Shader Design

All input clips are half-SBS (left eye in left half, right eye in right half of the frame). A stereo-aware shader detects which half it's in and applies the effect per-eye — see `stereo_zoom.glsl` for the pattern.

The current node chain is: `CLIP → FBK → EFX1 → EFX2 → OUT`

### What Works in Stereo

**Stereo-preserving** (safe — identical per-pixel operation on both eyes):
- Continuous color effects: hue rotation, saturation, contrast, color curves. These don't touch spatial information at all, so parallax is perfectly preserved.
- Pixelation/mosaic: as long as both eyes get the same grid, depth is maintained.
- Edge detection/enhancement: operates on local neighborhoods, preserves relative positions.
- Feedback: already in the chain (`FBK` node). Feeds the output back into itself, creating trails and echoes that inherit the stereo depth of the source.

**Stereo-bending** (violates parallax but creates interesting sculptural effects):
- `stereo_zoom` (current): zooms each eye to its own center. Breaks parallax but gives the image a physical, embossed quality.
- Rotation: weird but sometimes works. The depth plane tilts rather than breaks.
- Wave/displacement: sinusoidal warping applied identically to each eye's local coordinates. The distortion is coherent between eyes, so the brain interprets it as a warped surface rather than a broken image.
- Mirror/kaleidoscope: horizontal mirror within each eye creates symmetry while depth persists at the seam.

**Stereo-specific** (effects that exist because of stereo):
- Convergence shift: horizontally offset one eye relative to the other to push the perceived depth plane forward or backward. A small shift is a powerful depth control.
- Per-eye color: different color treatment per eye (e.g. desaturate one eye, tint each differently). Creates an anaglyph-like quality in SBS, and the visual system tries to reconcile the difference, producing a shimmer.

### Shader Ideas

| Shader | Type | Category | Description |
|--------|------|----------|-------------|
| `stereo_zoom` | stereo-bending | fx | **Exists.** Per-eye centered zoom |
| `stereo_hue` | preserving | fx | Continuous hue rotation, CV-controlled. Safe for stereo. |
| `stereo_edge` | preserving | fx | Sobel edge detection per-eye. Turns depth into wireframe. |
| `stereo_converge` | stereo-specific | fx | Horizontal offset between eyes — CV-controllable depth plane |
| `stereo_tint` | stereo-specific | fx | Different hue/saturation per eye. Anaglyph shimmer. |
| `stereo_wave` | stereo-bending | fx | Sinusoidal displacement per-eye. Warped depth surface. |
| `stereo_mirror` | stereo-bending | fx | Horizontal mirror within each eye. Symmetric depth. |
| `stereo_pixelate` | preserving | fx | Mosaic with matched grids per eye |

### Stereo Generators

Generating stereoscopic content from scratch is harder. A generator shader outputs one frame, so it would need to render the scene from two viewpoints — left eye in the left half, right eye in the right half — within a single shader call.

For simple procedural geometry (planes, spheres, grids), this is possible: offset the camera x-position by an eye separation amount and render each half. But Structure's GLES 2.0 constraints mean ray marching is generally too slow, limiting this to simple SDF scenes or flat geometry with parallax displacement.

An alternative is to use two `gen` nodes in the Structure patch, each rendering one eye with a slight camera offset, then compositing them into half-SBS with a `mix` node. This is more flexible but uses more of the node chain.

## Deploying to Structure

Copy shaders to the SD card:

```bash
cp glsl/fx/stereo_zoom.glsl /Volumes/STRUCT_SD/glsl/fx/
```

## Development Workflow

Structure shaders are GLES 2.0 fragment shaders. The [GLSL Sandbox at Erogenous Tones](http://glsl.erogenous-tones.com/) provides an in-browser editor with live preview and test video textures for prototyping before deploying to hardware.

### Shader Template

All Structure shaders use this header:

```glsl
precision mediump float;
varying vec2 tcoord;    // location (UV coordinates)
uniform sampler2D tex;  // texture one (input video)
uniform sampler2D tex2; // texture two
uniform vec2 tres;      // size of texture (screen)
uniform vec4 fparams;   // 4 floats coming in (CV-controllable)
uniform ivec4 iparams;  // 4 ints coming in
uniform float ftime;    // 0.0 to 1.0 (ramp)
uniform int itime;      // increases when ftime hits 1.0
//f0::label     <- parameter name shown in Structure UI
//f1::label
//f2::label
float f0 = mix(0.05, 0.95, fparams[0]);  // remap to usable range
```

The `//f0::label` comments name the CV-controllable parameters in Structure's interface. Parameters arrive as 0.0-1.0 via `fparams[]` and are typically remapped with `mix()`.

### Browsing Example Shaders

The playground gallery is a JavaScript app that requires a browser to render. Use headless Chrome to scrape it:

```bash
# Fetch the gallery page and extract shader IDs
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --dump-dom "http://glsl.erogenous-tones.com/" 2>/dev/null \
  | grep -oE 'href="/e#[0-9.]*"'

# Fetch individual shader source via the JSON API
curl -s "http://glsl.erogenous-tones.com/item/1341.0"
# Returns: {"code":"...", "name":"acidZigZags", "type":"gen", ...}
```

The `/item/{id}` endpoint returns JSON with `code` (GLSL source), `name`, `type` (gen/fx/mix/etc), and `parent` (fork source).

### Writing a New Shader

1. Browse examples on the playground or fetch via the API for inspiration
2. Start from the template above
3. Test in the [playground editor](http://glsl.erogenous-tones.com/e) (supports live preview with test video)
4. Save the `.glsl` file in the appropriate category directory (e.g., `glsl/fx/`)
5. Copy to SD card and test on hardware

### Structure Hardware Constraints

- GLES 2.0 only (no compute shaders, limited precision)
- Ray marching, large loops, and complex math generally too slow
- Simple shaders layered with effects work best
- Resolutions: 640x480 or 320x240
