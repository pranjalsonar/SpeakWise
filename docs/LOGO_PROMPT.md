# SpeakWise logo – prompt for a design tool

Paste the prompt below into your design/image tool. Then save the exported files into
`mobile/assets/images/` with the names in "Files to export" (they are already wired in `app.json`).

---

## Prompt

Design a logo and app icon for **SpeakWise**, a mobile app that coaches students to become
confident public speakers. You read a short article, speak about it to your phone's camera for
1–2 minutes, and get friendly AI feedback on your voice, eye contact and content.

**Personality:** warm, encouraging, calm and grown-up, like a supportive coach, not a corporate
tool and not a children's toy. Organic, friendly, confident.

**Concept (pick the strongest, keep it simple):**
- A rounded speech bubble that contains a short sound-wave (3–5 rounded vertical bars of
  different heights), or
- A soft letter "S" whose curve turns into a sound wave or a speech-bubble tail, or
- A microphone silhouette merged with a speech bubble.
The mark must still read at 48 px: bold shapes, no thin lines, no tiny details.

**Style:**
- Flat vector, solid fills, rounded corners and soft geometric curves.
- No gradients, no 3D, no glossy effects, no drop shadows, no photo realism, no text inside the icon.
- Generous breathing room around the mark.

**Colours (use only these):**
- Terracotta (primary) `#C67139`
- Deep terracotta (pressed/shadow tone) `#8C491A`
- Sage green (secondary accent, optional) `#728157`
- Cream (background) `#F5EAD8`
- Ink (text/dark) `#201E1D`
- Off-white (on terracotta) `#F9F4ED`

**Wordmark:** "SpeakWise" set in **Caprasimo** (a soft, chunky display serif), ink `#201E1D`
on cream. Mark on the left, wordmark on the right, plus a stacked version (mark above wordmark).

**Deliverables:**
1. App icon, 1024×1024: terracotta mark on a solid cream background (or cream mark on a
   terracotta background, whichever is stronger). Square canvas; the platform will round the corners.
2. Android adaptive-icon foreground, 1024×1024, transparent background, the mark only, kept
   inside the central 66% safe zone (about 676×676 px) so nothing is cut off by circular masks.
3. Monochrome version of the mark (single solid colour, transparent background) for Android's
   themed icons.
4. Splash mark, 1024×1024, transparent background, the mark only, terracotta, centred.
5. Horizontal and stacked wordmark lockups, transparent background, as SVG and PNG.
6. A version of the mark that works on a dark warm background `#1F1D1A` (cream or terracotta mark).

Show the icon at large size and at 48 px, on cream and on dark backgrounds.

---

## Files to export → `mobile/assets/images/`

| File | Size | Content |
|---|---|---|
| `icon.png` | 1024×1024 | Full app icon (mark on solid background) |
| `android-icon-foreground.png` | 1024×1024 | Mark only, transparent, inside the central 66% |
| `android-icon-background.png` | 1024×1024 | Solid cream `#F5EAD8` (or your chosen icon background) |
| `android-icon-monochrome.png` | 1024×1024 | Single-colour mark, transparent |
| `splash-icon.png` | 1024×1024 | Mark only, transparent (shown on cream / dark splash) |
| `favicon.png` | 48×48 | Small mark (web only) |

After replacing the files, the new icon and splash appear in the next EAS build (APK).
Expo Go always shows its own icon and splash, so you won't see them there.
