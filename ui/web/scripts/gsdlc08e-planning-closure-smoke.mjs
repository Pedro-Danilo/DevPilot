import fs from "node:fs";
const roadmap=fs.readFileSync(new URL("../src/pages/RoadmapWorkbenchView.ts",import.meta.url),"utf8");
const status=fs.readFileSync(new URL("../src/pages/ProjectStatusView.ts",import.meta.url),"utf8");
const client=fs.readFileSync(new URL("../src/api/client.ts",import.meta.url),"utf8");
const required=["Planning Workbench","Roadmap → Backlog → Sprint","DEVPL_LOCAL","MANUAL","IMPORT","AGENT","Approve humano","planningClosure","backlogPropose","sprintPropose","planningAuthoringStatus","roadmapGenerate","backlogDerive","sprintDerive"];
for(const token of required){if(!(roadmap+client).includes(token)) throw new Error(`missing planning closure token: ${token}`);}
for(const token of ["IMPLEMENTING_READY","journey_state","planningClosure"]){if(!status.includes(token)) throw new Error(`missing Project Status planning token: ${token}`);}
if(!roadmap.includes("BLOCKED BY SEQUENCE")) throw new Error("sequential planning gate UI missing");
if(roadmap.includes("REQ-001")||roadmap.includes("REQ-002")||roadmap.includes("RISK-001")) throw new Error("placeholder authority IDs must not be hardcoded in planning UI");
if(!roadmap.includes("Ver/editar JSON técnico avanzado")) throw new Error("raw JSON must be advanced/optional");
console.log("PASS - GSDLC-08-E/C04 planning closure static smoke");
