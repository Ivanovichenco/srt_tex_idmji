import os
import re
import yt_dlp
import string

def is_playlist(url):
    """Checks if the URL is a YouTube playlist."""
    return 'list=' in url

def sanitize_filename(name):
    """
    Sanitizes a string to be a valid filename.
    Removes invalid characters and limits length.
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    sanitized_name = ''.join(c if c in valid_chars else '_' for c in name)
    sanitized_name = sanitized_name.strip()
    return sanitized_name[:100]

def srt_to_txt(srt_content):
    """
    Converts SRT subtitle content to plain text.
    """
    text = re.sub(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', srt_content)
    text = re.sub(r'^\d+\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\n', '', text, flags=re.MULTILINE)
    return text.strip()

def download_subtitles(video_url, download_playlist=False):
    """
    Downloads SRT and TXT subtitles for a given YouTube URL.
    Can download a single video or a full playlist.

    Returns a tuple: (success, message_or_path)
    """
    print(f"DEBUG: Starting download for URL: {video_url}, Playlist mode: {download_playlist}")
    try:
        # 1. Get info and determine output path
        info_opts = {'quiet': True, 'no_warnings': True}
        if download_playlist:
            info_opts['extract_flat'] = 'in_playlist'

        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            if download_playlist:
                # For playlists, the main title is the directory
                base_title = sanitize_filename(info.get('title', 'youtube_playlist'))
            else:
                # For single videos, the video title is the directory
                base_title = sanitize_filename(info.get('title', 'youtube_video'))

        download_path = base_title
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        print(f"DEBUG: Download path set to: {download_path}")

        # 2. Set yt-dlp options
        ydl_opts_srt = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['es'],
            'subtitlesformat': 'srt',
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': not download_playlist,
            'outtmpl': os.path.join(download_path, f'%(title)s.%(ext)s'),
        }
        print(f"DEBUG: yt-dlp options set with noplaylist={not download_playlist}")

        # 3. Download SRT file(s)
        print("DEBUG: Downloading SRT files...")
        with yt_dlp.YoutubeDL(ydl_opts_srt) as ydl:
            error_code = ydl.download([video_url])
            if error_code != 0:
                print(f"DEBUG: yt-dlp finished with a non-zero error code: {error_code}")

        print("DEBUG: SRT download process finished.")

        # 4. Convert all downloaded .srt files to .txt
        print("DEBUG: Converting SRT files to TXT...")
        converted_count = 0
        for filename in os.listdir(download_path):
            if filename.endswith(".es.srt"):
                srt_filepath = os.path.join(download_path, filename)
                try:
                    with open(srt_filepath, 'r', encoding='utf-8') as f:
                        srt_content = f.read()
                    
                    txt_content = srt_to_txt(srt_content)
                    
                    base_filename = filename[:-7] # Remove '.es.srt'
                    txt_filename = os.path.join(download_path, f"{base_filename}.txt")
                    final_srt_path = os.path.join(download_path, f"{base_filename}.srt")

                    with open(txt_filename, 'w', encoding='utf-8') as f:
                        f.write(txt_content)
                    
                    os.rename(srt_filepath, final_srt_path)
                    
                    converted_count += 1
                    print(f"DEBUG: Converted and renamed {filename}")

                except Exception as e:
                    print(f"DEBUG: Could not process file {filename}: {e}")

        if converted_count == 0:
            return (False, "No se encontraron subtítulos en español.")

        print(f"DEBUG: Conversion successful for {converted_count} file(s).")
        return (True, download_path)

    except yt_dlp.utils.DownloadError as e:
        print(f"DEBUG: DownloadError: {e}")
        if "is not a valid URL" in str(e):
            return (False, "La URL introducida no es válida.")
        return (False, "Error de descarga. Comprueba la URL y tu conexión.")
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        return (False, f"Ocurrió un error inesperado: {e}")
