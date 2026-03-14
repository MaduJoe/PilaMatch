// ---------------------------------------------------------------------------
// Shared review checklist labels by reviewer role
// ---------------------------------------------------------------------------

interface ChecklistLabels {
  timePunctuality: string;
  professionalism: string;
  wouldRehire: string;
}

/**
 * Full-length labels used in forms (e.g. write-review dialog).
 */
export const CHECKLIST_LABELS: Record<'instructor' | 'studio', ChecklistLabels> = {
  studio: {
    timePunctuality: '시간 준수',
    professionalism: '전문성',
    wouldRehire: '재고용 의향',
  },
  instructor: {
    timePunctuality: '강사에 대한 소통·지원',
    professionalism: '수업 환경',
    wouldRehire: '재협업 의향',
  },
};

/**
 * Compact labels used in badges and summary views.
 */
export const CHECKLIST_LABELS_SHORT: Record<'instructor' | 'studio', ChecklistLabels> = {
  studio: {
    timePunctuality: '시간 준수',
    professionalism: '전문성',
    wouldRehire: '재고용',
  },
  instructor: {
    timePunctuality: '소통·지원',
    professionalism: '수업 환경',
    wouldRehire: '재협업',
  },
};
