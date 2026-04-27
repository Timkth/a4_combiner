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

if "uploaded_once" not in st.session_state:
    st.session_state.uploaded_once = set()


# ---------------- UPLOAD (FIXED: NO RE-ADDING BUG) ---------------- #
uploaded = st.file_uploader(
    "Upload images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key="uploader"
)

if uploaded:
    for file in uploaded:
        if file.name not in st.session_state.uploaded_once:
            st.session_state.images.append(file)
            st.session_state.uploaded_once.add(file.name)


# ---------------- IMAGE FIT (NO CROPPING, ASPECT SAFE) ---------------- #
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
    page_images = st.session_state.images[start:start + IMAGES_PER_PAGE]

    for i in range(IMAGES_PER_PAGE):
        col = i % COLS
        row = i // COLS

        x0 = col * (cell_w + margin)
        y0 = row * (cell_h + margin)

        if i < len(page_images):
            img = Image.open(page_images[i])
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
def get_total_pages():
    if not st.session_state.images:
        return 1
    return (len(st.session_state.images) - 1) // IMAGES_PER_PAGE + 1


# ---------------- UI ---------------- #
st.title("📄 A4 Image Combiner")


# ---------------- MARGIN ---------------- #
st.session_state.margin = st.number_input(
    "Margin (px)",
    min_value=0,
    max_value=200,
    value=st.session_state.margin,
    step=1
)


# ---------------- REMOVE IMAGES (FIXED) ---------------- #
st.subheader("Loaded Images")

for idx in range(len(st.session_state.images)):
    col1, col2 = st.columns([4, 1])

    with col1:
        st.image(st.session_state.images[idx], width=120)

    with col2:
        if st.button("❌", key=f"rm_{idx}"):
            removed = st.session_state.images.pop(idx)
            st.session_state.uploaded_once.discard(removed.name)
            st.rerun()


# ---------------- CLEAR ---------------- #
c1, c2 = st.columns(2)

with c1:
    if st.button("🧹 Clear Page"):
        start = st.session_state.page * IMAGES_PER_PAGE
        removed = st.session_state.images[start:start + IMAGES_PER_PAGE]

        for f in removed:
            st.session_state.uploaded_once.discard(f.name)

        st.session_state.images = (
            st.session_state.images[:start] +
            st.session_state.images[start + IMAGES_PER_PAGE:]
        )
        st.rerun()

with c2:
    if st.button("❌ Clear All"):
        st.session_state.images = []
        st.session_state.uploaded_once = set()
        st.session_state.page = 0
        st.rerun()


# ---------------- NAVIGATION (FIXED SYNC) ---------------- #
total_pages = get_total_pages()

c1, c2, c3 = st.columns([1, 2, 1])

with c1:
    if st.button("⬅ Prev"):
        if st.session_state.page > 0:
            st.session_state.page -= 1
            st.rerun()

with c2:
    current_page = st.session_state.page + 1
    st.write(f"Page {current_page} / {total_pages}")

with c3:
    if st.button("Next ➡"):
        if st.session_state.page < total_pages - 1:
            st.session_state.page += 1
            st.rerun()


# ---------------- PREVIEW ---------------- #
if st.session_state.images:
    preview = generate_page(st.session_state.page, draw_boxes=True)
    st.image(preview, use_container_width=True)


# ---------------- EXPORT ---------------- #
def export_pdf():
    pages = []

    for p in range(get_total_pages()):
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


if st.session_state.images:
    pdf = export_pdf()

    st.download_button(
        "📥 Download PDF",
        pdf,
        file_name="a4_export.pdf",
        mime="application/pdf"
    )