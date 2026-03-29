import customtkinter as ctk
import json
import itertools
import os
import sys

# --- 1. BACKEND LOGIC ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_data():
    # Use the helper to find the real path of the JSON
    json_path = resource_path('fishing_data.json')
    
    if not os.path.exists(json_path):
        return None
    with open(json_path, 'r') as file:
        return json.load(file)

def is_quest_or_reward(item):
    """Helper function to identify if an item is a quest/reward item."""
    if item.get("cost_type") == "reward":
        return True
    if "quest" in item.get("location", "").lower():
        return True
    return False

def calculate_best_loadouts(data, weights, top_n=3, exclude_quests=False):
    rods = data['rods']
    lines = data['lines']
    bobbers = data['bobbers']

    # Pre-filter lists to improve calculation speed and drop unwanted items
    if exclude_quests:
        rods = [r for r in rods if not is_quest_or_reward(r)]
        lines = [l for l in lines if not is_quest_or_reward(l)]
        bobbers = [b for b in bobbers if not is_quest_or_reward(b)]

    all_combinations = []
    for rod, line, bobber in itertools.product(rods, lines, bobbers):
        rod_quest = is_quest_or_reward(rod)
        line_quest = is_quest_or_reward(line)
        bobber_quest = is_quest_or_reward(bobber)
        
        all_combinations.append({
            "rod": f"{rod['name']}*" if rod_quest else rod['name'], 
            "line": f"{line['name']}*" if line_quest else line['name'], 
            "bobber": f"{bobber['name']}*" if bobber_quest else bobber['name'],
            "has_quest_item": rod_quest or line_quest or bobber_quest,
            "raw_stats": {
                "luck": rod['luck'] + line['luck'] + bobber['luck'],
                "strength": rod['strength'] + line['strength'] + bobber['strength'],
                "expertise": rod['expertise'] + line['expertise'] + bobber['expertise'],
                "attraction": rod['attraction'] + line['attraction'] + bobber['attraction'],
                "big_catch": rod['big_catch'] + line['big_catch'] + bobber['big_catch'],
                "max_weight": rod['max_weight'] 
            },
            "total_cost": rod['cost_amount'] + line['cost_amount'] + bobber['cost_amount'],
        })

    # Guard clause in case filtering leaves us with no valid combinations
    if not all_combinations:
        return []

    stat_keys = ["luck", "strength", "expertise", "attraction", "big_catch", "max_weight"]
    bounds = {stat: {"min": min(c['raw_stats'][stat] for c in all_combinations), 
                     "max": max(c['raw_stats'][stat] for c in all_combinations)} for stat in stat_keys}

    for combo in all_combinations:
        norm_stats = {}
        score = 0.0
        for stat in stat_keys:
            raw, mn, mx = combo['raw_stats'][stat], bounds[stat]['min'], bounds[stat]['max']
            val = 0.0 if mx == mn else (raw - mn) / (mx - mn)
            norm_stats[stat] = val
            score += val * weights.get(stat, 0.0)
        combo['normalized_stats'] = norm_stats
        combo['score'] = score

    return sorted(all_combinations, key=lambda x: x['score'], reverse=True)[:top_n]


# --- 2. FRONTEND GUI LOGIC ---

valid_stats = ["luck", "strength", "expertise", "attraction", "big_catch", "max_weight"]
display_names = {
    "luck": "Luck", "strength": "Strength", "expertise": "Expertise",
    "attraction": "Attraction", "big_catch": "Big Catch", "max_weight": "Max Weight"
}
reverse_names = {v: k for k, v in display_names.items()}
priority_dropdowns = []

def update_priority_dropdowns(choice):
    num_stats = int(choice)
    
    # 1. Save current selections before wiping the UI
    current_selections = [drop.get() for drop in priority_dropdowns]
    
    for widget in dynamic_frame.winfo_children():
        widget.destroy()
    priority_dropdowns.clear()
    
    for i in range(num_stats):
        row_frame = ctk.CTkFrame(dynamic_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=6, padx=20)
        
        lbl = ctk.CTkLabel(row_frame, text=f"Priority {i+1}", font=main_font, width=80, anchor="w")
        lbl.pack(side="left", padx=(0, 15))
        
        drop = ctk.CTkOptionMenu(row_frame, values=list(display_names.values()), font=main_font, dropdown_font=main_font)
        drop.pack(side="left", fill="x", expand=True)
        
        # 2. Restore previous selection if it exists, else default
        if i < len(current_selections):
            drop.set(current_selections[i])
        else:
            drop.set("Luck") 
            
        priority_dropdowns.append(drop)

def on_calculate_clicked():
    for widget in result_scroll.winfo_children():
        widget.destroy()
    
    game_data = load_data()
    if not game_data:
        error_lbl = ctk.CTkLabel(result_scroll, text="ERROR: 'fishing_data.json' missing.", text_color="red")
        error_lbl.pack(pady=20)
        return

    selections = [drop.get() for drop in priority_dropdowns]
    user_weights = {stat: 0.0 for stat in valid_stats}
    selected_keys = []
    
    # Check the states of our toggles
    is_even_weight = even_weight_switch.get() == 1
    exclude_quests = exclude_quest_switch.get() == 1
    
    current_weight = float(len(selections))
    
    for sel in selections:
        stat_key = reverse_names[sel]
        if stat_key not in selected_keys:
            selected_keys.append(stat_key)
            # Apply equal weight (1.0) or cascading weight based on the toggle
            user_weights[stat_key] = 1.0 if is_even_weight else current_weight
            if not is_even_weight:
                current_weight -= 1.0

    if not selected_keys:
        return

    top_builds = calculate_best_loadouts(game_data, user_weights, top_n=3, exclude_quests=exclude_quests)
    
    if not top_builds:
        empty_lbl = ctk.CTkLabel(result_scroll, text="No combinations found with these filters.", text_color="orange")
        empty_lbl.pack(pady=20)
        return

    display_order = selected_keys + [s for s in valid_stats if s not in selected_keys]

    for i, build in enumerate(top_builds, 1):
        card = ctk.CTkFrame(result_scroll, corner_radius=10, fg_color=("gray85", "gray16"))
        card.pack(fill="x", pady=(0, 15), padx=5)

        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        rank_lbl = ctk.CTkLabel(header_frame, text=f"🏆 RANK #{i}", font=ctk.CTkFont(size=16, weight="bold", family="Segoe UI"))
        rank_lbl.pack(side="left")
        
        score_lbl = ctk.CTkLabel(header_frame, text=f"Score: {build['score']:.2f}", font=ctk.CTkFont(size=14), text_color="gray60")
        score_lbl.pack(side="right")

        loadout_text = f"{build['rod']}   +   {build['line']}   +   {build['bobber']}"
        loadout_lbl = ctk.CTkLabel(card, text=loadout_text, font=ctk.CTkFont(size=15, weight="bold"))
        loadout_lbl.pack(anchor="w", padx=15, pady=(5, 10))

        stats_frame = ctk.CTkFrame(card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        row, col = 0, 0
        for stat in display_order:
            val = build['raw_stats'][stat]
            
            if stat == "max_weight":
                formatted_val = f"{val:,}" 
                suffix = " kg"
            elif stat == "attraction":
                formatted_val = f"{val:+}"
                suffix = "%"
            else:
                formatted_val = f"{val:+}"
                suffix = ""

            is_priority = stat in selected_keys
            prefix = "⭐ " if is_priority else "• "
            color = "white" if is_priority else "gray60"
            font_weight = "bold" if is_priority else "normal"
            
            stat_text = f"{prefix}{display_names[stat]}: {formatted_val}{suffix}"
            
            stat_lbl = ctk.CTkLabel(
                stats_frame, 
                text=stat_text, 
                text_color=color,
                font=ctk.CTkFont(size=13, weight=font_weight)
            )
            
            stat_lbl.grid(row=row, column=col, sticky="w", padx=(0, 30), pady=2)
            
            col += 1
            if col > 1:  
                col = 0
                row += 1

        cost_suffix = "*" if build['has_quest_item'] else ""
        cost_lbl = ctk.CTkLabel(card, text=f"💰 Total Cost: ${build['total_cost']:,}{cost_suffix}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2ecc71")
        cost_lbl.pack(anchor="w", padx=15, pady=(0, 10))


# --- 3. WINDOW SETUP & STYLING ---

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue") 

app = ctk.CTk()
app.geometry("650x900") 
app.title("FISH! ROD OPTIMIZER")

title_font = ctk.CTkFont(family="Segoe UI", size=28, weight="bold")
subtitle_font = ctk.CTkFont(family="Segoe UI", size=14) 
main_font = ctk.CTkFont(family="Segoe UI", size=14)

# HEADER
header_frame = ctk.CTkFrame(app, fg_color="transparent")
header_frame.pack(pady=(30, 20), fill="x")

title = ctk.CTkLabel(header_frame, text="Fishing Loadout Optimizer", font=title_font)
title.pack()

instructions = ctk.CTkLabel(header_frame, text="Select your desired stats to find the perfect gear combination.", font=subtitle_font, text_color="gray70")
instructions.pack(pady=(5, 0))

# SETTINGS CARD
settings_card = ctk.CTkFrame(app, corner_radius=15)
settings_card.pack(pady=10, padx=40, fill="x")

num_stats_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
num_stats_frame.pack(pady=(20, 10), padx=20, fill="x")
ctk.CTkLabel(num_stats_frame, text="How many stats to prioritize?", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold")).pack(side="left")
num_stats_dropdown = ctk.CTkOptionMenu(
    num_stats_frame, values=["1", "2", "3", "4", "5", "6"], 
    command=update_priority_dropdowns, width=80, font=main_font
)
num_stats_dropdown.pack(side="right")
num_stats_dropdown.set("3")

divider = ctk.CTkFrame(settings_card, height=2, fg_color=("gray70", "gray30"))
divider.pack(fill="x", padx=20, pady=10)

dynamic_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
dynamic_frame.pack(pady=(0, 5), fill="x")
update_priority_dropdowns("3")

# --- TOGGLES SECTION ---

SWITCH_STYLE = dict(
    switch_width=35,
    switch_height=16,
    border_width=0,
    button_length=4,
    )

toggles_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
toggles_frame.pack(fill="x", padx=20, pady=(5, 5))

even_weight_switch = ctk.CTkSwitch(toggles_frame, text="Weight stats equally", font=main_font, **SWITCH_STYLE)
even_weight_switch.pack(side="left", padx=(0, 20))

exclude_quest_switch = ctk.CTkSwitch(toggles_frame, text="Exclude Quest/Reward Items", font=main_font, **SWITCH_STYLE)
exclude_quest_switch.pack(side="left")

legend_lbl = ctk.CTkLabel(settings_card, text="* obtained through quest line or received as a reward", font=ctk.CTkFont(size=12), text_color="gray60")
legend_lbl.pack(pady=(0, 15), padx=25, anchor="w")
# ----------------------------

# CALCULATE BUTTON
calc_btn = ctk.CTkButton(
    app, text="FIND BEST LOADOUTS", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), 
    height=45, corner_radius=8, command=on_calculate_clicked
)
calc_btn.pack(pady=25)

# RESULTS AREA
result_scroll = ctk.CTkScrollableFrame(app, corner_radius=15, fg_color="transparent")
result_scroll.pack(pady=(0, 30), padx=(20,10), fill="both", expand=True)

placeholder = ctk.CTkLabel(result_scroll, text="Your optimized loadouts will appear here...", text_color="gray50", font=main_font)
placeholder.pack(pady=40)

app.mainloop()