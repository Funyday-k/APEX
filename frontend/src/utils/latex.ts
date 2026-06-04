/** Strip LaTeX delimiters and convert common math tokens for plain-text fallback. */
export function latexToPlain(text: string | null | undefined): string {
  if (!text) return '';
  return text
    .replace(/\$\$([^$]+)\$\$/g, '$1')
    .replace(/\$([^$]+)\$/g, '$1')
    .replace(/\\mathrm\{([^}]+)\}/g, '$1')
    .replace(/\\text\{([^}]+)\}/g, '$1')
    .replace(/\\cdot/g, '·')
    .replace(/\\times/g, '×')
    .replace(/\\,/g, ' ')
    .replace(/\\ /g, ' ')
    .replace(/\\log/g, 'log')
    .replace(/\\ln/g, 'ln')
    .replace(/\\sigma/g, 'σ')
    .replace(/\\chi/g, 'χ')
    .replace(/\\odot/g, '⊙')
    .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1/$2)')
    .replace(/_\{([^}]+)\}/g, '_$1')
    .replace(/\^\{([^}]+)\}/g, '^$1')
    .replace(/\\/g, '')
    .trim();
}

/** Whether text likely contains LaTeX that should be rendered with KaTeX. */
export function hasLatex(text: string | null | undefined): boolean {
  if (!text) return false;
  return /\\[a-zA-Z]|_\{|_\w|\^\{|\^\\|\$[^$]+\$/.test(text);
}
