precision mediump float;
// stereo_zoom : centered zoom on L and R sides of SBS image
// f0 = zoom level (center = no zoom, right = zoom in, left = zoom out)
varying vec2 tcoord;    // location
uniform sampler2D tex;  // texture one
uniform sampler2D tex2; // texture two
uniform vec2 tres;      // size of texture (screen)
uniform vec4 fparams;   // 4 floats coming in
uniform ivec4 iparams;  // 4 ints coming in
uniform float ftime;    // 0.0 to 1.0
uniform int itime;      // increases when ftime hits 1.0
//f0:zoom:
//f1::
//f2::
float f0 = mix(0.1, 4.0, fparams[0]);

void main(void) {
    vec2 uv = tcoord;
    float zoom = f0;

    // Determine which eye we're in (left or right half)
    float eye_center;
    float eye_uv_x;
    if (uv.x < 0.5) {
        // Left eye: center at 0.25
        eye_center = 0.25;
        eye_uv_x = uv.x;
    } else {
        // Right eye: center at 0.75
        eye_center = 0.75;
        eye_uv_x = uv.x;
    }

    // Scale UV around the eye center
    float scaled_x = eye_center + (eye_uv_x - eye_center) / zoom;
    float scaled_y = 0.5 + (uv.y - 0.5) / zoom;

    // Black fill when outside the eye's bounds
    bool out_of_bounds = false;
    if (uv.x < 0.5) {
        if (scaled_x < 0.0 || scaled_x > 0.5) out_of_bounds = true;
    } else {
        if (scaled_x < 0.5 || scaled_x > 1.0) out_of_bounds = true;
    }
    if (scaled_y < 0.0 || scaled_y > 1.0) out_of_bounds = true;

    if (out_of_bounds) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        gl_FragColor = texture2D(tex, vec2(scaled_x, scaled_y));
    }
}
