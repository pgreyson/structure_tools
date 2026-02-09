precision mediump float;
// stereo_sbs : side-by-side compositor for stereo generation
// Composites input 1 (left eye) and input 2 (right eye) into
// half-SBS format. Use with a nodeset that has two generators
// (e.g. GEN1 → MIX1 ← GEN2) where each gen renders the scene
// from a slightly different camera position.
//
// f0 = eye separation (how much the camera offset differs between eyes)
//       center = default separation, adjustable via CV
varying vec2 tcoord;    // location
uniform sampler2D tex;  // texture one (left eye / input 1)
uniform sampler2D tex2; // texture two (right eye / input 2)
uniform vec2 tres;      // size of texture (screen)
uniform vec4 fparams;   // 4 floats coming in
uniform ivec4 iparams;  // 4 ints coming in
uniform float ftime;    // 0.0 to 1.0
uniform int itime;      // increases when ftime hits 1.0
//f0::blend
//f1::
//f2::
float f0 = fparams[0];  // 0=hard split, 1=crossfade at seam

void main(void) {
    vec2 uv = tcoord;

    if (uv.x < 0.5) {
        // Left half: sample from input 1 (left eye)
        vec2 eye_uv = vec2(uv.x * 2.0, uv.y);
        gl_FragColor = texture2D(tex, eye_uv);
    } else {
        // Right half: sample from input 2 (right eye)
        vec2 eye_uv = vec2((uv.x - 0.5) * 2.0, uv.y);
        gl_FragColor = texture2D(tex2, eye_uv);
    }
}
