class TimeFormatService:
    @staticmethod
    async def seconds_to_format(seconds: int) -> str:
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        time_parts = []
        if days:
            time_parts.append(f"{days}d")
        if hours:
            time_parts.append(f"{hours}h")
        if minutes:
            time_parts.append(f"{minutes}m")
        time_parts.append(f"{seconds}s")
        return " ".join(time_parts)

    @staticmethod
    async def format_to_seconds(input_time: str):
        conversions = {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}
        total_seconds = 0
        parts = input_time.split()
        for part in parts:
            try:
                value = int(part[:-1])
                unit = part[-1].lower()
                total_seconds += value * conversions.get(unit, 0)
            except ValueError:
                return None
        return total_seconds


seconds_to_format = TimeFormatService.seconds_to_format
format_to_seconds = TimeFormatService.format_to_seconds
