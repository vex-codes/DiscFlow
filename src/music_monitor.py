import subprocess

def get_current_track_info():
    """
    Queries Spotify and Apple Music for the current track.
    Returns a dictionary with 'artist', 'song', 'album', and 'status'.
    """
    
    # 1. Check Spotify
    spotify_script = """
    if application "Spotify" is running then
        tell application "Spotify"
            if player state is playing then
                return (get artist of current track) & "||" & (get name of current track) & "||" & (get album of current track) & "||playing"
            else
                return "||||paused"
            end if
        end tell
    end if
    return "||||stopped"
    """
    
    try:
        result = subprocess.run(['osascript', '-e', spotify_script], capture_output=True, text=True)
        output = result.stdout.strip()
        if output and output != "||||stopped":
            parts = output.split("||")
            if len(parts) == 4:
                return {
                    'artist': parts[0],
                    'song': parts[1],
                    'album': parts[2],
                    'status': parts[3]
                }
    except Exception as e:
        print(f"Error checking Spotify: {e}")

    # 2. Check Apple Music (if Spotify isn't playing)
    music_script = """
    if application "Music" is running then
        tell application "Music"
            if player state is playing then
                return (get artist of current track) & "||" & (get name of current track) & "||" & (get album of current track) & "||playing"
            else
                return "||||paused"
            end if
        end tell
    end if
    return "||||stopped"
    """
    
    try:
        result = subprocess.run(['osascript', '-e', music_script], capture_output=True, text=True)
        output = result.stdout.strip()
        if output and output != "||||stopped":
            parts = output.split("||")
            if len(parts) == 4:
                return {
                    'artist': parts[0],
                    'song': parts[1],
                    'album': parts[2],
                    'status': parts[3]
                }
    except Exception as e:
        print(f"Error checking Music: {e}")

    return {'artist': '', 'song': '', 'album': '', 'status': 'stopped'}
