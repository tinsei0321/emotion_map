---
name: emc-eval-empty-context-vs-runtime
description: "EMC Flash eval runs diagnose with empty context; real serve runs with buildContext grounding — eval% doesn't guarantee runtime routing when layers are loaded"
metadata: 
  node_type: memory
  type: project
  originSessionId: d3f82260-4ca0-40ff-9082-d005d35e81db
---

`tests/eval_template_flash.py` calls `build_diagnose_prompt('')` — **empty context**. So the eval tests Flash's template selection purely from the question + static prompt appendices (paradigm tree, few-shot). It does **not** simulate loaded layers.

Real serve runs diagnose with `buildContext()` grounding (the visible-layers list). So for **ambiguous queries with multiple candidate layers loaded**, runtime routing can diverge from the eval's empty-context prediction.

Concrete (C1, 07-16): "居住用地里情绪差的地方" → eval expects `overlay` (and hits it empty-context), but with 用地_居住 + L2 points loaded, Flash picked **`zonal`** (boundary=用地_居住, agg polarity). zonal is a valid interpretation — not a hard bug; accepted.

**How to apply**: Don't treat eval N% as proof of runtime routing for boundary/layer-slot filling (merge/clip/overlay/area_stats). To verify routing WITH grounding, replicate the eval with a hand-crafted grounding string (simulate `buildContext` output) + Flash, or drive the browser — the empty-context eval alone won't catch it. Same lesson as [[verify-real-endpoint]]: test the real path, not the simulated one. The buildContext fix that made Flash fill boundary slots is recorded in revision-log 5.105 (commit 82cbc8b).
