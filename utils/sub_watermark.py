import os
import re
import asyncio
from utils.ffmpeg import get_media_info

async def extract_and_watermark_subs(input_video, watermark_text, temp_dir):
    """
    Extracts subtitle streams, injects watermark at 00:00:03 -> 00:00:30,
    and returns a list of paths to the modified subtitle files in order of their stream index.
    Returns: list of string paths (or None if a stream failed to extract/patch)
    """
    try:
        info = await get_media_info(input_video)
        sub_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "subtitle"]
        
        if not sub_streams:
            return [] # No subtitles to edit
            
        extracted_subs = []
        
        for idx, s in enumerate(sub_streams):
            codec = s.get("codec_name", "srt")
            # Fallback for complex picture-based subs like pgs or vobsub
            if codec in ["hdmv_pgs_subtitle", "dvd_subtitle"]:
                extracted_subs.append(None)
                continue
                
            extract_ext = ".ass" if codec in ["ass", "ssa"] else ".srt"
            temp_extract_file = os.path.join(temp_dir, f"temp_raw_sub_{idx}{extract_ext}")
            final_srt_file = os.path.join(temp_dir, f"sub_{idx}.srt")
            
            raw_index = s.get("index")
            
            # Extract raw stream without conversion to avoid decoding errors
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-i", input_video, "-map", f"0:{raw_index}", "-c", "copy", temp_extract_file,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if os.path.exists(temp_extract_file):
                try:
                    with open(temp_extract_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                    # Inject watermark at the very beginning of the SRT file
                    wm_block = f"1\n00:00:00,000 --> 00:00:15,000\n{watermark_text}\n\n"
                    
                    if extract_ext == ".ass":
                        # Pure Python ASS -> SRT converter
                        events_section = False
                        format_cols = []
                        srt_lines = [wm_block.strip() + "\n"]
                        srt_index = 2
                        
                        for line in content.splitlines():
                            line = line.strip()
                            if not line: continue
                            if line.startswith("[Events]"):
                                events_section = True
                                continue
                            elif line.startswith("[") and events_section:
                                events_section = False
                                
                            if events_section:
                                if line.startswith("Format:"):
                                    format_cols = [c.strip() for c in line.replace("Format:", "").split(",")]
                                elif line.startswith("Dialogue:"):
                                    if not format_cols: continue
                                    c_part = line.split("Dialogue:", 1)[1].strip()
                                    vals = c_part.split(",", len(format_cols) - 1)
                                    if len(vals) == len(format_cols):
                                        d_map = dict(zip(format_cols, vals))
                                        start_ass = d_map.get("Start", "0:00:00.00")
                                        end_ass = d_map.get("End", "0:00:00.00")
                                        
                                        def to_sec(t):
                                            parts = t.split(":")
                                            if len(parts) != 3: return 0
                                            try:
                                                h, m, s_c = parts[0], parts[1], parts[2]
                                                s_v = s_c.split(".")[0]
                                                return int(h)*3600 + int(m)*60 + int(s_v)
                                            except Exception:
                                                return 0
                                                
                                        # Skip overlapping subtitles in the first 15s to prioritize our watermark
                                        if to_sec(start_ass) < 15:
                                            continue
                                        
                                        def to_srt_time(t):
                                            parts = t.split(":")
                                            if len(parts) != 3: return "00:00:00,000"
                                            h, m, s_c = parts[0], parts[1], parts[2]
                                            s_parts = s_c.split(".")
                                            s_v, cs = s_parts[0], s_parts[1] if len(s_parts) > 1 else "00"
                                            ms = cs + "0" if len(cs) == 2 else cs.ljust(3, "0")
                                            return f"{int(h):02d}:{int(m):02d}:{int(s_v):02d},{ms}"
                                            
                                        start_srt = to_srt_time(start_ass)
                                        end_srt = to_srt_time(end_ass)
                                        text_srt = d_map.get("Text", "").replace("\\N", "\n").replace("\\n", "\n")
                                        text_srt = re.sub(r"\{.*?\}", "", text_srt)
                                        
                                        srt_lines.append(f"{srt_index}\n{start_srt} --> {end_srt}\n{text_srt}\n")
                                        srt_index += 1
                                        
                        content = "\n".join(srt_lines)
                    else:
                        # Existing SRT file - Parse and remove early blocks
                        srt_out_lines = [wm_block.strip() + "\n"]
                        srt_idx = 2
                        current_block = []
                        keep_block = True
                        
                        for line in content.splitlines():
                            line = line.strip()
                            if not line:
                                if current_block:
                                    if keep_block and len(current_block) > 2:
                                        current_block[0] = str(srt_idx)
                                        srt_out_lines.append("\n".join(current_block) + "\n")
                                        srt_idx += 1
                                    current_block = []
                                    keep_block = True
                                continue
                                
                            if len(current_block) == 1 and "-->" in line:
                                st = line.split("-->")[0].strip()
                                parts = st.split(":")
                                if len(parts) >= 3:
                                    try:
                                        h, m, s_ms = parts[0][-2:], parts[1], parts[2]
                                        s_v = s_ms.split(",")[0]
                                        secs = int(h)*3600 + int(m)*60 + int(s_v)
                                        if secs < 15:
                                            keep_block = False
                                    except Exception:
                                        pass
                                        
                            current_block.append(line)
                            
                        if current_block and keep_block and len(current_block) > 2:
                            current_block[0] = str(srt_idx)
                            srt_out_lines.append("\n".join(current_block) + "\n")
                            
                        content = "\n".join(srt_out_lines)
                            
                    with open(final_srt_file, "w", encoding="utf-8") as f:
                        f.write(content)
                        
                    # Cleanup temp raw
                    try:
                        os.remove(temp_extract_file)
                    except Exception:
                        pass
                        
                    extracted_subs.append(final_srt_file)
                except Exception as e:
                    print(f"Failed to patch sub {idx}: {e}")
                    extracted_subs.append(None)
            else:
                stderr_text = stderr.decode('utf-8', errors='ignore')
                print(f"FFMPEG failed to extract sub {idx}, file not found. STDERR: {stderr_text}")
                extracted_subs.append(None)
                
        return extracted_subs
    except Exception as e:
        print(f"Error extracting subs: {e}")
        return []
