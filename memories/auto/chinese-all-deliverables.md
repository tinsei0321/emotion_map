---
name: chinese-all-deliverables
description: "User wants Chinese in ALL written deliverables (plans, reports, docs, prose), not just chat replies — English only for code/paths/identifiers"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e2916142-0dbf-4da0-85af-8d5a363143bd
---

User expects Chinese for every written deliverable — plan files, reports, docs, commit-message prose, code-comment narrative — not only chat replies. Was annoyed when a plan file was written mostly in English: "我明确的说过我们的各种交流都用中文".

**Why:** CLAUDE.md's "默认中文回复" had been read as chat-only; the user intends it to cover all artifacts and deliverables.

**How to apply:** In any written output (plan/report/doc/PR body/handoff), write the narrative in Chinese; keep code, commands, variable names, file paths, library names, and technical identifiers in English. Apply project-wide, every time.
