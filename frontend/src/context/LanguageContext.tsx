import React, { createContext, useContext, useState, useEffect } from 'react';

export type SupportedLanguage = 'en' | 'es' | 'hi' | 'te' | 'zh';

export interface LanguageOption {
  code: SupportedLanguage;
  label: string;
  native: string;
  flag: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'en', label: 'English', native: 'English', flag: '🇺🇸' },
  { code: 'es', label: 'Spanish', native: 'Español', flag: '🇪🇸' },
  { code: 'hi', label: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు', flag: '🇮🇳' },
  { code: 'zh', label: 'Mandarin', native: '中文', flag: '🇨🇳' },
];

const TRANSLATIONS: Record<SupportedLanguage, Record<string, string>> = {
  en: {
    voice_greeting: 'Hello! I am your Autonomous Medical Assistant. How can I help you today?',
    voice_desc: 'Speak naturally to describe symptoms or schedule appointments across partner hospitals.',
    press_to_speak: 'Press to Speak',
    listening: 'Listening to your voice...',
    processing: 'Analyzing symptoms & doctor availability...',
    doctor_discovery: 'Doctor & Specialist Discovery',
    book_appointment: 'Book Appointment',
    select_slot: 'Select Consultation Time',
    triage_desk: 'Clinical Triage Desk',
    pain_level: 'Reported Pain Severity (1 - 10)',
    body_location: 'Primary Pain / Symptom Region',
    emergency_warning: 'If you are experiencing a life-threatening emergency, please call 911 immediately.',
    care_pass: 'Digital Clinical Care Pass',
    kiosk_checkin: 'Contactless Kiosk Check-In',
    print_pass: 'Print Care Pass',
    download_pdf: 'Download PDF Pass',
    apple_wallet: 'Add to Mobile Wallet',
    mic_device: 'Audio Input Microphone',
    volume_level: 'Microphone Input Level',
  },
  es: {
    voice_greeting: '¡Hola! Soy su asistente médico autónomo. ¿Cómo puedo ayudarle hoy?',
    voice_desc: 'Hable con naturalidad para describir síntomas o programar citas en nuestros hospitales asociados.',
    press_to_speak: 'Presione para hablar',
    listening: 'Escuchando su voz...',
    processing: 'Analizando síntomas y disponibilidad de médicos...',
    doctor_discovery: 'Descubrimiento de médicos y especialistas',
    book_appointment: 'Reservar cita',
    select_slot: 'Seleccionar horario de consulta',
    triage_desk: 'Mesa de triaje clínico',
    pain_level: 'Severidad del dolor reportado (1 - 10)',
    body_location: 'Región primaria del dolor / síntoma',
    emergency_warning: 'Si experimenta una emergencia potencialmente mortal, llame al 911 de inmediato.',
    care_pass: 'Pase de atención clínica digital',
    kiosk_checkin: 'Registro sin contacto en quiosco',
    print_pass: 'Imprimir pase',
    download_pdf: 'Descargar pase en PDF',
    apple_wallet: 'Agregar a Mobile Wallet',
    mic_device: 'Micrófono de entrada de audio',
    volume_level: 'Nivel de entrada del micrófono',
  },
  hi: {
    voice_greeting: 'नमस्ते! मैं आपका स्वायत्त चिकित्सा सहायक हूँ। आज मैं आपकी क्या मदद कर सकता हूँ?',
    voice_desc: 'लक्षणों का वर्णन करने या साझेदार अस्पतालों में अपॉइंटमेंट बुक करने के लिए स्वाभाविक रूप से बोलें।',
    press_to_speak: 'बोलने के लिए दबाएं',
    listening: 'आपकी आवाज़ सुन रहे हैं...',
    processing: 'लक्षणों और डॉक्टरों की उपलब्धता का विश्लेषण कर रहे हैं...',
    doctor_discovery: 'डॉक्टर और विशेषज्ञ खोजें',
    book_appointment: 'अपॉइंटमेंट बुक करें',
    select_slot: 'परामर्श का समय चुनें',
    triage_desk: 'क्लिनिकल ट्राइएज डेस्क',
    pain_level: 'दर्द की गंभीरता (1 - 10)',
    body_location: 'दर्द / लक्षण का मुख्य भाग',
    emergency_warning: 'यदि आप जानलेवा आपात स्थिति का सामना कर रहे हैं, तो कृपया तुरंत आपातकालीन सेवा 112/911 पर कॉल करें।',
    care_pass: 'डिजिटल केयर पास',
    kiosk_checkin: 'कियोस्क संपर्क रहित चेक-इन',
    print_pass: 'पास प्रिंट करें',
    download_pdf: 'पीडीएफ पास डाउनलोड करें',
    apple_wallet: 'मोबाइल वॉलेट में जोड़ें',
    mic_device: 'ऑडियो इनपुट माइक्रोफ़ोन',
    volume_level: 'माइक्रोफ़ोन इनपुट स्तर',
  },
  te: {
    voice_greeting: 'నమస్కారం! నేను మీ వైద్య సహాయకుడిని. ఈ రోజు మీకు ఏ విధంగా సహాయపడగలను?',
    voice_desc: 'లక్షణాలను వివరించడానికి లేదా భాగస్వామి ఆసుపత్రులలో అపాయింట్‌మెంట్‌లను బుక్ చేయడానికి మాట్లాడండి.',
    press_to_speak: 'మాట్లాడటానికి నొక్కండి',
    listening: 'మీ స్వరాన్ని వింటున్నాము...',
    processing: 'లక్షణాలు మరియు వైద్యుల లభ్యతను విశ్లేషిస్తున్నాము...',
    doctor_discovery: 'వైద్యులు మరియు నిపుణుల అన్వేషణ',
    book_appointment: 'అపాయింట్‌మెంట్ బుక్ చేయండి',
    select_slot: 'సంప్రదింపు సమయాన్ని ఎంచుకోండి',
    triage_desk: 'క్లినికల్ ట్రయాజ్ డెస్క్',
    pain_level: 'నొప్పి తీవ్రత (1 - 10)',
    body_location: 'నొప్పి / లక్షణం ఉన్న ప్రాంతం',
    emergency_warning: 'తీవ్రమైన అత్యవసర పరిస్థితి అయితే, వెంటనే 108/911 అత్యవసర సేవలను సంప్రదించండి.',
    care_pass: 'డిజిటల్ కేర్ పాస్',
    kiosk_checkin: 'కాంటాక్ట్‌లెస్ కియోస్క్ చెక్-ఇన్',
    print_pass: 'పాస్ ప్రింట్ చేయండి',
    download_pdf: 'PDF పాస్ డౌన్‌లోడ్ చేయండి',
    apple_wallet: 'మొబైల్ వాలెట్‌కు జోడించండి',
    mic_device: 'ఆడియో ఇన్‌పుట్ మైక్రోఫోన్',
    volume_level: 'మైక్రోఫోన్ వాల్యూమ్ స్థాయి',
  },
  zh: {
    voice_greeting: '您好！我是您的全自主医疗助手。今天有什么可以为您效劳？',
    voice_desc: '自然说话以描述症状或预约合作医院的专科医生。',
    press_to_speak: '按住说话',
    listening: '正在聆听您的声音...',
    processing: '正在分析症状与医生日程...',
    doctor_discovery: '医生与专科查询',
    book_appointment: '预约门诊',
    select_slot: '选择就诊时段',
    triage_desk: '临床分诊台',
    pain_level: '疼痛等级自评 (1 - 10)',
    body_location: '主要不适 / 疼痛部位',
    emergency_warning: '如遇危及生命的急症，请立即拨打急救电话 120/911。',
    care_pass: '电子就诊凭证',
    kiosk_checkin: '自助终端无接触签到',
    print_pass: '打印凭证',
    download_pdf: '下载 PDF 就诊单',
    apple_wallet: '添加至手机钱包',
    mic_device: '音频输入麦克风',
    volume_level: '麦克风输入电平',
  },
};

interface LanguageContextType {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  t: (key: string, defaultText?: string) => string;
  currentOption: LanguageOption;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<SupportedLanguage>(() => {
    const saved = localStorage.getItem('nexus_language');
    if (saved && ['en', 'es', 'hi', 'te', 'zh'].includes(saved)) {
      return saved as SupportedLanguage;
    }
    return 'en';
  });

  useEffect(() => {
    localStorage.setItem('nexus_language', language);
  }, [language]);

  const setLanguage = (lang: SupportedLanguage) => {
    setLanguageState(lang);
  };

  const t = (key: string, defaultText?: string): string => {
    const langDict = TRANSLATIONS[language] || TRANSLATIONS.en;
    if (langDict[key]) return langDict[key];
    if (TRANSLATIONS.en[key]) return TRANSLATIONS.en[key];
    return defaultText || key;
  };

  const currentOption =
    SUPPORTED_LANGUAGES.find((opt) => opt.code === language) || SUPPORTED_LANGUAGES[0];

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, currentOption }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return ctx;
};
