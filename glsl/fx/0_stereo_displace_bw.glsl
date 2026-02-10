precision mediump float;
// stereo_displace_bw : stereo_displace with wide 3-tap depth blur
// (4px spacing, ~8px kernel) to smooth aliasing at depth discontinuities.
// Supports both luma and chromadepth modes.
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
float f1 = mix(1.0, 4.0, fparams[1] * fparams[1]);   // depth contrast
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

    float margin = f0 * 0.5;

    float local_x;
    if (uv.x < 0.5) {
        local_x = uv.x * 2.0;
    } else {
        local_x = (uv.x - 0.5) * 2.0;
    }
    float base_x = margin + local_x * (1.0 - 2.0 * margin);

    // Wide 3-tap depth blur — 4px spacing covers ~8px kernel
    float px = 4.0 / tres.x;
    vec3 cL = texture2D(tex, vec2(base_x - px, uv.y)).rgb;
    vec3 cC = texture2D(tex, vec2(base_x, uv.y)).rgb;
    vec3 cR = texture2D(tex, vec2(base_x + px, uv.y)).rgb;

    // Depth per tap
    float dL, dC, dR;
    if (f2 < 0.5) {
        dL = dot(cL, vec3(0.299, 0.587, 0.114));
        dC = dot(cC, vec3(0.299, 0.587, 0.114));
        dR = dot(cR, vec3(0.299, 0.587, 0.114));
    } else {
        dL = 1.0 - rgb2hue(cL);
        dC = 1.0 - rgb2hue(cC);
        dR = 1.0 - rgb2hue(cR);
    }

    // Weighted average (1,2,1)/4
    float depth = (dL + 2.0 * dC + dR) / 4.0;

    // Expand depth contrast
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
