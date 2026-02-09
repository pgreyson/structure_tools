# Structure Monitoring

Monitor the Structure module's video output on Viture XR glasses and a 3D projector simultaneously using an Elgato capture device and OBS.

## Signal Flow

```
Structure module (plays half-SBS video + stereo shaders)
    ↓ composite SD out (4:3)
Analog → HDMI converter (stretches 4:3 to 16:9 HDMI)
    ↓ HDMI (16:9)
Elgato 4K S capture device
    ↓ HDMI passthrough        ↓ USB capture
3D projector (half-SBS in)   Mac (OBS)
                                ↓ fullscreen projector
                             Viture glasses (3840x1080 full SBS)
```

Structure outputs half-SBS (both eyes squeezed into a single 4:3 SD frame). The analog→HDMI converter stretches this to fill a 16:9 HDMI frame. The Elgato passes the HDMI through to a 3D projector and simultaneously captures it as a 1920x1080 video source on the Mac. OBS then stretches the capture horizontally to produce full SBS for the Viture glasses — each eye gets its own 1920x1080 panel, but the content is still aspect-ratio-distorted from the 4:3→16:9 conversion.

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

**Stretch to bounds** doubles the width of the 1920x1080 capture to fill the 3840x1080 canvas, splitting the half-SBS into two 1920x1080 eye panels for the Viture glasses.

### Fullscreen Projector

Right-click the OBS Preview → Fullscreen Projector → Viture display (monitor 1).

> **TODO:** The image is currently horizontally stretched on the Viture display. The analog→HDMI converter stretches the 4:3 SD signal to fill 16:9 HDMI, and that distortion carries through the whole chain. Need to pillarbox each eye at the final stage to restore 4:3 aspect ratio within each 1920x1080 panel (black bars on sides).

## Design Philosophy: Maximize Signal at Each Stage

The chain deliberately avoids pillarboxing or letterboxing until the final display stage. At every intermediate step, the full frame is used — content is squeezed or stretched to fill the available resolution rather than wasting pixels on black bars. This preserves as much signal as possible through each conversion:

- Structure packs both eyes into the full 4:3 SD frame (half-SBS)
- The analog→HDMI converter fills the full 16:9 HDMI frame
- The Elgato captures the full 1920x1080 frame
- OBS stretches to fill the full 3840x1080 canvas

Pillarboxing only happens at the end, where the display needs correct aspect ratio. A full-SBS HD processing chain would eliminate the squeeze/stretch problem entirely. Erogenous Tones promises an HD version of Structure coming "soon" — but given tariffs are making CN manufacturing challenging for small Eurorack businesses (viz LZX/Chromagnon), don't hold your breath.

## Hardware

- **Structure**: Erogenous Tones Structure Eurorack video module
- **Converter**: Composite SD analog → HDMI
- **Capture**: Elgato 4K S (HDMI passthrough + USB capture)
- **Projector**: Any 3D projector supporting half-SBS input
- **Glasses**: Viture XR glasses (3840x1080 full SBS display)
