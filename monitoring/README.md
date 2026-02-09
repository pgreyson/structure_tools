# Structure Monitoring

Monitor the Structure module's video output on Viture XR glasses and a 3D projector simultaneously using an Elgato capture device and OBS.

## Signal Flow

```
Structure module (plays half-SBS video + stereo shaders)
    ↓ composite SD out (4:3)
Analog → HDMI converter (stretches 4:3 to 16:9 HDMI)
    ↓ HDMI (16:9)
Elgato 4K S capture device
    ↓ HDMI passthrough        ↓ USB capture (1920x1080)
3D projector (half-SBS in)   Mac (OBS)
                                ↓ source filter: halfsbs_pillarbox.shader
                                ↓ transform: stretch to bounds (3840x1080)
                                ↓ fullscreen projector
                             Viture glasses (3840x1080 full SBS)
```

Structure outputs half-SBS (both eyes squeezed into a single 4:3 SD frame). The analog→HDMI converter stretches this to fill a 16:9 HDMI frame. The Elgato passes the HDMI through to a 3D projector and simultaneously captures it as a 1920x1080 video source on the Mac. OBS corrects the aspect ratio per-eye with a shader filter, then stretches the capture horizontally to produce full SBS for the Viture glasses.

## OBS Setup

Profile: `structure->elegato->viture_half_to_full_sbs`

### Canvas/Output (Settings → Video)

| Setting | Value |
|---------|-------|
| Base (Canvas) Resolution | 3840x1080 |
| Output (Scaled) Resolution | 3840x1080 |
| FPS | 30 |

The 3840x1080 canvas matches the Viture glasses' full side-by-side stereo format.

### Aspect Ratio Correction (Source Filter)

The analog→HDMI converter stretches the 4:3 SD signal to fill 16:9 HDMI. The stretch factor is (16/9) / (4/3) = **4/3**. To correct this per-eye in the half-SBS frame, we use [obs-shaderfilter](https://github.com/exeldro/obs-shaderfilter) with a custom shader.

Install obs-shaderfilter:
```bash
gh release download 2.6.0 --repo exeldro/obs-shaderfilter --pattern "*macos-arm64.pkg" --dir /tmp
open /tmp/obs-shaderfilter-2.6.0-macos-arm64.pkg
# click through installer, restart OBS
```

Apply the filter:
1. Right-click the Elgato source → Filters
2. Add → **User-defined shader**
3. Enable **Load shader text from file**
4. Select `monitoring/halfsbs_pillarbox.shader`

The shader squeezes each eye to 3/4 width (undoing the 4/3 stretch) and centers it with black pillarboxing. The `aspect_correction` slider defaults to 0.75 and can be fine-tuned if the converter's stretch isn't exactly 4:3→16:9.

### Scene Source Transform

Source: **Video Capture Device** (`macos-avcapture`) → Elgato 4K S

Right-click source → Edit Transform:

| Setting | Value |
|---------|-------|
| Size | 3840x1080 |
| Bounding Box Type | **Stretch to bounds** |
| Bounding Box Size | 3840x1080 |
| Positional Alignment | Top Left |
| Position | 0, 0 |

**Stretch to bounds** doubles the width of the 1920x1080 capture to fill the 3840x1080 canvas, splitting the half-SBS into two 1920x1080 eye panels for the Viture glasses. The shader filter runs first, so each eye is already aspect-corrected before the stretch.

### Fullscreen Projector

Right-click the OBS Preview → Fullscreen Projector → Viture display (monitor 1).

## Design Philosophy: Maximize Signal at Each Stage

The chain deliberately avoids pillarboxing or letterboxing until the final display stage. At every intermediate step, the full frame is used — content is squeezed or stretched to fill the available resolution rather than wasting pixels on black bars. This preserves as much signal as possible through each conversion:

- Structure packs both eyes into the full 4:3 SD frame (half-SBS)
- The analog→HDMI converter fills the full 16:9 HDMI frame
- The Elgato captures the full 1920x1080 frame
- OBS stretches to fill the full 3840x1080 canvas

Pillarboxing only happens at the end, in the OBS shader filter, where the display needs correct aspect ratio. A full-SBS HD processing chain would eliminate the squeeze/stretch problem entirely. Erogenous Tones promises an HD version of Structure coming "soon" — but given tariffs are making CN manufacturing challenging for small Eurorack businesses (viz LZX/Chromagnon), don't hold your breath.

## Hardware

- **Structure**: Erogenous Tones Structure Eurorack video module
- **Converter**: Composite SD analog → HDMI
- **Capture**: Elgato 4K S (HDMI passthrough + USB capture)
- **Projector**: Any 3D projector supporting half-SBS input
- **Glasses**: Viture XR glasses (3840x1080 full SBS display)
- **OBS plugin**: [obs-shaderfilter](https://github.com/exeldro/obs-shaderfilter) v2.6.0
