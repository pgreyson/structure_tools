precision mediump float;
// stereo_rects_R : stereoscopic floating rectangles - RIGHT EYE
//
// Renders colored rectangles at different z-depths, drifting and
// rotating. The depth of each rectangle determines its parallax
// offset and perspective size. Pair with stereo_rects_L on GEN1
// and route both through stereo_sbs on MIX1:
//   GEN1 (L) → MIX1 ← GEN2 (this, R)
//
// The only difference between L and R is the sign of EYE_X.
// Convergence is at mid-depth — closer rects pop out, farther
// rects recede behind the screen.
//
// f0 = speed (animation rate)
// f1 = spread (stereo depth / eye separation)
// f2 = hue (color rotation)
varying vec2 tcoord;    // location
uniform sampler2D tex;  // texture one
uniform sampler2D tex2; // texture two
uniform vec2 tres;      // size of texture (screen)
uniform vec4 fparams;   // 4 floats coming in
uniform ivec4 iparams;  // 4 ints coming in
uniform float ftime;    // 0.0 to 1.0
uniform int itime;      // increases when ftime hits 1.0
//f0:speed:
//f1:spread:
//f2:hue:
float f0 = mix(0.2, 2.0, fparams[0]);
float f1 = mix(0.005, 0.03, fparams[1]);
float f2 = fparams[2];

// +1.0 for left eye, -1.0 for right eye
const float EYE_X = -1.0;

// Soft-edged rectangle SDF
float rectSDF(vec2 p, vec2 center, vec2 halfsize, float angle) {
    float ca = cos(angle);
    float sa = sin(angle);
    vec2 d = p - center;
    vec2 rd = vec2(ca * d.x + sa * d.y, -sa * d.x + ca * d.y);
    vec2 q = abs(rd) - halfsize;
    return max(q.x, q.y);
}

// HSV to RGB
vec3 hsv2rgb(float h, float s, float v) {
    vec3 rgb = clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    return v * mix(vec3(1.0), rgb, s);
}

// Per-rect pseudo-random
float hash(float n) {
    return fract(sin(n * 127.1) * 43758.5453);
}

void main(void) {
    vec2 p = tcoord - 0.5;
    float time = (float(itime) + ftime) * f0;
    float eye_sep = f1;

    vec3 col = vec3(0.03);

    // 6 rectangles, drawn back (i=0) to front (i=5)
    for (int i = 0; i < 6; i++) {
        float fi = float(i);
        float depth = 1.0 - fi * 0.1;  // 1.0 (far) to 0.5 (near)

        // Unique oscillation per rect
        vec2 center = vec2(
            sin(time * (0.3 + fi * 0.11) + fi * 2.1) * 0.28,
            cos(time * (0.25 + fi * 0.09) + fi * 1.7) * 0.22
        );

        // Stereo parallax — convergence at depth 0.75
        center.x += EYE_X * eye_sep * (1.0 / depth - 1.0 / 0.75);

        // Perspective size (nearer = larger)
        vec2 halfsize = vec2(
            0.05 + hash(fi) * 0.04,
            0.03 + hash(fi + 7.0) * 0.03
        ) / depth;

        // Slow rotation
        float angle = time * (0.15 + fi * 0.07) + fi * 0.8;

        // Draw
        float d = rectSDF(p, center, halfsize, angle);
        float mask = 1.0 - smoothstep(-0.004, 0.004, d);

        // Color
        float hue = fract(fi / 6.0 + f2);
        vec3 rc = hsv2rgb(hue, 0.7, 0.9);

        col = mix(col, rc, mask);
    }

    gl_FragColor = vec4(col, 1.0);
}
