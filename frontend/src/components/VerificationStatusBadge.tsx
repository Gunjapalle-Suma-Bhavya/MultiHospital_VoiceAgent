import React from 'react';
import { ShieldCheck, Clock, AlertTriangle } from 'lucide-react';

interface VerificationStatusBadgeProps {
  status?: string;
  isEhrVerified?: boolean;
}

export const VerificationStatusBadge: React.FC<VerificationStatusBadgeProps> = ({
  status = 'CONFIRMED',
  isEhrVerified = true,
}) => {
  if (status === 'CONFIRMED' && isEhrVerified) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        <ShieldCheck className="w-3 h-3 text-emerald-400" />
        <span>5-POINT EHR VERIFIED</span>
      </span>
    );
  }

  if (status === 'SYNC_PENDING') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <Clock className="w-3 h-3 text-amber-400 animate-pulse" />
        <span>EHR SYNC PENDING</span>
      </span>
    );
  }

  if (status === 'CANCELLED') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black bg-rose-500/10 text-rose-400 border border-rose-500/20">
        <AlertTriangle className="w-3 h-3 text-rose-400" />
        <span>CANCELLED</span>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">
      {status}
    </span>
  );
};
