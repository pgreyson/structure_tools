precision mediump float;
// stereo_displace : create stereo depth from monocular input
//
// Takes a flat (monocular) video synthesis input and produces half-SBS
// stereo by displacing pixels horizontally based on color/luminance.
// Same principle as ChromaDepth glasses but rendered digitally:
// color or brightness is mapped to depth, then each pixel is shifted
// in opposite horizontal directions for L/R eyes. The displacement
// between eyes IS parallax — your brain reads it as depth.
//
// How it works:
//   1. Map output UV to a base position in the mono source frame.
//      Both eyes share the same base_x so depth is read consistently.
//   2. Sample color at base_x and derive a depth value (0-1).
//   3. Apply contrast curve to expand the depth range — pushes depth
//      values away from the 0.5 midpoint so subtle gradients produce
//      stronger near/far separation.
//   4. Shift base_x by +displacement for left eye, -displacement
//      for right eye. The shift magnitude scales with depth.
//
// Depth modes:
//   Luminance: brightness = depth. Works with any video synthesis
//   output that has contrast.
//   ChromaDepth: hue = depth, following the ChromaDepth spectral
//   mapping (red = near, through the spectrum, to violet = far).
//   Same principle as ChromaDepth diffractive glasses but rendered
//   digitally for SBS displays. Best with content that has hue
//   variation at similar brightness.
//
// Overlap cropping:
//   Displacement creates monocular-only edges. The base coordinate
//   is restricted to [margin, 1-margin] where margin = max_disp/2.
//   This crops to the region visible to both eyes and scales to fill.
//
// f0 = depth — displacement intensity (squared curve, max ~8%)
// f1 = contrast — depth curve (left = linear, right = high contrast)
// f2 = mode — luminance (left) or chromadepth/hue (right)
varying vec2 tcoord;    // location
uniform sampler2D tex;  // texture one
uniform sampler2D tex2; // texture two
uniform vec2 tres;      // size of texture (screen)
uniform vec4 fparams;   // 4 floats coming in
uniform ivec4 iparams;  // 4 ints coming in
uniform float ftime;    // 0.0 to 1.0
uniform int itime;      // increases when ftime hits 1.0
//f0:depth:
//f1:contrast:
//f2:mode:
float f0 = mix(0.0, 0.08, fparams[0] * fparams[0]);  // squared curve, max ~8%
float f1 = mix(1.0, 4.0, fparams[1] * fparams[1]);   // depth contrast multiplier
float f2 = fparams[2];                                 // 0=luminance, 1=chromadepth

// Convert RGB to hue (0.0 to 1.0)
float rgb2hue(vec3 c) {
    float cmax = max(c.r, max(c.g, c.b));
    float cmin = min(c.r, min(c.g, c.b));
    float delta = cmax - cmin;
    if (delta < 0.001) return 0.0;
    float hue;
    if (cmax == c.r)
        hue = mod((c.g - c.b) / delta, 6.0);
    else if (cmax == c.g)
        hue = (c.b - c.r) / delta + 2.0;
    else
        hue = (c.r - c.g) / delta + 4.0;
    return hue / 6.0;
}

void main(void) {
    vec2 uv = tcoord;

    // Overlap crop margin based on max displacement
    float margin = f0 * 0.5;

    // Map output UV to base position in mono source frame
    float local_x;
    if (uv.x < 0.5) {
        local_x = uv.x * 2.0;
    } else {
        local_x = (uv.x - 0.5) * 2.0;
    }
    float base_x = margin + local_x * (1.0 - 2.0 * margin);

    // Sample depth from the base position in the mono source
    vec3 color = texture2D(tex, vec2(base_x, uv.y)).rgb;

    // Compute depth value (0.0 to 1.0)
    float depth;
    if (f2 < 0.5) {
        // Luminance mode: brightness = depth
        depth = dot(color, vec3(0.299, 0.587, 0.114));
    } else {
        // ChromaDepth mode: hue along spectrum = depth
        // Red (hue 0) = near, through spectrum, to violet = far
        float hue = rgb2hue(color);
        depth = 1.0 - hue;
    }

    // Expand depth contrast — push values away from midpoint
    depth = clamp(0.5 + (depth - 0.5) * f1, 0.0, 1.0);

    // Displace in opposite directions per eye
    float displacement = (depth - 0.5) * f0;
    float source_x;
    if (uv.x < 0.5) {
        source_x = base_x + displacement;
    } else {
        source_x = base_x - displacement;
    }

    source_x = clamp(source_x, 0.0, 1.0);
    gl_FragColor = texture2D(tex, vec2(source_x, uv.y));
}
