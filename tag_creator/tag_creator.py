import cairo
import numpy
import qrcode
from PIL import Image
import math
from urllib.parse import urlparse, parse_qs
import requests
from io import BytesIO
import argparse

MM_TO_POINTS = 72 / 2.54 / 10

#Width and Height of QRCode in mm
WIDTH, HEIGHT = 25, 25


def get_yt_thumbnail(url):
	vid = video_id(url)

	img_url = 'https://img.youtube.com/vi/%s/0.jpg' % vid
	print(img_url)
	response = requests.get(img_url)
	img = Image.open(BytesIO(response.content))

	return img


def video_id(value):
	"""
	Examples:
	- http://youtu.be/SA2iWivDJiE
	- http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
	- http://www.youtube.com/embed/SA2iWivDJiE
	- http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
	"""
	query = urlparse(value)
	if query.hostname == 'youtu.be':
		return query.path[1:]
	if query.hostname in ('www.youtube.com', 'youtube.com'):
		if query.path == '/watch':
			p = parse_qs(query.query)
			return p['v'][0]
		if query.path[:7] == '/embed/':
			return query.path.split('/')[2]
		if query.path[:3] == '/v/':
			return query.path.split('/')[2]
	# fail?
	return None


def surface_from_pil(im, alpha=1.0, format=cairo.FORMAT_ARGB32):
	"""
	:param im: Pillow Image
	:param alpha: 0..1 alpha to add to non-alpha images
	:param format: Pixel format for output surface
	"""
	assert format in (cairo.FORMAT_RGB24, cairo.FORMAT_ARGB32), "Unsupported pixel format: %s" % format
	if 'A' not in im.getbands():
			im.putalpha(int(alpha * 256.))
	arr = bytearray(im.tobytes('raw', 'BGRa'))
	surface = cairo.ImageSurface.create_for_data(arr, format, im.width, im.height)
	return surface


def add_tag(cr, yt_url, off_x, off_y, margin, width, height):

	cr.rectangle(*[MM_TO_POINTS*v for v in (0+off_x,0+off_y, width, height)]) # Thumbnail-Rectangle
	cr.rectangle(*[MM_TO_POINTS*v for v in (0+off_x,0+off_y+margin+height, width, width)]) # QR-Code-Rectangle
	cr.stroke()
	
	surface = surface_from_pil(qrcode.make(yt_url).convert('RGB'))
	print(surface.get_width(), surface.get_height())

	cr.save()
	sfx, sfy = (width*MM_TO_POINTS/surface.get_width(), height*MM_TO_POINTS/surface.get_height())
	cr.scale(sfx, sfy)
	cr.set_source_surface(surface, off_x*MM_TO_POINTS/sfx, (off_y+margin+height)*MM_TO_POINTS/sfy)
	cr.paint()
	cr.restore()

	thumbnail_img = crop_to_square(get_yt_thumbnail(yt_url))
	cr.save()
	surface = surface_from_pil(thumbnail_img) #.transpose(Image.ROTATE_180)
	sfx, sfy = (width*MM_TO_POINTS/surface.get_width(), height*MM_TO_POINTS/surface.get_height())
	cr.scale(sfx, sfy)
	cr.set_source_surface(surface, off_x*MM_TO_POINTS/sfx, (off_y)*MM_TO_POINTS/sfy)
	cr.paint()
	cr.restore()

def crop_to_square(image):
	width, height = image.size
	# Find the smallest side length
	min_side = min(width, height)
	# Calculate coordinates for cropping
	left = (width - min_side) / 2
	top = (height - min_side) / 2
	right = (width + min_side) / 2
	bottom = (height + min_side) / 2
	# Crop the image
	cropped_image = cropped_image.crop((left, top, right, bottom))
	cropped_image.show()
	return cropped_image

def draw():
	parser = argparse.ArgumentParser(description='Convert Youtube URLs to QR code tags')
	parser.add_argument('urls', metavar='URL', type=str, nargs='+', help='Youtube URLs')
	args = parser.parse_args()

	pdf_width, pdf_height = 504,568
	ps = cairo.PDFSurface("pdffile.pdf", pdf_width, pdf_height)
	cr = cairo.Context(ps)
	cr.set_source_rgb(0, 0, 0)
	cr.set_line_width(0.2 * MM_TO_POINTS)

	idx_x = 0
	idx_y = 0
	margin = 5
	width = WIDTH
	height = HEIGHT
	for url in args.urls:
		if (idx_x+1)*(width+margin) >= pdf_width/MM_TO_POINTS:
			idx_y += 1
			idx_x = 0 
		add_tag(cr, url, margin+idx_x*(width+margin), margin+idx_y*(height+margin)*2, margin, width, height)
		idx_x += 1
		
	
	cr.show_page()

draw()
