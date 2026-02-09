precision mediump float;
// stereo_displace : create stereo depth from monocular input
// Takes a flat (monocular) video synthesis input and produces half-SBS
// stereo by displacing pixels horizontally based on color/luminance.
// Same principle as ChromaDepth glasses but rendered digitally.
//
// f0 = displacement amount (depth intensity)
// f1 = depth mode: left = luminance, right = chromadepth (hue)
// f2 = depth invert: left = bright/red near, right = bright/red far
varying vec2 tcoord;    // location
uniform sampler2D tex;  // texture one
uniform sampler2D tex2; // texture two
uniform vec2 tres;      // size of texture (screen)
uniform vec4 fparams;   // 4 floats coming in
uniform ivec4 iparams;  // 4 ints coming in
uniform float ftime;    // 0.0 to 1.0
uniform int itime;      // increases when ftime hits 1.0
//f0::depth
//f1::mode
//f2::invert
float f0 = mix(0.0, 0.08, fparams[0]);   // max ~8% of frame width displacement
float f1 = fparams[1];                     // 0=luminance, 1=chromadepth
float f2 = fparams[2];                     // 0=normal, 1=inverted

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

    // The input is monocular — sample from the full frame
    // to determine depth at this position
    vec3 color = texture2D(tex, uv).rgb;

    // Compute depth value (0.0 to 1.0)
    float depth;
    if (f1 < 0.5) {
        // Luminance mode: brightness = depth
        depth = dot(color, vec3(0.299, 0.587, 0.114));
    } else {
        // ChromaDepth mode: hue along spectrum = depth
        // Red (hue 0) = near, violet (hue ~0.75) = far
        float hue = rgb2hue(color);
        // Map red→near (1.0), through spectrum, to violet→far (0.0)
        depth = 1.0 - hue;
    }

    // Invert if requested
    if (f2 > 0.5) depth = 1.0 - depth;

    // Compute displacement for this pixel
    float displacement = (depth - 0.5) * f0;

    // Output half-SBS: left eye in left half, right eye in right half
    float source_x;
    if (uv.x < 0.5) {
        // Left eye: sample shifted left
        source_x = uv.x * 2.0 + displacement;
    } else {
        // Right eye: sample shifted right
        source_x = (uv.x - 0.5) * 2.0 - displacement;
    }

    // Clamp to valid range
    source_x = clamp(source_x, 0.0, 1.0);

    gl_FragColor = texture2D(tex, vec2(source_x, uv.y));
}
