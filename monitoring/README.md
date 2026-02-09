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

### Scene Source

| Setting | Value |
|---------|-------|
| Source type | Video Capture Device (`macos-avcapture`) |
| Device | Elgato 4K S |
| Transform Scale | 2.0 x 1.0 |
| Bounds | 3840x1080 |
| Bounding Box Type | Scale to inner bounds |

The **2.0 x 1.0 scale** is the key setting: it stretches the half-SBS capture (both eyes squeezed into 1920x1080) horizontally to fill the 3840x1080 canvas, producing full SBS where each eye gets its own 1920x1080 panel.

### Fullscreen Projector

Right-click the OBS Preview → Fullscreen Projector → Viture display (monitor 1).

## Hardware

- **Structure**: Erogenous Tones Structure Eurorack video module
- **Converter**: Composite SD analog → HDMI
- **Capture**: Elgato 4K S (HDMI passthrough + USB capture)
- **Projector**: Any 3D projector supporting half-SBS input
- **Glasses**: Viture XR glasses (3840x1080 full SBS display)
