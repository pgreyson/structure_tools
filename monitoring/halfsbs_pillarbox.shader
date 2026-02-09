// halfsbs_pillarbox: correct 4:3→16:9 stretch in half-SBS capture
// Apply as source filter on the Elgato capture device in OBS.
// The analog→HDMI converter stretches 4:3 SD to 16:9 HDMI.
// This shader squeezes each eye back to correct aspect ratio
// with black pillarboxing, before the stretch-to-bounds transform
// doubles the width for full SBS output to Viture glasses.

uniform float aspect_correction<
    string label = "Aspect Correction";
    string widget_type = "slider";
    float minimum = 0.5;
    float maximum = 1.0;
    float step = 0.01;
> = 0.75; // 3/4 = undo 4/3 stretch

float4 mainImage(VertData v_in) : TARGET
{
    float2 uv = v_in.uv;

    // Determine which eye (left half or right half)
    float eye_left = step(uv.x, 0.5);     // 1.0 if left eye, 0.0 if right
    float eye_start = eye_left * 0.0 + (1.0 - eye_left) * 0.5;
    float eye_width = 0.5;

    // Position within this eye (0.0 to 1.0)
    float eye_uv_x = (uv.x - eye_start) / eye_width;

    // Squeeze to correct aspect ratio, centered
    float padding = (1.0 - aspect_correction) * 0.5;
    float corrected_x = (eye_uv_x - padding) / aspect_correction;

    // Black bars outside content area
    if (corrected_x < 0.0 || corrected_x > 1.0)
        return float4(0.0, 0.0, 0.0, 1.0);

    // Map back to source UV
    float source_x = eye_start + corrected_x * eye_width;
    return image.Sample(textureSampler, float2(source_x, uv.y));
}
