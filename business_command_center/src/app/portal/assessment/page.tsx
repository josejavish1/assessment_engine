import React from 'react';
import { 
  getQuestionnaireBundle, 
  loadSavedAssessmentResponses 
} from '@/app/actions/questionnaire';
import { AssessmentContainer } from '@/components/questionnaire/AssessmentContainer';

export const metadata = {
  title: 'Cuestionario de Evaluación de Infraestructura · Assessment Engine',
  description: 'Formulario estructurado de autoevaluación técnica en 10 torres tecnológicas CMMI/O-FAIR.',
};

export default async function AssessmentPage() {
  const defaultSlug = 'cliente_assessment';
  const bundle = await getQuestionnaireBundle();
  const savedAnswers = await loadSavedAssessmentResponses(defaultSlug);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <AssessmentContainer
        initialBundle={bundle}
        initialAnswers={savedAnswers}
        clientSlug={defaultSlug}
      />
    </div>
  );
}
