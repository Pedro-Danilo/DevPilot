import fs from 'node:fs';
const main=fs.readFileSync(new URL('../src/main.ts', import.meta.url),'utf8');
const css=fs.readFileSync(new URL('../src/styles.css', import.meta.url),'utf8');
const checks={skip_link:main.includes("skip-link")&&main.includes("Saltar al contenido principal"),main_landmark:main.includes("role', 'main")&&main.includes("route-main"),nav_label:main.includes("aria-label",),focus_visible:css.includes(':focus-visible'),reduced_motion:css.includes('prefers-reduced-motion'),target_44:css.includes('min-height: 44px')};
const failed=Object.entries(checks).filter(([,ok])=>!ok).map(([id])=>id);
console.log(JSON.stringify({schema_id:'devpilot.uoc011.accessibility_smoke.v1',status:failed.length?'BLOCK':'PASS',checks,failed},null,2));
process.exit(failed.length?2:0);
