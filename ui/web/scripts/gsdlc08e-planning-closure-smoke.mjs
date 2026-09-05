import fs from "node:fs";
const roadmap=fs.readFileSync(new URL("../src/pages/RoadmapWorkbenchView.ts",import.meta.url),"utf8");
const status=fs.readFileSync(new URL("../src/pages/ProjectStatusView.ts",import.meta.url),"utf8");
const client=fs.readFileSync(new URL("../src/api/client.ts",import.meta.url),"utf8");
const required=["Planning Workbench","Roadmap → backlog → sprint","MANUAL","IMPORT","AGENT","Trace graph planning","Approve humano","planningClosure","backlogPropose","sprintPropose"];
for(const token of required){if(!(roadmap+client).includes(token)) throw new Error(`missing planning closure token: ${token}`);}
for(const token of ["IMPLEMENTING_READY","journey_state","planningClosure"]){if(!status.includes(token)) throw new Error(`missing Project Status planning token: ${token}`);}
if(!roadmap.includes("b.disabled=true")) throw new Error("role-bound UI disable missing");
if(!roadmap.includes("advisorMount.replaceChildren")) throw new Error("advisor render must be idempotent");
console.log("PASS - GSDLC-08-E planning closure static smoke");
