# ReadToMe-TTS — Decisions (append-only)

Each entry: context, decision, why, alternatives, outcome. New entries go at the end via
`history/tools/log-entry.sh <project> decision "<title>"`. A changed decision is a new entry that
`--supersedes` the old id; the old entry stays. Format: `history/README.md`.

### D-0001 — 2026-11-18 — Latency strategy: pipeline + persistent stream + silence caps
- **Logged:** 2026-11-18 17:49 UTC by Claude Code / Fable 5
- **Context:** v0.3.2 had ~200ms fixed clipboard wait, no synthesis/playback overlap (every sentence boundary waited for the next sentence's synthesis), a new PortAudio stream per sentence (~100-250ms gap each), and untrimmed model-generated silences (~200-400ms per sentence end).
- **Decision:** (1) Poll clipboard every 10ms after Ctrl+C instead of fixed 150ms sleep. (2) Producer/consumer pipeline: synthesis thread fills a bounded queue (8 chunks) while playback consumes. (3) One persistent sd.OutputStream per utterance, blocking writes in ~93ms slices for responsive interruption. (4) Cap model silences in post-processing: sentence/newline trailing+leading silence to sentence_pause_ms (150 default), internal (comma) silences to comma_pause_ms (100 default), threshold 330/32767 amplitude. (5) Warmup synthesis after model load to absorb ONNX Runtime first-inference cost. (6) Feed text to Piper line-by-line so whole-text phonemization doesn't delay first audio.
- **Why:** Each item attacks a distinct measured latency source; together they cut hotkey-to-speech ~150-300ms and inter-sentence gaps from ~500ms+ to a consistent ~150ms. DSP silence capping was chosen over Piper API knobs because piper 1.4.1's SynthesisConfig has no sentence-silence setting and the pauses live inside the model's own output.
- **Alternatives:** sounddevice callback-based streaming (more complex, no gain over blocking writes here); splitting sentences in Python instead of relying on espeak (worse sentence detection); tuning length_scale to shrink pauses (also speeds up speech — wrong tool).
- **Outcome:** Shipped in v0.3.3; user confirmed pauses feel right. Pause caps made tray-configurable in v0.4.0.


### D-0002 — 2026-11-18 — Stop shortcut as second modifier-only hotkey (default Ctrl+Alt)
- **Logged:** 2026-11-18 17:49 UTC by Claude Code / Fable 5
- **Context:** v0.4.0 adds a way to stop speech without quitting ("buzz button"). Options: tray menu only, Esc key, reuse of read hotkey, or a second configurable global hotkey.
- **Decision:** Second HotkeyManager instance with capture_text=False (callback fires without the Ctrl+C clipboard dance), default "ctrl+alt", plus a "Stop Speaking" tray item. combos_conflict() rejects read/stop combos that would trigger each other, including modifier-only subsets (a modifier-only combo fires while any superset is held). If an upgraded config has a read shortcut conflicting with the stop default, the stop hotkey is simply not registered (tray item still works) rather than breaking the read shortcut.
- **Why:** Modifier-only default matches the read shortcut rationale (works over RDP/Citrix full keystroke capture; user drives via macro mouse buttons). Ctrl+Alt chosen over Ctrl+Shift because Ctrl+Shift+<key> app shortcuts are far more common than Ctrl+Alt ones; AltGr (=Ctrl+Alt) only matters on non-US layouts and the shortcut is configurable.
- **Alternatives:** Esc to stop (conflicts with normal Esc use, not configurable); pressing read hotkey with empty selection as stop gesture (unreliable — selection usually still highlighted).
- **Outcome:** Implemented in v0.4.0 with conflict validation on both configure flows.

