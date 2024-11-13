import streamlit as st
import whisper
import numpy as np
from collections import Counter
import re
import json
import sounddevice as sd
import wavio
import tempfile
import os
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

class AccentAnalyzer:
    def __init__(self):
        self.model = whisper.load_model("base")
        
        # Enhanced accent characteristics including African accents
        self.accent_patterns = {
            "Ghanaian": {
                "word_patterns": r"\b(please|sorry|okay|aiih)\b",
                "vocabulary": [
                    "charlie", "chale", "ei", "herh", "ah", "ooo", "abi",
                    "kafra", "medaase", "yoo", "massa", "aswear",
                    "anyways", "whereby", "somehow"
                ],
                "phonetic_patterns": {
                    "th_substitution": r"\b(th[aeiou])",  # 'th' sound often pronounced as 't'
                    "final_stress": r"ing\b",  # distinctive stress on final syllables
                    "vowel_patterns": r"(er|or)\b"  # distinctive vowel sounds
                },
                "grammatical_patterns": [
                    r"(?i)\b(am|is|are)\s+having\b",  # stative verbs in continuous form
                    r"(?i)\b(make|let)\s+I\b",        # distinctive verb usage
                    r"(?i)\b(since|for)\s+long\b"     # time expressions
                ]
            },
            "Nigerian": {
                "word_patterns": r"\b(abi|sha|na|wahala|shebi)\b",
                "vocabulary": [
                    "bros", "oga", "wahala", "gist", "abeg", "wetin",
                    "joor", "sha", "sef", "shey", "oyibo", "yeye",
                    "pikin", "chop", "kpeke", "kele"
                ],
                "phonetic_patterns": {
                    "th_substitution": r"\b(th[aeiou])",
                    "vowel_lengthening": r"([aeiou])\1+",
                    "syllable_timing": r"\b\w+ing\b"
                },
                "grammatical_patterns": [
                    r"(?i)\b(no|not)\s+be\b",
                    r"(?i)\bdey\b",
                    r"(?i)\bna\b"
                ]
            },
            "Kenyan": {
                "word_patterns": r"\b(sijui|sawa|pole|jambo)\b",
                "vocabulary": [
                    "maze", "sawa", "kwani", "sijui", "pole", "tafadhali",
                    "hapana", "mzee", "mambo", "poa", "asante", "karibu"
                ],
                "phonetic_patterns": {
                    "consonant_clusters": r"(str|spr|scr)",
                    "vowel_harmony": r"([aeiou])\1",
                    "stress_pattern": r"\b\w+ly\b"
                }
            },
            "South African": {
                "word_patterns": r"\b(ja|né|shame|ag)\b",
                "vocabulary": [
                    "shame", "just now", "robot", "braai", "lekker",
                    "howzit", "yebo", "eish", "bru", "aikona", "voetsek",
                    "now now", "ja", "né"
                ],
                "phonetic_patterns": {
                    "vowel_raising": r"(ee|oo)\b",
                    "final_devoicing": r"[bdg]\b",
                    "trilled_r": r"\br\w+"
                }
            },
            "British": {
                "word_patterns": r"\b(rather|quite|proper|bloody)\b",
                "vocabulary": [
                    "bloody", "mate", "brilliant", "cheers", "proper",
                    "quid", "fiver", "tenner", "bloke", "knackered",
                    "peckish", "gobsmacked", "chuffed"
                ],
                "phonetic_patterns": {
                    "non_rhotic": r"[aeiou]r\b",
                    "t_glottalization": r"\bt\w+",
                    "ing_pronunciation": r"ing\b"
                }
            },
            "American": {
                "word_patterns": r"\b(like|awesome|totally|gonna|wanna)\b",
                "vocabulary": [
                    "guys", "awesome", "y'all", "gonna", "wanna",
                    "trash", "elevator", "apartment", "candy", "soccer",
                    "buck", "period", "high school"
                ],
                "phonetic_patterns": {
                    "rhotic": r"er\b",
                    "t_flapping": r"\b\w+ter\b",
                    "dropped_g": r"in'\b"
                }
            },
            "Inuktitut": {
        "word_patterns": r"\b(amma|kisiani|uvvaluunniit|suli|taimaa)\b",
        "vocabulary": [
            "ainngai", "nakurmiik", "tunngatit", "tavvauvutit",
            "ii", "aaka", "qujannamiik", "aksut", "ilaali"
        ],
        "phonetic_patterns": {
            "double_consonants": r"([ptkg])\1",
            "uvular_sounds": r"[qr]",
            "vowel_length": r"[aiu]{2}"
        },
        "grammatical_patterns": [
            r"\w+vuq\b",     # 3rd person singular
            r"\w+juq\b",     # Participial
            r"\w+mit\b"      # Ablative case
        ]
    },

    # CAUCASIAN FAMILY
    "Chechen": {
        "word_patterns": r"\b(я|амма|йа|хlун|муха)\b",
        "vocabulary": [
            "баркалла", "дика ду", "къинтера", "маршалла",
            "хlаъ", "хlан-хlа", "дика", "нийса", "чlогlа"
        ],
        "phonetic_patterns": {
            "ejectives": r"[пткцчl]l",
            "pharyngeals": r"хl",
            "lateral_consonants": r"[лхl]"
        },
        "grammatical_patterns": [
            r"\w+ш\b",       # Infinitive
            r"\w+на\b",      # Past tense
            r"\w+ш\b"        # Plural
        ]
    },

    # AUSTRONESIAN FAMILY - POLYNESIAN BRANCH
    "Māori": {
        "word_patterns": r"\b(me|engari|rānei|pēhea|āhea)\b",
        "vocabulary": [
            "kia ora", "tēnā koe", "aroha", "ka pai",
            "āe", "kāo", "tahi", "rua", "nō reira"
        ],
        "phonetic_patterns": {
            "long_vowels": r"[āēīōū]",
            "consonant_pairs": r"[tkpmnngrw][aeiou]",
            "diphthongs": r"(ae|ai|ao|au|ei|oi|ou)"
        },
        "grammatical_patterns": [
            r"(?i)\bkua\s+\w+\b",    # Past tense
            r"(?i)\bka\s+\w+\b",     # Future/present
            r"(?i)\b(ngā|te)\s+\w+\b" # Articles
        ]
    },

    # QUECHUAN FAMILY
    "Quechua": {
        "word_patterns": r"\b(hina|ichaqa|utaq|imayna|hayka)\b",
        "vocabulary": [
            "allillanchu", "sulpayki", "paqarin kama", "rimaykullayki",
            "ari", "mana", "allin", "munay", "sumaq"
        ],
        "phonetic_patterns": {
            "ejectives": r"[ptkqč]'",
            "aspirates": r"[ptkqč]h",
            "uvular_stops": r"q"
        },
        "grammatical_patterns": [
            r"\w+chka\b",    # Progressive
            r"\w+rqa\b",     # Past tense
            r"\w+kuna\b"     # Plural
        ]
    },

    # NIGER-CONGO - BANTU BRANCH
    "Zulu": {
        "word_patterns": r"\b(futhi|kodwa|noma|ngani|kanjani)\b",
        "vocabulary": [
            "sawubona", "ngiyabonga", "uxolo", "hamba kahle",
            "yebo", "cha", "kahle", "ncono", "kakhulu"
        ],
        "phonetic_patterns": {
            "clicks": r"[qxc]",
            "aspirated_stops": r"[ptkq]h",
            "nasalized_vowels": r"[aeiou]n"
        },
        "grammatical_patterns": [
            r"(?i)\buku\w+\b",    # Infinitive
            r"(?i)\bizi\w+\b",    # Plural class 8
            r"(?i)\baba\w+\b"     # Class 2 prefix
        ]
    },

    # TIBETO-BURMAN FAMILY
    "Tibetan": {
        "word_patterns": r"\b(དང་|ཡིན་|རེད་|འདུག་|སོང་)\b",
        "vocabulary": [
            "ཐུགས་རྗེ་ཆེ", "བཀྲ་ཤིས་བདེ་ལེགས", "དགོངས་དག",
            "གཟིགས་གསོལ", "ལགས་རེད", "མ་རེད", "ཡག་པོ"
        ],
        "phonetic_patterns": {
            "tones": r"[གདབ]$",
            "aspirated": r"[ཁཆཐཕ]",
            "nasals": r"[ངཉཎནམ]"
        },
        "grammatical_patterns": [
            r"\w+པ་རེད\b",    # Past tense
            r"\w+གི་འདུག\b",   # Present continuous
            r"\w+བཞིན་ཡོད\b"    # Progressive
        ]
    },

    # MON-KHMER FAMILY
    "Khmer": {
        "word_patterns": r"\b(និង|ប៉ុន្តែ|ឬ|ហេតុអ្វី|យ៉ាងម៉េច)\b",
        "vocabulary": [
            "សូមអរគុណ", "អត់អីទេ", "សូមទោស", "ជំរាបសួរ",
            "បាទ/ចាស", "ទេ", "ល្អ", "យល់ព្រម", "ត្រូវហើយ"
        ],
        "phonetic_patterns": {
            "aspirated": r"[ខឃថធផភ]",
            "register": r"[់័ៈៗ]",
            "clusters": r"[កខគឃងចឆជឈញ][្]"
        },
        "grammatical_patterns": [
            r"(?i)\bកំពុង\w+\b",     # Progressive
            r"(?i)\bបាន\w+\b",      # Past tense
            r"(?i)\bនឹង\w+\b"       # Future
        ]
    },

    # DRAVIDIAN FAMILY
    "Telugu": {
        "word_patterns": r"\b(మరియు|కానీ|లేదా|ఎందుకు|ఎలా)\b",
        "vocabulary": [
            "నమస్కారం", "ధన్యవాదాలు", "క్షమించండి", "శుభోదయం",
            "అవును", "కాదు", "మంచిది", "సరే", "బాగుంది"
        ],
        "phonetic_patterns": {
            "aspirated": r"[ఖఘఛఝఠఢథధఫభ]",
            "retroflex": r"[టఠడఢణ]",
            "vowel_length": r"[ాీూెేైోౌం]"
        },
        "grammatical_patterns": [
            r"\w+తున్నాను\b",    # Present continuous
            r"\w+ను\b",         # Past tense
            r"\w+తాను\b"        # Future
        ]
    },

    # AINU FAMILY
    "Ainu": {
        "word_patterns": r"\b(kor|ne|wa|ta|un)\b",
        "vocabulary": [
            "irankarapte", "iyayraykere", "pirka", "hunna",
            "ruwe", "somo", "hawe", "yakun", "nisa"
        ],
        "phonetic_patterns": {
            "consonant_pairs": r"[ptcksmrw][aeiou]",
            "final_vowels": r"[aeiou]$",
            "pitch_accent": r"\w+ru\b"
        },
        "grammatical_patterns": [
            r"\w+as\b",      # Plural
            r"\w+an\b",      # Progressive
            r"\w+pe\b"       # Nominalizer
        ]
    },

    # TUPIAN FAMILY
    "Guarani": {
        "word_patterns": r"\b(ha|térã|ramo|mba'éichapa|moõpa)\b",
        "vocabulary": [
            "aguyje", "mba'éichapa", "jajotopá peve", "iporã",
            "heẽ", "nahániri", "porã", "upéicha", "añete"
        ],
        "phonetic_patterns": {
            "nasal_vowels": r"[ãẽĩõũ]",
            "glottal_stop": r"'",
            "stress_pattern": r"\w+́\b"
        },
        "grammatical_patterns": [
            r"\w+ta\b",      # Future
            r"\w+ma\b",      # Perfect
            r"\w+kuéra\b"    # Plural
        ]
    },

    "Finnish": {
        "word_patterns": r"\b(no|joo|kyllä|siis|vaan)\b",
        "vocabulary": [
            "kiitos", "ole hyvä", "anteeksi", "terve", "näkemiin",
            "hauska", "hyvä", "totta kai", "selvä", "mukava"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[äöy]+\w*[aou]|[aou]+\w*[äöy]",
            "gemination": r"(\w)\1",
            "diphthongs": r"(ai|ei|oi|ui|yi|äi|öi|au|eu|iu|ou|äy|öy)"
        },
        "grammatical_patterns": [
            r"\w+ssa\b",  # Inessive case
            r"\w+sta\b",  # Elative case
            r"\w+ksi\b"   # Translative case
        ]
    },

    "Hungarian": {
        "word_patterns": r"\b(igen|nem|hát|szóval|akkor)\b",
        "vocabulary": [
            "köszönöm", "kérem", "bocsánat", "szia", "viszlát",
            "persze", "rendben", "jó", "nagyon", "tessék"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[eéiíöőüű]+\w*[aáoóuú]|[aáoóuú]+\w*[eéiíöőüű]",
            "long_vowels": r"[áéíóőúű]",
            "digraphs": r"(sz|gy|ny|ty|zs)"
        },
        "grammatical_patterns": [
            r"\w+ban\b",  # Inessive case
            r"\w+ból\b",  # Elative case
            r"\w+val\b"   # Instrumental case
        ]
    },

    # CELTIC BRANCH
    "Irish": {
        "word_patterns": r"\b(tá|níl|bhí|agus|go)\b",
        "vocabulary": [
            "slán", "go raibh maith agat", "más é do thoil é", 
            "dia duit", "conas atá tú", "maith", "ceart go leor"
        ],
        "phonetic_patterns": {
            "broad_slender": r"[aouáóú][^aouáóú]+[aouáóú]|[eiéí][^aouáóú]+[eiéí]",
            "lenition": r"[bcdfgmpt]h",
            "eclipsis": r"(mb|gc|nd|bhf|ng|bp|dt)"
        },
        "grammatical_patterns": [
            r"(?i)\b(ag|ar|as|chuig|de|do|faoi|i|le|ó|roimh|thar|trí|um)\b",
            r"\w+adh\b",  # Verbal noun
            r"\w+igh\b"   # Genitive case
        ]
    },

    # AUSTROASIATIC FAMILY
    "Vietnamese": {
        "word_patterns": r"\b(và|rồi|nhưng|vì|thì)\b",
        "vocabulary": [
            "cảm ơn", "không có chi", "xin lỗi", "tạm biệt",
            "chào", "được", "vâng", "không", "đúng", "tốt"
        ],
        "phonetic_patterns": {
            "tones": r"[áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữự]",
            "final_consonants": r"[ptcmnŋ]$",
            "diphthongs": r"(ia|ưa|ua)"
        },
        "grammatical_patterns": [
            r"(?i)\b(đã|đang|sẽ)\b",  # Tense markers
            r"(?i)\b(những|các)\b",    # Plural markers
            r"(?i)\b(của|ở|trong)\b"   # Prepositions
        ]
    },

    # NIGER-CONGO FAMILY
    "Swahili": {
        "word_patterns": r"\b(na|kwa|ya|wa|za)\b",
        "vocabulary": [
            "asante", "karibu", "pole", "jambo", "kwaheri",
            "ndiyo", "hapana", "tafadhali", "sawa", "vizuri"
        ],
        "phonetic_patterns": {
            "prenasalization": r"(mb|nd|ng|nj)",
            "vowel_harmony": r"[aeiou]+",
            "stress_pattern": r"\w+a\b"
        },
        "grammatical_patterns": [
            r"(?i)\bni\w+\b",     # Present tense
            r"(?i)\bwa\w+\b",     # Possessive
            r"(?i)\b[mk]\w+\b"    # Noun classes
        ]
    },

    # AFROASIATIC FAMILY
    "Hebrew": {
        "word_patterns": r"\b(אז|רק|גם|אבל|או)\b",
        "vocabulary": [
            "שלום", "תודה", "בבקשה", "סליחה", "להתראות",
            "כן", "לא", "בסדר", "מצוין", "טוב"
        ],
        "phonetic_patterns": {
            "gutturals": r"[עחה]",
            "dagesh": r"\w{2,}",
            "schwa": r"ְ"
        },
        "grammatical_patterns": [
            r"(?i)\bה\w+\b",      # Definite article
            r"(?i)\b\w+ים\b",     # Masculine plural
            r"(?i)\b\w+ות\b"      # Feminine plural
        ]
    },

    "Amharic": {
        "word_patterns": r"\b(እና|ግን|ወይም|ስለ|እንደ)\b",
        "vocabulary": [
            "ሰላም", "አመሰግናለሁ", "እባክሽ/ህ", "ይቅርታ", "ደህና ሁን",
            "አዎ", "አይ", "ጥሩ", "እሺ", "በጣም"
        ],
        "phonetic_patterns": {
            "ejectives": r"[ጵጥጭጽፅ]",
            "gemination": r"(\w)\1",
            "labialization": r"[ሏቿኳጓ]"
        },
        "grammatical_patterns": [
            r"(?i)\b\w+አል\b",     # Negative
            r"(?i)\b\w+ኛል\b",     # Present
            r"(?i)\b\w+ዎች\b"      # Plural
        ]
    },

    # KOREANIC FAMILY
    "Korean": {
        "word_patterns": r"\b(그리고|하지만|또는|왜|어떻게)\b",
        "vocabulary": [
            "감사합니다", "괜찮습니다", "미안합니다", "안녕하세요", 
            "네", "아니요", "좋아요", "알겠습니다", "잘"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[아오우]|[어으이]",
            "consonant_assimilation": r"ㄱㄴ|ㄱㅁ|ㄱㄹ",
            "final_consonants": r"[ㄱㄴㄷㄹㅁㅂㅇ]$"
        },
        "grammatical_patterns": [
            r"(?i)\b\w+습니다\b",  # Formal polite
            r"(?i)\b\w+요\b",      # Informal polite
            r"(?i)\b\w+고\b"       # Conjunctive
        ]
    },

    # MONGOLIC FAMILY
    "Mongolian": {
        "word_patterns": r"\b(бас|харин|эсвэл|яагаад|хэрхэн)\b",
        "vocabulary": [
            "баярлалаа", "зүгээр", "уучлаарай", "сайн байна уу",
            "тийм", "үгүй", "сайн", "за", "болж байна"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[аоуы]|[эөүи]",
            "long_vowels": r"[аэиоөуү]{2}",
            "palatalization": r"[нлт]ь"
        },
        "grammatical_patterns": [
            r"(?i)\b\w+сан\b",     # Past tense
            r"(?i)\b\w+даг\b",     # Habitual
            r"(?i)\b\w+уд\b"       # Plural
        ]
    },

    # TAI-KADAI FAMILY
    "Thai": {
        "word_patterns": r"\b(และ|แต่|หรือ|ทำไม|อย่างไร)\b",
        "vocabulary": [
            "ขอบคุณ", "ไม่เป็นไร", "ขอโทษ", "สวัสดี",
            "ใช่", "ไม่", "ดี", "ตกลง", "เข้าใจ"
        ],
        "phonetic_patterns": {
            "tones": r"[่้๊๋]",
            "vowel_length": r"[าิีึืุู]",
            "final_consonants": r"[งมนยวบด]$"
        },
        "grammatical_patterns": [
            r"(?i)\bจะ\w+\b",      # Future marker
            r"(?i)\bกำลัง\w+\b",    # Progressive
            r"(?i)\b\w+ๆ\b"        # Reduplication
        ]
    },

    # KARTVELIAN FAMILY
    "Georgian": {
        "word_patterns": r"\b(და|მაგრამ|ან|რატომ|როგორ)\b",
        "vocabulary": [
            "გმადლობთ", "არაფრის", "ბოდიში", "გამარჯობა",
            "კი", "არა", "კარგი", "გასაგებია", "რა თქმა უნდა"
        ],
        "phonetic_patterns": {
            "ejectives": r"[პტკწც]'",
            "consonant_clusters": r"[მნრლ]{2,}",
            "stress_pattern": r"\w+ი\b"
        },
        "grammatical_patterns": [
            r"(?i)\b\w+ებ\b",      # Plural
            r"(?i)\b\w+ის\b",      # Genitive
            r"(?i)\b\w+ში\b"       # In/into
        ]
    },"German": {
        "word_patterns": r"\b(also|ja|nein|doch|mal)\b",
        "vocabulary": [
            "genau", "sehr", "natürlich", "vielleicht", "schon",
            "aber", "dann", "jetzt", "heute", "hier", "dort",
            "bitte", "danke", "tschüss", "auf wiedersehen"
        ],
        "phonetic_patterns": {
            "final_devoicing": r"[bdg]\b",
            "ch_sound": r"ch\b",
            "umlauts": r"[äöüß]"
        },
        "grammatical_patterns": [
            r"(?i)\b(haben|sein)\s+\w+en\b",  # Perfect tense structure
            r"\b\w+en\b$",                     # Verb infinitives
            r"(?i)\bzu\s+\w+en\b"             # zu + infinitive
        ]
    },
    "Dutch": {
        "word_patterns": r"\b(wel|even|toch|maar|nog)\b",
        "vocabulary": [
            "lekker", "gezellig", "hoor", "dus", "maar",
            "even", "gewoon", "wel", "natuurlijk", "helemaal",
            "eigenlijk", "best", "prima", "graag"
        ],
        "phonetic_patterns": {
            "ui_sound": r"ui",
            "ij_sound": r"ij",
            "g_sound": r"\bg\w+"
        },
        "grammatical_patterns": [
            r"(?i)\b(hebben|zijn)\s+ge\w+\b",
            r"\bge\w+t\b",
            r"(?i)\bte\s+\w+en\b"
        ]
    },

    # Romance Branch
    "French": {
        "word_patterns": r"\b(donc|alors|voilà|quoi|bien)\b",
        "vocabulary": [
            "bon", "alors", "voilà", "donc", "quoi",
            "enfin", "bref", "ben", "euh", "quand même",
            "plutôt", "franchement", "effectivement"
        ],
        "phonetic_patterns": {
            "nasal_vowels": r"[aeiou]n\b",
            "liaison": r"\b\w+s\s+[aeiou]",
            "silent_letters": r"\w[tdsp]\b"
        },
        "grammatical_patterns": [
            r"(?i)\bne\s+\w+\s+pas\b",
            r"(?i)\bil\s+y\s+a\b",
            r"(?i)\bc'est\b"
        ]
    },
    "Spanish": {
        "word_patterns": r"\b(pues|entonces|bueno|vale|oye)\b",
        "vocabulary": [
            "vale", "bueno", "pues", "oye", "mira",
            "claro", "venga", "hombre", "tío", "tía",
            "guay", "genial", "vale", "hala"
        ],
        "phonetic_patterns": {
            "ll_sound": r"ll",
            "ñ_sound": r"ñ",
            "silent_h": r"\bh\w+"
        },
        "grammatical_patterns": [
            r"(?i)\besta(r|s|mos|n)\b",
            r"(?i)\bhaber\s+\w+do\b",
            r"(?i)\blo\s+que\b"
        ]
    },

    # SINO-TIBETAN FAMILY
    "Mandarin": {
        "word_patterns": r"\b(的|了|吧|呢|啊)\b",
        "vocabulary": [
            "好的", "那个", "这个", "就是", "没有",
            "可以", "不要", "真的", "什么", "怎么",
            "为什么", "所以", "但是", "因为"
        ],
        "phonetic_patterns": {
            "tones": r"[āáǎà]",
            "final_particles": r"[吗呢啊吧]$",
            "er_sound": r"儿$"
        },
        "grammatical_patterns": [
            r"(?i)\b[在正]\s*\w+",  # Progressive aspect
            r"(?i)\b了\s*\w+了\b",   # Completed action
            r"(?i)\b都\s*\w+\b"      # Universal quantifier
        ]
    },

    # JAPONIC FAMILY
    "Japanese": {
        "word_patterns": r"\b(です|ます|けど|って|ね)\b",
        "vocabulary": [
            "はい", "いいえ", "すみません", "ありがとう", "お願いします",
            "そうですか", "なるほど", "ごめんなさい", "大丈夫", "よろしく"
        ],
        "phonetic_patterns": {
            "long_vowels": r"[あいうえお]ー",
            "syllable_structure": r"[かきくけこ]",
            "pitch_accent": r"\w+っ\w+"
        },
        "grammatical_patterns": [
            r"(?i)\b\w+ています\b",
            r"(?i)\b\w+んです\b",
            r"(?i)\b\w+ようです\b"
        ]
    },

    # ARABIC FAMILY
    "Modern Standard Arabic": {
        "word_patterns": r"\b(يا|في|من|على|إلى)\b",
        "vocabulary": [
            "نعم", "لا", "شكراً", "من فضلك", "السلام عليكم",
            "إن شاء الله", "الحمد لله", "مرحباً", "مع السلامة"
        ],
        "phonetic_patterns": {
            "emphatic_consonants": r"[صضطظ]",
            "pharyngeal_sounds": r"[حع]",
            "long_vowels": r"[اوي]"
        },
        "grammatical_patterns": [
            r"(?i)\bال\w+\b",         # Definite article
            r"(?i)\b\w+ون\b",         # Masculine plural
            r"(?i)\b\w+ات\b"          # Feminine plural
        ]
    },

    # DRAVIDIAN FAMILY
    "Tamil": {
        "word_patterns": r"\b(ஆமா|இல்லை|சரி|ஏன்|என்ன)\b",
        "vocabulary": [
            "வணக்கம்", "நன்றி", "மன்னிக்கவும்", "சரி",
            "பரவாயில்லை", "புரிகிறது", "பாருங்கள்"
        ],
        "phonetic_patterns": {
            "retroflex": r"[டணரல]",
            "aspirated": r"க்ஹ",
            "vowel_harmony": r"[அஆஇஈஉஊ]"
        },
        "grammatical_patterns": [
            r"(?i)\b\w+கிறேன்\b",    # Present tense
            r"(?i)\b\w+வேன்\b",      # Future tense
            r"(?i)\b\w+தான்\b"       # Emphasis marker
        ]
    },

    # SLAVIC BRANCH
    "Russian": {
        "word_patterns": r"\b(ну|вот|же|да|нет)\b",
        "vocabulary": [
            "хорошо", "спасибо", "пожалуйста", "извините",
            "конечно", "точно", "правда", "ладно", "давай"
        ],
        "phonetic_patterns": {
            "palatalization": r"[бвгдзклмнпрстфх]ь",
            "vowel_reduction": r"о|е",
            "consonant_clusters": r"\w{3,}"
        },
        "grammatical_patterns": [
            r"(?i)\b\w+ть\b",         # Verb infinitive
            r"(?i)\b\w+ся\b",         # Reflexive verbs
            r"(?i)\b\w+[ыи]\b"        # Plural nouns
        ]
    },

    # AUSTRONESIAN FAMILY
    "Indonesian": {
        "word_patterns": r"\b(sudah|belum|akan|sedang|lagi)\b",
        "vocabulary": [
            "iya", "tidak", "terima kasih", "sama-sama", "permisi",
            "maaf", "silakan", "tolong", "selamat", "bagus"
        ],
        "phonetic_patterns": {
            "ng_sound": r"ng",
            "stress_pattern": r"\w+kan\b",
            "diphthongs": r"[aeiou][aeiou]"
        },
        "grammatical_patterns": [
            r"(?i)\bme\w+kan\b",      # Transitive verbs
            r"(?i)\bber\w+\b",        # Intransitive verbs
            r"(?i)\b\w+-\w+\b"        # Reduplications
        ]
    },

    # TURKIC FAMILY
    "Turkish": {
        "word_patterns": r"\b(evet|hayır|tamam|şey|yani)\b",
        "vocabulary": [
            "merhaba", "teşekkürler", "lütfen", "affedersiniz",
            "tabii", "elbette", "peki", "pardon", "güzel"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[aeıioöuü]",
            "consonant_harmony": r"[ptçkfsşh][bdgcv]",
            "final_devoicing": r"[bdgcz]\b"
        },
        "grammatical_patterns": [
            r"(?i)\b\w+yor\b",        # Present continuous
            r"(?i)\b\w+mek\b",        # Infinitive
            r"(?i)\b\w+lar\b"         # Plural
        ]
    },

    # PERSIAN FAMILY
    "Farsi": {
        "word_patterns": r"\b(بله|خیر|باشه|چطور|خوب)\b",
        "vocabulary": [
            "سلام", "ممنون", "خواهش می‌کنم", "ببخشید",
            "حتماً", "البته", "چشم", "قربان", "عالی"
        ],
        "phonetic_patterns": {
            "ezafe": r"\s+[ِی]\s",
            "stress_pattern": r"\w+ید\b",
            "consonant_clusters": r"\w{2,}"
        },
        "grammatical_patterns": [
            r"(?i)\bمی‌\w+\b",        # Present tense marker
            r"(?i)\b\w+است\b",        # To be
            r"(?i)\b\w+‌ها\b"         # Plural marker
        ]
    },"Luo": {
        "word_patterns": r"\b(to|kata|kendo|nango|nade)\b",
        "vocabulary": [
            "oyawore", "erokamano", "akwaye", "ber nade",
            "ee", "ooyo", "ber", "adhi", "oriti"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[aeiou]+",
            "tone_patterns": r"[áàâ]",
            "final_consonants": r"[mnŋ]$"
        },
        "grammatical_patterns": [
            r"\w+o\b",       # Present tense
            r"\w+e\b",       # Past tense
            r"\w+ni\b"       # Future tense
        ]
    },

    # SALISHAN FAMILY
    "Halkomelem": {
        "word_patterns": r"\b(ye|tl'|kw'|te|tset)\b",
        "vocabulary": [
            "háy̓ kw'a", "kw'ets'i", "í:mex", "éy",
            "híth", "éwe", "kw'áy", "tl'ó", "stl'í"
        ],
        "phonetic_patterns": {
            "glottalized": r"[ptkcqmwnlyw]'",
            "lateral_affricates": r"tl'|ƛ",
            "pharyngeals": r"ʕ|ħ"
        },
        "grammatical_patterns": [
            r"\w+em\b",      # Intransitive
            r"\w+et\b",      # Transitive
            r"\w+elh\b"      # Past tense
        ]
    },

    # HMONG-MIEN FAMILY
    "Hmong": {
        "word_patterns": r"\b(thiab|tab|sis|vim|li|cas)\b",
        "vocabulary": [
            "ua tsaug", "tsis ua li cas", "thov txim", "nyob zoo",
            "yog", "tsis yog", "zoo", "mus", "los"
        ],
        "phonetic_patterns": {
            "tones": r"[bdgjsvz]$",
            "aspirated": r"th|kh|ph|qh",
            "nasalized": r"n[aeiou]"
        },
        "grammatical_patterns": [
            r"tau\s+\w+",    # Past tense
            r"yuav\s+\w+",   # Future tense
            r"tab\s+tom"     # Progressive
        ]
    },

    # TUNGUSIC FAMILY
    "Evenki": {
        "word_patterns": r"\b(tada|ekun|onnako|aŋi|ele)\b",
        "vocabulary": [
            "eme", "biral", "aya", "sagdami", "mindu",
            "eʤi", "beje", "oro", "uluki", "dagamar"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[аэиоөуү]+",
            "consonant_clusters": r"[нңмлр][кптчс]",
            "final_nasals": r"[нң]$"
        },
        "grammatical_patterns": [
            r"\w+ран\b",     # Present tense
            r"\w+чан\b",     # Past tense
            r"\w+ʤaңан\b"    # Future tense
        ]
    },

    # CHIBCHAN FAMILY
    "Kuna": {
        "word_patterns": r"\b(degi|igi|geb|bia|ibu)\b",
        "vocabulary": [
            "nuedi", "dog nuedi", "weligwa", "be nae",
            "eye", "suli", "nued", "gole", "an be"
        ],
        "phonetic_patterns": {
            "nasalization": r"[ãẽĩõũ]",
            "stress_pattern": r"\w+́\b",
            "glottalization": r"'"
        },
        "grammatical_patterns": [
            r"\w+mali\b",    # Present
            r"\w+sa\b",      # Past
            r"\w+oe\b"       # Future
        ]
    },

    # SIOUAN FAMILY
    "Lakota": {
        "word_patterns": r"\b(na|čha|yuŋkȟáŋ|tȟkȟá|héčha)\b",
        "vocabulary": [
            "pilamaya", "tokša ake", "čhaŋté wašté", "háu",
            "hó", "hiyá", "wašté", "lila", "tȟáŋka"
        ],
        "phonetic_patterns": {
            "ejectives": r"[ptkčs]'",
            "aspirated": r"[ptkčs]h",
            "nasal_vowels": r"[ąį̨ų]"
        },
        "grammatical_patterns": [
            r"\w+pi\b",      # Plural
            r"\w+ktA\b",     # Future
            r"\w+šni\b"      # Negative
        ]
    },

    # URALIC - SAMOYED BRANCH
    "Nenets": {
        "word_patterns": r"\b(тарем|ңамгэ|ханяна|хэбидя|тедахав)\b",
        "vocabulary": [
            "лакамбой", "ңарка вада", "хаерˮ", "сава",
            "теда", "яңгу", "мерця", "яля", "пи"
        ],
        "phonetic_patterns": {
            "glottal_stop": r"ˮ",
            "nasals": r"[ңмн]",
            "vowel_harmony": r"[аоуыэи]+"
        },
        "grammatical_patterns": [
            r"\w+дм'\b",     # First person
            r"\w+сь\b",      # Past tense
            r"\w+ңэ\b"       # Dative
        ]
    },

    # HOKAN FAMILY
    "Washo": {
        "word_patterns": r"\b(ga|di|mi|ʔum|hádi)\b",
        "vocabulary": [
            "míʔi", "dewp'áʔi", "dáʔaw", "ʔumʔáyʔi",
            "háʔa", "géwe", "dímeʔ", "lémeʔ", "ʔímeʔ"
        ],
        "phonetic_patterns": {
            "glottalized": r"[ptkcmnwy]'",
            "stress": r"[áéíóú]",
            "glottal_stop": r"ʔ"
        },
        "grammatical_patterns": [
            r"\w+yi\b",      # Present
            r"\w+aʔ\b",      # Past
            r"\w+lu\b"       # Future
        ]
    },

    # IROQUOIAN FAMILY
    "Cherokee": {
        "word_patterns": r"\b(ale|howa|nvdi|gado|igvyi)\b",
        "vocabulary": [
            "osiyo", "wado", "donadagohvi", "tohiju",
            "nvwa", "tla", "osti", "usdi", "uwo"
        ],
        "phonetic_patterns": {
            "nasalization": r"[ãẽĩõũ]",
            "tone": r"[́̀̌̂]",
            "aspiration": r"[tkg]h"
        },
        "grammatical_patterns": [
            r"\w+ga\b",      # Present
            r"\w+oi\b",      # Past
            r"\w+di\b"       # Future
        ]
    },

    # CHUKOTKO-KAMCHATKAN FAMILY
    "Chukchi": {
        "word_patterns": r"\b(ынкъам|ытри|миңкри|иңқун|рэқы)\b",
        "vocabulary": [
            "ытлён", "вальэ", "қэлғи", "мытык", "тэгэлғын",
            "ии", "вэнқо", "нымэйыңқин", "гым", "мури"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[аоуэи]+",
            "consonant_clusters": r"[йңқғвл][тпкмн]",
            "final_consonants": r"[нңқт]$"
        },
        "grammatical_patterns": [
            r"\w+ркын\b",    # Present
            r"\w+гъэ\b",     # Past
            r"\w+ңы\b"       # Future
        ]
    },"Cree": {
        "word_patterns": r"\b(êkwa|mâka|ahpo|tânisi|tânêhki)\b",
        "vocabulary": [
            "tânisi", "ay-hay", "kinanâskomitin", "wâciyê",
            "êha", "namôya", "miywâsin", "maskihkiy", "wâpan"
        ],
        "phonetic_patterns": {
            "long_vowels": r"[âêîôû]",
            "consonant_clusters": r"[hkmnst][kwty]",
            "final_consonants": r"[kmnst]$"
        },
        "grammatical_patterns": [
            r"\w+wak\b",     # Animate plural
            r"\w+win\b",     # Nominalization
            r"\w+pan\b"      # Past tense
        ]
    },

    # ATHABASKAN FAMILY
    "Navajo": {
        "word_patterns": r"\b(dóó|ndi|éí|háálá|háago)\b",
        "vocabulary": [
            "yáʼátʼééh", "ahéheeʼ", "nizhóní", "hózǫ́",
            "aoo'", "dooda", "ayóo", "nihaa", "yá"
        ],
        "phonetic_patterns": {
            "tone": r"[́̀]",
            "nasalization": r"[ą̨į̨ǫ̨ų̨]",
            "glottalization": r"[dltszkgy]'"
        },
        "grammatical_patterns": [
            r"\w+ígíí\b",    # Nominalization
            r"\w+go\b",      # Subordinate
            r"\w+į́į́\b"       # Past perfective
        ]
    },

    # ARAWAKAN FAMILY
    "Garifuna": {
        "word_patterns": r"\b(luma|dan|lun|ida|ligiya)\b",
        "vocabulary": [
            "buiti", "seremein", "mabuiga", "uwagu",
            "áu", "máma", "buidu", "fulasu", "haruga"
        ],
        "phonetic_patterns": {
            "stress": r"[áéíóú]",
            "nasalization": r"[ãẽĩõũ]",
            "length": r"([aeiou])\1"
        },
        "grammatical_patterns": [
            r"\w+tina\b",    # Future
            r"\w+bai\b",     # Past
            r"\w+tiña\b"     # Conditional
        ]
    },

    # MAYAN FAMILY
    "K'iche'": {
        "word_patterns": r"\b(are|rech|chi|rumal|jasche)\b",
        "vocabulary": [
            "maltyox", "utz", "sachaj", "xaq", 
            "je'", "man", "nim", "saq", "q'eq"
        ],
        "phonetic_patterns": {
            "glottalized": r"[ptkcqb]'",
            "ejectives": r"[PTKCQ]'",
            "vowel_length": r"[aeiou]:"
        },
        "grammatical_patterns": [
            r"\w+ik\b",      # Intransitive
            r"\w+aj\b",      # Agent nouns
            r"\w+em\b"       # Participle
        ]
    },

    # NIGER-CONGO - KRU BRANCH
    "Bété": {
        "word_patterns": r"\b(ni|ka|le|ko|sa)\b",
        "vocabulary": [
            "kɔ́ɔ́", "gbɛ̀lɛ̀", "yálá", "zìzì",
            "ɛ̀ɛ̀", "ɔ̀ɔ̀", "kpá", "gbɔ́", "yɔ́"
        ],
        "phonetic_patterns": {
            "tones": r"[́̀]",
            "labiovelars": r"[kg]b|[kg]p",
            "vowel_harmony": r"[ɛɔ]|[ie]"
        },
        "grammatical_patterns": [
            r"\w+lɛ\b",      # Perfect
            r"\w+ka\b",      # Future
            r"\w+ni\b"       # Progressive
        ]
    },

    # URALIC - FINNIC BRANCH
    "Veps": {
        "word_patterns": r"\b(i|ka|vai|miše|kut)\b",
        "vocabulary": [
            "tervhen", "spasib", "prostkat", "hüvä",
            "ka", "ei", "čoma", "laske", "püštta"
        ],
        "phonetic_patterns": {
            "palatalization": r"[tdnl]'",
            "vowel_harmony": r"[aou]|[äöy]",
            "gemination": r"(\w)\1"
        },
        "grammatical_patterns": [
            r"\w+b\b",       # Present
            r"\w+i\b",       # Past
            r"\w+škande\b"   # Conditional
        ]
    },

    # AUSTRONESIAN - OCEANIC BRANCH
    "Fijian": {
        "word_patterns": r"\b(ka|se|ni|mai|kei)\b",
        "vocabulary": [
            "bula", "vinaka", "kerekere", "moce",
            "io", "sega", "totoka", "levu", "lailai"
        ],
        "phonetic_patterns": {
            "prenasalized": r"[mbndŋg]",
            "vowel_length": r"[aeiou]{2}",
            "stress": r"\w+a\b"
        },
        "grammatical_patterns": [
            r"e\s+\w+",      # Present
            r"sa\s+\w+",     # Past
            r"na\s+\w+"      # Future
        ]
    },

    # ISOLATE
    "Burushaski": {
        "word_patterns": r"\b(ke|ki|ko|ta|be)\b",
        "vocabulary": [
            "salaam", "bayé", "šukria", "halkiš",
            "haa", "bésa", "mubaarak", "biṣár", "théego"
        ],
        "phonetic_patterns": {
            "retroflex": r"[ṭḍṣ]",
            "aspirated": r"[ptkc]h",
            "vowel_length": r"[aeiou]:"
        },
        "grammatical_patterns": [
            r"\w+um\b",      # Present
            r"\w+an\b",      # Past
            r"\w+imi\b"      # Future
        ]
    },

    # SINO-TIBETAN - LOLO-BURMESE BRANCH
    "Lahu": {
        "word_patterns": r"\b(lâ|mà|qo|leh|ve)\b",
        "vocabulary": [
            "a-bô-ma", "ha-leh", "dà-là", "g'â",
            "hî", "mâ", "yâ", "chɨ", "nɔ̂"
        ],
        "phonetic_patterns": {
            "tones": r"[̂̀́̌]",
            "aspirated": r"[ptk]h",
            "nasalization": r"[ãẽĩõũ]"
        },
        "grammatical_patterns": [
            r"\w+ve\b",      # Present
            r"\w+tà\b",      # Past
            r"\w+leh\b"      # Perfect
        ]
    },

    # TRANS-NEW GUINEA FAMILY
    "Enga": {
        "word_patterns": r"\b(dee|doko|ongo|aipa|dupa)\b",
        "vocabulary": [
            "waa", "yaka", "emba", "andake",
            "kini", "daa", "epe", "koo", "paka"
        ],
        "phonetic_patterns": {
            "vowel_length": r"[aeiou]{2}",
            "stress_pattern": r"\w+pe\b",
            "tone": r"[́̀]"
        },
        "grammatical_patterns": [
            r"\w+nge\b",     # Present
            r"\w+pu\b",      # Past
            r"\w+ta\b"       # Future
        ]
    },
     "Yakut": {
        "word_patterns": r"\b(уонна|эбэтэр|да|дуо|хайдах)\b",
        "vocabulary": [
            "үтүө күнүнэн", "баһыыба", "бырастыы", "көрсүөххэ",
            "ээ", "суох", "үчүгэй", "сөп", "үөрүү"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[аоуыэөүи]+",
            "long_vowels": r"[аааоооуууыыыэээөөөүүүиии]",
            "diphthongs": r"(ыа|иэ|уо|үө)"
        },
        "grammatical_patterns": [
            r"\w+ар\b",      # Present
            r"\w+та\b",      # Past
            r"\w+ыа\b"       # Future
        ]
    },

    # AUSTRO-ASIATIC - MUNDA BRANCH
    "Santali": {
        "word_patterns": r"\b(ar|do|ente|cet|okare)\b",
        "vocabulary": [
            "johar", "marsal", "dạ", "hola",
            "hẽ", "bã", "bese", "hijuḱ", "seteḱ"
        ],
        "phonetic_patterns": {
            "glottalization": r"[ḱ]",
            "checked_vowels": r"[ạẹịọụ]",
            "nasalization": r"[ãẽĩõũ]"
        },
        "grammatical_patterns": [
            r"\w+keya\b",    # Present
            r"\w+lena\b",    # Past
            r"\w+aka\b"      # Perfect
        ]
    },

    # NIGER-CONGO - ADAMAWA BRANCH
    "Mumuye": {
        "word_patterns": r"\b(ne|ka|do|ba|mi)\b",
        "vocabulary": [
            "soso", "yaawe", "kpahi", "doro",
            "ee", "ayi", "mai", "kpan", "ren"
        ],
        "phonetic_patterns": {
            "tone_patterns": r"[́̀̂]",
            "labial_velars": r"kp|gb",
            "nasalization": r"[ãẽĩõũ]"
        },
        "grammatical_patterns": [
            r"\w+wa\b",      # Present
            r"\w+ye\b",      # Past
            r"\w+ro\b"       # Future
        ]
    },

    # AFROASIATIC - CUSHITIC BRANCH
    "Somali": {
        "word_patterns": r"\b(iyo|lakin|ama|maxaa|sidee)\b",
        "vocabulary": [
            "nabadgelyo", "mahadsanid", "cafis", "subax wanaagsan",
            "haa", "maya", "wanaagsan", "hagaag", "aad"
        ],
        "phonetic_patterns": {
            "pharyngeal": r"[ħʕ]",
            "tone": r"[́̀]",
            "gemination": r"(\w)\1"
        },
        "grammatical_patterns": [
            r"\w+ayaa\b",    # Focus marker
            r"\w+tay\b",     # Past feminine
            r"\w+kay\b"      # Past masculine
        ]
    },

    # JAPONIC - RYUKYUAN BRANCH
    "Okinawan": {
        "word_patterns": r"\b(yaa|shi|ya|ni|ga)\b",
        "vocabulary": [
            "haisai", "nifeedeebiru", "mensooree", "uugami",
            "uu", "iinee", "churaasan", "yutasarun", "ganjuu"
        ],
        "phonetic_patterns": {
            "glottalization": r"[ʔ]",
            "long_vowels": r"[aeiou]{2}",
            "pitch_accent": r"\w+n\b"
        },
        "grammatical_patterns": [
            r"\w+un\b",      # Present
            r"\w+tan\b",     # Past
            r"\w+yun\b"      # Progressive
        ]
    },

    # NIGER-CONGO - GUR BRANCH
    "Dagbani": {
        "word_patterns": r"\b(ni|ka|bee|din|wula)\b",
        "vocabulary": [
            "deseba", "mba", "naawuni", "antire",
            "ee", "ayi", "viela", "kaman", "pahi"
        ],
        "phonetic_patterns": {
            "tone": r"[́̀̂]",
            "nasalization": r"[ãẽĩõũ]",
            "vowel_harmony": r"[aeiou]+"
        },
        "grammatical_patterns": [
            r"\w+ra\b",      # Past
            r"\w+ya\b",      # Future
            r"\w+mi\b"       # Habitual
        ]
    },

    # AUSTRONESIAN - FORMOSAN BRANCH
    "Amis": {
        "word_patterns": r"\b(ato|ano|han|ko|to)\b",
        "vocabulary": [
            "nga'ay ho", "salamat", "pa'or", "kapah",
            "hay", "caay", "malakaka", "henay", "mamang"
        ],
        "phonetic_patterns": {
            "glottal_stop": r"'",
            "stress_pattern": r"\w+ay\b",
            "consonant_clusters": r"[mnŋ][ptk]"
        },
        "grammatical_patterns": [
            r"\w+en\b",      # Focus object
            r"\w+an\b",      # Focus location
            r"\w+ay\b"       # Focus actor
        ]
    },

    # SINO-TIBETAN - BODISH BRANCH
    "Dzongkha": {
        "word_patterns": r"\b(དང|ཡང|མས|འདི|ག)\b",
        "vocabulary": [
            "གཏང་རག་ཞུ", "བཀྲ་ཤིས་བདེ་ལེགས", "དགོངས་དག", "ག་དེ་སྨོ",
            "ལགས", "མེན", "ལེགས་ཤོམ", "འོང", "བཀའ་དྲིན་ཆེ"
        ],
        "phonetic_patterns": {
            "tone": r"[̄́̀]",
            "aspirated": r"[པཕཁཆཐ]",
            "nasalization": r"[ངཉཎནམ]"
        },
        "grammatical_patterns": [
            r"\w+གི\b",      # Genitive
            r"\w+པས\b",     # Past
            r"\w+ནི\b"       # Future
        ]
    },

    # NILO-SAHARAN - NILOTIC BRANCH
    "Maasai": {
        "word_patterns": r"\b(ore|naa|amu|kake|ajo)\b",
        "vocabulary": [
            "supa", "ashe", "kotok", "endaa",
            "ee", "mme", "sidai", "keju", "tampa"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[aeiou]+",
            "tone": r"[́̀]",
            "consonant_clusters": r"[mnŋ][ptk]"
        },
        "grammatical_patterns": [
            r"\w+ita\b",     # Present
            r"\w+ta\b",      # Past
            r"\w+aki\b"      # Future
        ]
    },

    # TUPIAN - TUPI-GUARANI BRANCH
    "Nheengatu": {
        "word_patterns": r"\b(aé|yawé|mairamé|maã|awá)\b",
        "vocabulary": [
            "puranga", "marandua", "yané", "kuíri",
            "eẽ", "umbaá", "katú", "suí", "irumu"
        ],
        "phonetic_patterns": {
            "nasalization": r"[ãẽĩõũ]",
            "stress": r"[áéíóú]",
            "glottalization": r"'"
        },
        "grammatical_patterns": [
            r"\w+ana\b",     # Perfect
            r"\w+wara\b",    # Agent
            r"\w+rama\b"     # Future
        ]
    },

    "ǂHoan": {
        "word_patterns": r"\b(kí|há|ǁa|ǂa|ǃa)\b",
        "vocabulary": [
            "ǂʼāã", "ǁxóõ", "ǃáa", "ǂqχʼã",
            "ǁàa", "ǂìi", "ǃóo", "ǁàe", "kyá"
        ],
        "phonetic_patterns": {
            "clicks": r"[ǂǁǃ][ʼʰ̃ʱ]?",
            "tone": r"[́̀̂̄̌]",
            "nasalization": r"[ãẽĩõũ]"
        },
        "grammatical_patterns": [
            r"\w+ki\b",      # Present
            r"\w+ha\b",      # Past
            r"\w+ku\b"       # Future
        ]
    },

    # AUSTRALIAN - PAMA-NYUNGAN FAMILY
    "Warlpiri": {
        "word_patterns": r"\b(manu|kala|ngula|nyarrpa|ngaju)\b",
        "vocabulary": [
            "yuwayi", "lawa", "ngurrju", "wangkaya",
            "jalangu", "yarda", "kari", "yapa", "wati"
        ],
        "phonetic_patterns": {
            "retroflex": r"[ṭṇḷṛ]",
            "palatal": r"[ñjy]",
            "stress": r"\w+rla\b"
        },
        "grammatical_patterns": [
            r"\w+rni\b",     # Present
            r"\w+ja\b",      # Past
            r"\w+ku\b"       # Purposive
        ]
    },

    # GUNWINYGUAN FAMILY
    "Bininj Kun-Wok": {
        "word_patterns": r"\b(dja|wanjh|yiman|baleh|ngudda)\b",
        "vocabulary": [
            "bonj", "kamak", "yoh", "makka",
            "murrngrayek", "manme", "kunred", "balanda", "djang"
        ],
        "phonetic_patterns": {
            "glottal_stop": r"[ʔ]",
            "long_stops": r"[kk|dd|bb]",
            "nasals": r"[ŋñn]"
        },
        "grammatical_patterns": [
            r"\w+men\b",     # Present
            r"\w+ni\b",      # Past
            r"\w+yan\b"      # Future
        ]
    },

    # SEPIK FAMILY
    "Iatmul": {
        "word_patterns": r"\b(wan|ak|mbak|nyan|kwa)\b",
        "vocabulary": [
            "kap", "mbɨt", "nyaŋ", "wun",
            "kɨnɨ", "apm", "yiga", "wupma", "ndɨk"
        ],
        "phonetic_patterns": {
            "prenasalized": r"[mb|nd|ŋg]",
            "vowel_length": r"[aeiɨu]{2}",
            "word_tone": r"[́̀]"
        },
        "grammatical_patterns": [
            r"\w+gat\b",     # Present
            r"\w+wun\b",     # Past
            r"\w+kiyak\b"    # Future
        ]
    },

    # TORRICELLI FAMILY
    "Arapesh": {
        "word_patterns": r"\b(aria|bai|anan|ko|ini)\b",
        "vocabulary": [
            "yopwe", "uwahik", "wosik", "iwagigin",
            "aun", "yowi", "aria", "nabai", "shamu"
        ],
        "phonetic_patterns": {
            "tone_patterns": r"[́̀̂]",
            "labialization": r"[kgŋ]w",
            "palatalization": r"[tdns]y"
        },
        "grammatical_patterns": [
            r"\w+ak\b",      # Present
            r"\w+as\b",      # Past
            r"\w+uk\b"       # Future
        ]
    },

    # HUON GULF FAMILY
    "Yabem": {
        "word_patterns": r"\b(ma|gebe|to|me|oc)\b",
        "vocabulary": [
            "aêŋ", "gêdêŋ", "malô", "êsêac",
            "biŋ", "masi", "ŋajam", "têtac", "lau"
        ],
        "phonetic_patterns": {
            "tone": r"[̂́̀]",
            "nasalization": r"[ŋ]",
            "vowel_marks": r"[êôâ]"
        },
        "grammatical_patterns": [
            r"\w+ac\b",      # Present
            r"\w+gac\b",     # Past
            r"\w+na\b"       # Future
        ]
    },

    # EAST BOUGAINVILLE FAMILY
    "Nasioi": {
        "word_patterns": r"\b(tewa|ninka|ning|deto|baka)\b",
        "vocabulary": [
            "dotu", "tamang", "sipung", "daamaang",
            "ehe", "aung", "tampara", "naning", "boto"
        ],
        "phonetic_patterns": {
            "nasalization": r"[ŋ]",
            "vowel_length": r"[aeiou]{2}",
            "stress": r"\w+ang\b"
        },
        "grammatical_patterns": [
            r"\w+ing\b",     # Present
            r"\w+ung\b",     # Past
            r"\w+aing\b"     # Future
        ]
    },

    # CENTRAL SOLOMONS FAMILY
    "Savosavo": {
        "word_patterns": r"\b(bo|to|ko|lo|ze)\b",
        "vocabulary": [
            "ate", "koba", "leme", "tona",
            "ko", "mane", "pai", "zogi", "tini"
        ],
        "phonetic_patterns": {
            "stress_pattern": r"\w+a\b",
            "consonant_clusters": r"[mng][bdt]",
            "final_vowels": r"[aeiou]$"
        },
        "grammatical_patterns": [
            r"\w+tu\b",      # Present
            r"\w+gh\b",      # Past
            r"\w+li\b"       # Future
        ]
    },

    # LOWER SEPIK-RAMU FAMILY
    "Yimas": {
        "word_patterns": r"\b(na|ma|kay|api|wan)\b",
        "vocabulary": [
            "apwi", "nampi", "krayŋ", "mpaŋ",
            "arm", "awa", "ŋayk", "mpuk", "tpuk"
        ],
        "phonetic_patterns": {
            "prenasalized": r"[mp|nt|ŋk]",
            "consonant_clusters": r"[ptk][wy]",
            "stress": r"[́]"
        },
        "grammatical_patterns": [
            r"\w+nan\b",     # Present
            r"\w+wat\b",     # Past
            r"\w+kayan\b"    # Future
        ]
    },

    # BORDER FAMILY
    "Imonda": {
        "word_patterns": r"\b(po|fe|uol|sue|ago)\b",
        "vocabulary": [
            "kafli", "aio", "maga", "tobto",
            "kuo", "ale", "sabla", "edu", "peha"
        ],
        "phonetic_patterns": {
            "nasalization": r"[ãẽĩõũ]",
            "glottalization": r"[ʔ]",
            "vowel_length": r"[aeiou]{2}"
        },
        "grammatical_patterns": [
            r"\w+fla\b",     # Present
            r"\w+na\b",      # Past
            r"\w+fe\b"       # Future
        ]
    },
    "Kayardild": {
        "word_patterns": r"\b(ngada|bilda|kada|bartha|mirra)\b",
        "vocabulary": [
            "kiija", "ngaaka", "warirra", "bukawa",
            "yuuda", "birdin", "kunawuna", "ngada", "thaldi"
        ],
        "phonetic_patterns": {
            "laminal_stops": r"[ṯṉ]",
            "retroflexes": r"[ṭṇḷṛ]",
            "long_vowels": r"[aeiou]{2}"
        },
        "grammatical_patterns": [
            r"\w+nangku\b",  # Present
            r"\w+jarri\b",   # Past
            r"\w+kuru\b"     # Future
        ]
    },

    # GREAT ANDAMANESE FAMILY
    "Önge": {
        "word_patterns": r"\b(ene|ara|ete|idi|uba)\b",
        "vocabulary": [
            "ekebe", "čirike", "akaṛa", "uǰuwe",
            "ele", "tawo", "mikwe", "čapwe", "bēu"
        ],
        "phonetic_patterns": {
            "retroflex": r"[ṭḍṇṛ]",
            "vowel_nasalization": r"[ãẽĩõũ]",
            "glottal": r"[ʔ]"
        },
        "grammatical_patterns": [
            r"\w+be\b",      # Present
            r"\w+ta\b",      # Past
            r"\w+le\b"       # Future
        ]
    },

    # YUKAGHIR FAMILY
    "Tundra Yukaghir": {
        "word_patterns": r"\b(taŋ|ile|tet|elen|monut)\b",
        "vocabulary": [
            "köde", "ile", "čumu", "sukun",
            "eː", "eːle", "metul", "amaː", "jaːn"
        ],
        "phonetic_patterns": {
            "vowel_harmony": r"[aouəi]+",
            "long_vowels": r"[aeiou]ː",
            "palatalization": r"[tdnl]'"
        },
        "grammatical_patterns": [
            r"\w+ŋa\b",      # Present
            r"\w+l'el\b",    # Past
            r"\w+te\b"       # Future
        ]
    },

    # NORTH CAUCASIAN FAMILY
    "Tsez": {
        "word_patterns": r"\b(sis|kid|zow|dow|ħal)\b",
        "vocabulary": [
            "bečed", "žek'u", "ħalt'i", "nesta",
            "hudzi", "ānu", "magalu", "elu", "šebi"
        ],
        "phonetic_patterns": {
            "ejectives": r"[ptkčc]'",
            "pharyngeals": r"[ħʕ]",
            "laterals": r"[ł]"
        },
        "grammatical_patterns": [
            r"\w+xo\b",      # Present
            r"\w+si\b",      # Past
            r"\w+no\b"       # Future
        ]
    },

    # YANOMAMIC FAMILY
    "Yanomami": {
        "word_patterns": r"\b(ipa|hei|yai|ham|kuo)\b",
        "vocabulary": [
            "hwei", "hapao", "awei", "matihi",
            "ma", "aipë", "totihitawë", "ohote", "pei"
        ],
        "phonetic_patterns": {
            "nasalization": r"[ãẽĩõũ]",
            "aspiration": r"[ptk]h",
            "tone": r"[́̀]"
        },
        "grammatical_patterns": [
            r"\w+mae\b",     # Present
            r"\w+nomai\b",   # Past
            r"\w+pë\b"       # Future
        ]
    },

    # CHAPACURAN FAMILY
    "Wari'": {
        "word_patterns": r"\b(na|cao|tam|xi|pan)\b",
        "vocabulary": [
            "hwam", "carawa", "tamana", "wijima",
            "te", "pa'", "xucucun", "nein", "wao"
        ],
        "phonetic_patterns": {
            "glottal_stop": r"'",
            "labials": r"[wmb]",
            "nasalization": r"[ãẽĩõũ]"
        },
        "grammatical_patterns": [
            r"\w+ain\b",     # Present
            r"\w+ram\b",     # Past
            r"\w+con\b"      # Future
        ]
    },

    # TOTONACAN FAMILY
    "Totonac": {
        "word_patterns": r"\b(chu|li|wa|na|pi)\b",
        "vocabulary": [
            "paxkat", "kilin", "taskujut", "tzey",
            "je'e", "ni'", "tlan", "chix", "laka"
        ],
        "phonetic_patterns": {
            "glottalization": r"'",
            "laterals": r"[lɬ]",
            "affricates": r"[ts|tʃ]"
        },
        "grammatical_patterns": [
            r"\w+y\b",       # Present
            r"\w+lh\b",      # Past
            r"\w+na'\b"      # Future
        ]
    },

    # WAKASHAN FAMILY
    "Kwak'wala": {
        "word_patterns": r"\b(gada|lax|ʼma|dłu|gax)\b",
        "vocabulary": [
            "giáxstin", "ʼyúła", "gílakas'la", "héłkas",
            "ʼma", "k'i", "ʼnákwała", "gukw", "tlás"
        ],
        "phonetic_patterns": {
            "glottalization": r"[ptkcmnwy]'",
            "laterals": r"[ł|λ|l']",
            "labials": r"[kʷgʷxʷ]"
        },
        "grammatical_patterns": [
            r"\w+ida\b",     # Present
            r"\w+xdi\b",     # Past
            r"\w+ł\b"        # Future
        ]
    },

    # ARAUCANIAN FAMILY
    "Mapudungun": {
        "word_patterns": r"\b(fey|nga|chi|kam|welu)\b",
        "vocabulary": [
            "mari mari", "pewkayal", "küme", "chaltu",
            "may", "no", "kümelay", "müna", "feley"
        ],
        "phonetic_patterns": {
            "interdentals": r"[ð]",
            "retroflexes": r"[ʈʂ]",
            "high_vowels": r"[ɨ]"
        },
        "grammatical_patterns": [
            r"\w+n\b",       # Present
            r"\w+fu\b",      # Past
            r"\w+a\b"        # Future
        ]
    },

    # BARBACOAN FAMILY
    "Awa Pit": {
        "word_patterns": r"\b(shi|aza|mɨ|na|pai)\b",
        "vocabulary": [
            "watsal", "aishtaish", "kwazhi", "kashna",
            "au", "chi", "wat", "payan", "kima"
        ],
        "phonetic_patterns": {
            "high_central_vowel": r"[ɨ]",
            "palatalization": r"[ʃʒ]",
            "nasalization": r"[ãẽĩõũ]"
        },
        "grammatical_patterns": [
            r"\w+tui\b",     # Present
            r"\w+zi\b",      # Past
            r"\w+na\b"       # Future
        ]
    },

    "Mangarrayi": {
        "word_patterns": r"\b(nga|ja|na|wu|ba)\b",
        "vocabulary": [
            "janggin", "wurr", "ngaya", "malam",
            "yo", "minj", "garlag", "buwarraq", "ganji"
        ],
        "phonetic_patterns": {
            "retroflex": r"[ṭṇḷṛ]",
            "glottal_stop": r"[q]",
            "long_vowels": r"[aeiou]{2}"
        },
        "grammatical_patterns": [
            r"\w+ma\b",      # Present
            r"\w+ni\b",      # Past
            r"\w+wa\b"       # Future
        ]
    },

    # KADUGLI-KRONGO FAMILY
    "Krongo": {
        "word_patterns": r"\b(àkà|ìsì|nɨ́|kà|mà)\b",
        "vocabulary": [
            "káasà", "àʔàŋ", "móosò", "ńtílé",
            "ɨ́ɨ́", "ùʔùŋ", "kàràkkà", "tɨ́níŋ", "màafá"
        ],
        "phonetic_patterns": {
            "tone": r"[́̀]",
            "vowel_length": r"[aɨiu]{2}",
            "glottal_stop": r"[ʔ]"
        },
        "grammatical_patterns": [
            r"\w+ŋ\b",       # Present
            r"\w+t\b",       # Past
            r"\w+má\b"       # Future
        ]
    },

    # WEST PAPUAN FAMILY
    "Ternate": {
        "word_patterns": r"\b(ma|si|ena|sone|toma)\b",
        "vocabulary": [
            "ngone", "tarima", "suba", "ngekom",
            "iya", "hièra", "laha", "futu", "sio"
        ],
        "phonetic_patterns": {
            "prenasalization": r"[mb|nd|ŋg]",
            "stress": r"[́]",
            "diphthongs": r"[ao]e"
        },
        "grammatical_patterns": [
            r"\w+ka\b",      # Present
            r"\w+si\b",      # Past
            r"\w+osi\b"      # Future
        ]
    },

    # EAST BIRD'S HEAD FAMILY
    "Meyah": {
        "word_patterns": r"\b(rot|gij|nou|sis|mar)\b",
        "vocabulary": [
            "ofa", "iwa", "erebesa", "aksa",
            "tenten", "guru", "eskeira", "make", "ofou"
        ],
        "phonetic_patterns": {
            "vowel_sequences": r"[aeiou]{2}",
            "final_consonants": r"[fkmrst]$",
            "stress_pattern": r"\w+a\b"
        },
        "grammatical_patterns": [
            r"\w+ef\b",      # Present
            r"\w+ij\b",      # Past
            r"\w+ma\b"       # Future
        ]
    },

    # CADDOAN FAMILY
    "Pawnee": {
        "word_patterns": r"\b(ra|ti|ku|ta|wi)\b",
        "vocabulary": [
            "čaˀuh", "čiki", "kíša", "náwa",
            "aˀa", "kaˀu", "tíkuks", "šakúru", "ráriks"
        ],
        "phonetic_patterns": {
            "glottal_stop": r"[ˀ]",
            "tone": r"[́̀]",
            "aspirated": r"[čkpt]h"
        },
        "grammatical_patterns": [
            r"\w+ku\b",      # Present
            r"\w+ruk\b",     # Past
            r"\w+hi\b"       # Future
        ]
    },

    # CHIMAKUAN FAMILY
    "Quileute": {
        "word_patterns": r"\b(ti|ła|kʷi|xa|či)\b",
        "vocabulary": [
            "hoʔopał", "tala", "kʷeʔši", "yixʷal",
            "ho", "hiʔi", "t'ičit", "k'ʷay", "xʷaʔ"
        ],
        "phonetic_patterns": {
            "labialization": r"[kxƛ]ʷ",
            "glottalization": r"[ptkcƛ]'",
            "ejectives": r"[ptkcčƛ]'"
        },
        "grammatical_patterns": [
            r"\w+li\b",      # Present
            r"\w+ƛi\b",      # Past
            r"\w+či\b"       # Future
        ]
    },

    # NUCLEAR TORRICELLI FAMILY
    "Mountain Arapesh": {
        "word_patterns": r"\b(aria|bai|eik|nya|ara)\b",
        "vocabulary": [
            "yopwei", "douk", "wosik", "nyutab",
            "awas", "uwahis", "yopwi", "nyubul", "aria"
        ],
        "phonetic_patterns": {
            "palatalization": r"ny",
            "labialization": r"[kg]w",
            "vowel_length": r"[aeiou]{2}"
        },
        "grammatical_patterns": [
            r"\w+ep\b",      # Present
            r"\w+as\b",      # Past
            r"\w+uk\b"       # Future
        ]
    },

    # ZAPAROAN FAMILY
    "Arabela": {
        "word_patterns": r"\b(na|qui|jua|cua|naa)\b",
        "vocabulary": [
            "panuu", "maaji", "ritia", "quiari",
            "jaa", "maja", "maninia", "seque", "cuno"
        ],
        "phonetic_patterns": {
            "vowel_length": r"[aeiou]{2}",
            "stress": r"[́]",
            "palatalization": r"[td]y"
        },
        "grammatical_patterns": [
            r"\w+ya\b",      # Present
            r"\w+quiaa\b",   # Past
            r"\w+nu\b"       # Future
        ]
    },

    # SÁLIBAN FAMILY
    "Piaroa": {
        "word_patterns": r"\b(tʰi|də|ku|re|me)\b",
        "vocabulary": [
            "isæ̃", "čuwa", "tʰiyæ", "məræ",
            "æ̃hæ̃", "ãʔã", "mene", "wæʔæ", "kʷakʷa"
        ],
        "phonetic_patterns": {
            "nasalization": r"[ãẽĩõũæ̃]",
            "aspiration": r"[ptk]ʰ",
            "labialization": r"[pk]ʷ"
        },
        "grammatical_patterns": [
            r"\w+sa\b",      # Present
            r"\w+di\b",      # Past
            r"\w+tʰæ\b"      # Future
        ]
    },

    # GUAICURUAN FAMILY
    "Mocoví": {
        "word_patterns": r"\b(qa|na|so|ka|da)\b",
        "vocabulary": [
            "ʔaam", "nawot", "qaiʔen", "lapiɢoʔ",
            "ʔee", "saʔa", "noʔen", "ʔven", "qom"
        ],
        "phonetic_patterns": {
            "glottal_stop": r"[ʔ]",
            "uvular": r"[q]",
            "voiced_velar": r"[ɢ]"
        },
        "grammatical_patterns": [
            r"\w+tak\b",     # Present
            r"\w+ñi\b",      # Past
            r"\w+am\b"       # Future
        ]
    },
    "Nasioi": {
        "word_patterns": r"\b(teni|nka|ning|baka|tewa)\b",
        "vocabulary": [
            "dotu", "tamang", "sipung", "daamaang",
            "ee", "aung", "tampara", "naninge", "baka"
        ],
        "phonetic_patterns": {
            "nasalization": r"[ŋ]",
            "vowel_length": r"[aeiou]{2}",
            "stress": r"\w+ang\b"
        },
        "grammatical_patterns": [
            r"\w+ing\b",     # Present
            r"\w+ung\b",     # Past
            r"\w+aing\b"     # Future
        ]
    },

    # TIWI ISOLATE
    "Tiwi": {
        "word_patterns": r"\b(nga|wa|ki|ta|ji)\b",
        "vocabulary": [
            "murrana", "wuta", "kirijini", "japarra",
            "yu", "karluwu", "wurumi", "yoi", "tuwawu"
        ],
        "phonetic_patterns": {
            "retroflexes": r"[ṭṇḷṛ]",
            "glides": r"[wy]",
            "stress_pattern": r"\w+rra\b"
        },
        "grammatical_patterns": [
            r"\w+mi\b",      # Present
            r"\w+ni\b",      # Past
            r"\w+rri\b"      # Future
        ]
    },

    # EASTERN DALY FAMILY
    "Matngele": {
        "word_patterns": r"\b(nya|wu|ma|nga|ya)\b",
        "vocabulary": [
            "ngayu", "wurang", "manya", "yawa",
            "yo", "nomo", "mayawa", "tyung", "wula"
        ],
        "phonetic_patterns": {
            "nasals": r"[ŋɲ]",
            "palatals": r"ty|ny",
            "long_vowels": r"[aeiou]{2}"
        },
        "grammatical_patterns": [
            r"\w+ma\b",      # Present
            r"\w+wa\b",      # Past
            r"\w+yu\b"       # Future
        ]
    },

    # GIIMBIYU FAMILY
    "Urningangk": {
        "word_patterns": r"\b(nga|ma|na|ga|wa)\b",
        "vocabulary": [
            "ngappi", "mara", "ngaralk", "ganji",
            "yo", "wagiman", "mayali", "guya", "warri"
        ],
        "phonetic_patterns": {
            "retroflex": r"[ṛḷṇṭ]",
            "nasals": r"[ŋɲ]",
            "glides": r"[wy]"
        },
        "grammatical_patterns": [
            r"\w+ni\b",      # Present
            r"\w+rr\b",      # Past
            r"\w+yi\b"       # Future
        ]
    },

    # LIMILNGAN-WULNA FAMILY
    "Limilngan": {
        "word_patterns": r"\b(u|wi|ma|da|gi)\b",
        "vocabulary": [
            "angul", "mipil", "daway", "girrk",
            "u-yi", "ma-yi", "wunggu", "dik-ma", "u-ma"
        ],
        "phonetic_patterns": {
            "retroflex": r"[ṛḷṇṭ]",
            "nasals": r"[ŋɲ]",
            "stops": r"[bdgʔ]"
        },
        "grammatical_patterns": [
            r"\w+ma\b",      # Present
            r"\w+yi\b",      # Past
            r"\w+gi\b"       # Future
        ]
    },

    # MURA FAMILY
    "Múra": {
        "word_patterns": r"\b(pa|ka|ma|na|ta)\b",
        "vocabulary": [
            "pahi", "kanam", "matsi", "nawa",
            "ee", "paa", "muka", "tapa", "wai"
        ],
        "phonetic_patterns": {
            "nasalization": r"[ãẽĩõũ]",
            "stress": r"[́]",
            "vowel_length": r"[aeiou]{2}"
        },
        "grammatical_patterns": [
            r"\w+tsi\b",     # Present
            r"\w+pa\b",      # Past
            r"\w+na\b"       # Future
        ]
    },

    # PEBA-YAGUAN FAMILY
    "Yagua": {
        "word_patterns": r"\b(ray|jiy|sa|ni|day)\b",
        "vocabulary": [
            "júú", "ramiy", "saachi", "niyan",
            "jii", "nee", "raatu", "jiya", "day"
        ],
        "phonetic_patterns": {
            "tone": r"[́̀]",
            "vowel_length": r"[aeiou]{2}",
            "palatalization": r"[td]y"
        },
        "grammatical_patterns": [
            r"\w+jada\b",    # Present
            r"\w+siy\b",     # Past
            r"\w+ra\b"       # Future
        ]
    },

    # PUINAVE ISOLATE
    "Puinave": {
        "word_patterns": r"\b(yat|din|kot|mot|ip)\b",
        "vocabulary": [
            "yopot", "diwat", "käm", "momot",
            "häʔä", "yaʔa", "kät", "wop", "mot"
        ],
        "phonetic_patterns": {
            "glottal_stop": r"[ʔ]",
            "vowel_harmony": r"[äöü]+",
            "final_stops": r"[ptk]$"
        },
        "grammatical_patterns": [
            r"\w+ot\b",      # Present
            r"\w+in\b",      # Past
            r"\w+at\b"       # Future
        ]
    },

    # TRUMAI ISOLATE
    "Trumai": {
        "word_patterns": r"\b(ke|ka|yi|hi|fa)\b",
        "vocabulary": [
            "ain", "kuta", "yis", "hï",
            "ï'ïn", "kain", "fak", "das", "chi"
        ],
        "phonetic_patterns": {
            "glottal_stop": r"[ʔ]",
            "central_vowel": r"[ï]",
            "nasalization": r"[ãẽĩõũ]"
        },
        "grammatical_patterns": [
            r"\w+tl\b",      # Present
            r"\w+ke\b",      # Past
            r"\w+ka\b"       # Future
        ]
    },

    # WARRWA FAMILY
    "Warrwa": {
        "word_patterns": r"\b(nya|wa|ya|ma|nga)\b",
        "vocabulary": [
            "ngaya", "warli", "yarra", "mala",
            "yu", "wirra", "mindi", "karra", "bina"
        ],
        "phonetic_patterns": {
            "retroflexes": r"[ṭṇḷṛ]",
            "laterals": r"[ly]",
            "nasals": r"[ŋɲ]"
        },
        "grammatical_patterns": [
            r"\w+rri\b",     # Present
            r"\w+na\b",      # Past
            r"\w+yi\b"       # Future
        ]
    }

            

        }

    def analyze_accent(self, audio_path):
        try:
            # Transcribe audio
            result = self.model.transcribe(audio_path)
            
            # Get basic information
            transcription = result["text"]
            detected_language = result["language"]
            segments = result["segments"]
            
            # Detailed analysis
            accent_scores = self._analyze_accent_features(transcription)
            prosody_features = self._analyze_prosody(segments)
            phonetic_features = self._analyze_phonetic_patterns(transcription)
            grammatical_features = self._analyze_grammatical_patterns(transcription)
            
            # Combine all analyses
            analysis = {
                "detected_language": detected_language,
                "transcription": transcription,
                "accent_confidence_scores": accent_scores,
                "prosody_features": prosody_features,
                "phonetic_features": phonetic_features,
                "grammatical_features": grammatical_features,
                "segments": segments
            }
            
            # Determine most likely accent with confidence weighting
            weighted_scores = self._calculate_weighted_scores(
                accent_scores,
                phonetic_features,
                grammatical_features
            )
            
            likely_accent = max(weighted_scores.items(), key=lambda x: x[1])[0]
            confidence = weighted_scores[likely_accent]
            
            analysis["most_likely_accent"] = {
                "accent": likely_accent,
                "confidence": confidence,
                "confidence_breakdown": {
                    "vocabulary_match": accent_scores[likely_accent],
                    "phonetic_match": phonetic_features.get(likely_accent, 0),
                    "grammatical_match": grammatical_features.get(likely_accent, 0)
                }
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error during accent analysis: {str(e)}")
            return None

    def _analyze_accent_features(self, text):
        scores = {accent: 0.0 for accent in self.accent_patterns.keys()}
        text = text.lower()
        
        for accent, patterns in self.accent_patterns.items():
            # Vocabulary analysis
            vocab_count = sum(1 for word in patterns["vocabulary"] if word.lower() in text)
            scores[accent] += vocab_count * 2
            
            # Word pattern analysis
            if "word_patterns" in patterns:
                pattern_matches = len(re.findall(patterns["word_patterns"], text))
                scores[accent] += pattern_matches * 1.5
        
        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}
        
        return scores

    def _analyze_prosody(self, segments):
        segment_durations = []
        pause_durations = []
        speech_rates = []
        
        for i, segment in enumerate(segments):
            duration = segment["end"] - segment["start"]
            segment_durations.append(duration)
            
            words = len(segment["text"].split())
            speech_rates.append(words / duration if duration > 0 else 0)
            
            if i > 0:
                pause_duration = segment["start"] - segments[i-1]["end"]
                pause_durations.append(pause_duration)
        
        return {
            "average_segment_duration": np.mean(segment_durations),
            "average_pause_duration": np.mean(pause_durations) if pause_durations else 0,
            "average_speech_rate": np.mean(speech_rates),
            "speech_rate_variance": np.var(speech_rates),
            "rhythm_pattern": self._determine_rhythm_pattern(segment_durations, speech_rates)
        }

    def _analyze_phonetic_patterns(self, text):
        scores = {accent: 0.0 for accent in self.accent_patterns.keys()}
        text = text.lower()
        
        for accent, patterns in self.accent_patterns.items():
            if "phonetic_patterns" in patterns:
                for pattern_name, pattern in patterns["phonetic_patterns"].items():
                    matches = len(re.findall(pattern, text))
                    scores[accent] += matches
        
        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}
        
        return scores

    def _analyze_grammatical_patterns(self, text):
        scores = {accent: 0.0 for accent in self.accent_patterns.keys()}
        text = text.lower()
        
        for accent, patterns in self.accent_patterns.items():
            if "grammatical_patterns" in patterns:
                for pattern in patterns["grammatical_patterns"]:
                    matches = len(re.findall(pattern, text))
                    scores[accent] += matches
        
        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}
        
        return scores

    def _determine_rhythm_pattern(self, durations, speech_rates):
        duration_variance = np.var(durations)
        rate_variance = np.var(speech_rates)
        
        if duration_variance < 0.1 and rate_variance < 0.5:
            return "syllable-timed"
        elif duration_variance > 0.2:
            return "stress-timed"
        else:
            return "mixed"

    def _calculate_weighted_scores(self, accent_scores, phonetic_scores, grammatical_scores):
        weighted_scores = {}
        
        # Weights for different features
        weights = {
            "vocabulary": 0.4,
            "phonetic": 0.35,
            "grammatical": 0.25
        }
        
        for accent in self.accent_patterns.keys():
            weighted_scores[accent] = (
                accent_scores.get(accent, 0) * weights["vocabulary"] +
                phonetic_scores.get(accent, 0) * weights["phonetic"] +
                grammatical_scores.get(accent, 0) * weights["grammatical"]
            )
            
        return weighted_scores

def pretty_print_analysis(analysis):
    """Helper function to print analysis results in a readable format"""
    if not analysis:
        print("No analysis available")
        return
        
    print("\n=== Accent Analysis Results ===")
    print(f"\nDetected Language: {analysis['detected_language']}")
    
    print("\nMost Likely Accent Analysis:")
    print(f"Accent: {analysis['most_likely_accent']['accent']}")
    print(f"Overall Confidence: {analysis['most_likely_accent']['confidence']:.2%}")
    print("\nConfidence Breakdown:")
    for aspect, score in analysis['most_likely_accent']['confidence_breakdown'].items():
        print(f"- {aspect}: {score:.2%}")
    
    print("\nAll Accent Probabilities:")
    for accent, score in sorted(analysis['accent_confidence_scores'].items(), 
                              key=lambda x: x[1], reverse=True):
        print(f"{accent}: {score:.2%}")
    
    print("\nProsody Features:")
    for feature, value in analysis['prosody_features'].items():
        if isinstance(value, float):
            print(f"{feature}: {value:.2f}")
        else:
            print(f"{feature}: {value}")
    
    print("\nTranscription:")
    print(analysis['transcription'])
def create_confidence_gauge(confidence, title):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = confidence * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 33], 'color': "lightgray"},
                {'range': [33, 66], 'color': "gray"},
                {'range': [66, 100], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': confidence * 100
            }
        }
    ))
    return fig

def create_accent_distribution_chart(accent_scores):
    fig = px.bar(
        x=list(accent_scores.keys()),
        y=list(accent_scores.values()),
        title="Accent Probability Distribution",
        labels={'x': 'Accent', 'y': 'Probability'},
    )
    fig.update_traces(marker_color='rgb(0, 0, 139)')
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def record_audio(duration, sample_rate=44100):
    st.write("Recording...")
    recording = sd.rec(int(duration * sample_rate), 
                      samplerate=sample_rate, 
                      channels=1)
    sd.wait()
    return recording, sample_rate

def save_audio(recording, sample_rate):
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_path = temp_dir / f"recording_{timestamp}.wav"
    
    wavio.write(str(temp_path), recording, sample_rate, sampwidth=2)
    return temp_path

def main():
    st.title(" Accent Analyzer")
    st.markdown("""
    This app analyzes speech accents from either uploaded audio files or live recordings.
    It can detect various accents including Ghanaian, Nigerian, Kenyan, South African, British, and American English.
    """)
    
    # Initialize the analyzer
    analyzer = AccentAnalyzer()
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["Upload Audio", "Record Audio"])
    
    with tab1:
        st.header("Upload Audio File")
        uploaded_file = st.file_uploader("Choose an audio file", 
                                       type=['wav', 'mp3', 'm4a'])
        
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                audio_path = tmp_file.name
    
    with tab2:
        st.header("Record Audio")
        duration = st.slider("Recording duration (seconds)", 
                           min_value=5, 
                           max_value=30, 
                           value=10)
        
        if st.button("Start Recording"):
            with st.spinner("Recording in progress..."):
                recording, sample_rate = record_audio(duration)
                audio_path = save_audio(recording, sample_rate)
                st.success("Recording completed!")
    
    # Analysis section
    if 'audio_path' in locals():
        st.header("Analysis Results")
        
        with st.spinner("Analyzing accent... This might take a minute..."):
            analysis = analyzer.analyze_accent(str(audio_path))
            
            if analysis:
                # Display main results
                st.subheader(" Primary Analysis")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Detected Accent", 
                             analysis['most_likely_accent']['accent'])
                    
                with col2:
                    st.metric("Confidence", 
                             f"{analysis['most_likely_accent']['confidence']:.2%}")
                
                # Confidence gauge
                st.plotly_chart(
                    create_confidence_gauge(
                        analysis['most_likely_accent']['confidence'],
                        "Accent Detection Confidence"
                    )
                )
                
                # Accent distribution
                st.plotly_chart(
                    create_accent_distribution_chart(
                        analysis['accent_confidence_scores']
                    )
                )
                
                # Detailed breakdown
                with st.expander("See detailed analysis"):
                    st.subheader("Confidence Breakdown")
                    for aspect, score in analysis['most_likely_accent']['confidence_breakdown'].items():
                        st.write(f"{aspect}: {score:.2%}")
                    
                    st.subheader("Prosody Features")
                    for feature, value in analysis['prosody_features'].items():
                        if isinstance(value, float):
                            st.write(f"{feature}: {value:.2f}")
                        else:
                            st.write(f"{feature}: {value}")
                    
                    st.subheader("Transcription")
                    st.write(analysis['transcription'])
                
                # Cleanup
                try:
                    os.unlink(audio_path)
                except:
                    pass
            
            else:
                st.error("Analysis failed. Please try again with a different audio file.")

if __name__ == "__main__":
    main()