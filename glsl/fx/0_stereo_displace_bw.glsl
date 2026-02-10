precision mediump float;
// stereo_displace_bw : same as stereo_displace but with wide 3-tap
// depth blur (4px spacing) to smooth aliasing at depth discontinuities.
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
float f0 = mix(0.0, 0.08, fparams[0]);
float f1 = fparams[1];
float f2 = mix(-0.03, 0.03, fparams[2]);

void main(void) {
    vec2 uv = tcoord;

    float margin = f0 * 0.5 + abs(f2);

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

    // Depth per tap (luma only)
    float dL = dot(cL, vec3(0.299, 0.587, 0.114));
    float dC = dot(cC, vec3(0.299, 0.587, 0.114));
    float dR = dot(cR, vec3(0.299, 0.587, 0.114));

    // Weighted average (1,2,1)/4
    float depth = (dL + 2.0 * dC + dR) / 4.0;

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
