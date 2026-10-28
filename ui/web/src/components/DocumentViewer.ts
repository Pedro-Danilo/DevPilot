// Contract route marker: ui.workspace-documents
import type { WorkspaceDocumentResource } from '../api/types';
import { renderUiStateNotice } from './ContractBadges';

export interface DocumentViewerOptions {
  document?: WorkspaceDocumentResource;
  loading?: boolean;
  error?: string;
  focusLine?: number | null;
  focusSection?: string | null;
  navigationOrigin?: 'finding' | 'traceability';
  navigationLabel?: string;
  onReturnToValidation?: () => void;
}

export function renderDocumentViewer(options: DocumentViewerOptions): HTMLElement {
  const section = document.createElement('section');
  section.className = 'document-viewer';
  section.setAttribute('aria-label', 'Visor read-only de documento');

  if (options.loading) {
    section.append(renderUiStateNotice('loading', 'Leyendo el documento seleccionado mediante identificador opaco…'));
    return section;
  }
  if (options.error) {
    section.append(renderUiStateNotice('error', options.error));
    return section;
  }
  if (!options.document) {
    section.append(renderUiStateNotice('empty', 'Selecciona un documento permitido para inspeccionarlo.'));
    return section;
  }

  const resource = options.document;
  const header = document.createElement('header');
  header.className = 'document-viewer__header';
  const titleBlock = document.createElement('div');
  const title = document.createElement('h2');
  title.textContent = resource.name;
  const path = document.createElement('code');
  path.textContent = resource.relative_path;
  titleBlock.append(title, path);
  const badges = document.createElement('div');
  badges.className = 'context-badges';
  badges.append(
    badge('READ-ONLY', 'pass'),
    badge((resource.extension ?? 'text').toUpperCase(), 'pending'),
    badge(String(resource.category ?? 'documentation').toUpperCase(), 'pending'),
    badge(viewModeLabel(resource), 'pending'),
  );
  header.append(titleBlock, badges);
  section.append(header, renderBreadcrumbs(resource));

  const metadata = document.createElement('dl');
  metadata.className = 'document-viewer__metadata';
  metadata.append(
    meta('SHA-256', resource.sha256 ?? 'no calculado'),
    meta('Tamaño', `${resource.size_bytes ?? 0} bytes`),
    meta('Modificado', resource.modified_at ?? 'no informado'),
    meta('Encoding', resource.encoding ?? 'no informado'),
  );
  section.append(metadata);

  const content = document.createElement('article');
  content.className = 'document-viewer__content';
  if (resource.extension === '.md') renderSafeMarkdown(content, String(resource.content ?? ''), options.focusLine, options.focusSection);
  else if (resource.extension === '.json' && resource.structured !== null && resource.structured !== undefined) {
    const pre = document.createElement('pre');
    pre.className = 'document-viewer__code';
    pre.textContent = JSON.stringify(resource.structured, null, 2);
    content.append(pre);
  } else {
    const pre = document.createElement('pre');
    pre.className = 'document-viewer__code';
    pre.textContent = resource.content ?? '';
    content.append(pre);
  }
  const navigationActive = Boolean(options.navigationOrigin);
  if (navigationActive) {
    const notice = document.createElement('div');
    notice.className = 'document-navigation-notice';
    notice.setAttribute('role', 'status');
    notice.setAttribute('aria-live', 'polite');
    const message = document.createElement('span');
    const prefix = options.navigationOrigin === 'traceability' ? 'Fuente de trazabilidad abierta:' : 'Finding abierto:';
    message.textContent = `${prefix} ${options.navigationLabel ?? resource.relative_path}${options.focusSection ? ` · sección “${options.focusSection}”` : ''}${options.focusLine ? ` · línea ${options.focusLine}` : ''}.`;
    notice.append(message);
    if (options.onReturnToValidation) {
      const back = document.createElement('button');
      back.type = 'button';
      back.className = 'button-link document-navigation-back';
      back.textContent = options.navigationOrigin === 'traceability' ? 'Volver a trazabilidad' : 'Volver a findings';
      back.addEventListener('click', options.onReturnToValidation);
      notice.append(back);
    }
    section.append(notice);
  }
  section.append(content);
  if (navigationActive) {
    globalThis.requestAnimationFrame(() => {
      const exactTarget = findNavigationTarget(content, options.focusLine, options.focusSection);
      const fallbackTarget = content.querySelector<HTMLElement>('h1, h2, h3, p, li') ?? content;
      const target = exactTarget ?? fallbackTarget;
      target.classList.add('document-navigation-target');
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      target.scrollIntoView({ behavior: 'smooth', block: exactTarget ? 'center' : 'start' });
      target.tabIndex = -1;
      target.focus({ preventScroll: true });
    });
  }
  return section;
}

function renderBreadcrumbs(resource: WorkspaceDocumentResource): HTMLElement {
  const nav = document.createElement('nav');
  nav.className = 'document-breadcrumbs';
  nav.setAttribute('aria-label', 'Ruta relativa del documento');
  for (const [index, item] of (resource.breadcrumbs ?? []).entries()) {
    const crumb = document.createElement('span');
    crumb.textContent = item.label;
    nav.append(crumb);
    if (index < (resource.breadcrumbs ?? []).length - 1) {
      const separator = document.createElement('span');
      separator.className = 'document-breadcrumbs__separator';
      separator.textContent = '/';
      nav.append(separator);
    }
  }
  return nav;
}

export function renderSafeMarkdown(target: HTMLElement, source: string, _focusLine?: number | null, _focusSection?: string | null): void {
  const parsed=splitFrontmatter(source);
  if(parsed.frontmatter.length)renderFrontmatter(target,parsed.frontmatter);
  const lines=parsed.body.replace(/\r\n/g,'\n').split('\n');
  const inline=(node:HTMLElement,text:string):void=>{
    const pattern=/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^\s)]+\))/g;
    let at=0;
    for(const match of text.matchAll(pattern)){
      node.append(document.createTextNode(text.slice(at,match.index)));
      const token=match[0];let child:HTMLElement;
      if(token.startsWith('`')){child=document.createElement('code');child.textContent=token.slice(1,-1);}
      else if(token.startsWith('**')){child=document.createElement('strong');child.textContent=token.slice(2,-2);}
      else if(token.startsWith('*')){child=document.createElement('em');child.textContent=token.slice(1,-1);}
      else{
        const link=/^\[([^\]]+)\]\((.*)\)$/.exec(token)!;
        let safe=false;try{safe=['http:','https:','mailto:'].includes(new URL(link[2],location.href).protocol);}catch{/* text fallback */}
        child=document.createElement(safe?'a':'span');child.textContent=link[1];
        if(safe){(child as HTMLAnchorElement).href=link[2];child.setAttribute('rel','noopener noreferrer');}
      }
      node.append(child);at=match.index!+token.length;
    }
    node.append(document.createTextNode(text.slice(at)));
  };
  const cells=(text:string)=>text.trim().replace(/^\||\|$/g,'').split('|').map(s=>s.trim());
  for(let i=0;i<lines.length;){
    const line=lines[i], sourceLine=i+1;
    if(!line.trim()){i++;continue;}
    let element:HTMLElement;
    if(/^\s*(```|~~~)/.test(line)){
      const fence=line.trim().slice(0,3), codeLines:string[]=[];i++;
      while(i<lines.length&&!lines[i].trim().startsWith(fence))codeLines.push(lines[i++]);
      if(i<lines.length)i++;
      element=document.createElement('pre');const code=document.createElement('code');code.textContent=codeLines.join('\n');element.append(code);
    }else if(line.includes('|')&&/^\s*\|?\s*:?-{3,}/.test(lines[i+1]??'')){
      const wrap=document.createElement('div');wrap.className='markdown-table-scroll';wrap.tabIndex=0;wrap.setAttribute('aria-label','Tabla Markdown con desplazamiento horizontal');
      const table=document.createElement('table'),head=document.createElement('thead'),tr=document.createElement('tr');
      for(const c of cells(line)){const th=document.createElement('th');th.scope='col';inline(th,c);tr.append(th);}head.append(tr);table.append(head);i+=2;
      const body=document.createElement('tbody');
      while(i<lines.length&&lines[i].includes('|')&&lines[i].trim()){
        const row=document.createElement('tr');for(const c of cells(lines[i++])){const td=document.createElement('td');inline(td,c);row.append(td);}body.append(row);
      }
      table.append(body);wrap.append(table);element=wrap;
    }else if(/^(#{1,6})\s+/.test(line)){
      const h=/^(#{1,6})\s+(.+)$/.exec(line)!;element=document.createElement(`h${h[1].length}`);element.id=slug(h[2]);inline(element,h[2]);i++;
    }else if(/^\s*>/.test(line)){
      element=document.createElement('blockquote');
      while(i<lines.length&&/^\s*>/.test(lines[i])){const p=document.createElement('p');inline(p,lines[i++].replace(/^\s*>\s?/,''));element.append(p);}
    }else if(/^\s*(?:[-*+] |\d+[.)] )/.test(line)){
      const ordered=/^\s*\d+[.)] /.test(line);element=document.createElement(ordered?'ol':'ul');
      while(i<lines.length&&(ordered?/^\s*\d+[.)] /:/^\s*[-*+] /).test(lines[i])){const li=document.createElement('li');li.dataset.sourceLine=String(i+1);li.tabIndex=-1;inline(li,lines[i++].replace(/^\s*(?:[-*+]|\d+[.)])\s+/,''));element.append(li);}
    }else{element=document.createElement('p');inline(element,line);i++;}
    element.dataset.sourceLine=String(sourceLine);element.tabIndex=-1;target.append(element);
  }
}


function findNavigationTarget(content: HTMLElement, focusLine?: number | null, focusSection?: string | null): HTMLElement | null {
  if (focusLine) {
    const line = String(focusLine);
    const byLine = Array.from(content.querySelectorAll<HTMLElement>('[data-source-line]')).find((item) => item.dataset.sourceLine === line);
    if (byLine) return byLine;
  }
  if (focusSection) {
    const sectionId = slug(focusSection);
    if (sectionId) {
      const bySection = Array.from(content.querySelectorAll<HTMLElement>('[id]')).find((item) => item.id === sectionId);
      if (bySection) return bySection;
    }
  }
  return null;
}

function badge(text: string, state: string): HTMLElement {
  const item = document.createElement('span');
  item.className = `badge ${state}`;
  item.textContent = text;
  return item;
}

function meta(label: string, value: string): HTMLElement {
  const wrapper = document.createElement('div');
  const term = document.createElement('dt');
  term.textContent = label;
  const description = document.createElement('dd');
  description.textContent = value;
  wrapper.append(term, description);
  return wrapper;
}

function splitFrontmatter(source: string): { frontmatter: string[]; body: string } {
  const lines = source.split(/\r?\n/);
  if (lines[0]?.trim() !== '---') return { frontmatter: [], body: source };
  const closing = lines.slice(1).findIndex((line) => line.trim() === '---');
  if (closing < 0) return { frontmatter: [], body: source };
  const end = closing + 1;
  return { frontmatter: lines.slice(1, end), body: lines.slice(end + 1).join('\n') };
}

function renderFrontmatter(target: HTMLElement, lines: string[]): void {
  const details=document.createElement('details'), summary=document.createElement('summary');
  details.className='document-frontmatter';summary.textContent='Metadatos de frontmatter';
  const pre=document.createElement('pre');pre.textContent=lines.join('\n');details.append(summary,pre);target.append(details);
}

function slug(value: string): string {
  return value.trim().toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9\s_-]/g, '').replace(/[\s_]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
}

function viewModeLabel(resource: WorkspaceDocumentResource): string {
  if (resource.extension === '.json' && resource.structured !== null && resource.structured !== undefined) return 'ESTRUCTURADO';
  if (resource.extension === '.md') return 'MARKDOWN SEGURO';
  return 'RAW SEGURO';
}
