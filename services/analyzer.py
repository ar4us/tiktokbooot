import logging
import asyncio
import json
import subprocess
from models.report import TechData

logger = logging.getLogger(__name__)

class MediaAnalyzer:
    async def analyze(self, url: str, formats: list[dict] = None, title: str = "", headers: dict = None) -> TechData | None:
        """
        Probe the video URL to get technical details.
        Falls back to formats metadata if probing fails.
        """
        import re
        
        if not url:
            return self._fallback_from_formats(formats, title)

        try:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
            # Build headers string for ffprobe
            header_str = ""
            if headers:
                header_str = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])

            cmd = [
                'ffprobe',
                '-v', 'error',
                '-user_agent', user_agent,
            ]
            
            if header_str:
                cmd.extend(['-headers', header_str])
            
            cmd.extend([
                '-show_format',
                '-show_streams',
                '-of', 'json',
                url
            ])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15.0)
            except asyncio.TimeoutError:
                logger.warning(f"ffprobe timed out for URL: {url}")
                process.kill()
                return self._fallback_from_formats(formats, title)

            if process.returncode == 0:
                data = self._parse_ffprobe(json.loads(stdout.decode()), formats=formats)
                # If ffprobe didn't find FPS, check the title for patterns like "120fps" or "60fps"
                if data and (not data.fps or data.fps == 0):
                    match = re.search(r'(\d+)\s*fps', title.lower())
                    if match:
                        data.fps = float(match.group(1))
                return data
            else:
                logger.warning(f"ffprobe failed: {stderr.decode()}")
                return self._fallback_from_formats(formats, title)

        except Exception as e:
            logger.error(f"Error during media analysis: {e}", exc_info=True)
            return self._fallback_from_formats(formats, title)

    def _extract_best_fps(self, formats: list[dict], ffprobe_fps: float = 0.0) -> float:
        """
        Dynamically determine the best FPS by scanning all formats and ffprobe data.
        Prioritizes: play_addr/original formats > max format fps > ffprobe > 30
        """
        if not formats:
            return ffprobe_fps if ffprobe_fps > 0 else 30.0

        logger.debug(f"Analyzing {len(formats)} formats for best FPS...")

        candidates = []
        priority_fps = 0.0

        for fmt in formats:
            fps = float(fmt.get('fps', 0) or 0)
            if fps <= 0:
                continue
            
            candidates.append(fps)
            
            # High priority formats
            fid = str(fmt.get('format_id', '')).lower()
            if 'play_addr' in fid or 'original' in fid:
                # If multiple priority formats, take the one with higher resolution/bitrate (last one in list usually)
                priority_fps = fps

        # Selection Logic
        if priority_fps > 0:
            return priority_fps
        
        if candidates:
            return max(candidates)
            
        if ffprobe_fps > 0:
            return ffprobe_fps
            
        return 30.0

    def _parse_ffprobe(self, data: dict, formats: list[dict] = None) -> TechData:
        streams = data.get('streams', [])
        video_stream = next((s for s in streams if s.get('codec_type') == 'video'), {})
        format_info = data.get('format', {})

        width = video_stream.get('width', 0)
        height = video_stream.get('height', 0)
        
        # Robust FFPROBE FPS Parsing
        def _parse_fps_str(value: str) -> float:
            try:
                if not value or value == "0/0":
                    return 0.0
                if "/" in value:
                    num, den = value.split('/')
                    return float(num) / float(den) if float(den) != 0 else 0.0
                return float(value)
            except:
                return 0.0

        avg_fps = _parse_fps_str(video_stream.get('avg_frame_rate'))
        r_fps = _parse_fps_str(video_stream.get('r_frame_rate'))
        ff_fps = avg_fps if avg_fps > 0 else r_fps
        
        # Combine with format metadata
        fps = self._extract_best_fps(formats, ff_fps)

        bitrate = int(format_info.get('bit_rate', 0)) // 1000 # to kbps
        size_mb = float(format_info.get('size', 0)) / (1024 * 1024)

        return TechData(
            resolution=f"{width}x{height}",
            fps=round(fps, 2),
            codec=video_stream.get('codec_name', 'unknown'),
            bitrate_kbps=bitrate,
            size_mb=round(size_mb, 2),
            formats=formats or []
        )

    def _fallback_from_formats(self, formats: list[dict], title: str = "") -> TechData | None:
        """Fallback to yt-dlp metadata if ffprobe fails."""
        import re
        
        # Determine best format for resolution
        best = formats[-1] if formats else {}
        width = best.get('width') or 0
        height = best.get('height') or 0
        tbr = best.get('tbr') or 0
        filesize = best.get('filesize') or 0
        
        # Dynamic FPS selection
        fps = self._extract_best_fps(formats)
        
        # If FPS still looks generic and title has info, override
        if fps == 30.0:
            match = re.search(r'(\d+)\s*fps', title.lower())
            if match:
                fps = float(match.group(1))
        
        size_mb = round(float(filesize) / (1024 * 1024), 2) if filesize else 0.0

        return TechData(
            resolution=f"{width}x{height}" if width else "Unknown",
            fps=fps,
            codec=best.get('vcodec', 'unknown') or 'unknown',
            bitrate_kbps=int(tbr) if tbr else 0,
            size_mb=size_mb,
            formats=formats or []
        )

