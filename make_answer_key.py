import fitz # PyMuPDF

def create_master_answer_key():
    template_path = "assets/RCC_Wilms_Tumor_Template.pdf"
    output_path = "ANSWER_KEY_MASTER_V13.pdf"
    
    try:
        doc = fitz.open(template_path)
        page = doc[0]
    except Exception as e:
        print(f"Error: {e}")
        return

    print("กำลังสร้างไฟล์เฉลย V13 (จูนพิกัดใหม่ให้ตรงเป๊ะ)...")

    # =======================================================
    # 1. CONFIG: พิกัดบังคับ (จูนใหม่ตรงนี้!)
    # =======================================================
    FORCE_MAPPING = {
        # [ระยะตัวที่1, ระยะตัวที่2, ระยะตัวที่3] (นับจากขอบขวาของคำค้นหา)
        
        # Measuring: ขยับเข้ามาชิดหน่อย เพื่อหลบ x ตัวหลัง
        "Measuring": [20, 65, 115],
        
        # Skin: ขยับตัวหลังออกไปหน่อย
        "The skin ellipse": [15, 90],
        
        # Mass: เปลี่ยนคำค้นหาให้ยาวขึ้น เพื่อไม่ให้เขียนทับตัวหนังสือ
        "infiltrative firm yellow white mass": [10, 60, 110],
        "well-defined firm white mass": [10, 60, 110]
    }

    # =======================================================
    # 2. CORE FUNCTIONS
    # =======================================================
    
    def fill_force(anchor_text, values, offsets):
        hits = page.search_for(anchor_text)
        if not hits: 
            # กรณีหาประโยคยาวไม่เจอ (บางที PDF ตัดคำ) ให้ลองหาคำสั้นลง
            if "infiltrative" in anchor_text:
                hits = page.search_for("infiltrative firm")
            elif "well-defined" in anchor_text:
                hits = page.search_for("well-defined firm")
            
            if not hits:
                print(f"⚠️ หาไม่เจอ: {anchor_text}")
                return
        
        target_rect = hits[0]
        # เลือก Anchor ที่มี Checkbox ข้างหน้า (สำหรับ Mass)
        if "infiltrative" in anchor_text or "well-defined" in anchor_text:
             for h in hits:
                 if page.search_for("☐", clip=fitz.Rect(0, h.y0, h.x0, h.y1)):
                     target_rect = h; break

        base_x = target_rect.x1
        base_y = target_rect.y1
        
        # ถ้าใช้คำค้นหาสั้น (infiltrative firm) ต้องบวกระยะเพิ่มไปอีก เพื่อข้ามคำว่า yellow white mass
        # ความกว้างโดยประมาณของ " yellow white mass" คือ 100 หน่วย
        extra_offset = 0
        if anchor_text == "infiltrative firm yellow white mass" and hits[0].x1 < 200: 
             # ถ้า x1 น้อยแสดงว่าเจอแค่คำสั้น ต้องบวกระยะเพิ่มเอง
             extra_offset = 90
        
        for i, val in enumerate(values):
            if i < len(offsets):
                x_pos = base_x + offsets[i] + extra_offset
                
                # ใช้ insert_text (เขียนสด)
                point = fitz.Point(x_pos, base_y - 2) 
                page.insert_text(point, str(val), fontsize=10, color=(0, 0, 0))

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
                center_x = t.x0 + 5 
                point = fitz.Point(center_x, t.y1 - 2)
                page.insert_text(point, str(val), fontsize=10, color=(0, 0, 0))

    def tick_box_smart(anchor, y_limit=None):
        hits = page.search_for(anchor)
        if not hits: return
        target_rect = None
        for h in hits:
            if y_limit and h.y0 > y_limit: continue
            target_rect = h; break
        if not target_rect: return
        box_hits = page.search_for("☐")
        closest = None; min_dist = 999
        for box in box_hits:
            if abs(box.y0 - target_rect.y0) > 20: continue 
            dist = target_rect.x0 - box.x1 
            if 0 < dist < 150 and dist < min_dist: min_dist = dist; closest = box
        if closest:
            cx = closest.x0 + (closest.width/2) - 3; cy = closest.y1 - 1
            page.insert_text(fitz.Point(cx, cy), "/", fontsize=12, color=(0, 0, 1))

    # =======================================================
    # 3. DATA & EXECUTION
    # =======================================================
    answer_data = {
        "specimen": ["18", "9", "6"],
        "skin": ["15", "7"],
        "mass_infiltrative": ["3.6", "3", "2.8"],
        "mass_welldefined": None,
        "margins": {
            "deep": "0.7", "superior": "3.5", "inferior": "1",
            "medial": "8", "lateral": "5", "skin": "0.4"
        },
        "checks": [
            "modified radical mastectomy", "appears normal", "is everted",
            "infiltrative firm", "is unremarkable", "in ( upper / lower"
        ],
        "circles": ["right", "lower", "outer"],
        "sections": {
            "nipple": "A1-1", "mass": "A2-1 to A4-1",
            "deep": "A5-1", "nearest": "A6-1 (Inferior)"
        }
    }

    mapping_config = {
        "specimen": ("Measuring", "after"),
        "skin": ("The skin ellipse", "after"),
        
        # ใช้ Key ใหม่ที่ยาวขึ้น
        "mass_infiltrative": ("infiltrative firm yellow white mass", "after"),
        "mass_welldefined": ("well-defined firm white mass", "after")
    }

    for data_key, (pdf_keyword, placement) in mapping_config.items():
        if answer_data[data_key]:
            is_forced = False
            for force_key, offsets in FORCE_MAPPING.items():
                if force_key in pdf_keyword:
                    fill_force(pdf_keyword, answer_data[data_key], offsets)
                    is_forced = True; break
            if not is_forced:
                fill_auto(pdf_keyword, answer_data[data_key], placement)

    for k, v in answer_data["margins"].items():
        label = k if "margin" in k or k == "skin" else f"{k} margin"
        fill_auto(f"cm. from {label}", [v], 'before')

    for check in answer_data["checks"]:
        if "upper / lower" in check: tick_box_smart(check, y_limit=650)
        else: tick_box_smart(check)

    for circle in answer_data["circles"]:
        if circle in ["right", "left"]:
            hits = page.search_for("( right / left )")
            if hits:
                r = hits[0]
                page.draw_oval(fitz.Rect(r.x0+5, r.y0, r.x0+35, r.y1), color=(1,0,0), width=1.5)
        elif circle in ["lower", "outer"]:
            loc_hits = page.search_for("in ( upper / lower")
            if loc_hits:
                lr = loc_hits[0]
                wh = page.search_for(circle, clip=fitz.Rect(0, lr.y0-5, 600, lr.y1+5))
                if wh: page.draw_oval(wh[0], color=(1,0,0), width=1.5)

    def write_manual(anchor, text, dx=-80):
        hits = page.search_for(anchor)
        if hits:
            r = hits[0]
            page.insert_text(fitz.Point(r.x0 + dx, r.y1 - 2), text, fontsize=10, color=(0,0,0))

    for k, v in answer_data["sections"].items():
        if k == "nipple": write_manual("= nipple", v)
        if k == "mass": write_manual("= mass", v)
        if k == "deep": write_manual("= deep resected margin", v)
        if k == "nearest": write_manual("= nearest resected margin", v)

    doc.save(output_path)
    print(f"✅ ไฟล์เฉลย V13 (จูนพิกัดแล้ว) สร้างเสร็จแล้ว: {output_path}")

if __name__ == "__main__":
    create_master_answer_key()