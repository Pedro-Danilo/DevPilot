import type { AuthSessionContext } from '../api/types';
import { DevPilotApiClient } from '../api/client';

export function renderAccountRoleView(session: AuthSessionContext): HTMLElement {
  const section=document.createElement('section'); section.className='account-role-view'; section.dataset.routeId='ui.account-role';
  const h=document.createElement('h2'); h.textContent='Cuenta y autoridad efectiva';
  const identity=document.createElement('dl'); identity.className='account-grid';
  for(const [k,v] of [['Actor',session.principal.actor_id],['Usuario',session.principal.username],['Nombre',session.principal.display_name],['Roles',session.principal.roles.join(', ')],['Workspaces',session.principal.workspace_scopes.join(', ')],['Autenticación',session.principal.auth_method],['Expira',session.absolute_expires_at]]){const dt=document.createElement('dt');dt.textContent=k;const dd=document.createElement('dd');dd.textContent=v;identity.append(dt,dd);}
  const capability=document.createElement('pre'); capability.className='viewer-pre'; capability.textContent='Cargando capability view derivada del servidor…';
  void new DevPilotApiClient().authCapabilities().then((v)=>{capability.textContent=JSON.stringify(v,null,2);}).catch(()=>{capability.textContent='No fue posible cargar capability view. La UI no eleva autoridad localmente.';});
  section.append(h,identity,capability); return section;
}
