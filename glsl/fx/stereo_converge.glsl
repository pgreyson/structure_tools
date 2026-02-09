precision mediump float;
// stereo_converge : shift convergence plane of half-SBS stereo
// Horizontally offsets one eye relative to the other to push the
// perceived depth plane forward or backward. Small shifts have
// a large perceptual effect.
//
// f0 = convergence shift (center = no shift, left = nearer, right = farther)
varying vec2 tcoord;    // location
uniform sampler2D tex;  // texture one
uniform sampler2D tex2; // texture two
uniform vec2 tres;      // size of texture (screen)
uniform vec4 fparams;   // 4 floats coming in
uniform ivec4 iparams;  // 4 ints coming in
uniform float ftime;    // 0.0 to 1.0
uniform int itime;      // increases when ftime hits 1.0
//f0:converge:
//f1::
//f2::
float f0 = mix(-0.05, 0.05, fparams[0]);  // +/- 5% of eye width

void main(void) {
    vec2 uv = tcoord;
    float shift = f0;

    float sample_x;
    if (uv.x < 0.5) {
        // Left eye: shift one direction
        sample_x = uv.x + shift * 0.5;
        sample_x = clamp(sample_x, 0.0, 0.5);
    } else {
        // Right eye: shift the other direction
        sample_x = uv.x - shift * 0.5;
        sample_x = clamp(sample_x, 0.5, 1.0);
    }

    gl_FragColor = texture2D(tex, vec2(sample_x, uv.y));
}
