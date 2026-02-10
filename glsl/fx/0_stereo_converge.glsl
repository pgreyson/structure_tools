precision mediump float;
// stereo_converge : shift convergence plane of half-SBS stereo
//
// Horizontally offsets one eye relative to the other to push the
// entire perceived depth plane forward or backward. This doesn't
// change parallax between objects — it shifts where "screen depth"
// sits. Small shifts have a large perceptual effect.
//
// Overlap cropping: the shift creates monocular-only edges (pixels
// visible to one eye but not the other). The output is cropped to
// the overlap region and scaled to fill, so both eyes see matching
// content at all positions.
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

    // Crop to overlap region and scale to fill.
    // Margin = max shift so neither eye samples past its half-boundary.
    float margin = 0.05 * 0.5;  // half of max shift range

    float local_x;
    if (uv.x < 0.5) {
        local_x = uv.x * 2.0;  // 0..1 within left eye
        float base_x = margin + local_x * (0.5 - 2.0 * margin);
        gl_FragColor = texture2D(tex, vec2(base_x + shift * 0.5, uv.y));
    } else {
        local_x = (uv.x - 0.5) * 2.0;  // 0..1 within right eye
        float base_x = 0.5 + margin + local_x * (0.5 - 2.0 * margin);
        gl_FragColor = texture2D(tex, vec2(base_x - shift * 0.5, uv.y));
    }
}
