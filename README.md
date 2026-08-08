# immersive-01 — Unicorn Viz effect pack

**Version 0.10.1**


Enveloping, hypnotic depth visuals for
[unicorn-viz](https://github.com/iDoMeteor/unicorn-viz).

## Effects
- **Tunnel** — classic infinite tunnel
- **Wormhole** — lensed spiral corridor
- **Cathedral of Bass** — layered, room-shaking flight down an infinite nave:
  a fly-through corridor with bass-flexing arch pillars, a pulsing core light,
  treble godrays, and beat-fired shockwave rings — the whole frame recoils on the
  low end (beat/bass camera shake + zoom punch + chromatic aberration). Tweakable:
  `speed`, `intensity`, `shake_gain`, `fog`, `shockwave`, `bloom`.

Each effect subclasses `unicornviz.effects.base.BaseEffect` and is auto-discovered.

## Changelog

- **0.10.1** — Tunnel no longer crashes every frame it is on screen. It wrote
  a `iMid` uniform that the shader stopped using when the hue phase moved to
  CPU integration, so GLSL optimised the declaration away and moderngl never
  exposed it — `KeyError: 'iMid'` on the first frame, caught by the core's
  crash containment, which quarantined the effect for the session after the
  second occurrence. The dead uniform and its write are removed; `self._mid`
  still drives the hue on the CPU, so the look is unchanged.

- **0.10.0** — Tunnel: the mid-band hue rotation is now a CPU-integrated phase (audit 2026-08-03 §8 Class A) — the palette rotates faster with the music instead of strobing to a random color every frame at large time phases.
- **0.9.0** — initial versioned release.
