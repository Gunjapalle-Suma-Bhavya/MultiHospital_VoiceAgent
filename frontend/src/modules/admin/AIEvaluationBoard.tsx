import React, { useState } from 'react';
import { DollarSign, TrendingDown, Award } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

export const AIEvaluationBoard: React.FC = () => {
  const [callVolume, setCallVolume] = useState(5000);

  const humanCost = callVolume * 3.75;
  const aiCost = callVolume * 0.125;
  const savings = humanCost - aiCost;

  const comparisonData = [
    { volume: '1k Calls', Human: 3750, AI: 125, NetSavings: 3625 },
    { volume: '5k Calls', Human: 18750, AI: 625, NetSavings: 18125 },
    { volume: '10k Calls', Human: 37500, AI: 1250, NetSavings: 36250 },
    { volume: '25k Calls', Human: 93750, AI: 3125, NetSavings: 90625 },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
      <div className="flex justify-between items-center pb-2 border-b border-slate-800">
        <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
          <DollarSign className="w-4 h-4 text-emerald-400" />
          <span>Voice AI Unit Economics &amp; ROI Telemetry</span>
        </h3>
        <span className="text-[10px] font-bold bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded flex items-center space-x-1">
          <Award className="w-3 h-3 mr-1" />
          <span>96.67% Operational Savings</span>
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
          <span className="text-[10px] font-bold text-emerald-400 uppercase">AI Voice Telephony</span>
          <div className="text-xl font-black text-white mt-1">
            $0.125 <span className="text-xs font-normal text-slate-400">/ call</span>
          </div>
          <div className="text-[10px] text-slate-500 mt-1">LLM $0.0002 &bull; Voice $0.037 &bull; SIP $0.087</div>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
          <span className="text-[10px] font-bold text-slate-400 uppercase">Human Receptionist</span>
          <div className="text-xl font-black text-slate-300 mt-1">
            $3.75 <span className="text-xs font-normal text-slate-400">/ call</span>
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Average 5-min manual phone intake</div>
        </div>
      </div>

      {/* Recharts ROI Comparison */}
      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
        <div className="text-[10px] font-bold uppercase text-slate-400">Volume Cost Comparison (USD $)</div>
        <div className="h-36 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={comparisonData} margin={{ top: 5, right: 5, left: -15, bottom: 0 }}>
              <XAxis dataKey="volume" stroke="#64748b" fontSize={10} />
              <YAxis stroke="#64748b" fontSize={10} />
              <Tooltip
                contentStyle={{ backgroundColor: '#020617', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '11px' }}
                itemStyle={{ color: '#e2e8f0' }}
              />
              <Legend wrapperStyle={{ fontSize: '10px' }} />
              <Bar dataKey="Human" name="Human Front-Desk ($)" fill="#f43f5e" radius={[4, 4, 0, 0]} />
              <Bar dataKey="AI" name="Voice AI Platform ($)" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Slider */}
      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
        <div className="flex justify-between text-xs">
          <span className="font-medium text-slate-300">Monthly Call Volume:</span>
          <span className="font-bold text-emerald-400">{callVolume.toLocaleString()} calls / mo</span>
        </div>
        <input
          type="range"
          min="1000"
          max="25000"
          step="1000"
          value={callVolume}
          onChange={(e) => setCallVolume(parseInt(e.target.value))}
          className="w-full accent-emerald-500 cursor-pointer"
        />
        <div className="flex justify-between text-xs pt-1 border-t border-slate-800">
          <span className="text-slate-400">Projected Monthly Savings:</span>
          <span className="font-extrabold text-emerald-400 text-sm">
            ${savings.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / month
          </span>
        </div>
      </div>
    </div>
  );
};
