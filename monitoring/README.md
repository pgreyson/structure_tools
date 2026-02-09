# Structure Monitoring

Monitor the Structure module's video output on Viture XR glasses and a 3D projector simultaneously using an Elgato capture device and OBS.

## Signal Flow

```
Structure module (plays half-SBS video + stereo shaders)
    ↓ composite SD out
Analog → HDMI converter
    ↓ HDMI
Elgato 4K S capture device
    ↓ HDMI passthrough        ↓ USB capture
3D projector (half-SBS in)   Mac (OBS)
                                ↓ fullscreen projector
                             Viture glasses (3840x1080 full SBS)
```

Structure outputs half-SBS (both eyes squeezed into a single 4:3 SD frame). The Elgato passes the HDMI through to a 3D projector that accepts half-SBS natively, and simultaneously captures it as a 1920x1080 video source on the Mac. OBS stretches the half-SBS horizontally to produce full SBS for the Viture glasses.

## OBS Setup

Profile: `structure->elegato->viture_half_to_full_sbs`

### Canvas/Output (Settings → Video)

| Setting | Value |
|---------|-------|
| Base (Canvas) Resolution | 3840x1080 |
| Output (Scaled) Resolution | 3840x1080 |
| FPS | 30 |

The 3840x1080 canvas matches the Viture glasses' full side-by-side stereo format.

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

**Stretch to bounds** is the key setting. The Elgato captures 1920x1080 (half-SBS with both eyes squeezed in). Stretching to the 3840x1080 bounding box doubles the width, unsqueezing each eye into its own full 1920x1080 panel for the Viture glasses.

> **TODO:** The image is currently horizontally stretched on the Viture display. Structure outputs 4:3 SD composite, but the Elgato captures it as 1920x1080 (16:9), stretching the 4:3 content. "Stretch to bounds" then doubles the width for full SBS, compounding the distortion. Need to pillarbox each eye to maintain 4:3 aspect ratio within each 1920x1080 panel (black bars on sides).

## Design Philosophy: Maximize Signal at Each Stage

The chain deliberately avoids pillarboxing or letterboxing until the final display stage. At every intermediate step, the full frame is used — content is squeezed or stretched to fill the available resolution rather than wasting pixels on black bars. This preserves as much signal as possible through each conversion:

- Structure packs both eyes into the full 4:3 SD frame (half-SBS)
- The Elgato captures the full frame at 1920x1080
- OBS stretches to fill the full 3840x1080 canvas

Pillarboxing only happens at the end, where the display needs correct aspect ratio. A full-SBS HD processing chain would eliminate the squeeze/stretch problem entirely. Erogenous Tones promises an HD version of Structure coming "soon" — but given tariffs are making CN manufacturing challenging for small Eurorack businesses (viz LZX/Chromagnon), don't hold your breath.

### Fullscreen Projector

Right-click the OBS Preview → Fullscreen Projector → Viture display (monitor 1).

## Hardware

- **Structure**: Erogenous Tones Structure Eurorack video module
- **Converter**: Composite SD analog → HDMI
- **Capture**: Elgato 4K S (HDMI passthrough + USB capture)
- **Projector**: Any 3D projector supporting half-SBS input
- **Glasses**: Viture XR glasses (3840x1080 full SBS display)
