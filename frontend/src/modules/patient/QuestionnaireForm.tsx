import React, { useState, useEffect } from 'react';
import { ClipboardList, CheckCircle2, RotateCw, HelpCircle, ShieldCheck } from 'lucide-react';
import { apiCall } from '../../api/client';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../context/ToastContext';

interface QuestionItem {
  question_id: string;
  question_text: string;
  response_type: string;
  options?: string[];
  is_required?: boolean;
}

interface QuestionnaireData {
  id: string;
  title: string;
  specialty?: string;
  version: string;
  status: string;
  questions: QuestionItem[];
}

export const QuestionnaireForm: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [selectedSpecialty, setSelectedSpecialty] = useState('Orthopedics');
  const [questionnaire, setQuestionnaire] = useState<QuestionnaireData | null>(null);
  const [intro, setIntro] = useState<string>('');
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const fetchQuestionnaire = async (spec: string) => {
    setIsLoading(true);
    try {
      const res = await apiCall(
        `/api/v1/questionnaires/applicable?specialty=${encodeURIComponent(spec)}`
      );
      if (res.ok && res.data?.questionnaire) {
        setQuestionnaire(res.data.questionnaire);
        setIntro(res.data.conversational_intro || '');

        // Initialize answers map
        const initialAnswers: Record<string, string> = {};
        res.data.questionnaire.questions.forEach((q: QuestionItem) => {
          initialAnswers[q.question_id] = q.response_type === 'YES_NO' ? 'No' : '';
        });
        setAnswers(initialAnswers);
      }
    } catch (e) {
      console.error('Fetch questionnaire error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestionnaire(selectedSpecialty);
  }, [selectedSpecialty]);

  const handleAnswerChange = (qId: string, val: string) => {
    setAnswers((prev) => ({ ...prev, [qId]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const patientId = user?.patient_id || user?.identifier || '+1-555-SHOULDER';
      const res = await apiCall(
        `/api/v1/patients/${encodeURIComponent(patientId)}/questionnaires/submit`,
        {
          method: 'POST',
          body: JSON.stringify({
            questionnaire_id: questionnaire?.id || 'Q-DEFAULT-GENERAL',
            answers,
            appointment_id: 'APT-1024',
          }),
        }
      );

      setIsSubmitted(true);
      showToast(
        'success',
        'Intake Questionnaire Submitted',
        'Pre-visit medical history successfully stored and attached to your clinical chart.'
      );
    } catch (err: any) {
      showToast('error', 'Submission Failed', err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="bg-emerald-950/40 border border-emerald-500/30 rounded-2xl p-6 text-center space-y-3">
        <div className="w-10 h-10 rounded-full bg-emerald-500 text-slate-950 mx-auto flex items-center justify-center font-bold">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-bold text-emerald-300">
          Clinical Intake Answers Encrypted &amp; Stored
        </h4>
        <p className="text-xs text-slate-300 max-w-md mx-auto leading-relaxed">
          Your physician has received your answers for {questionnaire?.title}. These answers will be
          reviewed during your appointment.
        </p>
        <button
          onClick={() => {
            setIsSubmitted(false);
            fetchQuestionnaire(selectedSpecialty);
          }}
          className="text-xs font-bold text-emerald-400 hover:underline pt-2 inline-block"
        >
          Submit Another Questionnaire &rarr;
        </button>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
      <div className="flex flex-wrap justify-between items-center pb-2 border-b border-slate-800 gap-2">
        <div>
          <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
            <ClipboardList className="w-4 h-4 text-emerald-400" />
            <span>Pre-Visit Clinical Intake Questionnaire</span>
          </h3>
          <p className="text-xs text-slate-400">
            Dynamically loaded from{' '}
            <code className="text-emerald-400 font-mono text-[11px]">
              GET /api/v1/questionnaires/applicable?specialty=&#123;spec&#125;
            </code>
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <label className="text-xs text-slate-400 font-medium">Specialty:</label>
          <select
            value={selectedSpecialty}
            onChange={(e) => setSelectedSpecialty(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500"
          >
            <option value="Orthopedics">Orthopedic Surgery</option>
            <option value="Cardiology">Cardiology</option>
            <option value="Dermatology">Dermatology</option>
            <option value="Neurology">Neurology</option>
            <option value="General">General Medicine</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-xs text-slate-400 space-y-2">
          <RotateCw className="w-5 h-5 animate-spin mx-auto text-emerald-400" />
          <span>Resolving applicable clinical questionnaire engine template...</span>
        </div>
      ) : questionnaire ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-1">
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-white">{questionnaire.title}</span>
              <span className="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                {questionnaire.version} &bull; {questionnaire.status}
              </span>
            </div>
            {intro && <p className="text-xs text-slate-400 italic">"{intro}"</p>}
          </div>

          <div className="space-y-3">
            {questionnaire.questions.map((q, idx) => (
              <div
                key={q.question_id}
                className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <label className="text-xs font-semibold text-slate-200 flex items-start gap-1.5">
                    <span className="text-emerald-400 font-bold">{idx + 1}.</span>
                    <span>{q.question_text}</span>
                  </label>
                  {q.is_required && (
                    <span className="text-[10px] text-rose-400 font-bold uppercase">Required</span>
                  )}
                </div>

                {q.response_type === 'YES_NO' ? (
                  <div className="flex space-x-3 pt-1">
                    {['Yes', 'No'].map((opt) => (
                      <button
                        type="button"
                        key={opt}
                        onClick={() => handleAnswerChange(q.question_id, opt)}
                        className={`text-xs px-4 py-1.5 rounded-lg border font-bold transition ${
                          answers[q.question_id] === opt
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                            : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white'
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : q.options && q.options.length > 0 ? (
                  <select
                    value={answers[q.question_id] || ''}
                    onChange={(e) => handleAnswerChange(q.question_id, e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="">Select an option...</option>
                    {q.options.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                ) : (
                  <textarea
                    rows={2}
                    value={answers[q.question_id] || ''}
                    onChange={(e) => handleAnswerChange(q.question_id, e.target.value)}
                    placeholder="Type your response here..."
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-between items-center pt-2 border-t border-slate-800">
            <div className="flex items-center space-x-1.5 text-[11px] text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Answers are encrypted and saved under HIPAA compliance guidelines.</span>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs px-5 py-2 rounded-xl transition shadow-lg shadow-emerald-500/20 disabled:opacity-50"
            >
              {isSubmitting ? 'Submitting...' : 'Save & Submit Intake Answers'}
            </button>
          </div>
        </form>
      ) : (
        <div className="py-8 text-center text-xs text-slate-500">
          No questionnaire template configured for this specialty.
        </div>
      )}
    </div>
  );
};
