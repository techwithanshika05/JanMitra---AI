import { createContext, useState, useEffect, useContext } from 'react'

export const LanguageContext = createContext()

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}

const TRANSLATIONS = {
  hi: {
    hero_badge: 'AI-संचालित · उत्तर प्रदेश',
    hero_title: 'सरकारी योजनाएं\nजटिल नहीं होनी चाहिए।',
    hero_sub: 'JanMitra AI नागरिकों को कल्याण योजनाओं, दस्तावेजों, पात्रता और सरकारी सेवाओं को बिना जटिल कागजी कार्रवाई के समझने में मदद करता है।',
    ask_ai: 'JanMitra AI से पूछें',
    find_schemes: 'मेरी योजनाएं खोजें',
    stat1: 'लाभार्थी',
    stat2: 'कल्याण योजनाएं',
    stat3: 'AI सहायता',
    stat4: 'उत्तर प्रदेश',
    feat_schemes: 'योजनाएं खोजें',
    feat_schemes_desc: 'अपनी आयु, व्यवसाय और श्रेणी के आधार पर सरकारी योजनाएं खोजें।',
    feat_checklist: 'दस्तावेज',
    feat_checklist_desc: 'कार्यालय जाने से पहले जानें कि आपको किन दस्तावेजों की आवश्यकता है।',
    feat_grievance: 'शिकायत दर्ज करें',
    feat_grievance_desc: 'शिकायत प्रक्रियाओं को समझें और औपचारिक शिकायत तैयार करें।',
    feat_life: 'जीवन घटनाएं',
    feat_life_desc: 'शादी, बच्चे के जन्म या 60 वर्ष की आयु के बाद प्रासंगिक सहायता खोजें।',
    chat_title: 'पूछें।\nसमझें।\nकार्यवाही करें।',
    chat_sub: 'उत्तर प्रदेश में कल्याण योजनाओं, राशन कार्ड, दस्तावेजों और सरकारी सेवाओं के लिए सरल मार्गदर्शन।',
    chat_welcome: 'नमस्ते! मैं JanMitra AI हूं, उत्तर प्रदेश के लिए आपका कल्याण सहायक। मुझे बताएं कि आप क्या करना चाहते हैं और मैं आपको अगले कदम समझने में मदद करूंगा।',
    chat_welcome2: 'आज मैं आपकी क्या मदद कर सकता हूं?',
    ai_disclaimer_short: 'AI मार्गदर्शन केवल सूचनात्मक है। आधिकारिक स्रोतों से महत्वपूर्ण जानकारी सत्यापित करें।',
    checklist_title: 'अपने दस्तावेज\nजाने से पहले तैयार करें।',
    checklist_sub: 'वह सरकारी सेवा चुनें जिसके लिए आप आवेदन कर रहे हैं। JanMitra AI आपके लिए एक स्पष्ट दस्तावेज चेकलिस्ट तैयार करेगा।',
    select_service: 'सरकारी सेवा',
    choose_service: 'अपनी सेवा चुनें',
    cl_empty_title: 'आपकी चेकलिस्ट यहां दिखाई देगी।',
    cl_empty_sub: 'शुरू करने के लिए बाएं पैनल से एक सरकारी सेवा चुनें।',
    schemes_title: 'सरकारी योजनाएं\nअपनी प्रोफ़ाइल के लिए बनाई गई।',
    schemes_sub: 'हमें कुछ बुनियादी विवरण बताएं और JanMitra AI आपकी प्रोफ़ाइल को प्रासंगिक कल्याण योजनाओं, लाभों और आवश्यक दस्तावेजों से मिलाएगा।',
    your_profile: 'अपने बारे में बताएं',
    age: 'आपकी आयु',
    occupation: 'आप क्या करते हैं?',
    farmer: 'किसान',
    labour: 'दिहाड़ी मजदूर',
    student: 'छात्र',
    unemployed: 'बेरोजगार / गृहणी',
    other: 'अन्य / नौकरीपेशा',
    category: 'सामाजिक श्रेणी',
    annual_income: 'वार्षिक पारिवारिक आय',
    find_my_schemes: 'मेरी योजनाएं खोजें',
    schemes_empty_title: 'आपके मैच यहां दिखाई देंगे',
    schemes_empty_sub: 'अपनी प्रोफ़ाइल पूरी करें और हम उपलब्ध कल्याण योजनाओं को उपयुक्त मैचों के लिए खोजेंगे।',
    grievance_title: 'पता नहीं\nअपनी शिकायत कहां दर्ज करें?',
    grievance_sub: 'अपनी समस्या चुनें, आधिकारिक उन्नयन पथ का पालन करें, और प्रक्रिया में खोए बिना एक औपचारिक शिकायत तैयार करें।',
    select_issue: 'क्या गलत हुआ?',
    complaint_sub: 'आवश्यक विवरण प्रदान करें और JanMitra AI संबंधित प्राधिकारी के लिए एक संरचित शिकायत मसौदा तैयार करेगा।',
    life_events_title: 'जीवन बदलता है।\nहम अगले कदम सरल बनाते हैं।',
    life_events_sub: 'अपना मील का पत्थर चुनें और JanMitra AI आपके लिए प्रासंगिक सरकारी योजनाओं, पात्रता मार्गदर्शन और आवश्यक दस्तावेजों को व्यवस्थित करेगा।',
    feedback_title: 'हमें बताएं कि\nवास्तव में क्या काम किया।',
    feedback_sub: 'एक रेटिंग JanMitra AI को अगले नागरिक के लिए स्पष्ट, तेज और अधिक उपयोगी बनाने में मदद कर सकती है।',
    helplines: 'महत्वपूर्ण हेल्पलाइन',
    disclaimer_title: 'AI के साथ मार्गदर्शन।\nआपके साथ निर्णय।',
    disclaimer_sub: 'JanMitra AI क्या करता है, इसकी सीमाएं कहां हैं, और AI-संचालित कल्याण मार्गदर्शन का उपयोग करने से पहले आपकी जानकारी कैसे संभाली जाती है, इसे समझें।',
  },
  hinglish: {
    hero_badge: 'AI-Powered · Uttar Pradesh',
    hero_title: 'Sarkari Yojnayen\nComplex nahi honi chahiye.',
    hero_sub: 'JanMitra AI citizens ko welfare schemes, documents, eligibility aur government services samajhne mein help karta hai — bina confusing paperwork ke.',
    ask_ai: 'JanMitra AI se Poocho',
    find_schemes: 'Meri Yojnayen Dhundho',
    stat1: 'Labharti',
    stat2: 'Welfare Schemes',
    stat3: 'AI Sahayta',
    stat4: 'Uttar Pradesh',
    feat_schemes: 'Yojnayen Dhundho',
    feat_schemes_desc: 'Apni umar, pesha aur category ke hisaab se government schemes dhundho.',
    feat_checklist: 'Documents',
    feat_checklist_desc: 'Office jaane se pehle jaano ki kaunse documents chahiye.',
    feat_grievance: 'Shikayat Darj Karo',
    feat_grievance_desc: 'Shikayat processes samjho aur formal complaint tayar karo.',
    feat_life: 'Life Events',
    feat_life_desc: 'Shaadi, bacche ya 60 saal ke baad relevant support dhundho.',
    chat_title: 'Poochho.\nSamjho.\nAction Lo.',
    chat_sub: 'UP mein welfare schemes, ration card, documents aur government services ke liye simple guidance.',
    chat_welcome: 'Namaste! Main JanMitra AI hoon, UP ka aapka welfare assistant. Mujhe batao aap kya karna chahte ho aur main agle steps samjhaunga.',
    chat_welcome2: 'Aaj main aapki kya help kar sakta hoon?',
    ai_disclaimer_short: 'AI guidance sirf informative hai. Official sources se important info verify karo.',
    checklist_title: 'Apne documents\njaane se pehle tayar karo.',
    checklist_sub: 'Woh government service choose karo jiske liye apply kar rahe ho. JanMitra AI tumhare liye document checklist tayar karega.',
    select_service: 'Government Service',
    choose_service: 'Apni Service Chuno',
    cl_empty_title: 'Tumhari checklist yahan dikhegi.',
    cl_empty_sub: 'Shuru karne ke liye left panel se government service chuno.',
    schemes_title: 'Government Schemes\nTumhari profile ke liye.',
    schemes_sub: 'Kuch basic details batao aur JanMitra AI tumhari profile ko relevant welfare schemes, benefits aur documents se match karega.',
    your_profile: 'Apne baare mein batao',
    age: 'Tumhari Umar',
    occupation: 'Tum kya karte ho?',
    farmer: 'Kisan',
    labour: 'Daily Wage Labour',
    student: 'Student',
    unemployed: 'Unemployed / Homemaker',
    other: 'Other / Salaried',
    category: 'Social Category',
    annual_income: 'Annual Family Income',
    find_my_schemes: 'Meri Yojnayen Dhundho',
    schemes_empty_title: 'Tumhare matches yahan dikhenge',
    schemes_empty_sub: 'Apni profile complete karo aur hum available welfare schemes mein suitable matches dhundhenge.',
    grievance_title: 'Pata nahi\napni shikayat kahan darj karein?',
    grievance_sub: 'Apni problem chuno, official escalation path follow karo, aur formal complaint tayar karo — process mein khoye bina.',
    select_issue: 'Kya galat hua?',
    complaint_sub: 'Zaroori details do aur JanMitra AI concerned authority ke liye structured complaint draft tayar karega.',
    life_events_title: 'Life badalti hai.\nHum agle steps simple banate hain.',
    life_events_sub: 'Apna milestone chuno aur JanMitra AI tumhare liye relevant government schemes, eligibility guidance aur documents organize karega.',
    feedback_title: 'Hamein batao\nasli mein kya kaam kiya.',
    feedback_sub: 'Ek rating JanMitra AI ko agle citizen ke liye clear, fast aur useful banane mein help kar sakti hai.',
    helplines: 'Important Helplines',
    disclaimer_title: 'AI ke saath Guidance.\nTumhare saath Decisions.',
    disclaimer_sub: 'JanMitra AI kya karta hai, iski limits kahan hain, aur AI-powered welfare guidance use karne se pehle tumhari info kaise handle hoti hai — yeh samjho.',
  },
  en: {}
}

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState('en')

  useEffect(() => {
    const saved = localStorage.getItem('janmitra_lang') || 'en'
    setLanguage(saved)
    applyTranslations(saved)
  }, [])

  const applyTranslations = (lang) => {
    const translations = TRANSLATIONS[lang] || {}
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n')
      if (translations[key]) {
        el.textContent = translations[key]
      }
    })
  }

  const changeLanguage = (lang) => {
    setLanguage(lang)
    localStorage.setItem('janmitra_lang', lang)
    applyTranslations(lang)
  }

  const t = (key) => {
    const translations = TRANSLATIONS[language] || {}
    return translations[key] || key
  }

  return (
    <LanguageContext.Provider value={{ language, changeLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}