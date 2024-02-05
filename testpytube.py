from pytube import YouTube, Playlist
from pytube.exceptions import VideoUnavailable


# def download(link):
#     youtubeObject = YouTube(link)
#     youtubeObject = youtubeObject.streams.get_highest_resolution()
#     try:
#         youtubeObject.download()
#     except:
#         print("error")
#     print("success")


def playlist(link):
    playlist_url = link
    p = Playlist(playlist_url)
    for url in p.video_urls:
        try:
            yt = YouTube(url)
        except VideoUnavailable:
            print(f'Video {url} is unavaialable, skipping.')
        else:
            print(f'Downloading video: {url}')
        yt.streams.first().download()


# link = input("link: ")
# yt = YouTube(link)
# resolution = input("rez: ")
#
# vids = yt.streams.filter(file_extension='mp4')
# for i in vids:
#     print(i)
# stream = yt.streams.get_audio_only()
# stream.download()
# print(stream.filesize_mb)
playlist("https://www.youtube.com/playlist?list=PLB8Nt5W7hnKAqp22trMMHWtxYaxrN5eT5")


