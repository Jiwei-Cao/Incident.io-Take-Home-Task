import argparse
import json
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import math

UTC = timezone.utc

# On call shift data class
@dataclass
class Shift:
    user: str
    start_time: datetime 
    end_time: datetime 

    # check if any shifts overlap a given time range
    def overlaps(self, range_start: datetime, range_end: datetime) -> bool:
        return self.start_time < range_end and range_start < self.end_time 
    
    # clip shift to fit within a specific time window
    def clipped(self, start_window: datetime, end_window: datetime) -> Optional["Shift"]:
        start_clip = max(self.start_time, start_window)
        end_clip = min(self.end_time, end_window)

        return Shift(self.user, start_clip, end_clip) if start_clip < end_clip else None

# Parse iso_z time to utc datetime 
def parse_iso_to_utc(iso_string: str) -> datetime:
    if iso_string.endswith("Z"):
        iso_string = iso_string[:-1] + "+00:00"

    date_time = datetime.fromisoformat(iso_string)

    return (date_time if date_time.tzinfo else date_time.replace(tzinfo=UTC)).astimezone(UTC)

# Format utc datetime to iso_z
def format_iso_z(date_time: datetime) -> str:
    return date_time.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

# Generate the base rotation shifts across the given time window
def generate_base_shifts(users: List[str], start_rotation: datetime, interval_days: int, start_window: datetime, end_window: datetime) -> List[Shift]:
    if not users:
        raise ValueError("schedule.users must be non-empty")
    
    if interval_days <= 0:
        raise ValueError("handover_interval_days must be > 0")
    
    shift_length = timedelta(days=interval_days)
    # generates the previous window just incase there is someone that needs a merge
    initial_index = math.floor((start_window - start_rotation).total_seconds() / shift_length.total_seconds()) - 1
    current_start = start_rotation + initial_index * shift_length 
    user_index = initial_index
    base_shifts = []

    while current_start < end_window:
        assigned_user = users[user_index % len(users)]
        base_shifts.append(Shift(assigned_user, current_start, current_start + shift_length))
        user_index += 1
        current_start += shift_length 

    return base_shifts

# Apply an override by replacing overlapping time ranges
def apply_override(shifts: List[Shift], override_user: str, override_start: datetime, override_end: datetime) -> List[Shift]:
    if override_start >= override_end:
        return shifts
    
    updated_shifts = []
    for shift in shifts:
        if not shift.overlaps(override_start, override_end):
            updated_shifts.append(shift)
            continue
        
        if shift.start_time < override_start:
            updated_shifts.append(Shift(shift.user, shift.start_time, min(shift.end_time, override_start)))
        
        if override_end < shift.end_time:
            updated_shifts.append(Shift(shift.user, max(shift.start_time, override_end), shift.end_time))

    updated_shifts.append(Shift(override_user, override_start, override_end))
    return updated_shifts   

# Sort shifts by start time and merge consecutive shifts for the same user
def merge_adjacent_shifts(shifts: List[Shift]) -> List[Shift]:
    if not shifts:
        return shifts 
    
    shifts.sort(key=lambda s: s.start_time)
    merged = [shifts[0]]

    for current in shifts[1:]:
        last = merged[-1]

        if last.user == current.user and last.end_time == current.start_time:
            merged[-1] = Shift(last.user, last.start_time, current.end_time)
        else:
            merged.append(current)
    
    return merged

# Main logic to render data to the required JSON results array
def render(schedule_path: str, overrides_path: Optional[str], from_str: str, until_str: str) -> List[dict]:
    # handle time formatting
    start_window, end_window = parse_iso_to_utc(from_str), parse_iso_to_utc(until_str)
    if start_window >= end_window:
        return []
    
    # parse schedule data
    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule_data = json.load(f)
    users = schedule_data.get("users", [])
    rotation_start = parse_iso_to_utc(schedule_data["handover_start_at"])
    interval_days = int(schedule_data["handover_interval_days"])

    shifts = generate_base_shifts(users, rotation_start, interval_days, start_window, end_window)

    # parse override data 
    overrides = [] 
    if overrides_path:
        with open(overrides_path, "r", encoding="utf-8") as f:
            overrides = json.load(f)
    if not isinstance(overrides, list):
        raise ValueError("overrides must be a JSON array")
    
    for override in overrides:
        override_segment = Shift(override["user"], parse_iso_to_utc(override["start_at"]), parse_iso_to_utc(override["end_at"])).clipped(start_window, end_window)
        if override_segment:
            shifts = apply_override(shifts, override_segment.user, override_segment.start_time, override_segment.end_time)

    clipped_shifts = []
    for shift in shifts:
        clipped = shift.clipped(start_window, end_window)

        if clipped:
            clipped_shifts.append(clipped)
    
    final_shifts = merge_adjacent_shifts(clipped_shifts)

    return [
        {
            "user": shift.user,
            "start_at": format_iso_z(shift.start_time),
            "end_at": format_iso_z(shift.end_time)
        }
        for shift in final_shifts 
    ]

# Parse CLI command and print the JSON results array 
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--schedule", required=True)
    p.add_argument("--overrides", required=False, default=None)
    p.add_argument("--from", dest="from_time", required=True)
    p.add_argument("--until", dest="until_time", required=True) 
    a = p.parse_args()

    try:
        out = render(a.schedule, a.overrides, a.from_time, a.until_time)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        raise SystemExit(2)
    
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()