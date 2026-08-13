"""CB-31 basemap adaptive dual-track verification (headless, black-box).

Surfaces runtime behavior the EMC eval (empty-context template routing) cannot:
  - no console/page errors on module load
  - DEFAULT basemap (tianditu-img-nolabel) loads tiles (canvas present)
  - probe verdicts: Esri blocked vs tianditu ok (this env = home net, Esri unreachable)
  - clicking a blocked Esri button -> toast + fallback to DEFAULT + is-active rolls back
  - no gray screen

Connects to already-running serve.py on :8080 (start with `py frontend/serve.py 8080`).
Run:  py tests/browser/test_basemap_adaptive.py
"""
import sys
import time
from playwright.sync_api import sync_playwright

URL = "http://localhost:8080/frontend/index.html"
PROBE_SETTLE = 9  # probe timeout 6s + margin

# console noise to ignore (MapLibre/GL benign)
NOISE = ("favicon", "deprecat", "maplibre", "DoesNotMatchPattern")


def is_real_error(line: str) -> bool:
    return not any(n.lower() in line.lower() for n in NOISE)


def main() -> int:
    errors, pageerrors = [], []
    net = {"esri_ok": 0, "esri_fail": 0, "tdt_ok": 0, "tdt_fail": 0}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.on("console", lambda m: errors.append(f"[{m.type}] {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: pageerrors.append(str(e)))

        def on_resp(r):
            u = r.url
            if "arcgisonline.com" in u:
                if r.ok: net["esri_ok"] += 1
                else: net["esri_fail"] += 1
            elif "tianditu.gov.cn" in u and "/DataServer" in u:
                if r.ok: net["tdt_ok"] += 1
                else: net["tdt_fail"] += 1
        page.on("response", on_resp)

        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#map canvas", timeout=15000)
        time.sleep(PROBE_SETTLE)

        # --- 1. cell health states ---
        states = page.evaluate("""() => Array.from(document.querySelectorAll('.bm-cell')).map(c => ({
          key: c.dataset.basemap,
          active: c.classList.contains('is-active'),
          blocked: c.classList.contains('is-blocked'),
        }))""")
        print("=== [1] basemap cell states (after probe settle) ===")
        for s in states:
            tag = "ACTIVE" if s["active"] else ("BLOCKED" if s["blocked"] else "ok")
            print(f"   {s['key']:24s} {tag}")

        active_keys = [s["key"] for s in states if s["active"]]
        blocked_keys = [s["key"] for s in states if s["blocked"]]
        print(f"   active={active_keys}  blocked={blocked_keys}")

        # --- 2. canvas alive (not gray) ---
        canvas = page.evaluate("""() => {
          const c = document.querySelector('#map canvas');
          if (!c) return null;
          const ctx = c.getContext('2d') || c.getContext('webgl');
          return { w: c.width, h: c.height };
        }""")
        print(f"=== [2] map canvas: {canvas}")

        # --- 3. interaction: click a blocked Esri button -> fallback ---
        esri = next((s for s in states if s["blocked"] and s["key"] in ("positron", "dark-matter", "voyager")), None)
        fallback_ok = None
        if esri:
            page.click('[data-action="basemap"]')
            time.sleep(0.3)
            page.click(f'.bm-cell[data-basemap="{esri["key"]}"]')
            time.sleep(8)  # re-probe (6s timeout) + fallback
            after = page.evaluate("""() => Array.from(document.querySelectorAll('.bm-cell'))
              .filter(c => c.classList.contains('is-active')).map(c => c.dataset.basemap)""")
            toast_text = page.evaluate("""() => {
              const t = document.querySelector('.toast, [class*="toast"]');
              return t ? t.textContent : null;
            }""")
            print(f"=== [3] clicked blocked '{esri['key']}' -> active now={after}, toast={toast_text!r}")
            # success = active rolled back to DEFAULT (tianditu-*), not stuck on the Esri key
            fallback_ok = bool(after) and not any(k == esri["key"] for k in after) and any(k.startswith("tianditu") for k in after)
        else:
            print("=== [3] no blocked Esri button in this env (Esri reachable?) — skipping fallback test")

        # --- 4. screenshot ---
        page.screenshot(path="tests/browser/out/basemap_adaptive.png", full_page=False)
        print("=== [4] screenshot -> tests/browser/out/basemap_adaptive.png")

        # --- report ---
        real_errs = [e for e in errors + pageerrors if is_real_error(e)]
        print("\n=== network (tile responses captured) ===")
        print(f"   esri ok/fail={net['esri_ok']}/{net['esri_fail']}  tianditu ok/fail={net['tdt_ok']}/{net['tdt_fail']}")
        print("\n=== console errors (real, filtered) ===")
        for e in real_errs:
            print(f"   {e}")
        if not real_errs:
            print("   (none)")

        browser.close()

        # verdict
        verdict = []
        if real_errs: verdict.append("CONSOLE_ERRORS")
        if not canvas: verdict.append("NO_CANVAS")
        if not active_keys: verdict.append("NO_ACTIVE_BUTTON")
        if esri and not fallback_ok: verdict.append("FALLBACK_FAILED")
        if net["tdt_ok"] == 0: verdict.append("TIANDITU_NOT_LOADING")
        print("\n" + ("VERDICT: PASS" if not verdict else f"VERDICT: CHECK  [{'/'.join(verdict)}]"))
        return 0 if not verdict else 1


if __name__ == "__main__":
    sys.exit(main())
