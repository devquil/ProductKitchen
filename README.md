# ProductKitchen 🍳
**Honest productivity tracking** — tasks + habits together so you can't fake one without the other.

## Setup
```bash
cd ProductKitchen
pip install -r requirements.txt
python -m streamlit run app.py
```
Opens at `http://localhost:8501`

## What it tracks

### Tasks Tracker
- Add tasks with title, description, priority, estimated hours, due date
- Start → Work → Done workflow
- Log actual hours as you work
- **Efficiency score**: estimated_hours / actual_hours (higher = faster)

### Habits Tracker
- Add habits with daily goal hours, icon, color
- Log hours daily
- Progress rings show today's completion
- Weekly bar chart of hours logged per day

### Combined Dashboard
The core innovation — it calculates **two scores** and blends them:

```
Combined Score = (Task Score × 0.5) + (Habit Score × 0.5)
```

**Task Score**: completion rate + average efficiency, penalised for overdue high-priority tasks
**Habit Score**: average progress toward daily goal across all habits

It then detects four **honesty signals**:
- **On Track** ✅ — tasks done AND hours consistent
- **Busy Idling** ⚠️ — hours logged but few tasks — are you actually producing?
- **Coasting** ⏸ — tasks done but not logging habit hours — don't coast yet
- **Suspicious** 🤨 — very few hours but tasks done fast — verify actual effort

This prevents the two most common productivity lies:
1. Spending hours to feel busy without finishing tasks
2. Finishing tasks fast then chilling while the clock still reads 8 hours
