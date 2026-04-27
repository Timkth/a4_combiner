import streamlit as st
from PIL import Image, ImageDraw
import io

# ---------------- CONFIG ---------------- #
A4_WIDTH = 2480
A4_HEIGHT = 3508

COLS = 2
ROWS = 4
IMAGES_PER_PAGE = COLS * ROWS


# ---------------- SESSION STATE ---------------- #
if "images" not in st.session_state:
    st.session_state.images = []

if "page" not in st.session_state:
    st.session_state.page = 0

if "margin" not in st.session_state:
    st.session_state.margin = 0


# ---------------- UPLOAD (NO DUPLICATES) ---------------- #
uploaded = st.file_uploader(
    "Upload images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded:
    existing = {f.name for f in st.session_state.images}

    for file in uploaded:
        if file.name not in existing:
            st.session_state.images.append(file)


# ---------------- IMAGE FIT (NO DISTORTION, NO GAPS) ---------------- #
def crop_to_fill(img, tw, th):
    img = img.convert("RGB")

    img_ratio = img.width / img.height
    target_ratio = tw / th

    if img_ratio > target_ratio:
        new_h = th
        new_w = int(th * img_ratio)
    else:
        new_w = tw
        new_h = int(tw / img_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - tw) // 2
    top = (new_h - th) // 2

    return img.crop((left, top, left + tw, top + th))


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
            img = crop_to_fill(img, cell_w, cell_h)
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


# ---------------- MARGIN (FIXED: NUMBER INPUT) ---------------- #
st.session_state.margin = st.number_input(
    "Margin (px)",
    min_value=0,
    max_value=200,
    value=st.session_state.margin,
    step=1
)


# ---------------- REMOVE IMAGES (WORKING + CLEAR UX) ---------------- #
st.subheader("Loaded Images")

cols = 4
for i in range(0, len(st.session_state.images), cols):
    row = st.columns(cols)

    for j, col in enumerate(row):
        idx = i + j

        if idx < len(st.session_state.images):
            with col:
                st.image(st.session_state.images[idx], use_container_width=True)

                if st.button("❌ Remove", key=f"rm_{idx}"):
                    st.session_state.images.pop(idx)
                    st.rerun()


# ---------------- CLEAR ---------------- #
c1, c2 = st.columns(2)

with c1:
    if st.button("🧹 Clear Page"):
        start = st.session_state.page * IMAGES_PER_PAGE
        st.session_state.images = (
            st.session_state.images[:start] +
            st.session_state.images[start + IMAGES_PER_PAGE:]
        )

with c2:
    if st.button("❌ Clear All"):
        st.session_state.images = []
        st.session_state.page = 0


# ---------------- NAVIGATION ---------------- #
total_pages = get_total_pages()

c1, c2, c3 = st.columns([1, 2, 1])

with c1:
    if st.button("⬅ Prev") and st.session_state.page > 0:
        st.session_state.page -= 1

with c2:
    st.write(f"Page {st.session_state.page + 1} / {total_pages}")

with c3:
    if st.button("Next ➡") and st.session_state.page < total_pages - 1:
        st.session_state.page += 1


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