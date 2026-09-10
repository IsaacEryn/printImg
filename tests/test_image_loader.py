from PIL import Image

from image_loader import SUPPORTED_EXTENSIONS, flatten_to_rgb, load_image


def test_supported_extensions():
    assert SUPPORTED_EXTENSIONS == (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")


def test_flatten_rgba_composites_on_white():
    im = Image.new("RGBA", (2, 1), (0, 0, 0, 0))
    im.putpixel((1, 0), (255, 0, 0, 255))
    out = flatten_to_rgb(im)
    assert out.mode == "RGB"
    assert out.getpixel((0, 0)) == (255, 255, 255)
    assert out.getpixel((1, 0)) == (255, 0, 0)


def test_flatten_grayscale_becomes_rgb():
    out = flatten_to_rgb(Image.new("L", (1, 1), 77))
    assert out.mode == "RGB"
    assert out.getpixel((0, 0)) == (77, 77, 77)


def test_load_png_with_alpha(tmp_path):
    path = tmp_path / "a.png"
    im = Image.new("RGBA", (3, 2), (0, 0, 255, 0))
    im.putpixel((0, 0), (0, 0, 255, 255))
    im.save(path)
    out = load_image(path)
    assert out.mode == "RGB"
    assert out.size == (3, 2)
    assert out.getpixel((0, 0)) == (0, 0, 255)
    assert out.getpixel((2, 1)) == (255, 255, 255)


def test_load_applies_exif_orientation(tmp_path):
    path = tmp_path / "rot.jpg"
    exif = Image.Exif()
    exif[0x0112] = 6  # 시계 방향 90도 회전 필요
    Image.new("RGB", (40, 20), "white").save(path, "JPEG", exif=exif.tobytes())
    out = load_image(path)
    assert out.size == (20, 40)


def test_load_gif_uses_first_frame(tmp_path):
    path = tmp_path / "anim.gif"
    first = Image.new("RGB", (4, 4), (255, 0, 0))
    second = Image.new("RGB", (4, 4), (0, 0, 255))
    first.save(path, save_all=True, append_images=[second], duration=100)
    out = load_image(path)
    assert out.mode == "RGB"
    assert out.getpixel((0, 0)) == (255, 0, 0)
