from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import asyncio
import aiohttp
import yt_dlp
import instaloader
import re
import json

app = FastAPI(title="SHARK API")

class DownloadRequest(BaseModel):
    url: str
    quality: str = "hd"
    platform: Optional[str] = None

async def download_instagram(url: str, quality: str):
    try:
        L = instaloader.Instaloader(quiet=True)
        
        shortcode_match = re.search(r'(?:/p/|/reel/|/tv/)([a-zA-Z0-9_-]+)', url)
        if not shortcode_match:
            return {"error": "Invalid URL"}
        
        shortcode = shortcode_match.group(1)
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        media_list = []
        for node in post.get_sidecar_nodes():
            if node.is_video:
                media_list.append({
                    "type": "video",
                    "url": node.video_url,
                    "quality": f"{node.video_width}x{node.video_height}"
                })
            else:
                media_list.append({
                    "type": "image",
                    "url": node.display_url
                })
        
        return {
            "status": "success",
            "media": media_list,
            "caption": post.caption[:200] if post.caption else "",
            "likes": post.likes
        }
    except Exception as e:
        return {"error": str(e)}

async def download_youtube(url: str, quality: str):
    try:
        ydl_opts = {'quiet': True}
        
        if quality == "audio":
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
        elif quality == "video":
            ydl_opts['format'] = 'bestvideo[ext=mp4]'
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            for f in info.get('formats', []):
                if f.get('ext') in ['mp4', 'webm', 'm4a']:
                    formats.append({
                        "format_id": f['format_id'],
                        "ext": f['ext'],
                        "quality": f.get('resolution', 'N/A')
                    })
            
            return {
                "status": "success",
                "title": info['title'],
                "duration": info['duration'],
                "formats": formats[:3],
                "best_url": info['url'] if 'url' in info else None
            }
    except Exception as e:
        return {"error": str(e)}

@app.post("/download")
async def download(request: DownloadRequest):
    url = request.url
    quality = request.quality
    
    platform = request.platform
    if not platform:
        if 'instagram.com' in url:
            platform = 'instagram'
        elif 'youtube.com' in url or 'youtu.be' in url:
            platform = 'youtube'
        elif 'twitter.com' in url or 'x.com' in url:
            platform = 'twitter'
        elif 'tiktok.com' in url:
            platform = 'tiktok'
        else:
            return {"status": "error", "reason": "platform_unknown"}
    
    try:
        if platform == 'instagram':
            result = await download_instagram(url, quality)
        elif platform == 'youtube':
            result = await download_youtube(url, quality)
        elif platform == 'twitter':
            result = {"status": "success", "note": "twitter_api_required"}
        elif platform == 'tiktok':
            result = {"status": "success", "note": "tiktok_api_required"}
        else:
            return {"status": "error", "reason": "unsupported_platform"}
        
        if "error" in result:
            return {"status": "error", "reason": result["error"]}
        
        result["platform"] = platform
        return result
        
    except Exception as e:
        return {"status": "error", "reason": str(e)}

@app.get("/stats")
async def stats():
    return {"total": 0, "success": 0, "failed": 0}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
