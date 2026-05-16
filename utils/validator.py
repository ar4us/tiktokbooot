import re

class URLValidator:
    # Regex for TikTok URLs: 
    # tiktok.com/@user/video/id
    # vm.tiktok.com/id
    # vt.tiktok.com/id
    TIKTOK_REGEX = re.compile(
        r'https?://(?:www\.|vm\.|vt\.)?tiktok\.com/.*',
        re.IGNORECASE
    )

    @classmethod
    def validate(cls, text: str) -> bool:
        if not text:
            return False
        # Extract URL from text if it contains other words
        urls = re.findall(r'(https?://\S+)', text)
        if not urls:
            return False
        
        # Check if the first URL found matches TikTok pattern
        return bool(cls.TIKTOK_REGEX.match(urls[0]))

    @classmethod
    def get_url(cls, text: str) -> str | None:
        urls = re.findall(r'(https?://\S+)', text)
        if urls and cls.TIKTOK_REGEX.match(urls[0]):
            return urls[0]
        return None
