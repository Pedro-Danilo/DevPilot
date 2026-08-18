import { DevPilotApiClient, DevPilotApiError } from '../api/client';

export function renderFirstRunOwnerView(onCreated: () => void): HTMLElement {
  const section=document.createElement('section'); section.className='auth-page first-run-owner-view'; section.dataset.authState='first-run';
  const card=document.createElement('div'); card.className='auth-card';
  card.innerHTML='<h1>Configurar propietario local</h1><p>Este paso se ejecuta una sola vez. Crea el primer owner local; no habilita IAM enterprise, acceso remoto ni multiusuario SaaS.</p>';
  const form=document.createElement('form'); form.className='auth-form';
  const user=input('username','usuario.local','username'); const display=input('display_name','Nombre visible','name'); const pass=input('password','Contraseña de al menos 12 caracteres','new-password'); pass.type='password'; pass.minLength=12;
  const confirm=input('confirm_password','Confirmar contraseña','new-password'); confirm.type='password'; confirm.minLength=12;
  const submit=document.createElement('button'); submit.type='submit'; submit.textContent='Crear owner local'; const status=document.createElement('p'); status.setAttribute('role','status'); status.className='auth-status';
  form.append(label('Usuario',user),label('Nombre visible',display),label('Contraseña',pass),label('Confirmación',confirm),submit,status);
  form.addEventListener('submit',async(ev)=>{ev.preventDefault(); if(pass.value!==confirm.value){status.textContent='Las contraseñas no coinciden.'; return;} submit.disabled=true; status.textContent='Creando owner y sesión local…'; try{await new DevPilotApiClient().authBootstrapOwner({username:user.value,display_name:display.value,password:pass.value}); pass.value=''; confirm.value=''; onCreated();}catch(e){pass.value='';confirm.value='';status.textContent=e instanceof DevPilotApiError?e.message:'No fue posible completar first-run.';}finally{submit.disabled=false;}});
  card.append(form); section.append(card); return section;
}
function input(name:string,placeholder:string,autocomplete:string){const i=document.createElement('input');i.name=name;i.placeholder=placeholder;i.setAttribute('autocomplete',autocomplete);i.required=true;return i;}
function label(text:string,input:HTMLInputElement){const l=document.createElement('label');l.textContent=text;l.append(input);return l;}
