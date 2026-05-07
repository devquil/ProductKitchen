"""
Level definitions for output score, habit streak, and per-tag ranks.
Each tag has its own ceiling — business tops out at Transcendent,
hobby caps at Artisan. Personal and fitness sit in between.
"""

# ── Per-tag level progressions ──────────────────────────────────────────────────
# Points = sum of (actual_hours × tag_weight) for completed tasks in that tag.
# Each level requires progressively more points.
#
# Business  (weight 3.0): 8 levels  — CEO / Transcendent ceiling
# Fitness   (weight 1.5): 6 levels  — Olympian ceiling
# Personal  (weight 1.2): 5 levels  — Operator ceiling
# Hobby     (weight 1.0): 4 levels  — Artisan ceiling
#
# Point formula per level: sum of actual_hours × tag_weight for completed tasks.

_TAG_LEVELS = {
    "business": [
        {"name": "Dreamer",      "emoji": "💤", "min_pts": 0,    "color": "#ef4444", "badge_bg": "#fef2f2", "border": "#fecaca", "description": "Has a vision. Now execute it."},
        {"name": "Founder",       "emoji": "🏗️", "min_pts": 15,   "color": "#ef4444", "badge_bg": "#fef2f2", "border": "#fca5a5", "description": "Building something real. First revenue territory."},
        {"name": "Operator",      "emoji": "⚙️",  "min_pts": 45,   "color": "#f97316", "badge_bg": "#fff7ed", "border": "#fed7aa", "description": "Business is running. You're in the game."},
        {"name": "Manager",       "emoji": "📊",  "min_pts": 120,  "color": "#f59e0b", "badge_bg": "#fffbeb", "border": "#fde68a", "description": "System is working. Now optimize it."},
        {"name": "Director",      "emoji": "🎯",  "min_pts": 300,  "color": "#3b82f6", "badge_bg": "#eff6ff", "border": "#bfdbfe", "description": "Strategic. You see what others miss."},
        {"name": "Executive",     "emoji": "🏢",  "min_pts": 600,  "color": "#8b5cf6", "badge_bg": "#f5f3ff", "border": "#ddd6fe", "description": "You're not working IN the business — you're running it."},
        {"name": "CEO",           "emoji": "👑",  "min_pts": 1000, "color": "#ec4899", "badge_bg": "#fdf2f8", "border": "#fbcfe8", "description": "Full ownership. Everything lands on your desk."},
        {"name": "Transcendent",  "emoji": "🏆",  "min_pts": 2000, "color": "#eab308", "badge_bg": "#fefce8", "border": "#fde047", "description": "Elite. This level is reserved for a different breed."},
    ],
    "fitness": [
        {"name": "Couch",         "emoji": "🛋️", "min_pts": 0,    "color": "#6b7280", "badge_bg": "#f9fafb", "border": "#e5e7eb", "description": "Every session starts with a decision."},
        {"name": "Beginner",       "emoji": "🌱", "min_pts": 8,    "color": "#84cc16", "badge_bg": "#f7fee7", "border": "#bbf7d0", "description": "Showing up. That's 80% of the game."},
        {"name": "Consistent",     "emoji": "🔄", "min_pts": 20,   "color": "#22c55e", "badge_bg": "#f0fdf4", "border": "#bbf7d0", "description": "Regular sessions. Body is adapting."},
        {"name": "Athlete",        "emoji": "🏃", "min_pts": 50,   "color": "#3b82f6", "badge_bg": "#eff6ff", "border": "#bfdbfe", "description": "You have a body now. Performance is the goal."},
        {"name": "Beast",          "emoji": "🦁", "min_pts": 100,  "color": "#f97316", "badge_bg": "#fff7ed", "border": "#fed7aa", "description": "Strong. Few people know what this level feels like."},
        {"name": "Olympian",       "emoji": "🏅", "min_pts": 200,  "color": "#eab308", "badge_bg": "#fefce8", "border": "#fde047", "description": "Top 1% of physical capability. Elite tier."},
    ],
    "personal": [
        {"name": "Chaos",          "emoji": "🌀", "min_pts": 0,    "color": "#6b7280", "badge_bg": "#f9fafb", "border": "#e5e7eb", "description": "Life admin wins. That's still a win."},
        {"name": "Organised",       "emoji": "📋", "min_pts": 10,   "color": "#06b6d4", "badge_bg": "#ecfeff", "border": "#a5f3fc", "description": "You're managing your life deliberately."},
        {"name": "Effective",       "emoji": "✅", "min_pts": 30,   "color": "#3b82f6", "badge_bg": "#eff6ff", "border": "#bfdbfe", "description": "Life runs smoothly. You're in control."},
        {"name": "Architect",       "emoji": "🏗️", "min_pts": 75,   "color": "#8b5cf6", "badge_bg": "#f5f3ff", "border": "#ddd6fe", "description": "Deliberate life design. You built the system."},
        {"name": "Operator",        "emoji": "⚡", "min_pts": 150,  "color": "#22c55e", "badge_bg": "#f0fdf4", "border": "#bbf7d0", "description": "Life as a well-oiled machine. Rare level."},
    ],
    "hobby": [
        {"name": "Curious",        "emoji": "❓", "min_pts": 0,    "color": "#6b7280", "badge_bg": "#f9fafb", "border": "#e5e7eb", "description": "Exploring. No skill required — just interest."},
        {"name": "Practitioner",    "emoji": "🎨", "min_pts": 8,    "color": "#8b5cf6", "badge_bg": "#f5f3ff", "border": "#ddd6fe", "description": "Making things. Skill is developing."},
        {"name": "Skilled",         "emoji": "🛠️", "min_pts": 25,   "color": "#a855f7", "badge_bg": "#faf5ff", "border": "#e9d5ff", "description": "People notice. Your work has quality."},
        {"name": "Artisan",         "emoji": "✨", "min_pts": 60,   "color": "#ec4899", "badge_bg": "#fdf2f8", "border": "#fbcfe8", "description": "Mastery territory. This is craft, not hobby."},
    ],
}


def tag_points(tasks, tag: str) -> float:
    """Total tag-weighted points from completed tasks in this tag."""
    from models.task import TaskStatus
    return sum(
        t.actual_hours * t.tag_weight()
        for t in tasks
        if t.tag == tag and t.status == TaskStatus.DONE
    )


def get_tag_level(tasks, tag: str) -> tuple:
    """
    Returns (level_dict, progress_to_next 0.0-1.0) for a given tag.
    Progress is 1.0 if at max level.
    """
    levels = _TAG_LEVELS.get(tag, _TAG_LEVELS["hobby"])
    pts = tag_points(tasks, tag)
    for i, lvl in enumerate(levels):
        if pts < lvl["min_pts"]:
            prev = levels[i - 1] if i > 0 else levels[0]
            range_start = prev["min_pts"]
            range_end = lvl["min_pts"]
            prog = (pts - range_start) / (range_end - range_start) if range_end > range_start else 1.0
            return prev, max(0.0, min(prog, 1.0))
    # At or above max level
    return levels[-1], 1.0


def get_peak_rank(tasks) -> dict:
    """The highest tag level across all tags — your peak rank."""
    best = None
    best_pts = -1
    for tag in _TAG_LEVELS:
        lvl, _ = get_tag_level(tasks, tag)
        pts = tag_points(tasks, tag)
        if pts > best_pts:
            best_pts = pts
            best = lvl
    if best is None:
        return _TAG_LEVELS["business"][0]
    return best


# ── Legacy: global output level (kept for streak/overall dashboard) ────────────

OUTPUT_LEVELS = [
    {"name": "Dead",        "emoji": "💀",  "min_score": 0.00, "color": "#6b7280", "badge_bg": "#f3f4f6", "border": "#d1d5db", "description": "Nothing tracked yet. Every legend started here."},
    {"name": "Waking Up",   "emoji": "🌱",  "min_score": 0.10, "color": "#84cc16", "badge_bg": "#f7fee7", "border": "#bbf7d0", "description": "First signals of life. The hardest part is showing up."},
    {"name": "Warming Up",  "emoji": "🔥",  "min_score": 0.25, "color": "#f59e0b", "badge_bg": "#fffbeb", "border": "#fde68a", "description": "You're moving. Don't worry about pace yet."},
    {"name": "Grinding",    "emoji": "⚙️",  "min_score": 0.40, "color": "#3b82f6", "badge_bg": "#eff6ff", "border": "#bfdbfe", "description": "Real output happening. This is where most people quit."},
    {"name": "On Fire",     "emoji": "🔥",  "min_score": 0.55, "color": "#f97316", "badge_bg": "#fff7ed", "border": "#fed7aa", "description": "Tasks done, hours logged, momentum building."},
    {"name": "Machine",     "emoji": "⚡",  "min_score": 0.70, "color": "#8b5cf6", "badge_bg": "#f5f3ff", "border": "#ddd6fe", "description": "You are a productivity machine. Respect."},
    {"name": "Unstoppable", "emoji": "🚀",  "min_score": 0.85, "color": "#ec4899", "badge_bg": "#fdf2f8", "border": "#fbcfe8", "description": "Peak output. You're not trying — you're just doing."},
    {"name": "Transcendent","emoji": "🏆",  "min_score": 0.95, "color": "#eab308", "badge_bg": "#fefce8", "border": "#fde047", "description": "Top 1% output. This is who you are now."},
]

STREAK_LEVELS = [
    {"name": "No Streak",   "emoji": "⭕",  "min_days": 0,   "color": "#6b7280", "badge_bg": "#f3f4f6", "border": "#d1d5db", "description": "Start today. Day 1 is the hardest."},
    {"name": "Day 1",       "emoji": "🌱",  "min_days": 1,   "color": "#84cc16", "badge_bg": "#f7fee7", "border": "#bbf7d0", "description": "First day done. Now make it two."},
    {"name": "Sprout",      "emoji": "🌿",  "min_days": 3,   "color": "#22c55e", "badge_bg": "#f0fdf4", "border": "#bbf7d0", "description": "3 days running. Habit is taking root."},
    {"name": "Grinder",     "emoji": "⚙️",  "min_days": 7,   "color": "#3b82f6", "badge_bg": "#eff6ff", "border": "#bfdbfe", "description": "A full week. Consistency is becoming your identity."},
    {"name": "Hammer",      "emoji": "🔨",  "min_days": 14,  "color": "#f59e0b", "badge_bg": "#fffbeb", "border": "#fde68a", "description": "Two weeks of iron discipline. You're getting dangerous."},
    {"name": "Machine",     "emoji": "⚡",  "min_days": 21,  "color": "#8b5cf6", "badge_bg": "#f5f3ff", "border": "#ddd6fe", "description": "Three weeks. This isn't motivation anymore — it's you."},
    {"name": "Beast",       "emoji": "🦁",  "min_days": 30,  "color": "#f97316", "badge_bg": "#fff7ed", "border": "#fed7aa", "description": "A full month. Most people never reach this. You did."},
    {"name": "Unstoppable", "emoji": "🚀",  "min_days": 60,  "color": "#ec4899", "badge_bg": "#fdf2f8", "border": "#fbcfe8", "description": "Two months of never breaking. You're built different."},
    {"name": "Legend",      "emoji": "👑",  "min_days": 90,  "color": "#eab308", "badge_bg": "#fefce8", "border": "#fde047", "description": "90 days. You are elite. This is who you are."},
    {"name": "Immortal",    "emoji": "🌀",  "min_days": 180, "color": "#06b6d4", "badge_bg": "#ecfeff", "border": "#a5f3fc", "description": "Half a year. You've transcended the need for willpower."},
    {"name": "God Mode",    "emoji": "🜏",  "min_days": 365, "color": "#1f2937", "badge_bg": "#111827", "border": "#374151", "description": "A full year. You didn't build a habit — you became one."},
]


def get_output_level(score: float) -> dict:
    for lvl in reversed(OUTPUT_LEVELS):
        if score >= lvl["min_score"]:
            return lvl
    return OUTPUT_LEVELS[0]


def get_streak_level(days: int) -> dict:
    for lvl in reversed(STREAK_LEVELS):
        if days >= lvl["min_days"]:
            return lvl
    return STREAK_LEVELS[0]


def level_progress(score: float, level: dict) -> float:
    all_levels = OUTPUT_LEVELS
    idx = all_levels.index(level)
    if idx == len(all_levels) - 1:
        return 1.0
    next_level = all_levels[idx + 1]
    range_size = next_level["min_score"] - level["min_score"]
    if range_size <= 0:
        return 1.0
    return min((score - level["min_score"]) / range_size, 1.0)


def streak_progress(days: int, level: dict) -> float:
    all_levels = STREAK_LEVELS
    idx = all_levels.index(level)
    if idx == len(all_levels) - 1:
        return 1.0
    next_level = all_levels[idx + 1]
    range_size = next_level["min_days"] - level["min_days"]
    if range_size <= 0:
        return 1.0
    return min((days - level["min_days"]) / range_size, 1.0)
