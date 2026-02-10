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
//   3. Shift base_x by +displacement for left eye, -displacement
//      for right eye. The shift magnitude scales with depth.
//   4. Apply convergence shift — a uniform offset that pushes the
//      entire depth plane nearer or farther without changing the
//      parallax between objects.
//
// Overlap cropping:
//   Both displacement and convergence create monocular-only edges.
//   The base coordinate is restricted to [margin, 1-margin] where
//   margin accounts for max displacement + current convergence.
//   This crops to the region visible to both eyes and scales to fill.
//
// f0 = depth — displacement intensity
// f1 = mode — luminance (left) or chromadepth/hue (right)
// f2 = converge — center = no shift, left = nearer, right = farther
varying vec2 tcoord;    // location
uniform sampler2D tex;  // texture one
uniform sampler2D tex2; // texture two
uniform vec2 tres;      // size of texture (screen)
uniform vec4 fparams;   // 4 floats coming in
uniform ivec4 iparams;  // 4 ints coming in
uniform float ftime;    // 0.0 to 1.0
uniform int itime;      // increases when ftime hits 1.0
//f0:depth:
//f1:mode:
//f2:converge:
float f0 = mix(0.0, 0.08, fparams[0]);   // max ~8% of frame width displacement
float f1 = fparams[1];                     // 0=luminance, 1=chromadepth
float f2 = mix(-0.03, 0.03, fparams[2]);  // convergence shift

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

    // Margin accounts for max displacement + convergence shift
    float margin = f0 * 0.5 + abs(f2);

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
    if (f1 < 0.5) {
        depth = dot(color, vec3(0.299, 0.587, 0.114));
    } else {
        float hue = rgb2hue(color);
        depth = 1.0 - hue;
    }

    // Displace + converge in opposite directions per eye
    float displacement = (depth - 0.5) * f0;
    float source_x;
    if (uv.x < 0.5) {
        source_x = base_x + displacement + f2;
    } else {
        source_x = base_x - displacement - f2;
    }

    source_x = clamp(source_x, 0.0, 1.0);
    gl_FragColor = texture2D(tex, vec2(source_x, uv.y));
}
