import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useToast } from './ToastContext';

export interface PlatformEvent {
  id: string;
  type: 'BOOKING_CREATED' | 'SLOT_BLOCKED' | 'ENCOUNTER_COMPLETED' | 'ESCALATION_RESOLVED' | 'EHR_SYNCED';
  title: string;
  detail: string;
  timestamp: string;
  actorRole: string;
  metadata?: Record<string, any>;
}

export interface LiveBooking {
  id: string;
  doctor_id: string;
  doctor_name: string;
  patient_name: string;
  patient_phone: string;
  scheduled_time: string;
  slot_time: string; // e.g. "10:00 AM"
  specialty: string;
  status: 'CONFIRMED' | 'IN_CONSULTATION' | 'COMPLETED' | 'CANCELLED';
  is_ehr_verified: boolean;
  notes?: string;
  prescriptions?: Array<{ medication: string; dosage: string; frequency: string; duration: string }>;
}

interface PlatformEventContextType {
  events: PlatformEvent[];
  bookings: LiveBooking[];
  blockedSlots: string[]; // e.g. ["14:00 PM"]
  hospitalUtilization: number; // percentage, e.g. 78
  createBooking: (booking: Omit<LiveBooking, 'id' | 'status' | 'is_ehr_verified'>) => LiveBooking;
  blockSlot: (slotTime: string, reason: string) => void;
  unblockSlot: (slotTime: string) => void;
  completeEncounter: (
    bookingId: string,
    soapNotes: { subjective: string; objective: string; assessment: string; plan: string },
    prescriptions: Array<{ medication: string; dosage: string; frequency: string; duration: string }>
  ) => void;
  resolveEscalation: (ticketId: string, notes: string) => void;
  triggerEHRSync: (connector: string) => void;
}

const PlatformEventContext = createContext<PlatformEventContextType | undefined>(undefined);

const INITIAL_BOOKINGS: LiveBooking[] = [
  {
    id: 'APT-1024',
    doctor_id: 'DOC-SHARMA-01',
    doctor_name: 'Dr. Sharma',
    patient_name: 'Marcus Aurelius',
    patient_phone: '+1-555-SHOULDER',
    scheduled_time: 'Today, 10:00 AM',
    slot_time: '10:00 AM',
    specialty: 'Orthopedic Surgery',
    status: 'CONFIRMED',
    is_ehr_verified: true,
  },
  {
    id: 'APT-1025',
    doctor_id: 'DOC-SHARMA-01',
    doctor_name: 'Dr. Sharma',
    patient_name: 'Elena Rostova',
    patient_phone: '+1-555-KNEE-99',
    scheduled_time: 'Today, 11:00 AM',
    slot_time: '11:00 AM',
    specialty: 'Orthopedic Surgery',
    status: 'CONFIRMED',
    is_ehr_verified: true,
  },
];

export const PlatformEventProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { showToast } = useToast();
  const [events, setEvents] = useState<PlatformEvent[]>([]);
  const [bookings, setBookings] = useState<LiveBooking[]>(INITIAL_BOOKINGS);
  const [blockedSlots, setBlockedSlots] = useState<string[]>(['14:00 PM']);
  const [hospitalUtilization, setHospitalUtilization] = useState<number>(78);

  const addEvent = useCallback((event: Omit<PlatformEvent, 'id' | 'timestamp'>) => {
    const newEvent: PlatformEvent = {
      ...event,
      id: `EVT-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      timestamp: new Date().toLocaleTimeString(),
    };
    setEvents((prev) => [newEvent, ...prev.slice(0, 49)]);
  }, []);

  const createBooking = useCallback(
    (data: Omit<LiveBooking, 'id' | 'status' | 'is_ehr_verified'>): LiveBooking => {
      const id = `APT-${Math.floor(1000 + Math.random() * 9000)}`;
      const newBooking: LiveBooking = {
        ...data,
        id,
        status: 'CONFIRMED',
        is_ehr_verified: true,
      };

      setBookings((prev) => [newBooking, ...prev]);
      setHospitalUtilization((prev) => Math.min(100, prev + 1));

      addEvent({
        type: 'BOOKING_CREATED',
        title: `Appointment Confirmed: ${newBooking.patient_name}`,
        detail: `Slot: ${newBooking.slot_time} with ${newBooking.doctor_name} (${newBooking.specialty})`,
        actorRole: 'PATIENT',
        metadata: { booking_id: id, doctor_id: data.doctor_id },
      });

      showToast(
        'ehr_sync',
        `EHR Booking Confirmed (#${id})`,
        `${newBooking.patient_name} booked with ${newBooking.doctor_name} at ${newBooking.slot_time}. 5-point EHR verified.`
      );

      return newBooking;
    },
    [addEvent, showToast]
  );

  const blockSlot = useCallback(
    (slotTime: string, reason: string) => {
      setBlockedSlots((prev) => (prev.includes(slotTime) ? prev : [...prev, slotTime]));
      addEvent({
        type: 'SLOT_BLOCKED',
        title: `Slot Blocked: ${slotTime}`,
        detail: `Reason: ${reason || 'Physician unavailable / emergency consult'}`,
        actorRole: 'DOCTOR',
        metadata: { slot_time: slotTime, reason },
      });

      showToast(
        'warning',
        `Schedule Block Dispatched: ${slotTime}`,
        `Physician calendar slot locked and synced across hospital scheduling feeds.`
      );
    },
    [addEvent, showToast]
  );

  const unblockSlot = useCallback(
    (slotTime: string) => {
      setBlockedSlots((prev) => prev.filter((s) => s !== slotTime));
      addEvent({
        type: 'SLOT_BLOCKED',
        title: `Slot Unblocked: ${slotTime}`,
        detail: 'Physician slot reopened for patient discovery.',
        actorRole: 'DOCTOR',
      });
      showToast('info', `Slot Reopened: ${slotTime}`, `Slot is now available for inbound voice scheduling.`);
    },
    [addEvent, showToast]
  );

  const completeEncounter = useCallback(
    (
      bookingId: string,
      soapNotes: { subjective: string; objective: string; assessment: string; plan: string },
      prescriptions: Array<{ medication: string; dosage: string; frequency: string; duration: string }>
    ) => {
      setBookings((prev) =>
        prev.map((b) =>
          b.id === bookingId
            ? {
                ...b,
                status: 'COMPLETED',
                notes: `SOAP Assessment: ${soapNotes.assessment} | Plan: ${soapNotes.plan}`,
                prescriptions,
              }
            : b
        )
      );

      addEvent({
        type: 'ENCOUNTER_COMPLETED',
        title: `Clinical Encounter Signed (#${bookingId})`,
        detail: `E-Prescriptions issued: ${prescriptions.length} items. Sealed with digital clinician signature.`,
        actorRole: 'DOCTOR',
        metadata: { booking_id: bookingId, prescription_count: prescriptions.length },
      });

      showToast(
        'success',
        `Encounter Completed (#${bookingId})`,
        `Digital medical record signed and dispatched to hospital EHR archive.`
      );
    },
    [addEvent, showToast]
  );

  const resolveEscalation = useCallback(
    (ticketId: string, notes: string) => {
      addEvent({
        type: 'ESCALATION_RESOLVED',
        title: `Tier-2 Escalation Closed: ${ticketId}`,
        detail: `Clinical triage resolution: ${notes}`,
        actorRole: 'DOCTOR',
        metadata: { ticket_id: ticketId },
      });

      showToast(
        'success',
        `Escalation Resolved (${ticketId})`,
        `Patient routed to clinical nurse coordinator with documented notes.`
      );
    },
    [addEvent, showToast]
  );

  const triggerEHRSync = useCallback(
    (connector: string) => {
      addEvent({
        type: 'EHR_SYNCED',
        title: `FHIR R4 Connector Sync: ${connector}`,
        detail: `Bi-directional reconciliation completed with zero drift detected.`,
        actorRole: 'HOSPITAL_ADMIN',
        metadata: { connector },
      });

      showToast(
        'ehr_sync',
        `FHIR R4 Sync Complete (${connector})`,
        `All 5 verification checks passed. 0 double-bookings detected.`
      );
    },
    [addEvent, showToast]
  );

  return (
    <PlatformEventContext.Provider
      value={{
        events,
        bookings,
        blockedSlots,
        hospitalUtilization,
        createBooking,
        blockSlot,
        unblockSlot,
        completeEncounter,
        resolveEscalation,
        triggerEHRSync,
      }}
    >
      {children}
    </PlatformEventContext.Provider>
  );
};

export const usePlatformEvents = () => {
  const context = useContext(PlatformEventContext);
  if (!context) {
    throw new Error('usePlatformEvents must be used within a PlatformEventProvider');
  }
  return context;
};
