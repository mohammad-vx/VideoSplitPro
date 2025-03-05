import os
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import numpy as np

def detect_audio_peaks(audio_segment, silence_thresh=-50, min_silence_len=500):
    """
    Detect non-silent periods in the audio segment.
    
    :param audio_segment: AudioSegment object
    :param silence_thresh: Silence threshold in dB
    :param min_silence_len: Minimum length of silence in milliseconds
    :return: List of tuples (start, end) in seconds
    """
    nonsilent_periods = detect_nonsilent(audio_segment, silence_thresh=silence_thresh, min_silence_len=min_silence_len)
    return [(start / 1000, end / 1000) for (start, end) in nonsilent_periods]

def rate_clip(clip_peaks):
    """
    Rate the clip based on the number of audio peaks.
    
    :param clip_peaks: List of audio peaks
    :return: Rating (number of peaks)
    """
    return len(clip_peaks)

def split_video_into_clips(video_path, output_folder, num_clips=5, min_duration=30, max_duration=90):
    """
    Split the video into clips based on audio peaks.
    
    :param video_path: Path to the input video file
    :param output_folder: Path to the output folder
    :param num_clips: Number of clips to generate
    :param min_duration: Minimum duration of each clip in seconds
    :param max_duration: Maximum duration of each clip in seconds
    :return: List of tuples (start, end, rating) for each clip
    """
    # Load the video
    video = VideoFileClip(video_path)
    
    # Extract audio and convert to AudioSegment
    audio = AudioSegment.from_file(video_path)
    
    # Detect audio peaks
    peak_times = detect_audio_peaks(audio)
    
    # Determine cut points
    cuts = []
    current_start = 0
    current_end = 0
    current_peaks = []
    
    for peak in peak_times:
        # If the current segment exceeds the maximum duration, finalize it
        if (peak[1] - current_start) > max_duration:
            if (current_end - current_start) >= min_duration:
                cuts.append((current_start, current_end, current_peaks))
            current_start = peak[0]
            current_end = peak[1]
            current_peaks = [peak]
        else:
            current_end = peak[1]
            current_peaks.append(peak)
    
    # Add the last segment if it meets the duration criteria
    if (current_end - current_start) >= min_duration:
        cuts.append((current_start, current_end, current_peaks))
    
    # Rate the clips
    rated_clips = [(start, end, rate_clip(peaks)) for start, end, peaks in cuts]
    
    # Sort clips by rating
    rated_clips.sort(key=lambda x: x[2], reverse=True)
    
    # Save the top clips
    for i, (start, end, rating) in enumerate(rated_clips[:num_clips]):
        clip = video.subclip(start, end)
        output_path = os.path.join(output_folder, f"clip_{i + 1}_rating_{rating}.mp4")
        clip.write_videofile(output_path, codec="libx264")
        print(f"Saved clip {i + 1}: from {start} to {end} seconds - Rating: {rating}")
    
    # Clean up
    video.close()
    
    # Return the list of clips for further modification
    return rated_clips[:num_clips]

def get_unique_filename(output_folder, base_name, extension="mp4"):
    """
    Generate a unique filename to avoid overwriting existing files.
    
    :param output_folder: Path to the output folder
    :param base_name: Base name of the file
    :param extension: File extension (default: mp4)
    :return: Unique file path
    """
    counter = 1
    while True:
        output_path = os.path.join(output_folder, f"{base_name}_{counter}.{extension}")
        if not os.path.exists(output_path):
            return output_path
        counter += 1

def format_time(seconds):
    """
    Format time in seconds to minutes and seconds.
    
    :param seconds: Time in seconds
    :return: Formatted string (e.g., "1:30")
    """
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def modify_clip(video_path, output_folder, clip_index, start_time, end_time, clips):
    """
    Modify a specific clip based on user input.
    
    :param video_path: Path to the input video file
    :param output_folder: Path to the output folder
    :param clip_index: Index of the clip to modify (1-based)
    :param start_time: Start time of the clip (in seconds)
    :param end_time: End time of the clip (in seconds)
    :param clips: List of clips to append the modified clip to
    """
    # Load the video
    video = VideoFileClip(video_path)
    
    while True:
        # Ask the user what modification they want
        modification_type = input("What modification do you want? (1: Add, 2: Trim, 0: Back): ")
        
        if modification_type == "0":
            # Return to the main menu
            print("Returning to the main menu.")
            break
        elif modification_type == "1":
            # Adding time
            add_type = input("Where do you want to add time? (1: Front, 2: Back, 3: Both, 0: Back): ")
            if add_type == "0":
                continue
            elif add_type == "1":
                front_time = float(input("How many seconds to add to the front? "))
                new_start = max(start_time - front_time, 0)
                new_end = end_time
            elif add_type == "2":
                back_time = float(input("How many seconds to add to the back? "))
                new_start = start_time
                new_end = min(end_time + back_time, video.duration)
            elif add_type == "3":
                front_time = float(input("How many seconds to add to the front? "))
                back_time = float(input("How many seconds to add to the back? "))
                new_start = max(start_time - front_time, 0)
                new_end = min(end_time + back_time, video.duration)
            else:
                print("Invalid choice. No changes made.")
                continue
        elif modification_type == "2":
            # Trimming time
            trim_type = input("Where do you want to trim? (1: Front, 2: Back, 3: Both, 4: Middle, 0: Back): ")
            if trim_type == "0":
                continue
            elif trim_type == "1":
                front_time = float(input("How many seconds to trim from the front? "))
                new_start = start_time + front_time
                new_end = end_time
            elif trim_type == "2":
                back_time = float(input("How many seconds to trim from the back? "))
                new_start = start_time
                new_end = end_time - back_time
            elif trim_type == "3":
                front_time = float(input("How many seconds to trim from the front? "))
                back_time = float(input("How many seconds to trim from the back? "))
                new_start = start_time + front_time
                new_end = end_time - back_time
            elif trim_type == "4":
                middle_start = float(input("From which second to start trimming? "))
                middle_end = float(input("To which second to end trimming? "))
                # Create two clips: before and after the middle part
                clip1 = video.subclip(start_time, start_time + middle_start)
                clip2 = video.subclip(start_time + middle_end, end_time)
                # Concatenate the two clips
                final_clip = concatenate_videoclips([clip1, clip2])
                # Generate a unique filename
                output_path = get_unique_filename(output_folder, f"clip_{clip_index}_middle_trimmed")
                final_clip.write_videofile(output_path, codec="libx264")
                print(f"Saved modified clip {clip_index}: removed from {start_time + middle_start} to {start_time + middle_end} seconds")
                # Add the modified clip to the list
                clips.append((start_time, start_time + middle_start, 0))  # First part
                clips.append((start_time + middle_end, end_time, 0))  # Second part
                return
            else:
                print("Invalid choice. No changes made.")
                continue
        else:
            print("Invalid choice. No changes made.")
            continue
        
        # Create the modified clip
        clip = video.subclip(new_start, new_end)
        
        # Generate a unique filename
        output_path = get_unique_filename(output_folder, f"clip_{clip_index}_modified")
        clip.write_videofile(output_path, codec="libx264")
        print(f"Saved modified clip {clip_index}: from {new_start} to {new_end} seconds")
        
        # Add the modified clip to the list
        clips.append((new_start, new_end, 0))  # Rating is set to 0 for modified clips
        break

def interactive_modification(video_path, output_folder, clips):
    """
    Interactively modify clips based on user input.
    
    :param video_path: Path to the input video file
    :param output_folder: Path to the output folder
    :param clips: List of tuples (start, end, rating) for each clip
    """
    while True:
        # Display the list of clips
        print("\nList of clips:")
        for i, (start, end, rating) in enumerate(clips):
            start_formatted = format_time(start)
            end_formatted = format_time(end)
            print(f"{i + 1}: From {start_formatted} to {end_formatted} - Rating: {rating}")
        
        # Ask the user which clip to modify
        clip_index = input("Enter the number of the clip you want to modify (1-{}), or 'done' to finish: ".format(len(clips)))
        if clip_index.lower() == "done":
            break
        
        try:
            clip_index = int(clip_index)
            if clip_index < 1 or clip_index > len(clips):
                print("Invalid clip number. Please enter a number between 1 and {}.".format(len(clips)))
                continue
        except ValueError:
            print("Invalid input. Please enter a number or 'done'.")
            continue
        
        # Modify the selected clip
        modify_clip(video_path, output_folder, clip_index, clips[clip_index - 1][0], clips[clip_index - 1][1], clips)

if __name__ == "__main__":
    video_path = r"C:\Users\MOO\Downloads\Video\فاهم 59 - فلسفة الصوم - مع الشيخ- أمجد سمير_2.mp4"  # Path to the input video
    output_folder = r"D:\output"  # Path to the output folder
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Ask the user how many clips they want
    num_clips = int(input("How many short clips do you want to extract? "))
    
    # Step 1: Split the video into clips
    clips = split_video_into_clips(video_path, output_folder, num_clips=num_clips, min_duration=30, max_duration=89)
    
    # Step 2: Interactively modify clips
    interactive_modification(video_path, output_folder, clips)
    
    print("Video splitting and modification completed!")
