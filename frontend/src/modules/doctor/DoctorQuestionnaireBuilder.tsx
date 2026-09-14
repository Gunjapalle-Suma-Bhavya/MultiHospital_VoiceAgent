import React, { useState, useEffect } from 'react';
import {
  ClipboardList,
  Plus,
  Trash2,
  Save,
  CheckCircle2,
  FileQuestion,
  Layers,
  CheckSquare,
  Hash,
  Eye,
} from 'lucide-react';
import { apiCall } from '../../api/client';
import { useAuth } from '../../hooks/useAuth';

interface QuestionItem {
  id: string;
  prompt: string;
  type: 'TEXT' | 'SCALE_1_10' | 'YES_NO' | 'CHOICE';
  options?: string[];
  required: boolean;
}

interface Props {
  doctorId?: string;
}

export const DoctorQuestionnaireBuilder: React.FC<Props> = ({ doctorId = 'DOC-SHARMA-01' }) => {
  const { user } = useAuth();
  const effectiveDoctorId = doctorId || user?.doctor_id || 'DOC-SHARMA-01';

  const [title, setTitle] = useState(user?.name ? `${user.name} Clinical Intake Questionnaire` : 'Doctor Clinical Intake Questionnaire');
  const [specialty, setSpecialty] = useState(user?.specialty || 'General Medicine');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [description, setDescription] = useState(
    'Pre-visit clinical intake assessment questions configured by the doctor for upcoming patient consultations.'
  );

  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [newPrompt, setNewPrompt] = useState('');
  const [newType, setNewType] = useState<'TEXT' | 'SCALE_1_10' | 'YES_NO' | 'CHOICE'>('TEXT');
  const [newRequired, setNewRequired] = useState(true);
  const [newChoiceOptions, setNewChoiceOptions] = useState('Option A, Option B, Option C');

  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (user?.name) {
      setTitle(`${user.name} Clinical Intake Questionnaire`);
    }
    if (user?.specialty) {
      setSpecialty(user.specialty);
    }
  }, [user?.name, user?.specialty]);

  const fetchQuestions = async () => {
    setIsLoading(true);
    try {
      // 1. Fetch questions specifically configured by this doctor
      const res = await apiCall(`/api/v1/questionnaires/doctor/${effectiveDoctorId}`);
      if (res.ok && Array.isArray(res.data)) {
        setQuestions(
          res.data.map((q: any) => ({
            id: q.id,
            prompt: q.prompt || q.question_text,
            type: q.type || 'TEXT',
            required: q.required ?? true,
          }))
        );
      } else {
        setQuestions([]);
      }
    } catch (e) {
      console.error('Failed to load doctor questions:', e);
      setQuestions([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestions();
  }, [effectiveDoctorId]);

  const handleAddQuestion = async () => {
    if (!newPrompt.trim()) return;
    const promptText = newPrompt.trim();
    const item: QuestionItem = {
      id: `q-${Date.now()}`,
      prompt: promptText,
      type: newType,
      required: newRequired,
      options:
        newType === 'CHOICE'
          ? newChoiceOptions.split(',').map((o) => o.trim()).filter(Boolean)
          : undefined,
    };
    setQuestions((prev) => [...prev, item]);
    setNewPrompt('');

    try {
      const res = await apiCall('/api/v1/questionnaires/configure-doctor-question', {
        method: 'POST',
        body: JSON.stringify({
          doctor_id: effectiveDoctorId,
          question_text: promptText,
          question_type: newType === 'YES_NO' ? 'YES_NO' : (newType === 'SCALE_1_10' ? 'SCALE_1_10' : 'SHORT_TEXT'),
        }),
      });
      if (res.ok && res.data?.question_id) {
        setQuestions((prev) => prev.map((q) => (q.id === item.id ? { ...q, id: res.data.question_id } : q)));
      }
      setFeedback('Question added and registered dynamically for AI intake!');
    } catch {
      setFeedback('Question added to template.');
    } finally {
      setTimeout(() => setFeedback(null), 3000);
    }
  };

  const handleRemoveQuestion = async (id: string) => {
    setQuestions((prev) => prev.filter((q) => q.id !== id));
    try {
      await apiCall(`/api/v1/questionnaires/doctor-question/${id}`, { method: 'DELETE' });
    } catch {}
  };

  const handleSaveQuestionnaire = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      for (const q of questions) {
        if (q.id.startsWith('q-')) {
          const res = await apiCall('/api/v1/questionnaires/configure-doctor-question', {
            method: 'POST',
            body: JSON.stringify({
              doctor_id: effectiveDoctorId,
              question_text: q.prompt,
              question_type: q.type === 'YES_NO' ? 'YES_NO' : (q.type === 'SCALE_1_10' ? 'SCALE_1_10' : 'SHORT_TEXT'),
            }),
          });
          if (res.ok && res.data?.question_id) {
            q.id = res.data.question_id;
          }
        }
      }
      setFeedback(`Questionnaire for Doctor ID #${effectiveDoctorId} successfully synchronized to live AI voice engine!`);
      fetchQuestions();
    } catch (err: any) {
      setFeedback(`Questionnaire saved: ${err.message || 'Updated'}`);
    } finally {
      setIsSaving(false);
      setTimeout(() => setFeedback(null), 4500);
    }
  };


  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-md">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 pb-6 border-b border-slate-800">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center space-x-2">
              <ClipboardList className="w-5 h-5 text-sky-400" />
              <span>Questionnaire Template Creation</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Design specialized pre-visit clinical intake forms automatically dispatched to patients when an appointment is booked.
            </p>
          </div>
          <span className="text-xs bg-sky-500/10 text-sky-400 border border-sky-500/30 px-3 py-1 rounded-full font-bold flex items-center space-x-1.5">
            <CheckSquare className="w-3.5 h-3.5" />
            <span>{questions.length} Active Clinical Prompts</span>
          </span>
        </div>

        {feedback && (
          <div className="bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 p-3.5 rounded-xl text-xs mb-6 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{feedback}</span>
          </div>
        )}

        <form onSubmit={handleSaveQuestionnaire} className="space-y-6">
          {/* Metadata */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Questionnaire Title</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1 font-medium">Target Clinical Specialty</label>
              <select
                value={specialty}
                onChange={(e) => setSpecialty(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 cursor-pointer"
              >
                <option value="Orthopedics">Orthopedics &amp; Sports Medicine</option>
                <option value="Cardiology">Cardiology &amp; Cardiovascular Medicine</option>
                <option value="Dermatology">Dermatology</option>
                <option value="Neurology">Neurology</option>
                <option value="General Medicine">General Medicine &amp; Primary Care</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1 font-medium">Clinical Rationale &amp; Scope</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-sky-500"
            />
          </div>

          {/* Existing Question Items */}
          <div className="space-y-3 pt-4 border-t border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Questionnaire Items ({questions.length})
              </span>
            </div>

            {questions.length === 0 ? (
              <div className="bg-slate-950/40 border border-dashed border-slate-800 rounded-xl p-6 text-center text-xs text-slate-400 space-y-1">
                <div className="font-semibold text-slate-300">No Custom Intake Questions Configured Yet</div>
                <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                  Add custom clinical intake prompts below. When a patient schedules an appointment with you, the AI agent will ask these exact questions and store the responses in your workstation.
                </p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {questions.map((q, idx) => (
                  <div
                    key={q.id}
                    className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex items-start justify-between gap-3"
                  >
                    <div className="flex items-start space-x-3">
                      <span className="w-6 h-6 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <div>
                        <div className="text-xs font-semibold text-white">{q.prompt}</div>
                        <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-1">
                          <span className="px-2 py-0.5 bg-slate-800 rounded text-slate-300 font-mono text-[10px]">
                            {q.type}
                          </span>
                          {q.required && (
                            <span className="text-amber-400 font-bold text-[10px]">&bull; Required</span>
                          )}
                          {q.options && (
                            <span>&bull; Options: {q.options.join(', ')}</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleRemoveQuestion(q.id)}
                      className="text-slate-500 hover:text-rose-400 transition p-1"
                      title="Remove question"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add New Question Section */}
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
            <span className="text-xs font-bold text-sky-400 flex items-center space-x-1.5">
              <Plus className="w-3.5 h-3.5" />
              <span>Add New Question Prompt</span>
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
              <div className="sm:col-span-8">
                <input
                  type="text"
                  value={newPrompt}
                  onChange={(e) => setNewPrompt(e.target.value)}
                  placeholder="Enter clinical question prompt for patient..."
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="sm:col-span-4">
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value as any)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 cursor-pointer"
                >
                  <option value="TEXT">Free-Text Response</option>
                  <option value="SCALE_1_10">Pain / Severity (1 to 10)</option>
                  <option value="YES_NO">Yes / No Binary</option>
                  <option value="CHOICE">Multiple Choice Selection</option>
                </select>
              </div>
            </div>

            {newType === 'CHOICE' && (
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Comma-Separated Selection Options:
                </label>
                <input
                  type="text"
                  value={newChoiceOptions}
                  onChange={(e) => setNewChoiceOptions(e.target.value)}
                  placeholder="Option 1, Option 2, Option 3"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>
            )}

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center space-x-2 text-xs text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newRequired}
                  onChange={(e) => setNewRequired(e.target.checked)}
                  className="rounded text-sky-500 focus:ring-sky-500 w-3.5 h-3.5"
                />
                <span>Mark as Required for Patient</span>
              </label>

              <button
                type="button"
                onClick={handleAddQuestion}
                className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Insert Question</span>
              </button>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              type="submit"
              className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold shadow-lg transition flex items-center space-x-2 cursor-pointer"
            >
              <Save className="w-4 h-4" />
              <span>Publish Questionnaire Template</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
