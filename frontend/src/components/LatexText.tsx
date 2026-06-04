import katex from 'katex';
import { hasLatex, latexToPlain } from '../utils/latex';

type Props = {
  text: string | null | undefined;
  className?: string;
  as?: 'span' | 'div';
  displayMode?: boolean;
};

export function LatexText({ text, className, as = 'span', displayMode = false }: Props) {
  if (!text) return null;
  const Tag = as;
  if (!hasLatex(text)) {
    return <Tag className={className}>{text}</Tag>;
  }
  try {
    const html = katex.renderToString(text.replace(/\$/g, ''), {
      throwOnError: false,
      displayMode,
    });
    return (
      <Tag
        className={`latex-text${className ? ` ${className}` : ''}`}
        dangerouslySetInnerHTML={{ __html: html }}
        title={latexToPlain(text)}
      />
    );
  } catch {
    return <Tag className={className}>{latexToPlain(text)}</Tag>;
  }
}
