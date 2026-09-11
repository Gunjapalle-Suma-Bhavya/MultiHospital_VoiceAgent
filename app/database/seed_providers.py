from datetime import time
from app.database.config import SessionLocal
from app.database.models import (
    Hospital, HospitalStatus, Doctor, DoctorStatus,
    DoctorCalendar, CalendarType, DoctorWorkingHour
)
from app.database.mongodb import persist_to_mongodb

def seed_providers():
    db = SessionLocal()
    try:
        hospitals_data = [
            {
                id: HOSP-CITY-01,
                name: City Memorial Hospital,
                code: CITYMEM,
                address: 100 Medical Center Way, Metro City,
                phone_number: +1-555-1000,
                hospital_status: APPROVED,
                is_active: True
            },
            {
                id: HOSP-CARE-02,
                name: Care Regional Hospital,
                code: CAREREG,
                address: 250 Healthcare Blvd, South Valley,
                phone_number: +1-555-2000,
                hospital_status: APPROVED,
                is_active: True
            },
            {
                id: HOSP-METRO-03,
                name: Metro Health Medical Center,
                code: METROHLTH,
                address: 500 Central Ave, Metro City,
                phone_number: +1-555-3000,
                hospital_status: APPROVED,
                is_active: True
            },
            {
                id: HOSP-STJUDE-04,
                name: St. Jude Health System,
                code: STJUDE,
                address: 750 Beacon St, North District,
                phone_number: +1-555-4000,
                hospital_status: APPROVED,
                is_active: True
            }
        ]

        for hd in hospitals_data:
            h = db.query(Hospital).filter(Hospital.id == hd[id]).first()
            if not h:
                h = Hospital(
                    id=hd[id],
                    name=hd[name],
                    code=hd[code],
                    address=hd[address],
                    phone_number=hd[phone_number],
                    hospital_status=HospitalStatus.APPROVED,
                    is_active=True
                )
                db.add(h)
            else:
                h.name = hd[name]
                h.hospital_status = HospitalStatus.APPROVED
                h.is_active = True
            db.commit()
            try:
                persist_to_mongodb(hospitals, hd)
            except Exception:
                pass

        doctors_data = [
            {id: DOC-SHARMA-01, hosp_id: HOSP-CITY-01, name: Dr. Sharma, specialty: Orthopedics, dept: Orthopedic Surgery},
            {id: DOC-RAO-02, hosp_id: HOSP-CARE-02, name: Dr. Rao, specialty: Orthopedics, dept: Orthopedic Surgery},
            {id: DOC-GOMEZ-03, hosp_id: HOSP-METRO-03, name: Dr. Elena Gomez, specialty: Orthopedics, dept: Joint & Spine Care},
            {id: DOC-JENKINS-04, hosp_id: HOSP-CITY-01, name: Dr. Sarah Jenkins, specialty: Cardiology, dept: Cardiovascular Center},
            {id: DOC-CHEN-05, hosp_id: HOSP-CARE-02, name: Dr. David Chen, specialty: Cardiology, dept: Interventional Cardiology},
            {id: DOC-PATEL-06, hosp_id: HOSP-METRO-03, name: Dr. Amit Patel, specialty: Cardiology, dept: Cardiology & Arrhythmia},
            {id: DOC-MARCUS-07, hosp_id: HOSP-CITY-01, name: Dr. Lisa Marcus, specialty: Dermatology, dept: Dermatology & Skin Center},
            {id: DOC-WHITE-08, hosp_id: HOSP-CARE-02, name: Dr. Kevin White, specialty: Dermatology, dept: Clinical Dermatology},
            {id: DOC-VANCE-09, hosp_id: HOSP-CITY-01, name: Dr. Amanda Vance, specialty: Neurology, dept: Neurology & Stroke Institute},
            {id: DOC-MALHOTRA-10, hosp_id: HOSP-STJUDE-04, name: Dr. Vikram Malhotra, specialty: Neurology, dept: Neuroscience Center},
            {id: DOC-GREEN-11, hosp_id: HOSP-METRO-03, name: Dr. Rachel Green, specialty: Gastroenterology, dept: Digestive Health},
            {id: DOC-KIM-12, hosp_id: HOSP-CARE-02, name: Dr. Robert Kim, specialty: Gastroenterology, dept: GI & Endoscopy},
            {id: DOC-WATSON-13, hosp_id: HOSP-CARE-02, name: Dr. Emily Watson, specialty: General Medicine, dept: Family Medicine},
            {id: DOC-REED-14, hosp_id: HOSP-CITY-01, name: Dr. Marcus Reed, specialty: General Medicine, dept: Internal Medicine}
        ]

        for dd in doctors_data:
            doc = db.query(Doctor).filter(Doctor.id == dd[id]).first()
            if not doc:
                doc = Doctor(
                    id=dd[id],
                    hospital_id=dd[hosp_id],
                    name=dd[name],
                    specialty=dd[specialty],
                    department=dd[dept],
                    doctor_status=DoctorStatus.ACTIVE,
                    is_active=True,
                    default_appointment_duration=30
                )
                db.add(doc)
            else:
                doc.hospital_id = dd[hosp_id]
                doc.name = dd[name]
                doc.specialty = dd[specialty]
                doc.department = dd[dept]
                doc.doctor_status = DoctorStatus.ACTIVE
                doc.is_active = True
            db.commit()

            cal = db.query(DoctorCalendar).filter(DoctorCalendar.doctor_id == dd[id]).first()
            if not cal:
                cal = DoctorCalendar(
                    doctor_id=dd[id],
                    calendar_name=f{dd['name']} Primary,
                    calendar_type=CalendarType.HOSPITAL_CONSULTATION,
                    is_active=True
                )
                db.add(cal)
                db.commit()

            for day in range(7):
                wh = db.query(DoctorWorkingHour).filter(
                    DoctorWorkingHour.doctor_id == dd[id],
                    DoctorWorkingHour.day_of_week == day
                ).first()
                if not wh:
                    wh = DoctorWorkingHour(
                        doctor_id=dd[id],
                        day_of_week=day,
                        start_time=time(8, 0),
                        end_time=time(18, 0),
                        break_start=time(12, 0),
                        break_end=time(13, 0)
                    )
                    db.add(wh)
            db.commit()

            try:
                persist_to_mongodb(doctors, dd)
            except Exception:
                pass

        print(SUCCESSFULLY SEEDED DOCTORS AND HOSPITALS)
    finally:
        db.close()

if __name__ == __main__:
    seed_providers()
