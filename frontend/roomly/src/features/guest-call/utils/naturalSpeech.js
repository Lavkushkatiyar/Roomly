import { synthesizeSpeech } from "../api/text_to_voice";
import { playAudioBlob } from "./audioPlayback";



const MESSAGES = {
  "en-IN": {
    greeting: [
      "Hey! I'm Abhinash from ROOMLY. Tell me, how can I help you today?",
      "Hello! Abhinash here from ROOMLY. What can I do for you?",
      "Hi there! You're speaking with Abhinash from ROOMLY. How may I assist you?"
    ],
    processing: [
      "Sure, just a moment. Let me check that for you. <pauses>",
      "Of course! Give me a second to look into that. <pauses>",
      "Alright, let me check that for you. <pauses>",
      "One moment, please. I'll find that out for you. <pauses>"
    ]
  },

  "hi-IN": {
    greeting: [
      "नमस्कार! मैं अभिनाश, ROOMLY से बोल रहा हूँ। बताइए, मैं आपकी क्या मदद कर सकता हूँ?",
      "नमस्ते! ROOMLY से अभिनाश बोल रहा हूँ। बताइए, आपको क्या चाहिए?",
      "जी नमस्कार! मैं अभिनाश हूँ, ROOMLY से। बताइए, आपकी क्या सेवा कर सकता हूँ?"
    ],
    processing: [
      "जी, एक क्षण रुकिए। मैं आपके लिए चेक करता हूँ। <pauses>",
      "बिल्कुल, बस एक मिनट। मैं अभी देखता हूँ। <pauses>",
      "जी, ज़रा रुकिए। मैं पता करता हूँ। <pauses>",
      "ठीक है, मुझे एक पल दीजिए। मैं चेक करके बताता हूँ। <pauses>"
    ]
  },

  "hi-en": {
    greeting: [
      "Hey! Main Abhinash bol raha hoon, ROOMLY se. Bataiye, kya hua?",
      "Hello ji! Abhinash here from ROOMLY. Bataiye, kaise help kar sakta hoon?",
      "Ji, main Abhinash hoon ROOMLY se. Bataiye, aapko kya chahiye?"
    ],
    processing: [
      "Sure ji, ek second. Main aapke liye check karta hoon. <pauses>",
      "Bilkul, bas ek moment. Main dekh leta hoon. <pauses>",
      "Okay ji, ek minute dijiye. Main check karke batata hoon. <pauses>",
      "Ji, main abhi check karta hoon. Bas ek second. <pauses>"
    ]
  },

  "ta-IN": {
    greeting: [
      "வணக்கம்! நான் அபினாஷ், ROOMLY-லிருந்து பேசுகிறேன். சொல்லுங்கள், எப்படி உதவலாம்?",
      "ஹலோ! ROOMLY சார்பாக அபினாஷ் பேசுகிறேன். உங்களுக்கு என்ன உதவி வேண்டும்?",
      "வணக்கம்! நான் அபினாஷ். இன்று உங்களுக்கு என்ன உதவி செய்யலாம்?"
    ],
    processing: [
      "சரி, ஒரு நிமிடம். உங்களுக்காக நான் சரிபார்க்கிறேன். <pauses>",
      "நிச்சயமாக, ஒரு கணம் காத்திருக்கவும். நான் பார்த்துச் சொல்கிறேன். <pauses>",
      "சரி, இதை நான் சரிபார்த்துச் சொல்கிறேன். <pauses>",
      "ஒரு நிமிடம் கொடுங்கள். நான் இதைப் பார்த்துக்கொள்கிறேன். <pauses>"
    ]
  },

  "te-IN": {
    greeting: [
      "నమస్కారం! నేను అభినాష్, ROOMLY నుంచి మాట్లాడుతున్నాను. చెప్పండి, మీకు ఎలా సహాయం చేయగలను?",
      "హలో! ROOMLY నుంచి అభినాష్ మాట్లాడుతున్నాను. మీకు ఏం సహాయం కావాలి?",
      "నమస్కారం! నేను అభినాష్. ఈరోజు మీకు ఏ విధంగా సహాయం చేయగలను?"
    ],
    processing: [
      "సరే, ఒక్క క్షణం. మీ కోసం నేను చెక్ చేస్తాను. <pauses>",
      "తప్పకుండా, ఒక నిమిషం ఆగండి. నేను చూసి చెప్తాను. <pauses>",
      "అలాగే, మీ అభ్యర్థనను ఒకసారి పరిశీలిస్తాను. <pauses>",
      "ఒక్క క్షణం ఇవ్వండి. నేను వివరాలు తెలుసుకుంటాను. <pauses>"
    ]
  },

  "kn-IN": {
    greeting: [
      "ನಮಸ್ಕಾರ! ನಾನು ಅಭಿನಾಶ್, ROOMLY ನಿಂದ ಮಾತನಾಡುತ್ತಿದ್ದೇನೆ. ಹೇಳಿ, ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
      "ಹಲೋ! ROOMLY ವತಿಯಿಂದ ಅಭಿನಾಶ್ ಮಾತನಾಡುತ್ತಿದ್ದೇನೆ. ನಿಮಗೆ ಏನು ಸಹಾಯ ಬೇಕು?",
      "ನಮಸ್ಕಾರ! ನಾನು ಅಭಿನಾಶ್. ಇಂದು ನಿಮಗೆ ಏನು ಸಹಾಯ ಮಾಡಬಹುದು?"
    ],
    processing: [
      "ಸರಿ, ಒಂದು ಕ್ಷಣ. ನಿಮಗಾಗಿ ನಾನು ಪರಿಶೀಲಿಸುತ್ತೇನೆ. <pauses>",
      "ಖಂಡಿತ, ಒಂದು ನಿಮಿಷ ಕಾಯಿರಿ. ನಾನು ಪರಿಶೀಲಿಸಿ ಹೇಳುತ್ತೇನೆ. <pauses>",
      "ಆಯಿತು, ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಪರಿಶೀಲಿಸುತ್ತೇನೆ. <pauses>",
      "ಒಂದು ಕ್ಷಣ ಕೊಡಿ. ನಾನು ವಿವರಗಳನ್ನು ನೋಡುತ್ತೇನೆ. <pauses>"
    ]
  },

  "ml-IN": {
    greeting: [
      "നമസ്കാരം! ഞാൻ അഭിനാഷ്, ROOMLY-യിൽ നിന്നാണ് സംസാരിക്കുന്നത്. പറയൂ, എങ്ങനെ സഹായിക്കാം?",
      "ഹലോ! ROOMLY-യിൽ നിന്ന് അഭിനാഷ് സംസാരിക്കുന്നു. എന്ത് സഹായമാണ് വേണ്ടത്?",
      "നമസ്കാരം! ഞാൻ അഭിനാഷ്. ഇന്ന് എന്ത് സഹായമാണ് വേണ്ടത്?"
    ],
    processing: [
      "ശരി, ഒരു നിമിഷം. ഞാൻ നിങ്ങൾക്കായി പരിശോധിക്കാം. <pauses>",
      "തീർച്ചയായും, ഒരു മിനിറ്റ് കാത്തിരിക്കൂ. ഞാൻ നോക്കാം. <pauses>",
      "ശരി, ഞാൻ ഇത് പരിശോധിച്ചിട്ട് പറയാം. <pauses>",
      "ഒരു നിമിഷം തരൂ. ഞാൻ വിവരങ്ങൾ പരിശോധിക്കാം. <pauses>"
    ]
  },

  "mr-IN": {
    greeting: [
      "नमस्कार! मी अभिनाश, ROOMLY कडून बोलत आहे. सांगा, मी आपली कशी मदत करू शकतो?",
      "हॅलो! ROOMLY मधून अभिनाश बोलत आहे. आपल्याला काय मदत हवी आहे?",
      "नमस्कार! मी अभिनाश आहे. आज आपल्यासाठी काय करू शकतो?"
    ],
    processing: [
      "नक्कीच, एक क्षण थांबा. मी तुमच्यासाठी तपासतो. <pauses>",
      "हो, एक मिनिट द्या. मी पाहून सांगतो. <pauses>",
      "ठीक आहे, मी हे तपासून घेतो. <pauses>",
      "एक क्षण द्या, मी माहिती तपासतो. <pauses>"
    ]
  },

  "bn-IN": {
    greeting: [
      "নমস্কার! আমি অভিনাশ, ROOMLY থেকে বলছি। বলুন, কীভাবে আপনাকে সাহায্য করতে পারি?",
      "হ্যালো! ROOMLY থেকে অভিনাশ বলছি। আপনার কী সাহায্য দরকার?",
      "নমস্কার! আমি অভিনাশ। আজ আপনাকে কীভাবে সাহায্য করতে পারি?"
    ],
    processing: [
      "অবশ্যই, এক মুহূর্ত অপেক্ষা করুন। আমি আপনার জন্য দেখে নিচ্ছি। <pauses>",
      "ঠিক আছে, একটু সময় দিন। আমি দেখে বলছি। <pauses>",
      "একটু অপেক্ষা করুন, আমি বিষয়টি যাচাই করছি। <pauses>",
      "নিশ্চয়ই, আমি আপনার জন্য বিষয়টি দেখে নিচ্ছি। <pauses>"
    ]
  },

  "gu-IN": {
    greeting: [
      "નમસ્તે! હું અભિનાશ, ROOMLY તરફથી બોલું છું. કહો, હું તમારી કેવી રીતે મદદ કરી શકું?",
      "હેલો! ROOMLY તરફથી અભિનાશ બોલું છું. તમને શેની મદદ જોઈએ છે?",
      "નમસ્તે! હું અભિનાશ છું. આજે તમારા માટે શું કરી શકું?"
    ],
    processing: [
      "ચોક્કસ, એક ક્ષણ રાહ જુઓ. હું તમારા માટે તપાસું છું. <pauses>",
      "બરાબર, મને એક મિનિટ આપો. હું જોઈને કહું છું. <pauses>",
      "હું હમણાં તમારી વિનંતી તપાસું છું. <pauses>",
      "એક ક્ષણ આપશો? હું વિગતો તપાસી લઉં. <pauses>"
    ]
  },

  "pa-IN": {
    greeting: [
      "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਅਭਿਨਾਸ਼, ROOMLY ਤੋਂ ਬੋਲ ਰਿਹਾ ਹਾਂ। ਦੱਸੋ ਜੀ, ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
      "ਹੈਲੋ ਜੀ! ROOMLY ਵੱਲੋਂ ਅਭਿਨਾਸ਼ ਬੋਲ ਰਿਹਾ ਹਾਂ। ਤੁਹਾਨੂੰ ਕੀ ਮਦਦ ਚਾਹੀਦੀ ਹੈ?",
      "ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਜੀ! ਮੈਂ ਅਭਿਨਾਸ਼ ਹਾਂ। ਦੱਸੋ, ਤੁਹਾਡੇ ਲਈ ਕੀ ਕਰ ਸਕਦਾ ਹਾਂ?"
    ],
    processing: [
      "ਜ਼ਰੂਰ ਜੀ, ਇੱਕ ਪਲ ਰੁਕੋ। ਮੈਂ ਤੁਹਾਡੇ ਲਈ ਚੈੱਕ ਕਰਦਾ ਹਾਂ। <pauses>",
      "ਬਿਲਕੁਲ ਜੀ, ਇੱਕ ਮਿੰਟ ਦਿਓ। ਮੈਂ ਦੇਖ ਕੇ ਦੱਸਦਾ ਹਾਂ। <pauses>",
      "ਠੀਕ ਹੈ ਜੀ, ਮੈਂ ਹੁਣੇ ਚੈੱਕ ਕਰਦਾ ਹਾਂ। <pauses>",
      "ਇੱਕ ਪਲ ਜੀ, ਮੈਂ ਇਸ ਬਾਰੇ ਪਤਾ ਕਰਦਾ ਹਾਂ। <pauses>"
    ]
  }
};

export function getNaturalMessage(language, messageType) {
  const messages = MESSAGES[language]?.[messageType];
  if (!messages || (Array.isArray(messages) && messages.length === 0)) {
    throw new Error(
      `No ${messageType} speech is configured for language ${language}.`,
    );
  }

  if (!Array.isArray(messages)) {
    return messages;
  }

  const index = Math.floor(Math.random() * messages.length);
  return messages[index];
}

export async function playNaturalMessage(language, messageType, { signal } = {}) {
  const text = getNaturalMessage(language, messageType);
  const audioBlob = await synthesizeSpeech({ text, language, signal });
  if (signal?.aborted) {
    return;
  }
  await playAudioBlob(audioBlob, { signal });
}
