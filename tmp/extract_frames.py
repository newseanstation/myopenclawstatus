import cv2, os
video=r'C:\Users\shawn\\.openclaw\\media\\inbound\\file_30---7fda915d-2f6a-4010-b685-d339b88eb8d3.mp4'
outdir=r'C:\Users\shawn\\.openclaw\\workspace\\tmp\\video_frames_350'
os.makedirs(outdir, exist_ok=True)
cap=cv2.VideoCapture(video)
fps=cap.get(cv2.CAP_PROP_FPS) or 30
frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
step=max(int(fps*1.0),1)  # 1 frame per second
max_frames=90
idx=0
saved=0
while saved<max_frames:
    ret, frame=cap.read()
    if not ret:
        break
    if idx%step==0:
        t=idx/fps
        fn=os.path.join(outdir, f'frame_{saved:03d}_t{t:06.2f}.jpg')
        cv2.imwrite(fn, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        saved+=1
    idx+=1
cap.release()
print({'fps':fps,'frame_count':frame_count,'saved':saved,'outdir':outdir})
