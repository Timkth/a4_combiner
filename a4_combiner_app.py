import streamlit as st
from PIL import Image, ImageDraw
import io

# ---------------- CONFIG ---------------- #
A4_WIDTH = 2480
A4_HEIGHT = 3508

COLS = 2
ROWS = 4
IMAGES_PER_PAGE = COLS * ROWS

st.set_page_config(layout="centered")


# ---------------- STATE ---------------- #
if "images" not in st.session_state:
    st.session_state.images = []

if "page" not in st.session_state:
    st.session_state.page = 0

if "margin" not in st.session_state:
    st.session_state.margin = 0

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


# ---------------- UPLOAD ---------------- #
uploaded = st.file_uploader(
    "Upload images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded:
    for file in uploaded:
        data = file.read()
        if not any(img["data"] == data for img in st.session_state.images):
            st.session_state.images.append({"data": data})


# ---------------- RESET ---------------- #
def reset_all():
    st.session_state.images = []
    st.session_state.page = 0
    st.session_state.uploader_key += 1
    st.rerun()


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


# ---------------- PREVIEW ---------------- #
def generate_preview(page):
    full = generate_page(page, draw_boxes=True)
    preview = full.copy()
    preview.thumbnail((500, 700))
    return preview


# ---------------- PAGE COUNT ---------------- #
def get_pages():
    if not st.session_state.images:
        return 1
    return (len(st.session_state.images) - 1) // IMAGES_PER_PAGE + 1


# ---------------- UI ---------------- #
st.title("📄 Paparazzi A4 Combiner")


# ---------------- MARGIN ---------------- #
st.session_state.margin = st.number_input(
    "Margin (px)",
    min_value=0,
    max_value=200,
    value=st.session_state.margin
)


# ---------------- NAV BAR (FIXED) ---------------- #
nav1, nav2, nav3 = st.columns([1, 2, 1])

with nav1:
    if st.button("⬅"):
        if st.session_state.page > 0:
            st.session_state.page -= 1
            st.rerun()

with nav2:
    st.markdown(
        f"<div style='text-align:center;'>Page {st.session_state.page + 1} / {get_pages()}</div>",
        unsafe_allow_html=True
    )

with nav3:
    if st.button("➡"):
        if st.session_state.page < get_pages() - 1:
            st.session_state.page += 1
            st.rerun()


# ---------------- PREVIEW ---------------- #
if st.session_state.images:
    preview = generate_preview(st.session_state.page)
    st.image(preview)
else:
    st.info("Upload images to begin")


# ---------------- ACTIONS (BELOW PREVIEW) ---------------- #
if st.session_state.images:

    def export_pdf():
        pages = []
        for p in range(get_pages()):
            pages.append(generate_page(p, draw_boxes=False))

        buf = io.BytesIO()
        pages[0].save(
            buf,
            format="PDF",
            save_all=True,
            append_images=pages[1:],
            resolution=300
        )
        buf.seek(0)
        return buf

    pdf = export_pdf()

    st.download_button(
        "📥 Export PDF",
        pdf,
        file_name="a4_export.pdf",
        mime="application/pdf"
    )