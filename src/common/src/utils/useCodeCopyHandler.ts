import checkIcon from '../assets/images/check-icon.svg?raw'

let isRegistered = false;

export function useCodeCopyHandler(t: (key: string, defaultMsg?: string) => string) {
  if (isRegistered) return;

  const handler = async (e: MouseEvent) => {
    const target = e.target;
    if (!(target instanceof Element)) return;

    const codeBtn = target.closest<HTMLButtonElement>('.copy-code-btn');
    if (!codeBtn) return;

    const codeElement = codeBtn.closest('pre')?.querySelector<HTMLElement>('code');
    if (!codeElement) return;

    try {
      const original = codeBtn.innerHTML;
      await navigator.clipboard.writeText(codeElement.innerText);
      codeBtn.disabled = true;
      codeBtn.innerHTML = `
        ${checkIcon}
        <span class="font-[sora]">${t('copiedMessage')}</span>`;
      setTimeout(() => {
        codeBtn.innerHTML = original
        codeBtn.disabled = false;
      }, 3000);
    } catch(e) {
      console.error('Copy failed', e);
    }
  };
  document.body.addEventListener('click', handler);
  isRegistered = true;
}
