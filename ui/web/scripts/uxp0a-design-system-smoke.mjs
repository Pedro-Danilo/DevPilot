#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const webRoot=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const repoRoot=path.resolve(webRoot,'../..');
const read=(p)=>fs.readFileSync(path.join(webRoot,p),'utf8');
const readJson=(p)=>JSON.parse(read(p));
const projectState=JSON.parse(fs.readFileSync(path.join(repoRoot,'.devpilot/project_state.json'),'utf8'));
const tokens=read('src/design-tokens.css');
const styles=read('src/styles.css');
const main=read('src/main.ts');
const pkg=readJson('package.json');
const requiredTokens=['--dp-color-canvas','--dp-color-surface','--dp-color-text','--dp-color-action-primary','--dp-color-focus','--dp-state-pass-bg','--dp-state-warn-bg','--dp-state-block-bg','--dp-state-error-bg','--dp-state-pending-bg','--dp-space-4','--dp-radius-lg','--dp-shadow-panel','--dp-control-min-target'];
const failures=[];
for(const token of requiredTokens){if(!tokens.includes(token+':'))failures.push('missing-token:'+token);}
if(!styles.startsWith('@import "./design-tokens.css";')) failures.push('tokens-not-imported');
for(const marker of ['var(--dp-color-text)','var(--dp-color-canvas)','var(--dp-color-border)','var(--dp-color-action-primary)','var(--dp-color-focus)']){if(!styles.includes(marker))failures.push('token-not-adopted:'+marker);}
if(pkg.version!=='0.38.0-ux-p0-a') failures.push('package-version');
if(pkg.devpilot?.currentSprint!=='DEVPL-UX-P0-A') failures.push('current-sprint');
if(pkg.devpilot?.uxP0RoutePathsChanged!==false) failures.push('route-change-flag');
if(pkg.devpilot?.uxP0ServerAuthorityChanged!==false) failures.push('authority-change-flag');
if(projectState.current_phase!=='DEVPL-UX-P0'||projectState.current_micro_sprint!=='DEVPL-UX-P0-A') failures.push('project-state-rebind');
for(const pathMarker of ['/project/status','/pre-code','/planning/roadmap','/story/code','/release/closure','/recovery','/reconciliation']){if(!main.includes(`path: '${pathMarker}'`)) failures.push('route-missing:'+pathMarker);}
console.log(JSON.stringify({schema_id:'devpilot.ux_p0_a.design_system_smoke.v1',status:failures.length?'BLOCK':'PASS',required_tokens_total:requiredTokens.length,route_paths_changed:false,server_authority_changed:false,full_regression_runs:0,failures},null,2));
process.exit(failures.length?2:0);
