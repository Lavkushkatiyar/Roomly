import { synthesizeSpeech } from "../api/text_to_voice";
import { playAudioBlob } from "./audioPlayback";

const MESSAGES = {
  "en-IN": {
    greeting:
      "<excited> Good evening! Welcome to ROOMLY. <pauses> How may I assist you today?",
    processing: "<slow> Certainly, just a moment, please. <pauses>",
    continuation: "Is there anything else I can help you with?",
  },
  "hi-IN": {
    greeting:
      "<excited> नमस्कार! ROOMLY में आपका स्वागत है। <pauses> बताइए, मैं आपकी क्या सहायता कर सकता हूँ?",
    processing: "<slow> जी, बस एक क्षण। <pauses>",
    continuation: "क्या मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?",
  },
  "hi-en": {
    greeting:
      "<excited> नमस्कार! ROOMLY में आपका स्वागत है। <pauses> बताइए, मैं आपकी क्या मदद कर सकता हूँ?",
    processing: "<slow> जी, बस एक मिनट। <pauses>",
    continuation: "क्या मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?",
  },
  "ta-IN": {
    greeting:
      "<excited> வணக்கம்! ROOMLY-க்கு உங்களை வரவேற்கிறோம். <pauses> இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?",
    processing: "<slow> நிச்சயமாக, ஒரு கணம். <pauses>",
    continuation: "வேறு ஏதாவது உதவி தேவையா?",
  },
  "te-IN": {
    greeting:
      "<excited> నమస్కారం! ROOMLYకి స్వాగతం. <pauses> ఈరోజు నేను మీకు ఎలా సహాయం చేయగలను?",
    processing: "<slow> తప్పకుండా, ఒక్క క్షణం. <pauses>",
    continuation: "మీకు ఇంకా ఏదైనా సహాయం కావాలా?",
  },
  "kn-IN": {
    greeting:
      "<excited> ನಮಸ್ಕಾರ! ROOMLY ಗೆ ಸ್ವಾಗತ. <pauses> ನಿಮಗೆ ಇಂದು ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
    processing: "<slow> ಖಂಡಿತ, ಒಂದು ಕ್ಷಣ. <pauses>",
    continuation: "ನಾನು ನಿಮಗೆ ಇನ್ನೇನಾದರೂ ಸಹಾಯ ಮಾಡಬಹುದೇ?",
  },
  "ml-IN": {
    greeting:
      "<excited> നമസ്കാരം! ROOMLY-ലേക്ക് സ്വാഗതം. <pauses> ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?",
    processing: "<slow> തീർച്ചയായും, ഒരു നിമിഷം. <pauses>",
    continuation: "മറ്റെന്തെങ്കിലും സഹായം ആവശ്യമുണ്ടോ?",
  },
  "mr-IN": {
    greeting:
      "<excited> नमस्कार! ROOMLY मध्ये आपले स्वागत आहे. <pauses> आज मी आपली कशी मदत करू शकतो?",
    processing: "<slow> नक्कीच, एक क्षण थांबा. <pauses>",
    continuation: "मी आणखी काही मदत करू शकतो का?",
  },
  "bn-IN": {
    greeting:
      "<excited> নমস্কার! ROOMLY-তে আপনাকে স্বাগত। <pauses> আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
    processing: "<slow> অবশ্যই, এক মুহূর্ত। <pauses>",
    continuation: "আপনার কি আর কোনো সাহায্য দরকার?",
  },
  "gu-IN": {
    greeting:
      "<excited> નમસ્તે! ROOMLYમાં આપનું સ્વાગત છે. <pauses> આજે હું આપની કેવી રીતે મદદ કરી શકું?",
    processing: "<slow> ચોક્કસ, એક ક્ષણ. <pauses>",
    continuation: "શું હું આપની બીજી કોઈ રીતે મદદ કરી શકું?",
  },
  "pa-IN": {
    greeting:
      "<excited> ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ROOMLY ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ। <pauses> ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
    processing: "<slow> ਜ਼ਰੂਰ, ਇੱਕ ਪਲ ਜੀ। <pauses>",
    continuation: "ਕੀ ਮੈਂ ਤੁਹਾਡੀ ਹੋਰ ਕਿਸੇ ਚੀਜ਼ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
  },
};

export function getNaturalMessage(language, messageType) {
  const message = MESSAGES[language]?.[messageType];
  if (!message) {
    throw new Error(
      `No ${messageType} speech is configured for language ${language}.`,
    );
  }
  return message;
}

export async function playNaturalMessage(language, messageType, { signal } = {}) {
  const text = getNaturalMessage(language, messageType);
  const audioBlob = await synthesizeSpeech({ text, language, signal });
  if (signal?.aborted) {
    return;
  }
  await playAudioBlob(audioBlob, { signal });
}
