import math
import moviepy.editor as mpy
import moviepy.video.fx.all as vfx
import numpy as np

def moving_square_frame(t):
    """Generate a simple video with a moving square, to quickly check that the pipeline works."""
    w, h = 1280, 720
    s = min(h, 100)
    canvas = np.zeros((h, w, 3), dtype=np.ubyte)
    canvas[:,:,:] = 255
    canvas[(h-s)//2:(h+s)//2,int(w * t / 2):int(w * t / 2) + s,1:3] = 0
    return canvas

def moving_square():
    clip = mpy.VideoClip(moving_square_frame, duration=2)
    return clip.set_fps(60)

def motion_blur(clip, length=2, weight='uniform'):
    """Apply motion blur to the clip

    Args:
        length: the length of time in seconds before a given moment, that it averaged
        weight: 'uniform' for normal averaging, 'linear' for the weight of the frame linearly rising
                towards the moment of the frame
    """
    def make_frame(t):
        start = max(t - length, 0)
        finish = t
        frames = []
        weights = []
        for tframe, frame in clip.subclip(start, finish).iter_frames(with_times=True):
            frames.append(frame)
            if weight == 'linear':
                weights.append(tframe)
            elif weight == 'uniform':
                weights.append(1.)

        if not frames:
            frames = [clip.get_frame(t)]
            weights.append(1.)

        weights = np.array(weights)
        weights = weights / np.sum(weights)    

        frames = np.stack(frames)
        frames = frames.astype(np.float)

        weights = np.reshape(weights, (-1, 1, 1, 1))
        weighted_frames = frames * weights

        avg_frame = np.sum(weighted_frames, axis=0)
        avg_frame = avg_frame.astype(np.ubyte)

        return avg_frame
    newclip = mpy.VideoClip(make_frame, duration=clip.duration)
    newclip.set_duration(clip.duration)
    return newclip

# clip = moving_square()
clip = mpy.VideoFileClip('IMG_3070.MOV', audio=False)
clip = clip.fx(vfx.crop, x1=384, x2=3840 - 4*385, y1=432, y2=2160 - 648)
clip = clip.fx(motion_blur, length=2, weight='linear')
clip = clip.fx(vfx.speedx, 15)
clip.write_videofile('out6.mp4', fps=60, threads=8)
