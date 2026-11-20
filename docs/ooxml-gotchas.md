# OOXML Gotchas

Generated captions intentionally place the label and number inside one object bookmark so `REF bookmark \\h` displays the complete label plus number. That makes the label/number start an unsafe paragraph-splitting point in Word: pressing Enter there can move bookmark endpoints and split fields across paragraphs. This is a Word editing limitation exposed by the native structure, not a paragraph-style setting. Insert before the caption from the preceding body paragraph instead; treat any cross-paragraph field/bookmark finding as a failed edit.

Use `xml:space="preserve"` for field instructions and visible spaces. Keep bookmarks globally unique. Use style names for `STYLEREF`. For references the tested switch order is `REF bookmark \* CHARFORMAT \h`. The target Word build rejected the reverse switch order during field updates.
