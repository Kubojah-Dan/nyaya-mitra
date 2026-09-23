from typing import Optional


class TransitionMappingService:
    """Manages statutory transitions between historical and current Indian law.

    Effective July 1, 2024:
    - Indian Penal Code, 1860 (IPC) -> Bharatiya Nyaya Sanhita, 2023 (BNS)
    - Code of Criminal Procedure, 1973 (CrPC) -> Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
    - Indian Evidence Act, 1872 (IEA) -> Bharatiya Sakshya Adhiniyam, 2023 (BSA)
    """

    IPC_TO_BNS = {
        "420": {
            "current_act": "Bharatiya Nyaya Sanhita, 2023",
            "current_section": "318(4)",
            "title": "Cheating and dishonestly inducing delivery of property",
            "historical_act": "Indian Penal Code, 1860 (Section 420)",
            "note": "Section 420 of IPC is now Section 318(4) of BNS (up to 7 years imprisonment and fine).",
        },
        "302": {
            "current_act": "Bharatiya Nyaya Sanhita, 2023",
            "current_section": "103",
            "title": "Punishment for Murder",
            "historical_act": "Indian Penal Code, 1860 (Section 302)",
            "note": "Section 302 of IPC is now Section 103 of BNS (death or imprisonment for life and fine).",
        },
        "378": {
            "current_act": "Bharatiya Nyaya Sanhita, 2023",
            "current_section": "303",
            "title": "Theft",
            "historical_act": "Indian Penal Code, 1860 (Section 378)",
            "note": "Theft is now defined under Section 303 of BNS. Community service introduced for first-time petty theft.",
        },
        "379": {
            "current_act": "Bharatiya Nyaya Sanhita, 2023",
            "current_section": "303(2)",
            "title": "Punishment for Theft",
            "historical_act": "Indian Penal Code, 1860 (Section 379)",
            "note": "Punishment for theft is now under Section 303(2) of BNS.",
        },
        "506": {
            "current_act": "Bharatiya Nyaya Sanhita, 2023",
            "current_section": "351",
            "title": "Criminal Intimidation",
            "historical_act": "Indian Penal Code, 1860 (Section 506)",
            "note": "Criminal intimidation is now covered under Section 351 of BNS.",
        },
        "498A": {
            "current_act": "Bharatiya Nyaya Sanhita, 2023",
            "current_section": "85",
            "title": "Husband or relative of husband of a woman subjecting her to cruelty",
            "historical_act": "Indian Penal Code, 1860 (Section 498A)",
            "note": "Cruelty by husband or relatives is now Section 85 of BNS (up to 3 years imprisonment and fine).",
        },
        "354": {
            "current_act": "Bharatiya Nyaya Sanhita, 2023",
            "current_section": "74",
            "title": "Assault or criminal force to woman with intent to outrage her modesty",
            "historical_act": "Indian Penal Code, 1860 (Section 354)",
            "note": "Outraging modesty of a woman is now Section 74 of BNS.",
        },
    }

    CRPC_TO_BNSS = {
        "154": {
            "current_act": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "current_section": "173",
            "title": "Information in Cognizable Cases (FIR, Zero FIR & e-FIR)",
            "historical_act": "Code of Criminal Procedure, 1973 (Section 154)",
            "note": "FIR registration is now codified under Section 173 of BNSS, expressly authorizing Zero FIR and electronic FIR.",
        },
        "41A": {
            "current_act": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "current_section": "35(3)",
            "title": "Notice of Appearance before Police Officer",
            "historical_act": "Code of Criminal Procedure, 1973 (Section 41A)",
            "note": "Notice of appearance where arrest is not mandatory is now governed by Section 35(3) of BNSS.",
        },
        "164": {
            "current_act": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "current_section": "183",
            "title": "Recording of Confessions and Statements by Magistrate",
            "historical_act": "Code of Criminal Procedure, 1973 (Section 164)",
            "note": "Recording of statements and confessions before Magistrate is now Section 183 of BNSS, with audio-video recording provisions.",
        },
        "437": {
            "current_act": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "current_section": "480",
            "title": "When Bail May Be Taken in Case of Non-Bailable Offence",
            "historical_act": "Code of Criminal Procedure, 1973 (Section 437)",
            "note": "Regular bail in non-bailable offences before Magistrate is now Section 480 of BNSS.",
        },
        "439": {
            "current_act": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "current_section": "482",
            "title": "Special Powers of High Court or Sessions Court Regarding Bail",
            "historical_act": "Code of Criminal Procedure, 1973 (Section 439)",
            "note": "Special bail powers of Sessions Court and High Court are now under Section 482 of BNSS.",
        },
    }

    IEA_TO_BSA = {
        "65B": {
            "current_act": "Bharatiya Sakshya Adhiniyam, 2023",
            "current_section": "63",
            "title": "Admissibility of Electronic Records and Certificate Requirement",
            "historical_act": "Indian Evidence Act, 1872 (Section 65B)",
            "note": "Certificate requirement for digital evidence (WhatsApp, emails, recordings) is now governed by Section 63 of BSA.",
        },
    }

    @classmethod
    def map_outdated_section(cls, act_name_or_code: str, section: str) -> Optional[dict[str, str]]:
        clean_act = act_name_or_code.upper()
        clean_sec = section.strip().upper().replace("SECTION", "").replace("SEC.", "").strip()

        if "IPC" in clean_act or "PENAL" in clean_act:
            return cls.IPC_TO_BNS.get(clean_sec)
        elif "CRPC" in clean_act or "PROCEDURE" in clean_act:
            return cls.CRPC_TO_BNSS.get(clean_sec)
        elif "EVIDENCE" in clean_act or "IEA" in clean_act:
            return cls.IEA_TO_BSA.get(clean_sec)

        return None
