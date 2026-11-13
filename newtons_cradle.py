from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, math, subprocess, wave
W,H=720,960; FPS=30; D=16; R=35; L=290; half=1.25
from pathlib import Path
out = str(Path(__file__).resolve().parent) + '/'
def ft(n):
 for font in ['DejaVuSans.ttf', 'Arial.ttf', 'C:/Windows/Fonts/arial.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf']:
  try: return ImageFont.truetype(font, n)
  except OSError: pass
 return ImageFont.load_default(size=n)
yy,xx=np.mgrid[0:H,0:W]; bg=np.zeros((H,W,3),dtype=np.float32); bg[:]=[5,8,23]
for cx,cy,c,rad in [(80,380,[17,33,75],440),(650,550,[55,9,65],390),(360,850,[4,42,55],360)]:
 a=np.exp(-((xx-cx)**2+(yy-cy)**2)/rad**2); bg+=a[:,:,None]*c
bg=Image.fromarray(np.uint8(np.clip(bg,0,255)))
colors=[(30,205,255),(80,110,255),(177,72,255),(255,70,155),(255,183,38)]
sprites=[]
for col in colors:
 s=R*2+6; y,x=np.mgrid[0:s,0:s]; nx=(x-s/2)/R; ny=(y-s/2)/R; rr=nx*nx+ny*ny; nz=np.sqrt(np.maximum(0,1-rr)); light=np.maximum(0,-.45*nx-.65*ny+.61*nz)
 spec=np.maximum(0,-.32*nx-.50*ny+.80*nz)**50; rim=(1-nz)**3
 rgb=np.zeros((s,s,4));
 for k in range(3): rgb[:,:,k]=np.clip(col[k]*(.16+.72*light)+220*spec+rim*35,0,255)
 rgb[:,:,3]=(rr<=1)*255; sprites.append(Image.fromarray(rgb.astype('uint8')))
def tube(d,pts,width=9):
 d.line(pts,fill=(30,47,69),width=width+5,joint='curve'); d.line(pts,fill=(112,155,182),width=width,joint='curve'); d.line([(x-2,y-2) for x,y in pts],fill=(210,234,246),width=2,joint='curve')
proc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',out+'silent.mp4'],stdin=subprocess.PIPE,stderr=open(out+'encode.log','w'))
for f in range(D*FPS):
 t=f/FPS; im=bg.copy(); d=ImageDraw.Draw(im)
 d.text((360,95),"NEWTON’S CRADLE",font=ft(38),anchor='mm',fill=(238,246,255)); d.text((360,143),'MOTION • MOMENTUM • ENERGY',font=ft(16),anchor='mm',fill=(127,170,201))
 # subtle luminous floor and precision plinth
 for y in range(720,900,28): d.line((40,y,680,y),fill=(16,34,49),width=1)
 d.rounded_rectangle((79,720,659,795),radius=23,fill=(6,15,27),outline=(75,108,134),width=2)
 d.rounded_rectangle((80,720,658,767),radius=20,fill=(19,34,49),outline=(103,145,164),width=2)
 d.line((110,775,625,775),fill=(28,189,224),width=3)
 # rear support
 tube(d,[(154,725),(154,288),(610,288),(610,725)],8)
 # suspension: one end gives its motion to the other at each collision
 k=int(t/half); u=(t%half)/half; amp=.65
 angles=[0.]*5
 if k%2==0: angles[0]=-amp*math.cos(math.pi*u/2) if k==0 else 0
 # use quarter-cycle sections: left peak -> impact -> right peak -> impact -> left peak
 phase=t/half
 q=int(phase)%4; v=phase%1
 if q==0: angles[0]=-amp*math.cos(math.pi*v/2)
 elif q==1: angles[4]=amp*math.sin(math.pi*v/2)
 elif q==2: angles[4]=amp*math.cos(math.pi*v/2)
 else: angles[0]=-amp*math.sin(math.pi*v/2)
 positions=[]
 for i,a in enumerate(angles):
  px=220+i*70; x=px+L*math.sin(a); y=328+L*math.cos(a); positions.append((x,y))
  d.line((px+20,288,x,y),fill=(91,132,157),width=2)
  d.line((px,328,x,y),fill=(205,220,229),width=2)
 # glow and soft reflections
 glow=Image.new('RGBA',(W,H)); gd=ImageDraw.Draw(glow)
 for i,(x,y) in enumerate(positions):
  gd.ellipse((x-40,y-40,x+40,y+40),fill=(*colors[i],45)); gd.ellipse((x-30,737,x+30,751),fill=(*colors[i],80))
 im=Image.alpha_composite(im.convert('RGBA'),glow.filter(ImageFilter.GaussianBlur(17)))
 for i,(x,y) in enumerate(positions): im.alpha_composite(sprites[i],(round(x)-38,round(y)-38))
 d=ImageDraw.Draw(im)
 tube(d,[(109,748),(109,328),(565,328),(565,748)],10)
 tube(d,[(109,328),(154,288)],8); tube(d,[(565,328),(610,288)],8)
 # small impact light, tied to sound
 dist=min(abs(t-(1.25+2.5*j)) for j in range(8))
 if dist<.10:
  a=int(230*(1-dist/.1)); d.line((349,600,349,633),fill=(a,a,a),width=2)
 d.text((360,850),'ONE SWING. A CHAIN REACTION.',font=ft(19),anchor='mm',fill=(204,225,239))
 d.text((360,885),'Conservation of momentum in motion',font=ft(16),anchor='mm',fill=(113,157,185))
 proc.stdin.write(im.convert('RGB').tobytes())
 if f%120==0: print('frame',f,flush=True)
 if f==75: im.convert('RGB').save(out+'preview.jpg')
proc.stdin.close(); proc.wait()
# Crisp metallic click with a short resonant tail at every contact.
sr=48000; sound=np.zeros((D*sr,2)); rng=np.random.default_rng(7)
for j in range(8):
 at=1.25+2.5*j
 if at>=D: break
 tt=np.arange(int(.18*sr))/sr
 click=.50*rng.normal(size=len(tt))*np.exp(-tt*330)+.32*np.sin(2*np.pi*3100*tt)*np.exp(-tt*65)+.17*np.sin(2*np.pi*5200*tt)*np.exp(-tt*95)
 idx=int(at*sr); n=min(len(tt),len(sound)-idx); pan=.40 if j%2 else .60
 sound[idx:idx+n,0]+=click[:n]*pan; sound[idx:idx+n,1]+=click[:n]*(1-pan)
with wave.open(out+'clicks.wav','w') as w:
 w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(sound,-1,1)*32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg','-y','-i',out+'silent.mp4','-i',out+'clicks.wav','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',out+'newtons_cradle.mp4'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
print('DONE',flush=True)
