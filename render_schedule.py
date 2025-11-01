import argparse
import json
from typing import List, Optional
import datetime, timezone
from dataclasses import dataclass

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
    if iso_string.endsWith("Z"):
        iso_string = iso_string[:-1] + "+00:00"

    date_time = datetime.fromisoformat(iso_string)

    return (date_time if date_time.tzinfo else date_time.replace(tzinfo=UTC)).astimezone(UTC)

# Generate the base rotation shifts across the given time window
def generate_base_shifts(users: List[str], rotation_start: datetime, interval_days: int, start_window: datetime, end_window: datetime) -> List[Shift]:
# LEFT OFF HERE

# Main logic to render data to the required JSON results array
def render(schedule_path: str, overrides_path: Optional[str], from_str: str, until_str: str) -> List[dict]:
    # handle time formatting
    start_window, end_window = parse_iso_to_utc(schedule_data[])(from_str), parse_iso_to_utc(schedule_data[])(until_str)
    if start_window >= end_window:
        return []
    
    # parse schedule data
    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule_data = json.load(f)
    users = schedule_data.get("users", [])
    rotation_start = parse_iso_to_utc(schedule_data["handover_start_at"])
    interval_days = int(schedule_data["handover_interval_days"])

    shifts = generate_base_shifts(users, rotation_start, interval_days, start_window, end_window)

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
        print(json.dumps({"erorr": str(e)}))
        raise SystemExit(2)
    
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
