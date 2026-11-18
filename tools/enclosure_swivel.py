"""enclosure_swivel.py OUT.png : top view (front, y down) of the FLIPOUT-style halves, pivot on the right, camera sweep (needs shapely + pillow)
import sys
import shapely
from shapely import affinity
from PIL import Image, ImageDraw

S, A = 98.5, 22.5
P = (S - A, A)                       # pivot, right side
kb_half = shapely.box(0, 0, S, S)
keys = shapely.box(12.25, S - 53.1 - 1.5, S - 12.25, S - 1.5)          # Board B 74 x 53.1 at the bottom
battery = shapely.box((S - 85) / 2, S - 1.5 - 65, (S + 85) / 2, S - 1.5)  # 85 x 65 under it
pivot_boss = shapely.Point(P).buffer(6)
screen_closed = shapely.box(0, 0, S, S)
# open position: rotate about P so the screen half moves up (y < 0)
for ang in (90, -90):
    o = affinity.rotate(screen_closed, ang, origin=P)
    if o.bounds[1] < -1:
        OPEN = ang
        break
screen_open = affinity.rotate(screen_closed, OPEN, origin=P)
print('screen half open bounds', [round(v, 1) for v in screen_open.bounds], 'rotation', OPEN)
# camera (34 x 34 incl. margin) in the screen half's open frame: top-right of its top band, behind Board A by J704
cam_open = shapely.box(63.5, -51.5, 97.5, -17.5)
assert screen_open.buffer(0.01).contains(cam_open)
cam_closed = affinity.rotate(cam_open, -OPEN, origin=P)
print('camera closed bounds', [round(v, 1) for v in cam_closed.bounds])
sweep = shapely.union_all([affinity.rotate(cam_closed, OPEN * k / 90, origin=P) for k in range(0, 91)])
channel = sweep.intersection(kb_half)
print('channel bounds in keyboard half', [round(v, 1) for v in channel.bounds], 'area %.0f mm2' % channel.area)
print('channel hits keys: %.1f mm2, battery: %.1f mm2, pivot boss: %.1f mm2' % (channel.intersection(keys).area, channel.intersection(battery).area, channel.intersection(pivot_boss).area))
print('nearest channel edge to pivot centre: %.1f mm' % channel.distance(shapely.Point(P)))
# overlap band free of keys
print('open overlap band: y 0 to %.1f' % screen_open.intersection(kb_half).bounds[3])

# drawing
k = 5.0
ox, oy = 20, 20 + 60 * k
W, H = int(S * k + 40), int((S + 60) * k + 70)
img = Image.new('RGB', (W, H), (250, 250, 247))
d = ImageDraw.Draw(img)
def poly(g, fill=None, outline=None, width=2):
    for p in getattr(g, 'geoms', [g]):
        pts = [(ox + x * k, oy + y * k) for x, y in p.exterior.coords]
        d.polygon(pts, fill=fill, outline=outline, width=width)
poly(kb_half, fill=(225, 225, 225), outline=(60, 60, 60))
poly(battery, fill=(205, 222, 240), outline=(90, 120, 170))
poly(keys, fill=(190, 190, 190), outline=(80, 80, 80))
poly(channel, fill=(250, 205, 150), outline=(200, 120, 40))
poly(screen_open, outline=(40, 90, 200), width=3)
poly(cam_open, fill=(120, 170, 240), outline=(30, 60, 160))
poly(cam_closed, outline=(200, 60, 40), width=3)
px, py = ox + P[0] * k, oy + P[1] * k
d.ellipse([px - 6 * k, py - 6 * k, px + 6 * k, py + 6 * k], fill=(60, 60, 60))
lab = [((4, -50), 'screen half, open (blue outline)'), ((66, -14), 'camera, open'), ((cam_closed.bounds[0] + 1, cam_closed.bounds[1] + 14), 'camera, closed'),
       ((3, 5), 'channel in keyboard half (orange)'), ((14, 62), 'keyboard / Board B'), ((10, 37), 'battery under the keyboard (blue)'), ((P[0] - 6, P[1] + 8), 'pivot')]
for (x, y), t in lab:
    d.text((ox + x * k, oy + y * k), t, fill=(0, 0, 0))
d.text((10, H - 20), 'Top view from the front, open position, 1 square = 98.5 mm; pivot on the right, 22.5 mm in from both edges', fill=(0, 0, 0))
img.save(sys.argv[1])
