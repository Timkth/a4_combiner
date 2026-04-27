import streamlit as st
from PIL import Image, ImageDraw
import io

# ---------------- CONFIG ---------------- #
A4_WIDTH = 2480
A4_HEIGHT = 3508

COLS = 2
ROWS = 4
IMAGES_PER_PAGE = COLS * ROWS


# ---------------- STATE ---------------- #
if "images" not in st.session_state:
    st.session_state.images = []

if "page" not in st.session_state:
    st.session_state.page = 0

if "margin" not in st.session_state:
    st.session_state.margin = 0


# ---------------- UPLOAD ---------------- #
uploaded = st.file_uploader(
    "Upload images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded:
    for file in uploaded:
        data = file.read()

        # prevent duplicates by raw bytes hash
        if not any(img["data"] == data for img in st.session_state.images):
            st.session_state.images.append({"data": data})


# ---------------- IMAGE FIT ---------------- #
def fit_inside(img, tw, th):
    img = img.convert("RGB")
    img.thumbnail((tw, th))

    canvas = Image.new("RGB", (tw, th), "white")

    x = (tw - img.width) // 2
    y = (th - img.height) // 2

    canvas.paste(img, (x, y))
    return canvas


# ---------------- PAGE GENERATION ---------------- #
def generate_page(page, draw_boxes=True):
    margin = st.session_state.margin

    cell_w = (A4_WIDTH - (COLS - 1) * margin) // COLS
    cell_h = (A4_HEIGHT - (ROWS - 1) * margin) // ROWS

    canvas = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)

    start = page * IMAGES_PER_PAGE
    items = st.session_state.images[start:start + IMAGES_PER_PAGE]

    for i in range(IMAGES_PER_PAGE):
        col = i % COLS
        row = i // COLS

        x0 = col * (cell_w + margin)
        y0 = row * (cell_h + margin)

        if i < len(items):
            img = Image.open(io.BytesIO(items[i]["data"]))
            img = fit_inside(img, cell_w, cell_h)
            canvas.paste(img, (x0, y0))

        if draw_boxes:
            draw.rectangle(
                [x0, y0, x0 + cell_w, y0 + cell_h],
                outline="black",
                width=2
            )

    return canvas


# ---------------- PAGE COUNT ---------------- #
def get_pages():
    if not st.session_state.images:
        return 1
    return (len(st.session_state.images) - 1) // IMAGES_PER_PAGE + 1


# ---------------- UI ---------------- #
st.title("📄 A4 Image Combiner (Simple)")


# ---------------- MARGIN ---------------- #
st.session_state.margin = st.number_input(
    "Margin (px)",
    min_value=0,
    max_value=200,
    value=st.session_state.margin
)


# ---------------- NAVIGATION ---------------- #
pages = get_pages()

c1, c2, c3 = st.columns([1, 2, 1])

with c1:
    if st.button("⬅ Prev") and st.session_state.page > 0:
        st.session_state.page -= 1
        st.rerun()

with c2:
    st.write(f"Page {st.session_state.page + 1} / {pages}")

with c3:
    if st.button("Next ➡") and st.session_state.page < pages - 1:
        st.session_state.page += 1
        st.rerun()


# ---------------- PREVIEW ---------------- #
if st.session_state.images:
    preview = generate_page(st.session_state.page, draw_boxes=True)
    st.image(preview, use_container_width=True)


# ---------------- EXPORT ---------------- #
def export_pdf():
    pages_list = []

    for p in range(get_pages()):
        pages_list.append(generate_page(p, draw_boxes=False))

    buf = io.BytesIO()

    pages_list[0].save(
        buf,
        format="PDF",
        save_all=True,
        append_images=pages_list[1:],
        resolution=300
    )

    buf.seek(0)
    return buf


if st.session_state.images:
    pdf = export_pdf()

    st.download_button(
        "📥 Download PDF",
        pdf,
        file_name="a4_export.pdf",
        mime="application/pdf"
    )