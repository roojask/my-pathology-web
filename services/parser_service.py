import re

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    
    # 1. Standardize formatting
    text = re.sub(r"\bpoint\b", ".", text)
    text = re.sub(r"\bdash\b", "-", text)
    text = re.sub(r"\bto\b", "-", text) 
    text = text.replace("equal", "=")
    
    # 2. Fix ASR Errors (รวมคำผิดบ่อยๆ)
    text = text.replace("mast", "mass")
    text = text.replace("medium", "medial")
    text = text.replace("receptive", "resected")
    text = text.replace("recepted", "resected")
    text = text.replace("averted", "everted")
    text = text.replace("infutreative", "infiltrative")
    
    # 3. Word to Number
    NUM_WORDS = { "zero":"0", "one":"1", "two":"2", "three":"3", "four":"4", "five":"5", "six":"6", "seven":"7", "eight":"8", "nine":"9", "ten":"10" }
    for k, v in NUM_WORDS.items(): text = re.sub(rf"\b{k}\b", v, text)
    
    text = text.replace("centimeters", "cm").replace("millimeter", "mm")
    
    # 4. Handle Dimensions
    while " by " in text: text = text.replace(" by ", " x ")
    text = re.sub(r"(\d+(?:\.\d+)?)\s*(?:x)\s*(\d+(?:\.\d+)?)", r"\1 x \2", text)
    
    return text

def extract_data(text):
    data = { 
        "circles": [], "checks": [], "margins": {}, "sections": {},
        "specimen": None, "skin": None, 
        "mass_infiltrative": None, "mass_welldefined": None,
        "ratio": None,
        "nipple_other": None
    }

    # --- Circles ---
    if "right" in text: data["circles"].append("right")
    elif "left" in text: data["circles"].append("left")
    
    if "lower" in text: data["circles"].append("lower")
    if "upper" in text: data["circles"].append("upper")
    if "outer" in text: data["circles"].append("outer")
    if "inner" in text: data["circles"].append("inner")
    
    if "lower outer" in text or "upper outer" in text or "lower inner" in text or "upper inner" in text:
        data["checks"].append("in ( upper / lower")

    if "is a" in text or "is an" in text: data["circles"].append("is a")
    elif "there are" in text: data["circles"].append("are")
    elif "two" in text: data["circles"].append("two")
    elif "multiple" in text: data["circles"].append("are multiple")

    # --- Checkboxes ---
    if "modified radical" in text: data["checks"].append("modified radical mastectomy")
    if "simple mastectomy" in text: data["checks"].append("simple mastectomy")
    
    # --- Nipple Logic ---
    nipple_checked = False
    if "inverted" in text or "retracted" in text:
        data["checks"].append("shows inverted")
        nipple_checked = True
    if "everted" in text or "protruding" in text:
        data["checks"].append("is everted")
        nipple_checked = True
    if "ulceration" in text or "eroded" in text:
        data["checks"].append("shows ulceration")
        nipple_checked = True
    
    if not nipple_checked:
        nipple_phrase = re.search(r"nipple\s*(?:is|shows|appears)?\s*([a-z\s]+)", text)
        if nipple_phrase:
            desc = nipple_phrase.group(1).replace("is ", "").replace("shows ", "").strip()
            if len(desc) > 2 and "margin" not in desc and "cm" not in desc:
                data["nipple_other"] = desc

    if "appears normal" in text: data["checks"].append("appears normal") 
    
    # Unremarkable Logic
    if "unremarkable" in text: data["checks"].append("is unremarkable")

    # Infiltrative
    if "infiltrative" in text: data["checks"].append("infiltrative")
    if "well-defined" in text: data["checks"].append("well-defined")

    # --- Dimensions ---
    dims_3d = re.findall(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)", text)
    dims_2d = re.findall(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)", text)

    if len(dims_3d) >= 1:
        data["specimen"] = dims_3d[0]
        if len(dims_3d) >= 2:
            target = "mass_welldefined" if "well-defined" in text else "mass_infiltrative"
            data[target] = dims_3d[1]
    elif len(dims_2d) >= 1:
        data["specimen"] = (dims_2d[0][0], dims_2d[0][1], "")

    m_skin = re.search(r"skin.*?(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)", text)
    if m_skin: data["skin"] = m_skin.groups()

    # --- Margins ---
    margin_map = {
        "deep": ["deep"], "superior": ["superior"], "inferior": ["inferior"],
        "medial": ["medial", "media", "medium"], "lateral": ["lateral"], "skin": ["skin"]
    }

    for key, search_terms in margin_map.items():
        for term in search_terms:
            pattern = rf"([xX\d]*\.?\d+|[xX])\s*(?:cm)?\s*(?:from)?\s*[a-z\s]{{0,25}}\s*{term}"
            if key == "skin":
                 pattern = rf"([xX\d]*\.?\d+|[xX])\s*(?:cm)?\s*from\s*[a-z\s]{{0,25}}\s*{term}"

            matches = list(re.finditer(pattern, text))
            if matches:
                val = matches[-1].group(1)
                if val.replace('.','',1).isdigit() and val.startswith("."): val = "0" + val
                
                pdf_key = key if "margin" in key or key == "skin" else f"{key} margin"
                if key == "skin": pdf_key = "skin"
                data["margins"][pdf_key] = val
                break

    # --- Sections ---
    def find_code(keywords, context_text, range_chars=150, forbidden_pre=[]):
        if isinstance(keywords, str): keywords = [keywords]
        matches_found = []
        for kw in keywords:
            for m in re.finditer(kw, context_text):
                start_chk = max(0, m.start() - 30)
                prefix = context_text[start_chk:m.start()]
                if any(bad in prefix for bad in forbidden_pre): continue
                
                start_snip = max(0, m.start() - range_chars)
                snippet = context_text[start_snip:m.start()]
                codes = re.findall(r"a\s*(\d+)[-\s]*(\d+)", snippet)
                if codes:
                    c = codes[-1]
                    matches_found.append(f"A{c[0]}-{c[1]}")
        return matches_found[-1] if matches_found else None

    data["sections"]["nipple"] = find_code("nipple", text)
    data["sections"]["deep"] = find_code(["resected margin"], text, forbidden_pre=["inferior", "superior", "nearest"])
    
    nearest = find_code(["inferior", "nearest"], text)
    if nearest: data["sections"]["nearest"] = f"{nearest} (Inferior)"

    # Mass
    mass_range = re.search(r"(a\s*\d+[-\s]*\d+)\s*(?:-|to)\s*(a\s*\d+[-\s]*\d+).*?mass", text)
    if mass_range:
        def clean(c):
            nums = re.findall(r"\d+", c)
            if len(nums) >= 2: return f"A{nums[0]}-{nums[1]}"
            return c
        data["sections"]["mass"] = f"{clean(mass_range.group(1))} to {clean(mass_range.group(2))}"
    else:
        data["sections"]["mass"] = find_code(["mass", "mast"], text)

    ratio = re.search(r"ratio.*?approximately.*?(\d+).*?(\d+)", text)
    if ratio: data["ratio"] = (ratio.group(1), ratio.group(2))

    return data