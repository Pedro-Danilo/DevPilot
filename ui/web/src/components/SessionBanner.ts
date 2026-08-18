import type { AuthSessionContext } from '../api/types';
import { DevPilotApiClient } from '../api/client';

export function renderSessionBanner(session: AuthSessionContext, onLogout: () => void): HTMLElement {
  const banner=document.createElement('aside'); banner.className='session-banner'; banner.dataset.authenticated='true'; banner.setAttribute('aria-label','Sesión autenticada');
  const identity=document.createElement('div'); identity.className='session-banner__identity'; identity.textContent=`${session.principal.display_name} · ${session.principal.username}`;
  const roles=document.createElement('div'); roles.className='session-banner__roles'; roles.textContent=`Roles: ${session.principal.roles.join(', ')}`;
  const account=document.createElement('a'); account.href='/account'; account.textContent='Cuenta y roles';
  const logout=document.createElement('button'); logout.type='button'; logout.className='button-secondary'; logout.textContent='Cerrar sesión';
  logout.addEventListener('click',async()=>{logout.disabled=true; try{await new DevPilotApiClient().authLogout();}finally{onLogout();}});
  banner.append(identity,roles,account,logout); return banner;
}
