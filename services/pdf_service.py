import fitz 

# Measuring: [20, 60, 100]
FORCE_MAPPING = {
    "Measuring": [20, 60, 100], 
    "The skin ellipse": [25, 75],
    "infiltrative firm yellow white mass": [20, 70, 120],
    "well-defined firm white mass": [20, 70, 120]
}

def fill_pdf(template_path, output_path, data):
    doc = fitz.open(template_path)
    page = doc[0]

    def draw_centered_at(x_center, y_base, text):
        text_str = str(text)
        estimated_width = len(text_str) * 5 
        start_x = x_center - (estimated_width / 2)
        page.insert_text(fitz.Point(start_x, y_base), text_str, fontsize=10, color=(0, 0, 0))

    def fill_auto(anchor_text, values, placement='after'):
        hits = page.search_for(anchor_text)
        if not hits: return
        anchor_rect = hits[0]
        ref_y = (anchor_rect.y0 + anchor_rect.y1) / 2
        
        raw_dots = page.search_for(".")
        valid_dots = []
        for d in raw_dots:
            if abs((d.y0+d.y1)/2 - ref_y) < 5:
                if placement == 'after' and d.x0 > anchor_rect.x0: valid_dots.append(d)
                elif placement == 'before' and d.x1 < anchor_rect.x1: valid_dots.append(d)
        valid_dots.sort(key=lambda r: r.x0)
        
        slots = []
        if valid_dots:
            curr = valid_dots[0]
            for next_d in valid_dots[1:]:
                if next_d.x0 < curr.x1 + 15:
                    curr = fitz.Rect(curr.x0, min(curr.y0, next_d.y0), max(next_d.x1, curr.x1), max(next_d.y1, curr.y1))
                else:
                    slots.append(curr); curr = next_d
            slots.append(curr)
        
        slots.sort(key=lambda r: r.x0)
        if placement == 'before': slots.reverse()
        
        for i, val in enumerate(values):
            if i < len(slots):
                t = slots[i]
                center_x = (t.x0 + t.x1) / 2
                draw_centered_at(center_x, t.y1 - 2, val)

    def fill_force(anchor_text, values, offsets):
        hits = page.search_for(anchor_text)
        # Fallback search if exact phrase not found
        if not hits:
            if "infiltrative" in anchor_text: hits = page.search_for("infiltrative firm")
            elif "well-defined" in anchor_text: hits = page.search_for("well-defined firm")
            if not hits: return
        
        target_rect = hits[0]
        
        # Try to find the checkbox associated with this mass line
        # This is for anchor positioning purposes
        if "infiltrative" in anchor_text or "well-defined" in anchor_text:
             for h in hits:
                 if page.search_for("☐", clip=fitz.Rect(0, h.y0, h.x0, h.y1)):
                     target_rect = h; break
        
        base_x = target_rect.x1
        base_y = target_rect.y1 - 2
        extra_offset = 90 if anchor_text == "infiltrative firm yellow white mass" and hits[0].x1 < 200 else 0
        
        for i, val in enumerate(values):
            if i < len(offsets):
                final_x = base_x + offsets[i] + extra_offset
                draw_centered_at(final_x, base_y, val)

    mapping_config = {
        "specimen": ("Measuring", "after"),
        "skin": ("The skin ellipse", "after"),
        "mass_infiltrative": ("infiltrative firm yellow white mass", "after"),
        "mass_welldefined": ("well-defined firm white mass", "after")
    }

    # Main Filling Logic
    for data_key, (pdf_keyword, placement) in mapping_config.items():
        if data_key in data and data[data_key]:
            is_forced = False
            for force_key, offsets in FORCE_MAPPING.items():
                if force_key in pdf_keyword:
                    fill_force(pdf_keyword, data[data_key], offsets)
                    is_forced = True; break
            if not is_forced:
                fill_auto(pdf_keyword, data[data_key], placement)

    # Margins
    for k, v in data["margins"].items():
        label = k if "margin" in k or k == "skin" else f"{k} margin"
        fill_auto(f"cm. from {label}", [v], 'before')
        
    # Ratio
    if data.get("ratio"):
        hits = page.search_for("ratio of approximately")
        if hits:
            r = hits[0]
            page.insert_text(fitz.Point(r.x1 + 20, r.y1 - 2), str(data["ratio"][0]), fontsize=10)
            page.insert_text(fitz.Point(r.x1 + 60, r.y1 - 2), str(data["ratio"][1]), fontsize=10)

    # --- Smart Tick Box Functions ---
    def tick_box_in_area(search_area):
        box_hits = page.search_for("☐", clip=search_area)
        closest = None; min_dist = 999
        for box in box_hits:
            dist = abs(box.x0 - search_area.x0)
            if dist < min_dist:
                min_dist = dist
                closest = box
        if closest:
            cx = closest.x0 + (closest.width/2) - 3; cy = closest.y1 - 1
            page.insert_text(fitz.Point(cx, cy), "/", fontsize=12, color=(0, 0, 1))

    def tick_box_smart(anchor, search_clip=None):
        hits = page.search_for(anchor)
        if not hits: return
        target_rect = hits[0]
        # Define search area: slightly left and same height
        search_area = fitz.Rect(target_rect.x0 - 50, target_rect.y0 - 5, target_rect.x1 + 100, target_rect.y1 + 5)
        if search_clip: search_area = search_clip
        tick_box_in_area(search_area)

    # Ticking Logic
    for check in data["checks"]:
        if check == "is everted":
            tick_box_smart("The nipple")
        elif check == "shows inverted":
            tick_box_smart("shows inverted")
        elif check == "infiltrative":
            tick_box_smart("infiltrative")
        elif check == "well-defined":
            tick_box_smart("well-defined")
        elif check == "is unremarkable":
            hits = page.search_for("remaining of breast tissue")
            if hits:
                t = hits[0]
                area = fitz.Rect(t.x1, t.y0 - 5, t.x1 + 150, t.y1 + 5)
                tick_box_in_area(area)
        else:
            tick_box_smart(check)

    # --- Circles Logic ---
    for circle in data["circles"]:
        target_text = None
        if circle in ["right", "left"]: target_text = "( right / left )"
        elif circle in ["lower", "outer", "upper", "inner"]: 
            target_text = "in ( upper / lower"
        elif circle in ["is a", "are", "two", "are multiple"]:
            target_text = "( is a / are / two / are multiple )"

        if target_text:
            hits = page.search_for(target_text)
            if hits:
                anchor = hits[0]
                # Clip area around the line to find the specific word
                clip_rect = fitz.Rect(anchor.x0, anchor.y0-15, anchor.x1+400, anchor.y1+15)
                word_hits = page.search_for(circle, clip=clip_rect)
                
                # Special filter for 'are' to avoid matching parts of other words
                if circle == "are":
                    word_hits = [w for w in word_hits if page.get_text(w).strip() == "are"]
                
                if word_hits:
                    r = word_hits[0]
                    page.draw_oval(fitz.Rect(r.x0-2, r.y0, r.x1+2, r.y1), color=(1,0,0), width=1.5)

    # --- Manual Write Logic (Y-Axis Centered) ---
    def write_manual_at_rect(rect, text, offset_x=0, align="left", color=(0,0,0)):
        y_pos = rect.y1 - 5 
        if align == "right":
            text_width = len(str(text)) * 8
            start_x = rect.x0 - text_width - 25
            if start_x < 20: start_x = 20
            page.insert_text(fitz.Point(start_x, y_pos), str(text), fontsize=10, color=color)
        else:
            page.insert_text(fitz.Point(rect.x0 + offset_x, y_pos), str(text), fontsize=10, color=color)

    # 1. Normal Sections
    if data["sections"].get("nipple"):
        hits = page.search_for("= nipple")
        if hits: write_manual_at_rect(hits[-1], data["sections"]["nipple"], offset_x=-80)
        
    if data["sections"].get("mass"):
        hits = page.search_for("= mass")
        if hits: write_manual_at_rect(hits[-1], data["sections"]["mass"], offset_x=-80)

    # 2. Deep / Nearest (Exclusion Logic)
    nearest_hit = None
    nearest_search = page.search_for("nearest resected")
    if nearest_search: nearest_hit = nearest_search[0]
    
    deep_hit = None
    resected_hits = page.search_for("resected margin")
    for r in resected_hits:
        if nearest_hit and abs(r.y0 - nearest_hit.y0) < 10: continue
        deep_hit = r; break

    if nearest_hit and data["sections"].get("nearest"):
         write_manual_at_rect(nearest_hit, data["sections"]["nearest"], align="right")
         
    if deep_hit and data["sections"].get("deep"):
        write_manual_at_rect(deep_hit, data["sections"]["deep"], align="right")

    # 3. Nipple Other
    if data.get("nipple_other"):
         hits = page.search_for("shows ulceration")
         if hits: write_manual_at_rect(hits[-1], f"({data['nipple_other']})", offset_x=120, color=(1,0,0))

    doc.save(output_path)
    doc.close()
    return output_path