import { useT } from '../../i18n/useT';
import type { ExtractionCase } from '../../store/useStore';
import { useStore } from '../../store/useStore';

const REPS: ExtractionCase['representation'][] = ['line', 'scatter', 'band'];

export function CasesPanel() {
  const { cases, updateCase, addCase, deleteCase } = useStore();
  const { t } = useT();

  if (!cases.length) {
    return (
      <div className="cases-panel">
        <p className="hint">{t('casesEmpty')}</p>
        <button type="button" className="btn-muted" onClick={addCase}>
          {t('addCase')}
        </button>
      </div>
    );
  }

  return (
    <div className="cases-panel">
      <h3>{t('casesTitle')}</h3>
      <p className="hint">{t('casesHint')}</p>
      <ul className="cases-list">
        {cases.map((c, i) => (
          <li key={`case-${i}-${c.label}`} className="case-row">
            <label>
              {t('caseLabel')}
              <input
                value={c.label}
                onChange={(e) => updateCase(i, { label: e.target.value })}
              />
            </label>
            <label>
              {t('caseColor')}
              <input
                type="color"
                value={c.color_hex.startsWith('#') ? c.color_hex : '#3388ff'}
                onChange={(e) => updateCase(i, { color_hex: e.target.value })}
              />
            </label>
            <label>
              {t('caseRepresentation')}
              <select
                value={c.representation}
                onChange={(e) =>
                  updateCase(i, {
                    representation: e.target.value as ExtractionCase['representation'],
                  })
                }
              >
                {REPS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="btn-muted btn-sm" onClick={() => deleteCase(i)}>
              {t('deleteCase')}
            </button>
          </li>
        ))}
      </ul>
      <button type="button" className="btn-muted" onClick={addCase}>
        {t('addCase')}
      </button>
    </div>
  );
}
