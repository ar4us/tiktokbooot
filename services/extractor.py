import logging
import asyncio
import yt_dlp
import random
import tempfile
import os
from models.report import EngagementData
from config import Config
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'geo_bypass': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'add_header': [
                'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language: en-US,en;q=0.9',
                'Cache-Control: max-age=0',
                'Priority: u=0, i',
                'Sec-Ch-Ua: "Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
                'Sec-Ch-Ua-Mobile: ?0',
                'Sec-Ch-Ua-Platform: "Windows"',
                'Sec-Fetch-Dest: document',
                'Sec-Fetch-Mode: navigate',
                'Sec-Fetch-Site: none',
                'Sec-Fetch-User: ?1',
                'Upgrade-Insecure-Requests: 1',
            ],
            'extract_flat': False,
            'http_chunk_size': 1048576,
        }

    async def extract_info(self, url: str) -> EngagementData | None:
        """
        Extract metadata and stats from a TikTok URL using yt-dlp.
        Includes retry logic for 429 (Too Many Requests).
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1'
        ]

        retries = 3
        for attempt in range(retries + 1):
            try:
                loop = asyncio.get_running_loop()
                # Update UA for each attempt
                ua = random.choice(user_agents)
                self.ydl_opts['user_agent'] = ua
                
                try:
                    info = await asyncio.wait_for(loop.run_in_executor(None, self._extract, url), timeout=45.0)
                except asyncio.TimeoutError:
                    logger.warning(f"yt-dlp extraction timed out for URL: {url} (Attempt {attempt+1})")
                    if attempt < retries: continue
                    return None
                
                if not info:
                    if attempt < retries:
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    return None

                # Better Region Detection
                region_code = info.get('location') or info.get('country') or info.get('region')
                
                # Check uploader location
                if not region_code and 'uploader_location' in info:
                    region_code = info.get('uploader_location')

                # Check description/uploader for country keywords
                if not region_code:
                    text_to_search = (info.get('description', '') + " " + info.get('uploader', '')).lower()
                    country_keywords = {
                        "BR": ["brazil", "brasil", "🇧🇷"],
                        "US": ["usa", "united states", "america", "🇺🇸"],
                        "ID": ["indonesia", "indo", "🇮🇩"],
                        "VN": ["vietnam", "🇻🇳"],
                        "RU": ["russia", "россия", "🇷🇺"],
                        "MX": ["mexico", "méxico", "🇲🇽"],
                        "PH": ["philippines", "pilipinas", "🇵🇭"],
                        "TR": ["turkey", "türkiye", "🇹🇷"],
                        "PK": ["pakistan", "🇵🇰"],
                        "MY": ["malaysia", "🇲🇾"],
                        "IN": ["india", "🇮🇳"],
                        "FR": ["france", "🇫🇷"],
                        "DE": ["germany", "deutschland", "🇩🇪"],
                    }
                    for code, keywords in country_keywords.items():
                        if any(kw in text_to_search for kw in keywords):
                            region_code = code
                            logger.info(f"Detected region from keywords: {region_code}")
                            break

                # Fallback: check thumbnail URLs for IDC (Data Center)
                if not region_code:
                    thumbnails = info.get('thumbnails', [])
                    for thumb in thumbnails:
                        thumb_url = thumb.get('url', '')
                        if 'idc=' in thumb_url:
                            region_code = thumb_url.split('idc=')[-1].split('&')[0].upper()
                            logger.info(f"Detected region from IDC: {region_code}")
                            break
                
                # Final fallback
                if not region_code:
                    region_code = "GL" 

                return EngagementData(
                    views=info.get('view_count', 0),
                    likes=info.get('like_count', 0),
                    comments=info.get('comment_count', 0),
                    shares=info.get('repost_count', 0),
                    favorites=info.get('favorite_count', 0),
                    upload_timestamp=info.get('timestamp', 0),
                    hashtags=info.get('tags', []),
                    sound_title=info.get('track') or info.get('track_title'),
                    duration_sec=info.get('duration', 0),
                    uploader=info.get('uploader', 'Unknown'),
                    description=info.get('description', ''),
                    video_id=info.get('id', 'Unknown'),
                    source="Browser" if "tiktok.com" in info.get('webpage_url_domain', '') else "Mobile",
                    region=region_code,
                    is_shadow_banned=info.get('view_count', 0) == 0,
                    title=info.get('title', ''),
                    video_url=info.get('url'),
                    formats=info.get('formats', []),
                    http_headers=info.get('http_headers', {})
                )
            except Exception as e:
                if "429" in str(e):
                    logger.warning(f"TikTok rate limit (429) hit. Attempt {attempt+1}/{retries+1}")
                    if attempt < retries:
                        await asyncio.sleep(3 * (attempt + 1))
                        continue
                logger.error(f"Error extracting TikTok info: {e}")
                if attempt < retries: 
                    await asyncio.sleep(1)
                    continue
                return None
        return None

    def _extract(self, url: str):
        # Ensure Referer is set correctly for TikTok
        opts = self.ydl_opts.copy()
        if 'add_header' not in opts: opts['add_header'] = []
        opts['add_header'].append('Referer: https://www.tiktok.com/')
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    async def download(self, url: str, mode: str = 'video') -> str | None:
        """
        Download video or audio from TikTok.
        Returns the path to the downloaded file.
        """
        # Use configured temp directory
        out_template = os.path.join(Config.TEMP_DIR, 'tikbot_%(id)s.%(ext)s')

        opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': out_template,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'user_agent': self.ydl_opts['user_agent'],
            'add_header': [
                'Referer: https://www.tiktok.com/',
            ],
        }

        if mode == 'audio':
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # Video without watermark
            opts.update({
                'format': 'best',
            })

        try:
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(None, self._download, url, opts)
            
            # The actual filename might have changed due to post-processing (e.g. .mp3)
            # yt-dlp info['requested_downloads'][0]['filepath'] is the way to get it
            if info and 'requested_downloads' in info:
                return info['requested_downloads'][0]['filepath']
            
            return None
        except Exception as e:
            logger.error(f"Error downloading TikTok: {e}", exc_info=True)
            return None

    def _download(self, url: str, opts: dict):
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)
