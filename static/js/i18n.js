const languageOptions = [
  { code: "en", name: "English" },
  { code: "hi", name: "हिन्दी" },
  { code: "mr", name: "मराठी" },
  { code: "bn", name: "বাংলা" },
  { code: "ta", name: "தமிழ்" },
  { code: "te", name: "తెలుగు" },
  { code: "gu", name: "ગુજરાતી" },
  { code: "kn", name: "ಕನ್ನಡ" },
  { code: "ml", name: "മലയാളം" },
  { code: "pa", name: "ਪੰਜਾਬੀ" },
  { code: "ur", name: "اردو" },
];

const translations = {
  en: {
    officialEyebrow: "Official-source civic guidance",
    chooseLanguage: "Choose your language",
    continue: "Continue",
    languageChangeNote: "You can change this later from the header or profile page.",
    welcome: "Welcome to GovGuideAI",
    greeting: "Welcome to GovGuideAI. How can I help you today?",
    login: "Login",
    signup: "Sign up",
    createAccount: "Create Account",
    logout: "Logout",
    email: "Email",
    password: "Password",
    newHere: "New here?",
    alreadyAccount: "Already have an account?",
    profileSetup: "Profile Setup",
    createProfile: "Create Your Profile",
    editProfile: "Edit Profile",
    viewEditProfile: "View and Edit Profile",
    saveProfile: "Save Profile",
    saveChanges: "Save Changes",
    deleteProfile: "Delete Profile",
    deleteAccount: "Delete Account",
    fullName: "Full name *",
    ageDob: "Age or date of birth *",
    stateUt: "State or Union Territory *",
    district: "District *",
    occupation: "Occupation *",
    occupationOther: "Custom occupation",
    locationType: "Rural or urban *",
    preferredLanguage: "Preferred language *",
    gender: "Gender",
    annualIncome: "Annual household income range",
    disabilityStatus: "Disability status",
    maritalStatus: "Marital status",
    socialCategory: "Social category, only if relevant",
    select: "Select",
    rural: "Rural",
    urban: "Urban",
    student: "Student",
    farmer: "Farmer",
    employed: "Employed",
    selfEmployed: "Self-employed",
    businessOwner: "Business owner",
    unemployed: "Unemployed / None",
    retired: "Retired",
    homemaker: "Homemaker",
    other: "Other",
    backToChat: "Back to Chat",
    yourProfile: "Your Profile",
    edit: "Edit",
    name: "Name",
    age: "Age",
    state: "State/UT",
    location: "Location",
    language: "Language",
    officialSources: "Official sources only",
    trustCopy: "GovGuideAI uses your saved profile only to personalize government-service and scheme guidance.",
    disclaimer: "GovGuideAI provides guidance based on official sources. Final eligibility and approval are decided by the relevant government authority.",
    suggestedPrompts: "Example questions",
    passportPrompt: "Passport documents",
    schemePrompt: "Schemes for me",
    farmerPrompt: "Farmer schemes",
    grievancePrompt: "CPGRAMS help",
    wordCountPrompt: "Word count",
    askEyebrow: "Ask about Indian government services",
    chatTitle: "GovGuideAI Chat",
    clearConversation: "Clear conversation",
    message: "Message",
    messagePlaceholder: "Ask about a scheme, document, service, or official portal",
    send: "Send",
    microphone: "Microphone",
    startRecording: "Start recording",
    stopRecording: "Stop recording",
    cancel: "Cancel",
    replay: "Replay",
    mute: "Mute voice responses",
    unmute: "Unmute voice responses",
    stopSpeaking: "Stop speaking",
    listening: "Listening…",
    transcribing: "Transcribing…",
    thinking: "Thinking...",
    speaking: "Speaking...",
    idleVoice: "Voice ready",
    privacyNotice: "Audio is sent securely for transcription and is not intentionally stored by GovGuideAI.",
    micDenied: "Microphone permission denied. You can still use text chat.",
    emptyAudio: "The recording was empty. Please try again.",
    unsupportedAudio: "Unsupported audio format. Please use browser-recorded audio.",
    speechFailed: "Speech playback failed. The text answer is still available.",
    typing: "GovGuideAI is checking this for you...",
    memoryCleared: "Conversation memory is cleared. Please ask your next question.",
    profilePrivacy: "Profile information is used only for personalized government-service and scheme guidance, not advertising or unrelated analytics.",
    profileSetupCopy: "This helps GovGuideAI suggest schemes and services without asking you to repeat basic details. Do not enter Aadhaar, PAN, bank details, OTPs, or exact home address.",
    profilePrivacyDetailsTitle: "How profile information is handled",
    profilePrivacyDetails: "Your profile is stored for personalized recommendations, may be accessed only by authorized administration, and is not used for advertising. You can edit or delete your profile or account. Do not enter Aadhaar numbers, bank details, passwords, OTPs, or other highly sensitive information.",
    signupPrivacy: "Your profile is used only to personalize government-service and scheme guidance. Do not enter Aadhaar, PAN, bank details, OTPs, or exact home address.",
    loginCopy: "Log in to use your saved profile for personalized government-service and scheme suggestions.",
    profileSaved: "Profile saved.",
    deleteProfileConfirm: "Delete your saved profile? You will need to complete setup again before chatting.",
    deleteAccountConfirm: "Delete your account and profile? This cannot be undone.",
    languageSettings: "Language settings",
    officialSourcesBadge: "Official sources",
    emptyStateProfileNote: "Answers use your saved profile when it helps personalize scheme and service guidance.",
    sending: "Sending...",
    checkingSources: "Checking official sources...",
    preparingResponse: "Preparing response...",
    sourceSection: "Sources",
    officialSource: "Official source",
    openOfficialPortal: "Open official portal",
    lastVerified: "Last verified",
    toolUsed: "Tools used",
    readAnswerAloud: "Read answer aloud",
    stopReadingAloud: "Stop reading aloud",
    preparingAudio: "Preparing audio…",
    transcriptionFailed: "Transcription failed. Please try again or use text chat.",
    recordingUnsupported: "Voice recording is not supported in this browser. You can still use text chat.",
    recordingFailed: "The microphone could not start. Please try again or use text chat.",
    scholarshipPrompt: "Scholarships for me",
    studentSchemesPrompt: "Student schemes",
    educationSupportPrompt: "Education support",
    agricultureSupportPrompt: "Agriculture support",
    cropInsurancePrompt: "Crop insurance help",
    employeeBenefitsPrompt: "Employee benefits",
    housingSupportPrompt: "Housing support",
    skillDevelopmentPrompt: "Skill development",
    selfEmploymentPrompt: "Self-employment schemes",
    businessCreditPrompt: "Business credit support",
    msmeSupportPrompt: "MSME support",
    businessSchemesPrompt: "Business schemes",
    employmentSchemesPrompt: "Employment schemes",
    jobSeekerSupportPrompt: "Job seeker support",
    seniorCitizenSchemesPrompt: "Senior citizen schemes",
    pensionSupportPrompt: "Pension support",
    healthcareSupportPrompt: "Healthcare support",
    familySupportPrompt: "Family support",
    womenSchemesPrompt: "Women-focused schemes",
    profileBenefitsPrompt: "Benefits for my profile",
    occupationSupportPrompt: "Occupation support",
    searchingWeb: "Searching the web...",
  },
  hi: {
    officialEyebrow: "आधिकारिक स्रोतों से नागरिक मार्गदर्शन",
    chooseLanguage: "अपनी भाषा चुनें",
    continue: "जारी रखें",
    languageChangeNote: "आप इसे बाद में हेडर या प्रोफ़ाइल पेज से बदल सकते हैं।",
    welcome: "GovGuideAI में आपका स्वागत है",
    greeting: "GovGuideAI में आपका स्वागत है। आज मैं आपकी कैसे सहायता कर सकता हूँ?",
    login: "लॉग इन",
    signup: "साइन अप",
    createAccount: "खाता बनाएं",
    logout: "लॉग आउट",
    email: "ईमेल",
    password: "पासवर्ड",
    newHere: "नए हैं?",
    alreadyAccount: "पहले से खाता है?",
    profileSetup: "प्रोफ़ाइल सेटअप",
    createProfile: "अपनी प्रोफ़ाइल बनाएं",
    editProfile: "प्रोफ़ाइल संपादित करें",
    viewEditProfile: "प्रोफ़ाइल देखें और संपादित करें",
    saveProfile: "प्रोफ़ाइल सेव करें",
    saveChanges: "बदलाव सेव करें",
    deleteProfile: "प्रोफ़ाइल हटाएं",
    deleteAccount: "खाता हटाएं",
    fullName: "पूरा नाम *",
    ageDob: "उम्र या जन्म तिथि *",
    stateUt: "राज्य या केंद्र शासित प्रदेश *",
    district: "ज़िला *",
    occupation: "व्यवसाय *",
    occupationOther: "अपना व्यवसाय लिखें",
    locationType: "ग्रामीण या शहरी *",
    preferredLanguage: "पसंदीदा भाषा *",
    gender: "लिंग",
    annualIncome: "वार्षिक घरेलू आय सीमा",
    disabilityStatus: "दिव्यांगता स्थिति",
    maritalStatus: "वैवाहिक स्थिति",
    socialCategory: "सामाजिक श्रेणी, यदि ज़रूरी हो",
    select: "चुनें",
    rural: "ग्रामीण",
    urban: "शहरी",
    student: "विद्यार्थी",
    farmer: "किसान",
    employed: "नौकरीपेशा",
    selfEmployed: "स्वरोज़गार",
    businessOwner: "व्यवसाय मालिक",
    unemployed: "बेरोज़गार / नहीं",
    retired: "सेवानिवृत्त",
    homemaker: "गृहिणी/गृहस्थ",
    other: "अन्य",
    backToChat: "चैट पर वापस",
    yourProfile: "आपकी प्रोफ़ाइल",
    edit: "संपादित करें",
    name: "नाम",
    age: "उम्र",
    state: "राज्य/केंद्र शासित प्रदेश",
    location: "स्थान",
    language: "भाषा",
    officialSources: "केवल आधिकारिक स्रोत",
    trustCopy: "GovGuideAI आपकी सेव की गई प्रोफ़ाइल का उपयोग केवल सरकारी सेवाओं और योजनाओं के सुझावों के लिए करता है।",
    disclaimer: "GovGuideAI आधिकारिक स्रोतों के आधार पर मार्गदर्शन देता है। अंतिम पात्रता और मंज़ूरी संबंधित सरकारी प्राधिकरण तय करता है।",
    suggestedPrompts: "उदाहरण प्रश्न",
    passportPrompt: "पासपोर्ट दस्तावेज़",
    schemePrompt: "मेरे लिए योजनाएँ",
    farmerPrompt: "किसान योजनाएँ",
    grievancePrompt: "CPGRAMS सहायता",
    wordCountPrompt: "शब्द गणना",
    askEyebrow: "भारतीय सरकारी सेवाओं के बारे में पूछें",
    chatTitle: "GovGuideAI चैट",
    clearConversation: "बातचीत साफ़ करें",
    message: "संदेश",
    messagePlaceholder: "किसी योजना, दस्तावेज़, सेवा या आधिकारिक पोर्टल के बारे में पूछें",
    send: "भेजें",
    microphone: "माइक्रोफ़ोन",
    startRecording: "रिकॉर्डिंग शुरू करें",
    stopRecording: "रिकॉर्डिंग रोकें",
    cancel: "रद्द करें",
    replay: "फिर चलाएँ",
    mute: "आवाज़ बंद करें",
    unmute: "आवाज़ चालू करें",
    stopSpeaking: "बोलना रोकें",
    listening: "सुन रहा है...",
    transcribing: "लिखा जा रहा है...",
    thinking: "सोच रहा है...",
    speaking: "बोल रहा है...",
    idleVoice: "वॉइस तैयार है",
    privacyNotice: "ऑडियो ट्रांसक्रिप्शन के लिए सुरक्षित रूप से भेजा जाता है और GovGuideAI इसे जानबूझकर संग्रहीत नहीं करता।",
    micDenied: "माइक्रोफ़ोन अनुमति नहीं मिली। आप टेक्स्ट चैट का उपयोग कर सकते हैं।",
    emptyAudio: "रिकॉर्डिंग खाली थी। फिर कोशिश करें।",
    unsupportedAudio: "ऑडियो फ़ॉर्मैट समर्थित नहीं है। ब्राउज़र से रिकॉर्ड किया गया ऑडियो इस्तेमाल करें।",
    speechFailed: "आवाज़ चलाने में समस्या हुई। टेक्स्ट उत्तर उपलब्ध है।",
    typing: "GovGuideAI आपके लिए यह जाँच रहा है...",
    memoryCleared: "बातचीत की मेमोरी साफ़ हो गई है। अगला प्रश्न पूछें।",
    profilePrivacy: "प्रोफ़ाइल जानकारी केवल व्यक्तिगत सरकारी सेवा और योजना मार्गदर्शन के लिए उपयोग होती है, विज्ञापन या असंबंधित विश्लेषण के लिए नहीं।",
    profileSetupCopy: "इससे GovGuideAI बार-बार जानकारी पूछे बिना योजनाएँ और सेवाएँ सुझा सकता है। आधार, पैन, बैंक विवरण, OTP या पूरा पता न लिखें।",
    signupPrivacy: "आपकी प्रोफ़ाइल केवल सरकारी सेवा और योजना मार्गदर्शन को व्यक्तिगत बनाने के लिए उपयोग होती है। आधार, पैन, बैंक विवरण, OTP या पूरा पता न लिखें।",
    loginCopy: "व्यक्तिगत सरकारी सेवा और योजना सुझावों के लिए लॉग इन करें।",
    profileSaved: "प्रोफ़ाइल सेव हो गई।",
    deleteProfileConfirm: "सेव की गई प्रोफ़ाइल हटाएं? चैट से पहले फिर सेटअप करना होगा।",
    deleteAccountConfirm: "खाता और प्रोफ़ाइल हटाएं? यह वापस नहीं होगा।",
    languageSettings: "भाषा सेटिंग",
    officialSourcesBadge: "आधिकारिक स्रोत",
  },
  mr: {
    officialEyebrow: "अधिकृत स्रोतांवर आधारित नागरी मार्गदर्शन",
    chooseLanguage: "आपली भाषा निवडा",
    continue: "पुढे जा",
    languageChangeNote: "आपण हे नंतर हेडर किंवा प्रोफाइल पानावरून बदलू शकता.",
    welcome: "GovGuideAI मध्ये आपले स्वागत आहे",
    greeting: "GovGuideAI मध्ये आपले स्वागत आहे. आज मी आपली कशी मदत करू शकतो?",
    login: "लॉग इन",
    signup: "साइन अप",
    createAccount: "खाते तयार करा",
    logout: "लॉग आउट",
    email: "ईमेल",
    password: "पासवर्ड",
    newHere: "नवीन आहात?",
    alreadyAccount: "आधीच खाते आहे?",
    profileSetup: "प्रोफाइल सेटअप",
    createProfile: "आपले प्रोफाइल तयार करा",
    editProfile: "प्रोफाइल संपादित करा",
    viewEditProfile: "प्रोफाइल पहा आणि संपादित करा",
    saveProfile: "प्रोफाइल जतन करा",
    saveChanges: "बदल जतन करा",
    deleteProfile: "प्रोफाइल हटवा",
    deleteAccount: "खाते हटवा",
    fullName: "पूर्ण नाव *",
    ageDob: "वय किंवा जन्मतारीख *",
    stateUt: "राज्य किंवा केंद्रशासित प्रदेश *",
    district: "जिल्हा *",
    occupation: "व्यवसाय *",
    occupationOther: "स्वतःचा व्यवसाय लिहा",
    locationType: "ग्रामीण किंवा शहरी *",
    preferredLanguage: "पसंतीची भाषा *",
    gender: "लिंग",
    annualIncome: "वार्षिक कुटुंब उत्पन्न श्रेणी",
    disabilityStatus: "दिव्यांगत्व स्थिती",
    maritalStatus: "वैवाहिक स्थिती",
    socialCategory: "सामाजिक श्रेणी, लागू असल्यास",
    select: "निवडा",
    rural: "ग्रामीण",
    urban: "शहरी",
    student: "विद्यार्थी",
    farmer: "शेतकरी",
    employed: "नोकरीत",
    selfEmployed: "स्वयंरोजगार",
    businessOwner: "व्यवसाय मालक",
    unemployed: "बेरोजगार / नाही",
    retired: "निवृत्त",
    homemaker: "गृहिणी/गृहस्थ",
    other: "इतर",
    backToChat: "चॅटकडे परत",
    yourProfile: "आपले प्रोफाइल",
    edit: "संपादित करा",
    name: "नाव",
    age: "वय",
    state: "राज्य/केंद्रशासित प्रदेश",
    location: "ठिकाण",
    language: "भाषा",
    officialSources: "फक्त अधिकृत स्रोत",
    trustCopy: "GovGuideAI आपले जतन केलेले प्रोफाइल फक्त सरकारी सेवा आणि योजना मार्गदर्शनासाठी वापरते.",
    disclaimer: "GovGuideAI अधिकृत स्रोतांवर आधारित मार्गदर्शन देते. अंतिम पात्रता आणि मंजुरी संबंधित सरकारी प्राधिकरण ठरवते.",
    suggestedPrompts: "उदाहरण प्रश्न",
    passportPrompt: "पासपोर्ट कागदपत्रे",
    schemePrompt: "माझ्यासाठी योजना",
    farmerPrompt: "शेतकरी योजना",
    grievancePrompt: "CPGRAMS मदत",
    wordCountPrompt: "शब्द मोजणी",
    askEyebrow: "भारतीय सरकारी सेवांबद्दल विचारा",
    chatTitle: "GovGuideAI चॅट",
    clearConversation: "संभाषण साफ करा",
    message: "संदेश",
    messagePlaceholder: "योजना, कागदपत्र, सेवा किंवा अधिकृत पोर्टलबद्दल विचारा",
    send: "पाठवा",
    microphone: "मायक्रोफोन",
    startRecording: "रेकॉर्डिंग सुरू करा",
    stopRecording: "रेकॉर्डिंग थांबवा",
    cancel: "रद्द करा",
    replay: "पुन्हा ऐका",
    mute: "आवाज बंद करा",
    unmute: "आवाज सुरू करा",
    stopSpeaking: "बोलणे थांबवा",
    listening: "ऐकत आहे...",
    transcribing: "लिप्यंतरण होत आहे...",
    thinking: "विचार करत आहे...",
    speaking: "बोलत आहे...",
    idleVoice: "व्हॉइस तयार आहे",
    privacyNotice: "ऑडिओ लिप्यंतरणासाठी सुरक्षितपणे पाठवला जातो आणि GovGuideAI तो जाणूनबुजून साठवत नाही.",
    micDenied: "मायक्रोफोन परवानगी नाकारली. आपण टेक्स्ट चॅट वापरू शकता.",
    emptyAudio: "रेकॉर्डिंग रिकामी होती. पुन्हा प्रयत्न करा.",
    unsupportedAudio: "हा ऑडिओ प्रकार समर्थित नाही. ब्राउझरमधून रेकॉर्ड केलेला ऑडिओ वापरा.",
    speechFailed: "आवाज प्लेबॅक अयशस्वी. टेक्स्ट उत्तर उपलब्ध आहे.",
    typing: "GovGuideAI आपल्यासाठी हे तपासत आहे...",
    memoryCleared: "संभाषण मेमरी साफ झाली आहे. पुढचा प्रश्न विचारा.",
    profilePrivacy: "प्रोफाइल माहिती फक्त वैयक्तिक सरकारी सेवा आणि योजना मार्गदर्शनासाठी वापरली जाते.",
    profileSetupCopy: "यामुळे GovGuideAI पुन्हा तपशील न विचारता योजना आणि सेवा सुचवू शकते. आधार, PAN, बँक तपशील, OTP किंवा पूर्ण पत्ता देऊ नका.",
    signupPrivacy: "आपले प्रोफाइल फक्त सरकारी सेवा आणि योजना मार्गदर्शन वैयक्तिक करण्यासाठी वापरले जाते.",
    loginCopy: "वैयक्तिक सरकारी सेवा आणि योजना सूचना वापरण्यासाठी लॉग इन करा.",
    profileSaved: "प्रोफाइल जतन झाले.",
    deleteProfileConfirm: "जतन केलेले प्रोफाइल हटवायचे? चॅट करण्यापूर्वी पुन्हा सेटअप करावा लागेल.",
    deleteAccountConfirm: "खाते आणि प्रोफाइल हटवायचे? हे परत आणता येणार नाही.",
    languageSettings: "भाषा सेटिंग",
    officialSourcesBadge: "अधिकृत स्रोत",
  },
};

const compactLanguageData = {
  bn: ["সরকারি উৎসভিত্তিক নাগরিক সহায়তা", "আপনার ভাষা বেছে নিন", "চালিয়ে যান", "পরে হেডার বা প্রোফাইল পেজ থেকে ভাষা বদলানো যাবে।", "GovGuideAI-তে স্বাগতম", "GovGuideAI-তে স্বাগতম। আজ আমি কীভাবে সাহায্য করতে পারি?", "লগ ইন", "সাইন আপ", "অ্যাকাউন্ট তৈরি করুন", "লগ আউট", "ইমেল", "পাসওয়ার্ড", "নতুন?", "আগে থেকেই অ্যাকাউন্ট আছে?", "প্রোফাইল সেটআপ", "আপনার প্রোফাইল তৈরি করুন", "প্রোফাইল সম্পাদনা", "প্রোফাইল দেখুন ও সম্পাদনা করুন", "প্রোফাইল সংরক্ষণ", "পরিবর্তন সংরক্ষণ", "প্রোফাইল মুছুন", "অ্যাকাউন্ট মুছুন", "পুরো নাম *", "বয়স বা জন্মতারিখ *", "রাজ্য বা কেন্দ্রশাসিত অঞ্চল *", "জেলা *", "পেশা *", "নিজের পেশা লিখুন", "গ্রামীণ বা শহুরে *", "পছন্দের ভাষা *", "লিঙ্গ", "বার্ষিক পারিবারিক আয়ের সীমা", "প্রতিবন্ধকতার অবস্থা", "বৈবাহিক অবস্থা", "সামাজিক শ্রেণি, প্রযোজ্য হলে", "নির্বাচন করুন", "গ্রামীণ", "শহুরে", "ছাত্র/ছাত্রী", "কৃষক", "চাকরিজীবী", "স্বনিযুক্ত", "ব্যবসার মালিক", "বেকার / নেই", "অবসরপ্রাপ্ত", "গৃহকর্তা/গৃহিণী", "অন্যান্য", "চ্যাটে ফিরুন", "আপনার প্রোফাইল", "সম্পাদনা", "নাম", "বয়স", "রাজ্য/কেন্দ্রশাসিত অঞ্চল", "অবস্থান", "ভাষা", "শুধু সরকারি উৎস", "GovGuideAI আপনার সংরক্ষিত প্রোফাইল শুধু সরকারি পরিষেবা ও প্রকল্পের নির্দেশনা ব্যক্তিগত করতে ব্যবহার করে।", "GovGuideAI সরকারি উৎসের ভিত্তিতে নির্দেশনা দেয়। চূড়ান্ত যোগ্যতা ও অনুমোদন সংশ্লিষ্ট সরকারি কর্তৃপক্ষের সিদ্ধান্ত।", "উদাহরণ প্রশ্ন", "পাসপোর্ট নথি", "আমার জন্য প্রকল্প", "কৃষক প্রকল্প", "CPGRAMS সহায়তা", "শব্দ গণনা", "ভারতের সরকারি পরিষেবা সম্পর্কে জিজ্ঞাসা করুন", "GovGuideAI চ্যাট", "কথোপকথন পরিষ্কার করুন", "বার্তা", "কোনো প্রকল্প, নথি, পরিষেবা বা সরকারি পোর্টাল সম্পর্কে জিজ্ঞাসা করুন", "পাঠান", "মাইক্রোফোন", "রেকর্ডিং শুরু", "রেকর্ডিং বন্ধ", "বাতিল", "আবার শুনুন", "ভয়েস মিউট করুন", "ভয়েস চালু করুন", "বলা বন্ধ করুন", "শুনছে...", "লিপ্যন্তর হচ্ছে...", "ভাবছে...", "বলছে...", "ভয়েস প্রস্তুত", "অডিও লিপ্যন্তরের জন্য নিরাপদে পাঠানো হয় এবং GovGuideAI ইচ্ছাকৃতভাবে সংরক্ষণ করে না।", "মাইক্রোফোন অনুমতি অস্বীকার করা হয়েছে। টেক্সট চ্যাট ব্যবহার করা যাবে।", "রেকর্ডিং খালি ছিল। আবার চেষ্টা করুন।", "অডিও ফরম্যাট সমর্থিত নয়। ব্রাউজার-রেকর্ড করা অডিও ব্যবহার করুন।", "ভয়েস প্লেব্যাক ব্যর্থ। টেক্সট উত্তর আছে।", "GovGuideAI আপনার জন্য যাচাই করছে...", "কথোপকথনের মেমরি পরিষ্কার হয়েছে। পরের প্রশ্ন করুন।", "প্রোফাইল তথ্য শুধু ব্যক্তিগত সরকারি পরিষেবা ও প্রকল্প নির্দেশনার জন্য ব্যবহৃত হয়।", "এটি GovGuideAI-কে বারবার তথ্য না চেয়ে প্রকল্প ও পরিষেবা সাজেস্ট করতে সাহায্য করে। Aadhaar, PAN, ব্যাংক তথ্য, OTP বা সম্পূর্ণ ঠিকানা দেবেন না।", "আপনার প্রোফাইল শুধু সরকারি পরিষেবা ও প্রকল্প নির্দেশনা ব্যক্তিগত করতে ব্যবহার হয়।", "ব্যক্তিগত সরকারি পরিষেবা ও প্রকল্প সাজেশনের জন্য লগ ইন করুন।", "প্রোফাইল সংরক্ষিত।", "সংরক্ষিত প্রোফাইল মুছবেন? চ্যাটের আগে আবার সেটআপ করতে হবে।", "অ্যাকাউন্ট ও প্রোফাইল মুছবেন? এটি ফেরানো যাবে না।", "ভাষা সেটিংস", "সরকারি উৎস"],
  ta: ["அதிகாரப்பூர்வ ஆதார குடிமக்கள் வழிகாட்டல்", "உங்கள் மொழியைத் தேர்வு செய்யுங்கள்", "தொடரவும்", "இதனை பின்னர் தலைப்பு அல்லது சுயவிவரப் பக்கத்தில் மாற்றலாம்.", "GovGuideAI-க்கு வரவேற்கிறோம்", "GovGuideAI-க்கு வரவேற்கிறோம். இன்று நான் எப்படி உதவலாம்?", "உள்நுழை", "பதிவு செய்", "கணக்கு உருவாக்கு", "வெளியேறு", "மின்னஞ்சல்", "கடவுச்சொல்", "புதியவரா?", "ஏற்கனவே கணக்கு உள்ளதா?", "சுயவிவர அமைப்பு", "உங்கள் சுயவிவரத்தை உருவாக்கவும்", "சுயவிவரத்தைத் திருத்து", "சுயவிவரத்தைப் பார்த்து திருத்து", "சுயவிவரத்தை சேமி", "மாற்றங்களை சேமி", "சுயவிவரத்தை நீக்கு", "கணக்கை நீக்கு", "முழுப் பெயர் *", "வயது அல்லது பிறந்த தேதி *", "மாநிலம் அல்லது ஒன்றியப் பிரதேசம் *", "மாவட்டம் *", "தொழில் *", "தனிப்பயன் தொழில்", "கிராமம் அல்லது நகரம் *", "விருப்ப மொழி *", "பாலினம்", "ஆண்டு குடும்ப வருமான வரம்பு", "மாற்றுத்திறன் நிலை", "திருமண நிலை", "சமூக வகை, தேவையெனில்", "தேர்ந்தெடு", "கிராமப்புறம்", "நகர்ப்புறம்", "மாணவர்", "விவசாயி", "பணியாளர்", "சுயதொழில்", "தொழில் உரிமையாளர்", "வேலையில்லை / இல்லை", "ஓய்வு", "வீட்டுப்பணி", "மற்றவை", "அரட்டைக்கு திரும்பு", "உங்கள் சுயவிவரம்", "திருத்து", "பெயர்", "வயது", "மாநிலம்/ஒ.பி.", "இடம்", "மொழி", "அதிகாரப்பூர்வ ஆதாரங்கள் மட்டும்", "GovGuideAI சேமித்த சுயவிவரத்தை அரசு சேவை மற்றும் திட்ட வழிகாட்டலுக்கே பயன்படுத்துகிறது.", "GovGuideAI அதிகாரப்பூர்வ ஆதாரங்களின் அடிப்படையில் வழிகாட்டுகிறது. இறுதி தகுதி மற்றும் ஒப்புதல் சம்பந்தப்பட்ட அரசு அதிகாரியால் தீர்மானிக்கப்படும்.", "உதாரண கேள்விகள்", "பாஸ்போர்ட் ஆவணங்கள்", "எனக்கான திட்டங்கள்", "விவசாயி திட்டங்கள்", "CPGRAMS உதவி", "சொல் எண்ணிக்கை", "இந்திய அரசு சேவைகள் பற்றி கேளுங்கள்", "GovGuideAI அரட்டை", "உரையாடலை அழி", "செய்தி", "திட்டம், ஆவணம், சேவை அல்லது அதிகாரப்பூர்வ போர்டல் பற்றி கேளுங்கள்", "அனுப்பு", "மைக்ரோஃபோன்", "பதிவை தொடங்கு", "பதிவை நிறுத்து", "ரத்து", "மீண்டும் இயக்கு", "குரலை முடக்கு", "குரலை இயக்கு", "பேச்சை நிறுத்து", "கேட்கிறது...", "உரைமாற்றம்...", "யோசிக்கிறது...", "பேசுகிறது...", "குரல் தயார்", "ஒலி உரைமாற்றத்திற்காக பாதுகாப்பாக அனுப்பப்படுகிறது; GovGuideAI இதை நோக்கமாக சேமிப்பதில்லை.", "மைக்ரோஃபோன் அனுமதி மறுக்கப்பட்டது. உரை அரட்டை பயன்படுத்தலாம்.", "பதிவு காலியாக இருந்தது. மீண்டும் முயற்சிக்கவும்.", "ஒலி வடிவம் ஆதரிக்கப்படவில்லை. உலாவி பதிவு செய்த ஒலியைப் பயன்படுத்தவும்.", "குரல் இயக்கம் தோல்வியடைந்தது. உரை பதில் கிடைக்கிறது.", "GovGuideAI இதைச் சரிபார்க்கிறது...", "உரையாடல் நினைவகம் அழிக்கப்பட்டது. அடுத்த கேள்வி கேளுங்கள்.", "சுயவிவர தகவல் தனிப்பயன் அரசு சேவை மற்றும் திட்ட வழிகாட்டலுக்கே பயன்படும்.", "இது GovGuideAI-க்கு அடிப்படை விவரங்களை மீண்டும் கேட்காமல் திட்டங்கள் மற்றும் சேவைகளை பரிந்துரைக்க உதவும். Aadhaar, PAN, வங்கி விவரம், OTP அல்லது முழு முகவரி இட வேண்டாம்.", "உங்கள் சுயவிவரம் அரசு சேவை மற்றும் திட்ட வழிகாட்டலுக்கே பயன்படும்.", "தனிப்பயன் அரசு சேவை மற்றும் திட்ட பரிந்துரைகளுக்கு உள்நுழையவும்.", "சுயவிவரம் சேமிக்கப்பட்டது.", "சேமித்த சுயவிவரத்தை நீக்கவா? அரட்டைக்கு முன் மீண்டும் அமைக்க வேண்டும்.", "கணக்கும் சுயவிவரமும் நீக்கவா? இதை மீட்க முடியாது.", "மொழி அமைப்புகள்", "அதிகாரப்பூர்வ ஆதாரங்கள்"],
  te: ["అధికారిక మూలాల పౌర మార్గదర్శకం", "మీ భాషను ఎంచుకోండి", "కొనసాగించు", "దీనిని తరువాత హెడర్ లేదా ప్రొఫైల్ పేజీలో మార్చవచ్చు.", "GovGuideAIకి స్వాగతం", "GovGuideAIకి స్వాగతం. నేను ఈ రోజు మీకు ఎలా సహాయం చేయగలను?", "లాగిన్", "సైన్ అప్", "ఖాతా సృష్టించు", "లాగ్ అవుట్", "ఇమెయిల్", "పాస్‌వర్డ్", "కొత్తవారా?", "ఇప్పటికే ఖాతా ఉందా?", "ప్రొఫైల్ సెటప్", "మీ ప్రొఫైల్ సృష్టించండి", "ప్రొఫైల్ సవరించు", "ప్రొఫైల్ చూడండి మరియు సవరించండి", "ప్రొఫైల్ సేవ్ చేయండి", "మార్పులు సేవ్ చేయండి", "ప్రొఫైల్ తొలగించు", "ఖాతా తొలగించు", "పూర్తి పేరు *", "వయస్సు లేదా పుట్టిన తేదీ *", "రాష్ట్రం లేదా కేంద్ర పాలిత ప్రాంతం *", "జిల్లా *", "వృత్తి *", "ఇతర వృత్తి", "గ్రామీణ లేదా పట్టణ *", "ఇష్టమైన భాష *", "లింగం", "వార్షిక కుటుంబ ఆదాయ పరిధి", "వైకల్య స్థితి", "వివాహ స్థితి", "సామాజిక వర్గం, అవసరమైతే", "ఎంచుకోండి", "గ్రామీణ", "పట్టణ", "విద్యార్థి", "రైతు", "ఉద్యోగి", "స్వయం ఉపాధి", "వ్యాపార యజమాని", "నిరుద్యోగి / లేదు", "విరమణ", "గృహిణి/గృహస్థుడు", "ఇతర", "చాట్‌కు తిరిగి", "మీ ప్రొఫైల్", "సవరించు", "పేరు", "వయస్సు", "రాష్ట్రం/కే.పా.", "ప్రాంతం", "భాష", "అధికారిక మూలాలు మాత్రమే", "GovGuideAI మీ సేవ్ చేసిన ప్రొఫైల్‌ను ప్రభుత్వ సేవలు మరియు పథకాల సూచనలకే ఉపయోగిస్తుంది.", "GovGuideAI అధికారిక మూలాల ఆధారంగా మార్గదర్శనం ఇస్తుంది. తుది అర్హత మరియు ఆమోదం సంబంధిత ప్రభుత్వ అధికారుల నిర్ణయం.", "ఉదాహరణ ప్రశ్నలు", "పాస్‌పోర్ట్ పత్రాలు", "నాకు పథకాలు", "రైతు పథకాలు", "CPGRAMS సహాయం", "పదాల లెక్క", "భారత ప్రభుత్వ సేవల గురించి అడగండి", "GovGuideAI చాట్", "సంభాషణ తొలగించు", "సందేశం", "పథకం, పత్రం, సేవ లేదా అధికారిక పోర్టల్ గురించి అడగండి", "పంపు", "మైక్రోఫోన్", "రికార్డింగ్ ప్రారంభించు", "రికార్డింగ్ ఆపు", "రద్దు", "మళ్లీ విను", "వాయిస్ మ్యూట్", "వాయిస్ ఆన్", "మాట్లాడటం ఆపు", "వింటోంది...", "ట్రాన్స్‌క్రైబ్ చేస్తోంది...", "ఆలోచిస్తోంది...", "మాట్లాడుతోంది...", "వాయిస్ సిద్ధం", "ఆడియో ట్రాన్స్‌క్రిప్షన్ కోసం సురక్షితంగా పంపబడుతుంది మరియు GovGuideAI ఉద్దేశపూర్వకంగా నిల్వ చేయదు.", "మైక్రోఫోన్ అనుమతి నిరాకరించబడింది. టెక్స్ట్ చాట్ ఉపయోగించవచ్చు.", "రికార్డింగ్ ఖాళీగా ఉంది. మళ్లీ ప్రయత్నించండి.", "ఆడియో ఫార్మాట్ మద్దతు లేదు. బ్రౌజర్‌లో రికార్డ్ చేసిన ఆడియో ఉపయోగించండి.", "వాయిస్ ప్లేబ్యాక్ విఫలమైంది. టెక్స్ట్ సమాధానం అందుబాటులో ఉంది.", "GovGuideAI మీ కోసం దీన్ని పరిశీలిస్తోంది...", "సంభాషణ మెమరీ క్లియర్ అయింది. తదుపరి ప్రశ్న అడగండి.", "ప్రొఫైల్ సమాచారం వ్యక్తిగత ప్రభుత్వ సేవలు మరియు పథకాల మార్గదర్శనానికే ఉపయోగించబడుతుంది.", "ఇది GovGuideAIకి మళ్లీ వివరాలు అడగకుండా పథకాలు మరియు సేవలు సూచించడంలో సహాయపడుతుంది. Aadhaar, PAN, బ్యాంక్ వివరాలు, OTP లేదా పూర్తి చిరునామా ఇవ్వవద్దు.", "మీ ప్రొఫైల్ ప్రభుత్వ సేవలు మరియు పథకాల మార్గదర్శనానికే ఉపయోగించబడుతుంది.", "వ్యక్తిగత ప్రభుత్వ సేవలు మరియు పథకాల సూచనలకు లాగిన్ అవ్వండి.", "ప్రొఫైల్ సేవ్ అయింది.", "సేవ్ చేసిన ప్రొఫైల్ తొలగించాలా? చాట్ ముందు మళ్లీ సెటప్ చేయాలి.", "ఖాతా మరియు ప్రొఫైల్ తొలగించాలా? ఇది తిరిగి రాదు.", "భాష సెట్టింగ్‌లు", "అధికారిక మూలాలు"],
};

const compactKeys = Object.keys(translations.en);
Object.entries(compactLanguageData).forEach(([code, values]) => {
  translations[code] = Object.fromEntries(compactKeys.map((key, index) => [key, values[index] || translations.en[key]]));
});

["gu", "kn", "ml", "pa", "ur"].forEach((code) => {
  translations[code] = { ...translations.en, chooseLanguage: languageOptions.find((item) => item.code === code).name };
});

const authAndGuestTranslations = {
  en: {
    loginOtpCopy: "Verify your email or phone number to securely access your saved profile.",
    localDevelopmentVerification: "Local development verification is enabled. No real email or SMS will be sent.",
    adminDashboard: "Admin Dashboard",
    administratorSetup: "Administrator Setup",
    signupOtpCopy: "Start with a verified email or phone number, then complete your profile for personalized guidance.",
    continueWithEmail: "Continue with email",
    continueWithPhone: "Continue with phone number",
    emailAddress: "Email address",
    country: "Country",
    phoneNumber: "Phone number",
    phoneExample: "e.g. 98765 43210",
    sendCode: "Send code",
    sendingCode: "Sending code…",
    or: "or",
    continueAsGuest: "Continue as Guest",
    guestExplanation: "You can use GovGuideAI without creating an account. Recommendations may be less personalized, and your profile and chat history may not be saved.",
    reducedPersonalization: "Reduced personalization",
    noPermanentProfile: "No permanent profile",
    noSavedHistory: "No permanent saved chat history or cross-device access",
    temporaryMemoryOnly: "Temporary conversation memory only",
    usePasswordInstead: "Use email and password instead",
    loginWithPassword: "Login with password",
    createWithPassword: "Create with password",
    authPrivacyNotice: "Email or phone verification is used to secure your account. Guest users can continue without sharing these details, but personalization and saved history will be limited.",
    invalidEmail: "Enter a valid email address.",
    invalidPhone: "Enter a valid phone number.",
    couldNotSendCode: "We could not send the code right now. Please try again later.",
    emailUnavailable: "Email verification is temporarily unavailable.",
    phoneUnavailable: "Phone verification is temporarily unavailable.",
    waitBeforeCode: "Please wait before requesting another code.",
    incorrectOrExpiredCode: "That code is incorrect or has expired.",
    incorrectPassword: "Incorrect email or password.",
    secureVerification: "Secure verification",
    enterVerificationCode: "Enter verification code",
    codeSentTo: "We sent a 6-digit code to",
    sixDigitCode: "6-digit code",
    otpHelp: "Enter or paste the full code.",
    verify: "Verify",
    resendCode: "Resend code",
    codeExpired: "Code expired. Request a new code.",
    changeEmail: "Change email",
    changePhoneNumber: "Change phone number",
    verificationSuccessful: "Verification successful.",
    continuingToAccount: "Your secure session is ready.",
    developmentOnly: "Development only:",
    testCode: "test code",
    developmentOtpWarning: "Development OTP — not for production",
    passwordMinimum: "Use at least 8 characters.",
    sixDigitCodeRequired: "Enter all 6 digits.",
    openMenu: "Open menu",
    close: "Close",
    guestMode: "Guest mode",
    temporary: "Temporary",
    guestReducedNotice: "You can use every assistant tool, but recommendations have reduced personalization.",
    createAccountToSave: "Create an account to save your information",
    guestTrustCopy: "GovGuideAI provides official-source guidance without requiring personal details.",
    guestChatNotice: "Your chat works normally, but this session and its personalization are temporary.",
    emptyStateGuestNote: "You can share optional details in this conversation when they help, but they are not saved as a profile.",
  },
  hi: {
    continueWithEmail: "ईमेल से जारी रखें", continueWithPhone: "फ़ोन नंबर से जारी रखें", country: "देश", phoneNumber: "फ़ोन नंबर", sendCode: "कोड भेजें", continueAsGuest: "अतिथि के रूप में जारी रखें", reducedPersonalization: "कम व्यक्तिगत सुझाव", enterVerificationCode: "सत्यापन कोड दर्ज करें", verify: "सत्यापित करें", resendCode: "कोड फिर भेजें", codeExpired: "कोड की समय-सीमा समाप्त हो गई।", incorrectOrExpiredCode: "यह कोड गलत है या इसकी समय-सीमा समाप्त हो गई है।", changeEmail: "ईमेल बदलें", changePhoneNumber: "फ़ोन नंबर बदलें", createAccountToSave: "अपनी जानकारी सहेजने के लिए खाता बनाएं", guestMode: "अतिथि मोड", guestExplanation: "आप बिना खाता बनाए GovGuideAI का उपयोग कर सकते हैं। सुझाव कम व्यक्तिगत हो सकते हैं और प्रोफ़ाइल व चैट इतिहास सहेजा नहीं जाएगा।", authPrivacyNotice: "ईमेल या फ़ोन सत्यापन आपके खाते की सुरक्षा के लिए है। अतिथि बिना ये विवरण साझा किए जारी रख सकते हैं, लेकिन व्यक्तिगत सुझाव और सहेजा इतिहास सीमित रहेगा।",
  },
  mr: {
    continueWithEmail: "ईमेलने पुढे जा", continueWithPhone: "फोन क्रमांकाने पुढे जा", country: "देश", phoneNumber: "फोन क्रमांक", sendCode: "कोड पाठवा", continueAsGuest: "अतिथी म्हणून पुढे जा", reducedPersonalization: "मर्यादित वैयक्तिकरण", enterVerificationCode: "पडताळणी कोड टाका", verify: "पडताळा", resendCode: "कोड पुन्हा पाठवा", codeExpired: "कोडची मुदत संपली.", incorrectOrExpiredCode: "हा कोड चुकीचा आहे किंवा त्याची मुदत संपली आहे.", changeEmail: "ईमेल बदला", changePhoneNumber: "फोन क्रमांक बदला", createAccountToSave: "माहिती जतन करण्यासाठी खाते तयार करा",
  },
  bn: {
    continueWithEmail: "ইমেল দিয়ে চালিয়ে যান", continueWithPhone: "ফোন নম্বর দিয়ে চালিয়ে যান", country: "দেশ", phoneNumber: "ফোন নম্বর", sendCode: "কোড পাঠান", continueAsGuest: "অতিথি হিসেবে চালিয়ে যান", reducedPersonalization: "সীমিত ব্যক্তিগতকরণ", enterVerificationCode: "যাচাইকরণ কোড লিখুন", verify: "যাচাই করুন", resendCode: "কোড আবার পাঠান", codeExpired: "কোডের মেয়াদ শেষ।", incorrectOrExpiredCode: "কোডটি ভুল বা মেয়াদোত্তীর্ণ।", changeEmail: "ইমেল পরিবর্তন করুন", changePhoneNumber: "ফোন নম্বর পরিবর্তন করুন", createAccountToSave: "তথ্য সংরক্ষণ করতে অ্যাকাউন্ট তৈরি করুন",
  },
  ta: {
    continueWithEmail: "மின்னஞ்சலுடன் தொடரவும்", continueWithPhone: "தொலைபேசி எண்ணுடன் தொடரவும்", country: "நாடு", phoneNumber: "தொலைபேசி எண்", sendCode: "குறியீட்டை அனுப்பு", continueAsGuest: "விருந்தினராக தொடரவும்", reducedPersonalization: "குறைந்த தனிப்பயனாக்கம்", enterVerificationCode: "சரிபார்ப்புக் குறியீட்டை உள்ளிடவும்", verify: "சரிபார்", resendCode: "குறியீட்டை மீண்டும் அனுப்பு", codeExpired: "குறியீடு காலாவதியானது.", incorrectOrExpiredCode: "குறியீடு தவறானது அல்லது காலாவதியானது.", changeEmail: "மின்னஞ்சலை மாற்று", changePhoneNumber: "தொலைபேசி எண்ணை மாற்று", createAccountToSave: "தகவலைச் சேமிக்க கணக்கு உருவாக்கவும்",
  },
  te: {
    continueWithEmail: "ఇమెయిల్‌తో కొనసాగండి", continueWithPhone: "ఫోన్ నంబర్‌తో కొనసాగండి", country: "దేశం", phoneNumber: "ఫోన్ నంబర్", sendCode: "కోడ్ పంపండి", continueAsGuest: "అతిథిగా కొనసాగండి", reducedPersonalization: "తక్కువ వ్యక్తిగతీకరణ", enterVerificationCode: "ధృవీకరణ కోడ్ నమోదు చేయండి", verify: "ధృవీకరించండి", resendCode: "కోడ్ మళ్లీ పంపండి", codeExpired: "కోడ్ గడువు ముగిసింది.", incorrectOrExpiredCode: "కోడ్ తప్పు లేదా గడువు ముగిసింది.", changeEmail: "ఇమెయిల్ మార్చండి", changePhoneNumber: "ఫోన్ నంబర్ మార్చండి", createAccountToSave: "సమాచారాన్ని సేవ్ చేయడానికి ఖాతా సృష్టించండి",
  },
  gu: {
    continueWithEmail: "ઇમેઇલથી આગળ વધો", continueWithPhone: "ફોન નંબરથી આગળ વધો", country: "દેશ", phoneNumber: "ફોન નંબર", sendCode: "કોડ મોકલો", continueAsGuest: "મહેમાન તરીકે આગળ વધો", reducedPersonalization: "ઓછું વ્યક્તિગતકરણ", enterVerificationCode: "ચકાસણી કોડ દાખલ કરો", verify: "ચકાસો", resendCode: "કોડ ફરી મોકલો", codeExpired: "કોડની મુદત પૂરી થઈ.", incorrectOrExpiredCode: "કોડ ખોટો છે અથવા તેની મુદત પૂરી થઈ છે.", changeEmail: "ઇમેઇલ બદલો", changePhoneNumber: "ફોન નંબર બદલો", createAccountToSave: "માહિતી સાચવવા ખાતું બનાવો",
  },
  kn: {
    continueWithEmail: "ಇಮೇಲ್‌ನೊಂದಿಗೆ ಮುಂದುವರಿಸಿ", continueWithPhone: "ಫೋನ್ ಸಂಖ್ಯೆಯೊಂದಿಗೆ ಮುಂದುವರಿಸಿ", country: "ದೇಶ", phoneNumber: "ಫೋನ್ ಸಂಖ್ಯೆ", sendCode: "ಕೋಡ್ ಕಳುಹಿಸಿ", continueAsGuest: "ಅತಿಥಿಯಾಗಿ ಮುಂದುವರಿಸಿ", reducedPersonalization: "ಕಡಿಮೆ ವೈಯಕ್ತೀಕರಣ", enterVerificationCode: "ಪರಿಶೀಲನಾ ಕೋಡ್ ನಮೂದಿಸಿ", verify: "ಪರಿಶೀಲಿಸಿ", resendCode: "ಕೋಡ್ ಮತ್ತೆ ಕಳುಹಿಸಿ", codeExpired: "ಕೋಡ್ ಅವಧಿ ಮುಗಿದಿದೆ.", incorrectOrExpiredCode: "ಕೋಡ್ ತಪ್ಪಾಗಿದೆ ಅಥವಾ ಅವಧಿ ಮುಗಿದಿದೆ.", changeEmail: "ಇಮೇಲ್ ಬದಲಿಸಿ", changePhoneNumber: "ಫೋನ್ ಸಂಖ್ಯೆ ಬದಲಿಸಿ", createAccountToSave: "ಮಾಹಿತಿ ಉಳಿಸಲು ಖಾತೆ ರಚಿಸಿ",
  },
  ml: {
    continueWithEmail: "ഇമെയിൽ ഉപയോഗിച്ച് തുടരുക", continueWithPhone: "ഫോൺ നമ്പർ ഉപയോഗിച്ച് തുടരുക", country: "രാജ്യം", phoneNumber: "ഫോൺ നമ്പർ", sendCode: "കോഡ് അയയ്ക്കുക", continueAsGuest: "അതിഥിയായി തുടരുക", reducedPersonalization: "കുറഞ്ഞ വ്യക്തിഗതമാക്കൽ", enterVerificationCode: "സ്ഥിരീകരണ കോഡ് നൽകുക", verify: "സ്ഥിരീകരിക്കുക", resendCode: "കോഡ് വീണ്ടും അയയ്ക്കുക", codeExpired: "കോഡിന്റെ കാലാവധി കഴിഞ്ഞു.", incorrectOrExpiredCode: "കോഡ് തെറ്റാണ് അല്ലെങ്കിൽ കാലാവധി കഴിഞ്ഞു.", changeEmail: "ഇമെയിൽ മാറ്റുക", changePhoneNumber: "ഫോൺ നമ്പർ മാറ്റുക", createAccountToSave: "വിവരങ്ങൾ സൂക്ഷിക്കാൻ അക്കൗണ്ട് സൃഷ്ടിക്കുക",
  },
  pa: {
    continueWithEmail: "ਈਮੇਲ ਨਾਲ ਜਾਰੀ ਰੱਖੋ", continueWithPhone: "ਫ਼ੋਨ ਨੰਬਰ ਨਾਲ ਜਾਰੀ ਰੱਖੋ", country: "ਦੇਸ਼", phoneNumber: "ਫ਼ੋਨ ਨੰਬਰ", sendCode: "ਕੋਡ ਭੇਜੋ", continueAsGuest: "ਮਹਿਮਾਨ ਵਜੋਂ ਜਾਰੀ ਰੱਖੋ", reducedPersonalization: "ਘੱਟ ਨਿੱਜੀਕਰਨ", enterVerificationCode: "ਤਸਦੀਕੀ ਕੋਡ ਦਰਜ ਕਰੋ", verify: "ਤਸਦੀਕ ਕਰੋ", resendCode: "ਕੋਡ ਦੁਬਾਰਾ ਭੇਜੋ", codeExpired: "ਕੋਡ ਦੀ ਮਿਆਦ ਖਤਮ ਹੋ ਗਈ।", incorrectOrExpiredCode: "ਕੋਡ ਗਲਤ ਹੈ ਜਾਂ ਮਿਆਦ ਖਤਮ ਹੋ ਗਈ ਹੈ।", changeEmail: "ਈਮੇਲ ਬਦਲੋ", changePhoneNumber: "ਫ਼ੋਨ ਨੰਬਰ ਬਦਲੋ", createAccountToSave: "ਜਾਣਕਾਰੀ ਸੰਭਾਲਣ ਲਈ ਖਾਤਾ ਬਣਾਓ",
  },
  ur: {
    continueWithEmail: "ای میل کے ساتھ جاری رکھیں", continueWithPhone: "فون نمبر کے ساتھ جاری رکھیں", country: "ملک", phoneNumber: "فون نمبر", sendCode: "کوڈ بھیجیں", continueAsGuest: "مہمان کے طور پر جاری رکھیں", reducedPersonalization: "کم ذاتی نوعیت", enterVerificationCode: "تصدیقی کوڈ درج کریں", verify: "تصدیق کریں", resendCode: "کوڈ دوبارہ بھیجیں", codeExpired: "کوڈ کی میعاد ختم ہو گئی۔", incorrectOrExpiredCode: "کوڈ غلط ہے یا اس کی میعاد ختم ہو گئی ہے۔", changeEmail: "ای میل تبدیل کریں", changePhoneNumber: "فون نمبر تبدیل کریں", createAccountToSave: "معلومات محفوظ کرنے کے لیے اکاؤنٹ بنائیں",
  },
};

Object.entries(authAndGuestTranslations).forEach(([code, values]) => {
  translations[code] = { ...translations[code], ...authAndGuestTranslations.en, ...values };
});

function getStoredLanguage() {
  try {
    return window.localStorage.getItem("govguideaiLanguage") || "";
  } catch {
    return "";
  }
}

function getLanguage() {
  const stored = getStoredLanguage();
  if (translations[stored]) {
    return stored;
  }
  const sessionLanguage = document.body?.dataset.selectedLanguage;
  if (translations[sessionLanguage]) {
    return sessionLanguage;
  }
  const profileLanguage = window.govGuideProfileLanguage;
  return translations[profileLanguage] ? profileLanguage : "en";
}

function setLanguage(language) {
  const code = translations[language] ? language : "en";
  try {
    window.localStorage.setItem("govguideaiLanguage", code);
    window.localStorage.setItem("govguideaiLanguageSelected", "1");
  } catch {
    // The server-backed form/session remains authoritative when storage is unavailable.
  }
  applyTranslations();
  window.dispatchEvent(new CustomEvent("govguideai:languagechange", { detail: { language: code } }));
  return code;
}

function t(key) {
  const language = getLanguage();
  return translations[language]?.[key] || translations.en[key] || key;
}

function csrfToken() {
  return document.querySelector("meta[name='csrf-token']")?.content || "";
}

function applyTranslations() {
  const language = getLanguage();
  document.documentElement.lang = language;
  document.documentElement.dir = language === "ur" ? "rtl" : "ltr";

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
  });
  document.querySelectorAll("[data-i18n-title]").forEach((element) => {
    element.setAttribute("title", t(element.dataset.i18nTitle));
    element.setAttribute("aria-label", t(element.dataset.i18nTitle));
  });
  document.querySelectorAll("[data-confirm-key]").forEach((element) => {
    element.setAttribute("data-confirm", t(element.dataset.confirmKey));
  });
  document.querySelectorAll("[data-language-select]").forEach((select) => {
    select.value = language;
  });
  document.querySelectorAll("input[name='selected_language']").forEach((input) => {
    input.value = language;
  });
}

function ensureLanguageBeforePage() {
  if (!document.body.matches("[data-require-language]")) {
    return;
  }
  if (document.body.dataset.languageSelected === "true") {
    return;
  }
  try {
    if (window.localStorage.getItem("govguideaiLanguageSelected") === "1") {
      return;
    }
  } catch {
    // Continue to the language screen; its POST works without browser storage.
  }
  const next = encodeURIComponent(`${window.location.pathname}${window.location.search}`);
  window.location.replace(`/language?next=${next}`);
}

async function saveLanguageToProfile(language) {
  if (!window.govGuideUserId) {
    return;
  }
  try {
    await fetch("/api/profile/language", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken() },
      body: JSON.stringify({ language }),
    });
  } catch {
    // The browser copy remains useful even if a temporary server save fails.
  }
}

document.addEventListener("DOMContentLoaded", () => {
  ensureLanguageBeforePage();
  applyTranslations();

  document.querySelectorAll("[data-language-select]").forEach((select) => {
    select.value = getLanguage();
    select.addEventListener("change", () => {
      const language = setLanguage(select.value);
      saveLanguageToProfile(language);
    });
  });

  document.querySelectorAll("[data-language-choice]").forEach((button) => {
    const isSelected = button.dataset.languageChoice === getLanguage();
    button.classList.toggle("selected", isSelected);
    button.setAttribute("aria-checked", String(isSelected));
    button.addEventListener("click", () => {
      setLanguage(button.dataset.languageChoice);
      document.querySelectorAll("[data-language-choice]").forEach((item) => {
        const itemSelected = item === button;
        item.classList.toggle("selected", itemSelected);
        item.setAttribute("aria-checked", String(itemSelected));
      });
    });
  });

  const languageForm = document.querySelector("#languageForm");
  if (languageForm) {
    languageForm.addEventListener("submit", () => {
      const language = getLanguage();
      const selectedInput = languageForm.querySelector("input[name='selected_language']");
      if (selectedInput) selectedInput.value = language;
      saveLanguageToProfile(language);
    });
  }
});

window.GovGuideI18n = {
  languageOptions,
  translations,
  getLanguage,
  setLanguage,
  t,
  applyTranslations,
  saveLanguageToProfile,
  csrfToken,
};
