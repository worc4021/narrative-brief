from pathlib import Path

import pytest

from tools.plates import AssetStore


def _png(tmp_path: Path, name: str, size=(1600, 1000), colour=(20, 90, 160)) -> Path:
    from PIL import Image

    p = tmp_path / name
    Image.new("RGB", size, colour).save(p)
    return p


def test_transcodes_to_webp_data_uri(tmp_path):
    store = AssetStore()
    src = store.src(_png(tmp_path, "fig.png"))
    assert src.startswith("data:image/webp;base64,")
    assert store.warnings == ()


def test_identical_content_is_embedded_once(tmp_path):
    store = AssetStore()
    a = store.src(_png(tmp_path, "a.png"))
    b = store.src(_png(tmp_path, "b.png"))  # different filename, identical pixels
    assert a == b
    assert store.payload_bytes == len(a)


def test_different_images_produce_different_payloads(tmp_path):
    store = AssetStore()
    a = store.src(_png(tmp_path, "a.png", colour=(10, 10, 10)))
    b = store.src(_png(tmp_path, "b.png", colour=(240, 10, 10)))
    assert a != b


def test_narrow_source_warns_but_still_renders(tmp_path):
    store = AssetStore()
    src = store.src(_png(tmp_path, "small.png", size=(400, 300)))
    assert src.startswith("data:image/webp;base64,")
    assert len(store.warnings) == 1
    assert "400" in store.warnings[0] and "640" in store.warnings[0]


@pytest.mark.parametrize("mode", ["P", "L"])
def test_palette_and_greyscale_sources_are_converted_and_still_transcode(tmp_path, mode):
    # Plotting tools routinely write palette or greyscale PNGs, so this is the
    # common path for `image` visuals, not an edge case. WebP cannot encode
    # mode "P" at all, so without the conversion this raises.
    from PIL import Image

    p = tmp_path / f"{mode}.png"
    Image.new(mode, (1600, 1000)).save(p)
    assert Image.open(p).mode == mode

    store = AssetStore()
    src = store.src(p)
    assert src.startswith("data:image/webp;base64,")
    assert store.warnings == ()


def test_missing_file_raises_with_the_path(tmp_path):
    store = AssetStore()
    with pytest.raises(FileNotFoundError) as err:
        store.src(tmp_path / "nope.png")
    assert "nope.png" in str(err.value)


def test_webp_is_much_smaller_than_the_source_png(tmp_path):
    from PIL import Image

    src_path = _png(tmp_path, "big.png")
    img = Image.open(src_path).convert("RGB")
    for x in range(0, 1600, 3):  # add detail so PNG cannot trivially compress it
        for y in range(0, 1000, 97):
            img.putpixel((x, y), (x % 255, y % 255, 90))
    img.save(src_path)

    store = AssetStore()
    store.src(src_path)
    assert store.payload_bytes < src_path.stat().st_size
