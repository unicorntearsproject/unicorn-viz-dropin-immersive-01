"""
Cathedral of Bass — a layered, room-shaking flight down an infinite nave.

A single-pass but heavily layered fragment effect: you fly forward through a
cathedral corridor (angular panels + longitudinal bricks), bright arch pillars
flex with the bass, a core light pulses at the vanishing point, godray streaks
sweep with the treble, and beats fire expanding shockwave rings. The whole
frame *recoils* on the low end — a beat/bass-driven camera shake plus a zoom
"punch" and radial chromatic aberration make it feel like the room is moving.

Audio-reactive:
  - bass   → pillar flex, core-glow surge, zoom punch
  - mid    → wall brightness / colour motion
  - treble → godray sparkle, chromatic edge
  - beat   → camera-shake recoil + shockwave ring + violet bloom

Everything is tweakable via ``self.parameters`` (speed, intensity, shake_gain,
fog, shockwave, bloom) so the control room / OSC / MIDI can ride it like a rig.
Per-instance hue + twist + pillar phase keep runs distinct from frame 0.
"""
from __future__ import annotations

import moderngl

from unicornviz.effects.base import BaseEffect, AudioData

_VERT = """
#version 330
in vec2 in_vert;
out vec2 v_uv;
void main() {
    v_uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

_FRAG = """
#version 330
// Cathedral of Bass — layered immersive corridor + room-shake post.
uniform float iTime;
uniform vec2  iResolution;
uniform float iBass;
uniform float iMid;
uniform float iTreble;
uniform float iShake;      // beat-recoil envelope [0,1]
uniform float iFlash;      // beat-bloom / shockwave envelope [0,1]
uniform float iSpeed;
uniform float iIntensity;  // master
uniform float iFog;
uniform float iShock;
uniform float iBloom;
uniform float iShakeGain;
uniform float iHue;        // palette offset
uniform float iTwist;      // corridor roll
in  vec2 v_uv;
out vec4 fragColor;

vec3 pal(float t) {
    return 0.5 + 0.5 * cos(6.28318 * (t + vec3(0.0, 0.33, 0.67) + iHue));
}

// Layered corridor scene sampled at aspect-corrected, centred point p.
vec3 scene(vec2 p, float t) {
    float r = length(p) + 1e-4;
    float a = atan(p.y, p.x) + iTwist * sin(t * 0.2);
    float depth = 1.0 / r;                    // large near the vanishing point
    float z = depth * 1.2 - t * (1.2 + iSpeed);
    vec3 col = vec3(0.0);

    float fog = exp(-r * (2.2 - iFog * 1.5));

    // Tunnel walls: angular panels x longitudinal bricks.
    float ang = a / 6.28318;
    float wall = (0.5 + 0.5 * sin(ang * 24.0)) * (0.5 + 0.5 * sin(z * 3.0));
    col += pal(z * 0.05 + ang * 0.5) * wall * fog * (0.6 + iMid * 0.9);

    // Arch pillars: bright ribs at intervals of z, flexing with bass.
    float rib = smoothstep(0.12, 0.0, abs(fract(z * 0.5) - 0.5) - 0.02);
    rib *= smoothstep(0.95, 0.2, r);
    col += pal(z * 0.05 + 0.3) * rib * (0.8 + iBass * 1.8) * fog;

    // Core glow — the light at the end, surging with bass.
    col += vec3(1.0, 0.9, 0.8) * exp(-r * 6.0) * (1.4 + iBass * 3.2);

    // Godray streaks from centre, treble-lit.
    float rays = pow(0.5 + 0.5 * sin(a * 16.0 + t * 2.0), 6.0);
    col += pal(0.6) * rays * smoothstep(0.0, 0.6, r)
           * smoothstep(1.1, 0.4, r) * (0.15 + iTreble * 0.7);
    return col;
}

void main() {
    vec2 uv = v_uv * 2.0 - 1.0;
    uv.x *= iResolution.x / iResolution.y;
    float t = iTime;

    // Room shake: high-frequency beat recoil + bass zoom punch.
    float sh = iShake * iShakeGain;
    vec2 shake = vec2(sin(t * 63.0), cos(t * 57.0)) * sh * 0.06;
    float zoom = 1.0 - (iBass * 0.10 + iShake * 0.18) * iIntensity;
    vec2 p = uv * zoom + shake;

    // Radial chromatic aberration, stronger on hits and toward the edges.
    float ca = (0.004 + sh * 0.02) * (0.5 + length(p));
    vec2 dir = normalize(p + 1e-4);
    vec3 col;
    col.r = scene(p + dir * ca, t).r;
    col.g = scene(p, t).g;
    col.b = scene(p - dir * ca, t).b;

    // Beat shockwave ring expanding outward.
    float ring = max(0.0, sin(length(uv) * 14.0 - iFlash * 10.0));
    col += pal(0.15) * ring * iFlash * iShock * smoothstep(1.2, 0.1, length(uv));

    // Beat bloom + master intensity + cheap bright-lift bloom.
    col += vec3(0.9, 0.7, 1.0) * iFlash * 0.15;
    col *= 0.7 + 0.6 * iIntensity;
    col += pow(max(col - 0.6, 0.0), vec3(1.5)) * iBloom * 2.0;

    // Vignette, tonemap, grade.
    col *= 1.0 - 0.5 * smoothstep(0.6, 1.5, length(uv));
    col = col / (1.0 + col);
    col = pow(col, vec3(0.85));
    fragColor = vec4(col, 1.0);
}
"""


class CathedralOfBass(BaseEffect):
    NAME = "Cathedral of Bass"
    AUTHOR = "unicorn-viz"
    TAGS = ['immersive', 'bass', 'shader', 'raver', 'cathedral', 'hard']
    PING_PONG_FRIENDS = [
        # Immersive / cosmic neighbours
        'Wormhole',
        'Tunnel',
        'Black Hole Cathedral',
        'Cosmos',
        # Psychedelics
        'Plasma',
        'Kaleidoscope',
        'Psychedelic',
        # Audio-analysis visualizers
        'Audio Spectrum',
        'Audio Spectrogram',
        'Audio Tracks',
        'Audio Waveforms',
        'Audio Centroid',
        'Audio Sine',
    ]

    def _init(self) -> None:
        self.parameters = {
            "speed": float(self.config.get("speed", 1.0)),
            "intensity": float(self.config.get("intensity", 1.0)),
            "shake_gain": float(self.config.get("shake_gain", 1.0)),
            "fog": float(self.config.get("fog", 0.5)),
            "shockwave": float(self.config.get("shockwave", 1.0)),
            "bloom": float(self.config.get("bloom", 0.6)),
            # Startup randomisation so runs differ from frame 0.
            "hue": float(self.rng.uniform(0.0, 1.0)),
            "twist": float(self.rng.uniform(-0.6, 0.6)),
        }
        self._bass = 0.0
        self._mid = 0.0
        self._treble = 0.0
        self._shake = 0.0
        self._flash = 0.0
        self._prog = self._make_program(_VERT, _FRAG)
        self._vao, self._vbo = self._fullscreen_quad()

    def update(self, dt: float, audio: AudioData) -> None:
        super().update(dt, audio)
        self._bass = audio.bass_n
        self._mid = audio.mid_n
        self._treble = audio.treble_n
        # Beat-driven recoil + shockwave envelopes, with decay.
        self._shake = max(0.0, self._shake - dt * 3.6)
        self._flash = max(0.0, self._flash - dt * 2.6)
        if audio.beat:
            self._shake = 1.0
            self._flash = 1.0
        # Sub-bass also nudges the shake so heavy low end keeps the room moving.
        self._shake = max(self._shake, self._bass * 0.35)

    def render(self) -> None:
        p = self._prog
        p["iTime"].value = self.time
        p["iResolution"].value = (float(self.width), float(self.height))
        p["iBass"].value = self._bass
        p["iMid"].value = self._mid
        p["iTreble"].value = self._treble
        p["iShake"].value = self._shake
        p["iFlash"].value = self._flash
        p["iSpeed"].value = self.parameters["speed"]
        p["iIntensity"].value = self.parameters["intensity"]
        p["iFog"].value = self.parameters["fog"]
        p["iShock"].value = self.parameters["shockwave"]
        p["iBloom"].value = self.parameters["bloom"]
        p["iShakeGain"].value = self.parameters["shake_gain"]
        p["iHue"].value = self.parameters["hue"]
        p["iTwist"].value = self.parameters["twist"]
        self._vao.render(moderngl.TRIANGLE_STRIP)

    def destroy(self) -> None:
        self._vao.release()
        self._vbo.release()
        self._prog.release()
