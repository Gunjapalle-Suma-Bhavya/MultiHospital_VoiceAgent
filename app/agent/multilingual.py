"""
Multilingual Clinical Localization Engine.

Provides authentic, empathetic, and clinically precise patient communication across:
- Telugu (te)
- Hindi (hi)
- Spanish (es)
- Mandarin Chinese (zh)
- English (en)

Translates specialist triage, appointment booking confirmations, real-time availability,
emergency escalation, and hospital FAQs into the patient's preferred language.
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime


# Specialty Translations
SPECIALTY_NAMES: Dict[str, Dict[str, str]] = {
    "te": {
        "Orthopedics": "ఆర్థోపెడిక్స్ (ఎముకలు మరియు కీళ్ళు)",
        "Cardiology": "కార్డియాలజీ (గుండె సంరక్షణ)",
        "Dermatology": "డెర్మటాలజీ (చర్మ సంరక్షణ)",
        "Neurology": "న్యూరాలజీ (నరాల సంరక్షణ)",
        "Gastroenterology": "గ్యాస్ట్రోఎంటరాలజీ (జీర్ణ మరియు కడుపు సంరక్షణ)",
        "General Medicine": "జనరల్ మెడిసిన్ (సాధారణ వైద్యం)",
        "Emergency Medicine": "ఎమర్జెన్సీ మెడిసిన్ (అత్యవసర వైద్యం)",
        "Ophthalmology": "ఆప్తాల్మాలజీ (కంటి సంరక్షణ)",
        "ENT": "ఈఎన్‌టీ (చెవి, ముక్కు, గొంతు)",
        "Dentistry": "దంత వైద్యం",
    },
    "hi": {
        "Orthopedics": "ऑर्थोपेडिक्स (हड्डी एवं जोड़ रोग)",
        "Cardiology": "कार्डियोलॉजी (हृदय रोग विभाग)",
        "Dermatology": "डर्मेटोलॉजी (त्वचा रोग विभाग)",
        "Neurology": "न्यूरोलॉजी (तंत्रिका रोग विभाग)",
        "Gastroenterology": "गैस्ट्रोएंटरोलॉजी (पेट एवं पाचन रोग)",
        "General Medicine": "जनरल मेडिसिन (सामान्य चिकित्सा)",
        "Emergency Medicine": "इमरजेंसी मेडिसिन (आपातकालीन चिकित्सा)",
        "Ophthalmology": "नेत्र रोग विभाग",
        "ENT": "ईएनटी (कान, नाक, गला)",
        "Dentistry": "दंत चिकित्सा",
    },
    "es": {
        "Orthopedics": "Ortopedia y Traumatología",
        "Cardiology": "Cardiología",
        "Dermatology": "Dermatología",
        "Neurology": "Neurología",
        "Gastroenterology": "Gastroenterología",
        "General Medicine": "Medicina General / Interna",
        "Emergency Medicine": "Medicina de Urgencias",
        "Ophthalmology": "Oftalmología",
        "ENT": "Otorrinolaringología (ORL)",
        "Dentistry": "Odontología",
    },
    "zh": {
        "Orthopedics": "骨科与运动医学科",
        "Cardiology": "心血管内科",
        "Dermatology": "皮肤科",
        "Neurology": "神经内科",
        "Gastroenterology": "消化内科",
        "General Medicine": "全科医学 / 普通内科",
        "Emergency Medicine": "急诊医学科",
        "Ophthalmology": "眼科",
        "ENT": "耳鼻喉科",
        "Dentistry": "口腔科",
    }
}


def format_datetime_multilingual(dt: datetime, lang: str) -> str:
    """Formats datetime nicely in target language."""
    weekday_en = dt.strftime("%A")
    month_en = dt.strftime("%B")
    day = dt.day
    time_str = dt.strftime("%I:%M %p")

    if lang == "te":
        days_te = {
            "Monday": "సోమవారం", "Tuesday": "మంగళవారం", "Wednesday": "బుధవారం",
            "Thursday": "గురువారం", "Friday": "శుక్రవారం", "Saturday": "శనివారం", "Sunday": "ఆదివారం"
        }
        months_te = {
            "January": "జనవరి", "February": "ఫిబ్రవరి", "March": "మార్చి", "April": "ఏప్రిల్",
            "May": "మే", "June": "జూన్", "July": "జూలై", "August": "ఆగస్టు",
            "September": "సెప్టెంబర్", "October": "అక్టోబర్", "November": "నవంబర్", "December": "డిసెంబర్"
        }
        ampm_te = "ఉదయం" if dt.hour < 12 else ("మధ్యాహ్నం" if dt.hour < 17 else "సాయంత్రం")
        formatted_time = dt.strftime("%I:%M")
        return f"{days_te.get(weekday_en, weekday_en)}, {months_te.get(month_en, month_en)} {day}న {ampm_te} {formatted_time} గంటలకు"

    elif lang == "hi":
        days_hi = {
            "Monday": "सोमवार", "Tuesday": "मंगलवार", "Wednesday": "बुधवार",
            "Thursday": "गुरुवार", "Friday": "शुक्रवार", "Saturday": "शनिवार", "Sunday": "रविवार"
        }
        months_hi = {
            "January": "जनवरी", "February": "फ़रवरी", "March": "मार्च", "April": "अप्रैल",
            "May": "मई", "June": "जून", "July": "जुलाई", "August": "अगस्त",
            "September": "सितंबर", "October": "अक्टूबर", "November": "नवंबर", "December": "दिसंबर"
        }
        ampm_hi = "सुबह" if dt.hour < 12 else ("दोपहर" if dt.hour < 17 else "शाम")
        formatted_time = dt.strftime("%I:%M")
        return f"{days_hi.get(weekday_en, weekday_en)}, {day} {months_hi.get(month_en, month_en)} को {ampm_hi} {formatted_time} बजे"

    elif lang == "es":
        days_es = {
            "Monday": "lunes", "Tuesday": "martes", "Wednesday": "miércoles",
            "Thursday": "jueves", "Friday": "viernes", "Saturday": "sábado", "Sunday": "domingo"
        }
        months_es = {
            "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
            "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
            "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
        }
        return f"{days_es.get(weekday_en, weekday_en)}, {day} de {months_es.get(month_en, month_en)} a las {time_str}"

    elif lang == "zh":
        days_zh = {
            "Monday": "星期一", "Tuesday": "星期二", "Wednesday": "星期三",
            "Thursday": "星期四", "Friday": "星期五", "Saturday": "星期六", "Sunday": "星期日"
        }
        ampm_zh = "上午" if dt.hour < 12 else ("下午" if dt.hour < 18 else "晚上")
        formatted_time = dt.strftime("%I:%M")
        return f"{dt.month}月{day}日 {days_zh.get(weekday_en, '')} {ampm_zh} {formatted_time}"

    return dt.strftime("%A, %B %d at %I:%M %p")


class MultilingualClinicalLocalizer:
    """
    Localizes AI Patient Care Coordinator dialogue into Telugu, Hindi, Spanish, and Mandarin.
    """

    @classmethod
    def localize(
        cls,
        english_text: str,
        lang: str = "en",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        if not lang or lang.lower().startswith("en") or not english_text:
            return english_text

        target_lang = lang.lower().split("-")[0]
        ctx = context or {}

        # 1. Booking Confirmation Pattern
        if "Your appointment request has been sent to" in english_text or "is confirmed for" in english_text:
            return cls._localize_booking_confirmation(english_text, target_lang, ctx)

        # 2. Doctor / Specialist Triage Recommendation
        if "Based on clinical intake triage, a consultation with our" in english_text:
            return cls._localize_triage_recommendation(english_text, target_lang, ctx)

        # 3. Doctor Inquiry / Available Slots Offered
        if "I checked the real-time hospital calendar for" in english_text or "Open consultation slots tomorrow are" in english_text:
            return cls._localize_availability_slots(english_text, target_lang, ctx)

        # 4. Pure Greeting Pattern
        if "Hello! I am your AI Patient Care Coordinator" in english_text:
            return cls._localize_greeting(target_lang)

        # 5. Default Empathic Clinical Problem Fallback
        if "I hear your healthcare concern and I am here to help" in english_text:
            return cls._localize_problem_fallback(target_lang)

        # 6. Emergency Escalation
        if "EMERGENCY:" in english_text or "emergency services" in english_text:
            return cls._localize_emergency(target_lang)

        # 7. FAQs
        if "visiting hours for inpatient wards" in english_text or "outpatient specialty clinics are open" in english_text:
            return cls._localize_hours(target_lang)

        if "NexusHealth operates across regional hospital campuses" in english_text:
            return cls._localize_locations(target_lang)

        if "accept Medicare, Medicaid, and most major commercial insurance" in english_text:
            return cls._localize_insurance(target_lang)

        if "bring a valid government-issued photo ID" in english_text:
            return cls._localize_preparation(target_lang)

        if "successfully cancelled in the hospital EHR" in english_text:
            return cls._localize_cancellation(target_lang)

        if "do not currently have any active upcoming appointments" in english_text:
            return cls._localize_no_appointments(target_lang)

        # 8. Specialty Direct Advice Fallbacks
        if "our Orthopedic and Sports Medicine departments specialize" in english_text:
            return cls._localize_ortho_fallback(target_lang)
        if "our Cardiology Center led by Dr. Sarah Jenkins" in english_text:
            return cls._localize_cardio_fallback(target_lang)
        if "our Dermatology department specializes in diagnosing" in english_text:
            return cls._localize_derma_fallback(target_lang)
        if "our Neurology Center led by Dr. Amanda Vance" in english_text:
            return cls._localize_neuro_fallback(target_lang)
        if "our Gastroenterology specialists, Dr. Rachel Green" in english_text:
            return cls._localize_gastro_fallback(target_lang)
        if "our Internal Medicine team, including Dr. Emily Watson" in english_text:
            return cls._localize_internal_med_fallback(target_lang)

        return english_text

    # --- Specific Localization Builders ---

    @classmethod
    def _localize_booking_confirmation(cls, text: str, lang: str, ctx: Dict[str, Any]) -> str:
        m2 = re.search(r"sent to\s+(Dr\.?\s+.+?)\s+at\s+(.+?)\s+and is confirmed for\s+(.+?\s+(?:AM|PM))\.\s*Your verification code is\s+([A-Za-z0-9]+)", text)
        if m2:
            doc_name = m2.group(1).strip()
            hosp_name = m2.group(2).strip()
            raw_time = m2.group(3).strip()
            code = m2.group(4).strip()
        else:
            doc_name = ctx.get("doctor_name") or "Dr. Sharma"
            hosp_name = ctx.get("hospital_name") or "NexusHealth Hospital"
            raw_time = "Tomorrow"
            code = "CONF-1234"

        target_dt = ctx.get("target_datetime")
        if isinstance(target_dt, datetime):
            dt_str = format_datetime_multilingual(target_dt, lang)
        else:
            dt_str = raw_time
            if lang == "te":
                days_map = {"Sunday": "ఆదివారం", "Monday": "సోమవారం", "Tuesday": "మంగళవారం", "Wednesday": "బుధవారం", "Thursday": "గురువారం", "Friday": "శుక్రవారం", "Saturday": "శనివారం"}
                months_map = {"January": "జనవరి", "February": "ఫిబ్రవరి", "March": "మార్చి", "April": "ఏప్రిల్", "May": "మే", "June": "జూన్", "July": "జూలై", "August": "ఆగస్టు", "September": "సెప్టెంబర్", "October": "అక్టోబర్", "November": "నవంబర్", "December": "డిసెంబర్"}
                for k, v in days_map.items(): dt_str = dt_str.replace(k, v)
                for k, v in months_map.items(): dt_str = dt_str.replace(k, v)
                dt_str = dt_str.replace(" at ", " ").replace(" AM", " ఉదయం").replace(" PM", " సాయంత్రం") + " గంటలకు"

        if lang == "te":
            return (
                f"ఖచ్చితంగా! మీ అపాయింట్‌మెంట్ అభ్యర్థనను ప్రస్తుతం ప్రాసెస్ చేస్తున్నాను. "
                f"{hosp_name} లో {doc_name} వద్ద మీ అపాయింట్‌మెంట్ అభ్యర్థన పంపబడింది మరియు {dt_str} కి ఖరారైంది. "
                f"మీ ధృవీకరణ కోడ్ {code}. మీ స్లాట్ ఆసుపత్రి EHR సిస్టమ్‌లో మరియు {doc_name} షెడ్యూల్‌లో నమోదు చేయబడింది. "
                f"దయచేసి మీ ఫోటో గుర్తింపు కార్డు మరియు బీమా కార్డుతో 15 నిమిషాల ముందుగా రండి. ఈ రోజు నేను మీకు ఇంకేమైనా సహాయం చేయగలనా?"
            )
        elif lang == "hi":
            return (
                f"बिल्कुल! मैं आपके अपॉइंटमेंट के अनुरोध को अभी प्रोसेस कर रहा हूँ। "
                f"{hosp_name} में {doc_name} के साथ आपका अपॉइंटमेंट {dt_str} के लिए कन्फर्म कर दिया गया है। "
                f"आपका वेरिफिकेशन कोड {code} है। आपका स्लॉट अस्पताल EHR सिस्टम और डॉक्टर के शेड्यूल में दर्ज हो चुका है। "
                f"कृपया अपनी फोटो आईडी और बीमा कार्ड के साथ 15 मिनट पहले पहुंचें। क्या मैं आज आपकी कोई और मदद कर सकता हूँ?"
            )
        elif lang == "es":
            return (
                f"¡Por supuesto! Estoy procesando su solicitud de cita en este momento. "
                f"Su solicitud ha sido enviada al {doc_name} en {hosp_name} y está confirmada para el {dt_str}. "
                f"Su código de verificación es {code}. Su espacio está bloqueado en el sistema EHR del hospital y en la agenda del doctor. "
                f"Por favor llegue 15 minutos antes con su identificación oficial con fotografía y tarjeta de seguro. ¿Puedo ayudarle con algo más hoy?"
            )
        elif lang == "zh":
            return (
                f"好的！我正在为您处理预约申请。已成功向位于 {hosp_name} 的 {doc_name} 提交预约，"
                f"就诊时间已确认为 {dt_str}。您的就诊验证码是 {code}。"
                f"您的号源已在医院电子病历系统（EHR）及医生的就诊日程中锁定。"
                f"就诊当天请携带有效身份证件及医保卡提前 15 分钟到达诊室签到。请问今天还需要为您提供其他帮助吗？"
            )
        return text

    @classmethod
    def _localize_triage_recommendation(cls, text: str, lang: str, ctx: Dict[str, Any]) -> str:
        spec_match = re.search(r'consultation with our\s+(.+?)\s+department is strongly recommended', text)
        m1 = re.search(r'available:\s*(.+?)\.\s*Would you like me to reserve a priority consultation slot with\s*(.+?)(?:,|\sor\s)', text)

        spec = spec_match.group(1).strip() if spec_match else (ctx.get("specialty") or "General Medicine")
        doc_list = m1.group(1).strip() if m1 else "మా నిపుణులు"
        top_doc = m1.group(2).strip() if m1 else (ctx.get("doctor_name") or "డాక్టర్")

        spec_localized = SPECIALTY_NAMES.get(lang, {}).get(spec, spec)

        if lang == "te":
            return (
                f"మీ లక్షణాల పట్ల మీ ఆందోళనను నేను అర్థం చేసుకున్నాను. క్లినికల్ ఇన్‌టేక్ ట్రయాజ్ ఆధారంగా, "
                f"మా {spec_localized} విభాగం వైద్యులను సంప్రదించాల్సిందిగా గట్టిగా సిఫార్సు చేస్తున్నాము. "
                f"ప్రస్తుతం మా వద్ద అగ్రశ్రేణి నిపుణులు అందుబాటులో ఉన్నారు: {doc_list}. "
                f"మీరు {top_doc} తో ప్రాధాన్యతా సంప్రదింపు స్లాట్‌ను బుక్ చేయాలనుకుంటున్నారా, లేదా రేపటి సమయాలను చూడాలనుకుంటున్నారా?"
            )
        elif lang == "hi":
            return (
                f"मैं आपके लक्षणों को समझता हूँ। प्राथमिक क्लिनिकल ट्राइएज के आधार पर, "
                f"हमारे {spec_localized} के विशेषज्ञों से परामर्श की सिफारिश की जाती है। "
                f"हमारे पास शीर्ष विशेषज्ञ उपलब्ध हैं: {doc_list}। "
                f"क्या आप {top_doc} के साथ अपॉइंटमेंट बुक करना चाहेंगे, या कल के उपलब्ध समय देखना चाहेंगे?"
            )
        elif lang == "es":
            return (
                f"Comprendo su preocupación respecto a sus síntomas. Según el triaje clínico inicial, "
                f"se recomienda encarecidamente una consulta con nuestro departamento de {spec_localized}. "
                f"Actualmente contamos con excelentes especialistas disponibles: {doc_list}. "
                f"¿Le gustaría que reserve un turno de consulta prioritario con {top_doc}, o prefiere consultar los horarios disponibles para mañana?"
            )
        elif lang == "zh":
            return (
                f"我理解您对病情的担忧。根据临床接诊分诊评估，强烈推荐您预约我院的 {spec_localized} 进行就诊。"
                f"目前该专科有优质专家可预约：{doc_list}。"
                f"您是否希望为您优先锁定 {top_doc} 医生的面诊名额，或者查看明天的详细空闲时段？"
            )
        return text

    @classmethod
    def _localize_availability_slots(cls, text: str, lang: str, ctx: Dict[str, Any]) -> str:
        hosp_cal_match = re.search(r'calendar for\s+(Dr\.\s+[^at]+?)\s+at\s+([^.]+?)\.\s+We have open 30-minute consultation slots available tomorrow at:\s+([^.]+)', text)
        if hosp_cal_match:
            doc_name = hosp_cal_match.group(1).strip()
            hosp_name = hosp_cal_match.group(2).strip()
            slot_times = hosp_cal_match.group(3).strip()
            first_time = slot_times.split(",")[0].strip() if "," in slot_times else slot_times

            if lang == "te":
                return (
                    f"{hosp_name} లోని {doc_name} కోసం నేను రియల్-టైమ్ ఆసుపత్రి క్యాలెండర్‌ను తనిఖీ చేసాను. "
                    f"రేపు 30 నిమిషాల సంప్రదింపు స్లాట్లు అందుబాటులో ఉన్నాయి: {slot_times}. "
                    f"మీ కోసం {first_time} స్లాట్‌ను బుక్ చేయమంటారా, లేదా మీరు మరొక సమయాన్ని ఇష్టపడతారా?"
                )
            elif lang == "hi":
                return (
                    f"मैंने {hosp_name} में {doc_name} के लिए रीयल-टाइम अस्पताल कैलेंडर चेक किया है। "
                    f"कल 30 मिनट के परामर्श स्लॉट उपलब्ध हैं: {slot_times}। "
                    f"क्या मैं आपके लिए {first_time} का स्लॉट बुक कर दूँ, या आप कोई दूसरा समय पसंद करेंगे?"
                )
            elif lang == "es":
                return (
                    f"He consultado la agenda del hospital en tiempo real para {doc_name} en {hosp_name}. "
                    f"Tenemos turnos de consulta de 30 minutos disponibles mañana a las: {slot_times}. "
                    f"¿Desea que reserve el turno de las {first_time} para usted, o prefiere otro horario?"
                )
            elif lang == "zh":
                return (
                    f"我已为您实时查询 {hosp_name} 的 {doc_name} 门诊日程。"
                    f"明天开放的 30 分钟面诊时段包括：{slot_times}。"
                    f"需要为您直接锁定 {first_time} 的时段，还是您更倾向于其他时间？"
                )

        if lang == "te":
            return "రేపటి కోసం అందుబాటులో ఉన్న సంప్రదింపు సమయాలను తనిఖీ చేయమంటారా?"
        elif lang == "hi":
            return "क्या आप चाहते हैं कि मैं कल के लिए उपलब्ध समय स्लॉट देखूँ?"
        elif lang == "es":
            return "¿Desea que consulte los horarios de consulta disponibles para mañana?"
        elif lang == "zh":
            return "需要为您查询明天的可用就诊时段吗？"
        return text

    @classmethod
    def _localize_greeting(cls, lang: str) -> str:
        if lang == "te":
            return (
                "నమస్కారం! నేను నెక్సస్‌హెల్త్ మల్టీ-హాస్పిటల్ నెట్‌వర్క్ యొక్క AI పేషెంట్ కేర్ కోఆర్డినేటర్‌ని. "
                "ఈ రోజు డాక్టర్ అపాయింట్‌మెంట్ షెడ్యూల్ చేయడం, క్లినిక్ వేళలను తనిఖీ చేయడం లేదా మీ ఆరోగ్య అవసరాలలో నేను మీకు ఏ విధంగా సహాయపడగలను?"
            )
        elif lang == "hi":
            return (
                "नमस्ते! मैं नेक्ससहेल्थ मल्टी-हॉस्पिटल नेटवर्क का एआई पेशेंट केयर कोऑर्डिनेटर हूँ। "
                "आज मैं डॉक्टर का अपॉइंटमेंट बुक करने, क्लिनिक के समय की जांच करने या आपके स्वास्थ्य संबंधी प्रश्नों में कैसे मदद कर सकता हूँ?"
            )
        elif lang == "es":
            return (
                "¡Hola! Soy su Coordinador de Atención al Paciente de IA de la red multihospitalaria NexusHealth. "
                "¿Cómo puedo ayudarle hoy a programar una cita médica, consultar los horarios de las clínicas o atender sus necesidades de salud?"
            )
        elif lang == "zh":
            return (
                "您好！我是 NexusHealth 医疗网络的人工智能就医服务顾问。"
                "请问今天在预约专科门诊、查询出诊时间或解答健康疑问方面，有什么可以为您协助的？"
            )
        return ""

    @classmethod
    def _localize_problem_fallback(cls, lang: str) -> str:
        if lang == "te":
            return (
                "మీ ఆరోగ్య సమస్యను నేను విన్నాను మరియు మీకు సరైన వైద్య సంరక్షణ అందించడానికి నేను ఇక్కడ ఉన్నాను. "
                "మీరు వివరించిన లక్షణాల ఆధారంగా, సిటీ మెమోరియల్ హాస్పిటల్ లేదా కేర్ రీజినల్ హాస్పిటల్‌లోని మా వైద్యులతో సంప్రదింపులను మా క్లినికల్ బృందం గట్టిగా సిఫార్సు చేస్తోంది. "
                "మా వద్ద రేపటి కోసం బోర్డ్-సర్టిఫైడ్ నిపుణులు అందుబాటులో ఉన్నారు. మీరు మా నిపుణుడితో అపాయింట్‌మెంట్ బుక్ చేయాలనుకుంటున్నారా, లేదా అందుబాటులో ఉన్న సమయాలను పరిశీలించమంటారా?"
            )
        elif lang == "hi":
            return (
                "मैंने आपके स्वास्थ्य संबंधी चिंता को समझ लिया है और आपकी सही देखभाल के लिए यहाँ हूँ। "
                "आपके बताए लक्षणों के आधार पर, हमारी क्लिनिकल टीम सिटी मेमोरियल या केयर रीजनल अस्पताल में डॉक्टर से परामर्श लेने की सलाह देती है। "
                "कल के लिए हमारे पास शीर्ष विशेषज्ञ उपलब्ध हैं। क्या आप अपॉइंटमेंट बुक करना चाहेंगे या उपलब्ध समय देखना चाहेंगे?"
            )
        elif lang == "es":
            return (
                "Comprendo su inquietud de salud y estoy aquí para ayudarle a recibir la atención adecuada. "
                "Según los síntomas que ha descrito, nuestro equipo clínico recomienda una evaluación con nuestros médicos en City Memorial Hospital o Care Regional Hospital. "
                "Contamos con destacados especialistas certificados disponibles mañana. ¿Desea que reserve una cita con un especialista o prefiere consultar los horarios disponibles?"
            )
        elif lang == "zh":
            return (
                "我已详细了解您的不适症状，将全力协助您获得最匹配的医疗照护。"
                "结合您描述的情况，临床团队建议您前往城市纪念医院（City Memorial）或关怀区域医院（Care Regional）就诊。"
                "明天有多位资深主任医师开放预约。请问需要直接为您预约专家号，还是先查看空闲时间？"
            )
        return ""

    @classmethod
    def _localize_emergency(cls, lang: str) -> str:
        if lang == "te":
            return "అత్యవసర హెచ్చరిక: మీరు ప్రాణాపాయకరమైన అత్యవసర పరిస్థితిని ఎదుర్కొంటున్నట్లయితే, దయచేసి వెంటనే 108 లేదా 911 కి కాల్ చేయండి. మీ కాల్‌ను మా ఆన్-డ్యూటీ హెల్త్‌కేర్ ట్రయాజ్ కోఆర్డినేటర్‌కు బదిలీ చేస్తున్నాము. దయచేసి లైన్‌లో ఉండండి."
        elif lang == "hi":
            return "आपातकालीन चेतावनी: यदि आप जानलेवा आपात स्थिति का सामना कर रहे हैं, तो कृपया तुरंत 112 या 911 पर कॉल करें। आपकी कॉल को ऑन-ड्यूटी ट्रायज कोऑर्डिनेटर को ट्रांसफर किया जा रहा है। कृपया लाइन पर बने रहें।"
        elif lang == "es":
            return "EMERGENCIA: Si experimenta una emergencia que pone en peligro su vida, llame al 911 de inmediato. Transfiriendo su llamada al coordinador de triaje de guardia ahora mismo. Por favor permanezca en la línea."
        elif lang == "zh":
            return "急救警示：如遇危及生命的突发急症，请立即拨打 120/911 急救电话。正在为您转接值班急诊分诊协调员，请不要挂断电话。"
        return ""

    @classmethod
    def _localize_hours(cls, lang: str) -> str:
        if lang == "te":
            return (
                "మా ఔట్ పేషెంట్ స్పెషాలిటీ క్లినిక్‌లు సోమవారం నుండి శుక్రవారం వరకు ఉదయం 8:00 నుండి సాయంత్రం 6:00 వరకు, "
                "మరియు శనివారం ఉదయం 9:00 నుండి మధ్యాహ్నం 1:00 వరకు తెరిచి ఉంటాయి. ఇన్‌పేషెంట్ వార్డుల సాధారణ సందర్శన వేళలు ప్రతిరోజూ ఉదయం 8:00 నుండి రాత్రి 8:00 వరకు. "
                "మా నెట్‌వర్క్ ఆసుపత్రులన్నింటిలో ఎమర్జెన్సీ విభాగాలు 24/7 తెరిచి ఉంటాయి. మీరు క్లినిక్ వేళల్లో అపాయింట్‌మెంట్ షెడ్యూల్ చేయాలనుకుంటున్నారా?"
            )
        elif lang == "hi":
            return (
                "हमारे आउटपेशेंट स्पेशलिटी क्लिनिक सोमवार से शुक्रवार सुबह 8:00 से शाम 6:00 बजे तक और शनिवार को सुबह 9:00 से दोपहर 1:00 बजे तक खुले रहते हैं। "
                "इनपेशेंट वार्डों के लिए मिलने का सामान्य समय प्रतिदिन सुबह 8:00 से रात 8:00 बजे तक है। हमारे सभी नेटवर्क अस्पतालों के आपातकालीन विभाग 24/7 खुले रहते हैं।"
            )
        elif lang == "es":
            return (
                "Nuestras clínicas de especialidades atienden de lunes a viernes de 8:00 AM a 6:00 PM, y sábados de 9:00 AM a 1:00 PM. "
                "El horario de visitas para pacientes hospitalizados es de 8:00 AM a 8:00 PM todos los días. Las salas de urgencias atienden 24/7. ¿Le gustaría agendar una cita?"
            )
        elif lang == "zh":
            return (
                "我院专科门诊时间为周一至周五 08:00-18:00，周六 09:00-13:00。"
                "住院部探视时间为每日 08:00-20:00。网络内各院区急诊中心全年 24 小时无休。您需要预约门诊时间吗？"
            )
        return ""

    @classmethod
    def _localize_locations(cls, lang: str) -> str:
        if lang == "te":
            return (
                "నెక్సస్‌హెల్త్ ప్రాంతీయ ఆసుపత్రి క్యాంపస్‌లలో పనిచేస్తుంది: సిటీ మెమోరియల్ హాస్పిటల్ 100 మెడికల్ సెంటర్ వే, మెట్రో సిటీ వద్ద ఉంది; "
                "కేర్ రీజినల్ హాస్పిటల్ 250 హెల్త్‌కేర్ బ్లవ్‌డ్, సౌత్ వ్యాలీ వద్ద ఉంది; మరియు మెట్రో హెల్త్ మెడికల్ సెంటర్ 500 సెంట్రల్ ఏవ్ వద్ద ఉంది. "
                "అన్ని స్థానాల్లో పార్కింగ్ మరియు వీల్‌చైర్ సదుపాయం కలదు. మీరు ఏ క్యాంపస్‌ను సందర్శించాలనుకుంటున్నారు?"
            )
        elif lang == "hi":
            return (
                "नेक्ससहेल्थ विभिन्न रीजनल हॉस्पिटल परिसरों में कार्यरत है: सिटी मेमोरियल हॉस्पिटल (100 मेडिकल सेंटर वे), "
                "केयर रीजनल हॉस्पिटल (250 हेल्थकेयर बुलेवार्ड), और मेट्रो हेल्थ मेडिकल सेंटर (500 सेंट्रल एवेन्यू)। "
                "सभी स्थानों पर पार्किंग और व्हीलचेयर सुविधा उपलब्ध है। आप किस परिसर में जाना चाहेंगे?"
            )
        elif lang == "es":
            return (
                "NexusHealth opera en varios centros hospitalarios: City Memorial Hospital en 100 Medical Center Way; "
                "Care Regional Hospital en 250 Healthcare Blvd; y Metro Health Medical Center en 500 Central Ave. "
                "Todas las sedes disponen de estacionamiento validado y accesibilidad. ¿Cuál de nuestras sedes desea visitar?"
            )
        elif lang == "zh":
            return (
                "NexusHealth 拥有多家区域医疗院区：城市纪念医院位于 100 Medical Center Way；关怀区域医院位于 250 Healthcare Blvd；"
                "大都会医疗中心位于 500 Central Ave。各院区均配备专用患者停车场与无障碍通道。请问您想前往哪家院区？"
            )
        return ""

    @classmethod
    def _localize_insurance(cls, lang: str) -> str:
        if lang == "te":
            return (
                "నెక్సస్‌హెల్త్ ఆసుపత్రులు మెడికేర్, మెడికాయిడ్ మరియు బ్లూ క్రాస్ బ్లూ షీల్డ్, ఏట్నా, సిగ్నా, యునైటెడ్‌హెల్త్‌కేర్‌లతో సహా ప్రధాన వాణిజ్య బీమాలను అంగీకరిస్తాయి. "
                "మీ సంప్రదింపుకు ముందు మా బృందం మీ అర్హత మరియు కోపేను ధృవీకరిస్తుంది. మీరు స్పెషలిస్ట్‌తో అపాయింట్‌మెంట్ బుక్ చేయాలనుకుంటున్నారా?"
            )
        elif lang == "hi":
            return (
                "नेक्ससहेल्थ अस्पताल मेडिकेयर, मेडिकेड और प्रमुख वाणिज्यिक बीमा पॉलिसियों को स्वीकार करते हैं। "
                "हमारी टीम आपके परामर्श से पहले कवरेज और को-पे की पुष्टि करेगी। क्या आप डॉक्टर से अपॉइंटमेंट बुक करना चाहते हैं?"
            )
        elif lang == "es":
            return (
                "Los hospitales de NexusHealth aceptan Medicare, Medicaid y los principales seguros comerciales como Blue Cross, Aetna, Cigna y UnitedHealthcare. "
                "Verificaremos su cobertura y copago antes de su consulta. ¿Desea programar su cita?"
            )
        elif lang == "zh":
            return (
                "NexusHealth 支持各类主流医疗保险与医保计划。在您就诊前，我们的团队会协助核验您的报销资质与自付额。"
                "需要现在为您预约专科门诊吗？"
            )
        return ""

    @classmethod
    def _localize_preparation(cls, lang: str) -> str:
        if lang == "te":
            return (
                "మీ ఆసుపత్రి అపాయింట్‌మెంట్ కోసం, దయచేసి చెల్లుబాటు అయ్యే ప్రభుత్వ ఫోటో ఐడి, బీమా కార్డు మరియు ఏవైనా మునుపటి వైద్య రికార్డులు లేదా మందుల వివరాలను తీసుకురండి. "
                "చెక్-ఇన్ పూర్తి చేయడానికి మీ షెడ్యూల్ సమయానికి 15 నిమిషాల ముందుగా రావాలని మేము సిఫార్సు చేస్తున్నాము. అపాయింట్‌మెంట్ బుక్ చేయడంలో నేను మీకు సహాయపడగలనా?"
            )
        elif lang == "hi":
            return (
                "अस्पताल में अपनी अपॉइंटमेंट के लिए कृपया एक वैध सरकारी फोटो पहचान पत्र, सक्रिय बीमा कार्ड और अपनी पिछली मेडिकल रिपोर्ट साथ लाएं। "
                "समय पर चेक-इन के लिए 15 मिनट पहले पहुंचने की सलाह दी जाती है। क्या मैं अपॉइंटमेंट बुक करने में आपकी मदद करूँ?"
            )
        elif lang == "es":
            return (
                "Para su cita, por favor traiga una identificación oficial vigente con fotografía, tarjeta de seguro activa y cualquier registro médico o medicamento actual. "
                "Recomendamos llegar 15 minutos antes. ¿Puedo ayudarle a reservar un horario de consulta?"
            )
        elif lang == "zh":
            return (
                "门诊就医时，请务必携带本人有效身份证件、有效医保卡以及既往病历资料或当前用药清单。"
                "建议提前 15 分钟到达以完成报道登记。现在需要协助您挑选预约时间段吗？"
            )
        return ""

    @classmethod
    def _localize_cancellation(cls, lang: str) -> str:
        if lang == "te":
            return "ఆసుపత్రి EHR సిస్టమ్‌లో మీ రాబోయే అపాయింట్‌మెంట్ విజయవంతంగా రద్దు చేయబడింది. మీరు భవిష్యత్తు తేదీ కోసం రీషెడ్యూల్ చేయాలనుకుంటున్నారా?"
        elif lang == "hi":
            return "अस्पताल EHR सिस्टम में आपकी आगामी अपॉइंटमेंट सफलतापूर्वक रद्द कर दी गई है। क्या आप भविष्य के लिए रीशेड्यूल करना चाहेंगे?"
        elif lang == "es":
            return "Su próxima cita ha sido cancelada exitosamente en el sistema EHR del hospital. ¿Desea reprogramarla para una fecha posterior?"
        elif lang == "zh":
            return "您近期的就诊预约已在医院系统中成功取消。请问需要改约至其他日期吗？"
        return ""

    @classmethod
    def _localize_no_appointments(cls, lang: str) -> str:
        if lang == "te":
            return "ప్రస్తుతం మీ రికార్డులలో రద్దు చేయడానికి ఎలాంటి అపాయింట్‌మెంట్‌లు లేవు. మీరు కొత్త అపాయింట్‌మెంట్ షెడ్యూల్ చేయాలనుకుంటున్నారా?"
        elif lang == "hi":
            return "वर्तमान में आपके नाम पर कोई आगामी अपॉइंटमेंट दर्ज नहीं है। क्या आप नई अपॉइंटमेंट लेना चाहेंगे?"
        elif lang == "es":
            return "No tiene citas programadas actualmente en el sistema para cancelar. ¿Desea agendar una nueva consulta?"
        elif lang == "zh":
            return "系统中当前未查询到您名下有待就诊的预约记录。需要为您挂号预约新的门诊吗？"
        return ""

    @classmethod
    def _localize_ortho_fallback(cls, lang: str) -> str:
        if lang == "te":
            return (
                "మీరు ఆర్థోపెడిక్ నొప్పి లేదా కీళ్ల అసౌకర్యంతో బాధపడుతున్నారని నేను అర్థం చేసుకున్నాను. "
                "మా ఆర్థోపెడిక్ మరియు స్పోర్ట్స్ మెడిసిన్ విభాగాలు కీళ్ల మూల్యాంకనాలు, వెన్నెముక సంరక్షణ మరియు పునరావాస చికిత్సలో ప్రత్యేకత కలిగి ఉన్నాయి. "
                "సిటీ మెమోరియల్ హాస్పిటల్‌లో డాక్టర్ శర్మ మరియు కేర్ రీజినల్ హాస్పిటల్‌లో డాక్టర్ రావు అందుబాటులో ఉన్నారు. "
                "రేపటి కోసం మీ సంప్రదింపు స్లాట్‌లను తనిఖీ చేయమంటారా?"
            )
        elif lang == "hi":
            return "हड्डी या जोड़ों के दर्द के लिए हमारा ऑर्थोपेडिक्स विभाग विशेषज्ञ देखभाल प्रदान करता है। डॉ. शर्मा और डॉ. राव उपलब्ध हैं। क्या मैं कल के लिए समय देखूँ?"
        elif lang == "es":
            return "Nuestro departamento de Ortopedia y Medicina Deportiva se especializa en dolores articulares y de espalda. Los doctores Sharma y Rao están disponibles. ¿Desea consultar turnos para mañana?"
        elif lang == "zh":
            return "我院骨科中心擅长关节、脊柱与运动损伤诊疗。沙玛医生与劳医生均在开诊。需要查询明天的号源吗？"
        return ""

    @classmethod
    def _localize_cardio_fallback(cls, lang: str) -> str:
        if lang == "te":
            return (
                "గుండె లేదా ఛాతీ సమస్యలతో సంప్రదించినందుకు ధన్యవాదాలు. "
                "డాక్టర్ సారా జెంకిన్స్ మరియు డాక్టర్ డేవిడ్ చెన్ నేతృత్వంలోని మా కార్డియాలజీ విభాగం సమగ్ర గుండె పరీక్షలను అందిస్తుంది. "
                "మీకు తీవ్రమైన ఛాతీ నొప్పి ఉంటే వెంటనే 108 లేదా 911 కి కాల్ చేయండి. లేదంటే మా కార్డియాలజీ బృందంతో అపాయింట్‌మెంట్ బుక్ చేయమంటారా?"
            )
        elif lang == "hi":
            return "हृदय संबंधी लक्षणों के लिए हमारा कार्डियोलॉजी सेंटर डॉ. जेनकिंस और डॉ. चेन के नेतृत्व में उपलब्ध है। यदि तेज सीने में दर्द है तो तुरंत 112 पर कॉल करें, अन्यथा क्या मैं परामर्श बुक करूँ?"
        elif lang == "es":
            return "Nuestro Centro de Cardiología ofrece evaluaciones completas. Si siente dolor severo en el pecho, llame al 911 de inmediato. De lo contrario, ¿desea reservar una consulta cardiológica?"
        elif lang == "zh":
            return "感谢您咨询心血管专科。若出现剧烈胸痛或呼吸骤停前兆，请立即拨打 120 急救。常规面诊可由詹金斯医生或陈医生接诊，需要为您预约吗？"
        return ""

    @classmethod
    def _localize_derma_fallback(cls, lang: str) -> str:
        if lang == "te":
            return (
                "మీకు చర్మ సమస్యలు ఉన్నాయని నేను అర్థం చేసుకున్నాను. మా డెర్మటాలజీ విభాగం దద్దుర్లు, అలెర్జీలు మరియు చర్మ వ్యాధులను నయం చేయడంలో నిపుణత కలిగి ఉంది. "
                "సిటీ మెమోరియల్ హాస్పిటల్‌లో డాక్టర్ లిసా మార్కస్ మరియు కేర్ రీజినల్ హాస్పిటల్‌లో డాక్టర్ కెవిన్ వైట్ అందుబాటులో ఉన్నారు. రేపటి స్లాట్‌లను తనిఖీ చేయమంటారా?"
            )
        elif lang == "hi":
            return "त्वचा की समस्याओं व चकत्तों के लिए हमारे डर्मेटोलॉजी विशेषज्ञ डॉ. लिसा मार्कस और डॉ. केविन व्हाइट उपलब्ध हैं। क्या कल के लिए समय चेक करूँ?"
        elif lang == "es":
            return "Para problemas de la piel o alergias, nuestros dermatólogos Dr. Marcus y Dr. White están disponibles. ¿Desea revisar turnos para mañana?"
        elif lang == "zh":
            return "针对皮疹、过敏或皮肤病灶，我院皮肤科马库斯医生与怀特医生均可提供专业诊疗。需要查看明天的号源吗？"
        return ""

    @classmethod
    def _localize_neuro_fallback(cls, lang: str) -> str:
        if lang == "te":
            return (
                "మీ తలనొప్పి లేదా నరాల సమస్యలపై మీ ఆందోళనను నేను విన్నాను. "
                "డాక్టర్ అమండా వాన్స్ మరియు డాక్టర్ విక్రమ్ మల్హోత్రా నేతృత్వంలోని మా న్యూరాలజీ సెంటర్ మైగ్రేన్ మరియు నరాల సమస్యలను సమగ్రంగా పరిశీలిస్తుంది. రేపటి సమయాలు చూడమంటారా?"
            )
        elif lang == "hi":
            return "सिरदर्द या न्यूरोलॉजिकल लक्षणों के लिए हमारे विशेषज्ञ डॉ. अमांडा वेंस और डॉ. विक्रम मल्होत्रा उपलब्ध हैं। क्या मैं कल के समय की जांच करूँ?"
        elif lang == "es":
            return "Para migrañas o afecciones neurológicas, nuestro Centro de Neurología ofrece atención integral. ¿Desea consultar horarios para mañana?"
        elif lang == "zh":
            return "针对偏头痛、头晕或神经性不适，神经内科万斯主任与马霍特拉医生提供全方位诊治。需要查询明天的就诊时段吗？"
        return ""

    @classmethod
    def _localize_gastro_fallback(cls, lang: str) -> str:
        if lang == "te":
            return (
                "మీకు కడుపు నొప్పి లేదా జీర్ణ సమస్యలు ఉన్నందుకు చింతిస్తున్నాను. "
                "మా గ్యాస్ట్రోఎంటరాలజీ నిపుణులు డాక్టర్ రాచెల్ గ్రీన్ మరియు డాక్టర్ రాబర్ట్ కిమ్ జీర్ణశయాంతర సమస్యలకు సమగ్ర సంరక్షణను అందిస్తారు. రేపటి కోసం అపాయింట్‌మెంట్ సమయాలను తనిఖీ చేయమంటారా?"
            )
        elif lang == "hi":
            return "पेट व पाचन संबंधी समस्याओं के लिए गैस्ट्रोएंटरोलॉजी विशेषज्ञ डॉ. रेचेल ग्रीन और डॉ. रॉबर्ट किम उपलब्ध हैं। क्या कल के लिए अपॉइंटमेंट देखूँ?"
        elif lang == "es":
            return "Para molestias digestivas o estomacales, nuestros gastroenterólogos Dr. Green y Dr. Kim ofrecen atención especializada. ¿Desea revisar horarios para mañana?"
        elif lang == "zh":
            return "对于胃痛、反酸或胃肠道不适，消化内科格林医生与金医生均可提供检查诊治。需要为您查询明天的号源吗？"
        return ""

    @classmethod
    def _localize_internal_med_fallback(cls, lang: str) -> str:
        if lang == "te":
            return (
                "మీరు అనారోగ్యంతో ఉన్నందుకు చింతిస్తున్నాను. జ్వరం, దగ్గు లేదా ఇతర ఇన్ఫెక్షన్ల కోసం మా జనరల్ మెడిసిన్ బృందం (డాక్టర్ ఎమిలీ వాట్సన్, డాక్టర్ మార్కస్ రీడ్) అదే రోజు సంప్రదింపులను అందిస్తుంది. డాక్టర్ వాట్సన్‌తో అపాయింట్‌మెంట్ బుక్ చేయమంటారా?"
            )
        elif lang == "hi":
            return "बुखार, खांसी या अस्वस्थता के लिए हमारे इंटरनल मेडिसिन विशेषज्ञ डॉ. एमिली वॉटसन और डॉ. मार्कस रीड उपलब्ध हैं। क्या मैं अपॉइंटमेंट तय करूँ?"
        elif lang == "es":
            return "Para fiebre, malestar general o síntomas gripales, nuestro equipo de Medicina Interna ofrece atención el mismo día. ¿Desea programar su consulta?"
        elif lang == "zh":
            return "对于发热、咳嗽或全身不适，普通内科沃森医生与里德医生提供同日看诊服务。需要为您预约就诊吗？"
        return ""
