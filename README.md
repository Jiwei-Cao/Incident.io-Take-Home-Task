On-Call Schedule Renderer 
Generates a schedule between two timestamps using a rotation and an optional overrides input.

How to Run:
python3 render_schedule.py --schedule=schedule.json --overrides=overrides.json --from="2025-11-07T17:00:00Z" --until="2025-11-21T17:00:00Z"

Inputs
- schedule.json
- overrides.json (optional)

Output:
- A JSON array of final shifts

Notes
- No dependencies (Python 3.8+ only)