import { DevPilotApiClient, DevPilotApiError } from '../api/client';

export function renderLoginView(onAuthenticated: () => void, reason = ''): HTMLElement {
  const section=document.createElement('section'); section.className='auth-page login-view'; section.dataset.authState='login';
  const card=document.createElement('div'); card.className='auth-card';
  const h=document.createElement('h1'); h.textContent='Iniciar sesión en DevPilot';
  const p=document.createElement('p'); p.textContent='Autenticación local. La contraseña no se guarda en la UI y la sesión usa cookie HttpOnly + CSRF.';
  const notice=document.createElement('p'); notice.className='auth-notice'; notice.textContent=reasonMessage(reason);
  const form=document.createElement('form'); form.className='auth-form';
  const user=document.createElement('input'); user.name='username'; user.autocomplete='username'; user.required=true; user.placeholder='usuario.local'; user.minLength=3;
  const pass=document.createElement('input'); pass.name='password'; pass.type='password'; pass.autocomplete='current-password'; pass.required=true; pass.placeholder='Contraseña';
  const submit=document.createElement('button'); submit.type='submit'; submit.textContent='Ingresar';
  const status=document.createElement('p'); status.setAttribute('role','status'); status.className='auth-status';
  form.append(label('Usuario',user),label('Contraseña',pass),submit,status);
  form.addEventListener('submit',async(ev)=>{ev.preventDefault(); submit.disabled=true; status.textContent='Verificando credenciales…'; try { await new DevPilotApiClient().authLogin({username:user.value,password:pass.value}); pass.value=''; onAuthenticated(); } catch(e){ pass.value=''; status.textContent=authError(e); } finally { submit.disabled=false; }});
  card.append(h,p,notice,form); section.append(card); return section;
}
function label(text:string,input:HTMLInputElement){const l=document.createElement('label'); l.textContent=text; l.append(input); return l;}
function reasonMessage(reason:string):string { if(reason==='expired') return 'La sesión expiró. Vuelve a autenticarte.'; if(reason==='revoked') return 'La sesión fue revocada. Vuelve a autenticarte.'; if(reason==='logout') return 'Sesión cerrada correctamente.'; if(reason==='stale') return 'La autoridad de la sesión cambió y fue invalidada.'; if(reason==='required') return 'Debes iniciar sesión para abrir el Project Shell.'; return ''; }
function authError(error:unknown):string { if(error instanceof DevPilotApiError){ if(error.status===401) return 'Credenciales inválidas.'; if(error.status===429) return 'Demasiados intentos locales. Espera el intervalo indicado e inténtalo de nuevo.'; if(error.status===0) return 'API local no disponible.'; } return 'No fue posible iniciar sesión.'; }
