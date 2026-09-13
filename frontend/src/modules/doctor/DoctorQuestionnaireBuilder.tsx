import React, { useState } from 'react';
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

interface QuestionItem {
  id: string;
  prompt: string;
  type: 'TEXT' | 'SCALE_1_10' | 'YES_NO' | 'CHOICE';
  options?: string[];
  required: boolean;
}

export const DoctorQuestionnaireBuilder: React.FC = () => {
  const [title, setTitle] = useState('Pre-Op Orthopedic Shoulder & Joint Mobility Assessment');
  const [specialty, setSpecialty] = useState('Orthopedics');
  const [description, setDescription] = useState(
    'Standardized preoperative intake questionnaire assessing functional range of motion, nocturnal pain, and prior conservative therapy.'
  );

  const [questions, setQuestions] = useState<QuestionItem[]>([
    {
      id: 'q1',
      prompt: 'On a scale of 1 to 10, what is your current baseline joint pain at rest?',
      type: 'SCALE_1_10',
      required: true,
    },
    {
      id: 'q2',
      prompt: 'Does the pain wake you from sleep when lying on the affected shoulder?',
      type: 'YES_NO',
      required: true,
    },
    {
      id: 'q3',
      prompt: 'Which conservative interventions have you tried in the past 6 months?',
      type: 'CHOICE',
      options: ['Physical Therapy', 'Corticosteroid Injections', 'NSAIDs / Ice Therapy', 'None'],
      required: false,
    },
    {
      id: 'q4',
      prompt: 'Describe any specific daily movements or activities that trigger acute weakness or numbness.',
      type: 'TEXT',
      required: false,
    },
  ]);

  const [newPrompt, setNewPrompt] = useState('');
  const [newType, setNewType] = useState<'TEXT' | 'SCALE_1_10' | 'YES_NO' | 'CHOICE'>('TEXT');
  const [newRequired, setNewRequired] = useState(true);
  const [newChoiceOptions, setNewChoiceOptions] = useState('Option A, Option B, Option C');

  const [feedback, setFeedback] = useState<string | null>(null);
  const [savedCount, setSavedCount] = useState(3);

  const handleAddQuestion = () => {
    if (!newPrompt.trim()) return;
    const item: QuestionItem = {
      id: `q-${Date.now()}`,
      prompt: newPrompt.trim(),
      type: newType,
      required: newRequired,
      options:
        newType === 'CHOICE'
          ? newChoiceOptions.split(',').map((o) => o.trim()).filter(Boolean)
          : undefined,
    };
    setQuestions([...questions, item]);
    setNewPrompt('');
  };

  const handleRemoveQuestion = (id: string) => {
    setQuestions(questions.filter((q) => q.id !== id));
  };

  const handleSaveQuestionnaire = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedCount((prev) => prev + 1);
    setFeedback(`Questionnaire "${title}" successfully registered and published for patient intake!`);
    setTimeout(() => setFeedback(null), 4000);
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
