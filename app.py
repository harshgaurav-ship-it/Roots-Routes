import hashlib
from io import BytesIO
import re

import streamlit as st
from google import genai
from PIL import Image


st.set_page_config(
    page_title="Roots & Routes | Community Exchange",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap');
    :root {
        --ink: #202c25;
        --forest: #285344;
        --moss: #6b7d53;
        --clay: #b65d3b;
        --line: #e8e2d7;
    }
    .stApp,
    [data-testid="stAppViewContainer"] {
        background-color: #fdfbf7;
    }
    html, body, [class*="st-"] {
        color: var(--ink);
        font-family: 'DM Sans', sans-serif;
    }
    .block-container {
        max-width: none;
        width: 100%;
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: var(--ink);
        font-family: 'Fraunces', Georgia, serif;
        font-weight: 500;
    }
    [data-testid="stSidebar"] {
        background: #f0eee5;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] h1 { color: var(--forest); }
    .product-card {
        box-sizing: border-box;
        min-height: 260px;
        margin: 0 0 0.8rem;
        padding: 15px;
        border: 1px solid var(--line);
        border-top: 3px solid var(--moss);
        border-radius: 12px;
        background: #fff;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 160ms ease, box-shadow 160ms ease;
    }
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(32, 44, 37, 0.13);
    }
    .product-card h3 {
        margin: 0.4rem 0 0.65rem;
        font-size: 1.25rem;
    }
    .product-category {
        color: var(--clay);
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .product-price {
        margin: 0.6rem 0;
        color: var(--forest);
        font-size: 1.2rem;
        font-weight: 700;
    }
    .product-description {
        min-height: 2.8rem;
        color: #58645b;
        font-size: 0.92rem;
    }
    .product-artisan { font-size: 0.85rem; font-weight: 600; }
    .product-region { color: #6b756d; font-size: 0.8rem; }
    div.stButton > button[kind="primary"] {
        background: var(--forest);
        border-color: var(--forest);
    }
    div.stButton > button[kind="primary"]:hover {
        background: #1f4336;
        border-color: #1f4336;
    }
    @media (max-width: 700px) {
        .block-container { padding: 1.25rem 1rem 2rem; }
        .product-card { min-height: 0; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


PRODUCTS = [
    {
        "name": "Palash Festival Colors",
        "price": 320,
        "artisan": "Mina Soren",
        "region": "Dumka, Jharkhand",
        "category": "Forest produce",
        "description": "Illustrative natural color powders made with Palash flowers.",
        "search_terms": "palash butea monosperma flame forest flower festival holi natural colors dyes",
    },
    {
        "name": "Handwoven Bamboo Basket",
        "price": 650,
        "artisan": "Birsa Munda",
        "region": "West Singhbhum, Jharkhand",
        "category": "Handcraft",
        "description": "A sturdy, handwoven basket made with split bamboo.",
        "search_terms": "bamboo basket woven handwoven storage carrying craft home eco friendly",
    },
    {
        "name": "Raw Forest Honey",
        "price": 420,
        "artisan": "Jema Kisku",
        "region": "Mayurbhanj, Odisha",
        "category": "Forest produce",
        "description": "Small-batch honey gathered from seasonal forest blooms.",
        "search_terms": "honey raw forest wild sweet food natural seasonal flowers",
    },
    {
        "name": "Dokra Brass Elephant",
        "price": 1_850,
        "artisan": "Lakhiram Hembram",
        "region": "Bastar, Chhattisgarh",
        "category": "Metal craft",
        "description": "A cast-brass figure made using the traditional lost-wax process.",
        "search_terms": "dokra dhokra brass metal elephant art sculpture decor lost wax gift",
    },
    {
        "name": "Lac Bangles Set",
        "price": 540,
        "artisan": "Sukri Tudu",
        "region": "Ranchi, Jharkhand",
        "category": "Handcraft",
        "description": "A set of hand-shaped bangles finished with natural lac.",
        "search_terms": "lac bangles jewelry jewellery wearable craft red gift handmade",
    },
]

SEARCH_SYNONYMS = {
    "basket": {"woven", "storage"},
    "baskets": {"woven", "storage"},
    "decor": {"art", "sculpture"},
    "gift": {"bangles", "elephant", "handmade"},
    "healing": {"skincare", "skin", "natural"},
    "jewelry": {"jewellery", "bangles"},
    "lighting": {"oil", "karanj"},
    "natural": {"forest", "honey", "oil"},
    "woven": {"basket", "bamboo"},
}

VISION_PROMPT = (
    "You are a botanical and cultural expert. Identify the plant, flower, or "
    "traditional craft in this image. Then, provide a brief paragraph explaining "
    "its traditional uses among tribal communities in Jharkhand or eastern India."
)
VISION_MODEL = 'gemini-3.8-flash'


def call_vision_api(image_bytes: bytes, api_key: str) -> str:
    """Send a PIL-converted image and the required prompt to Gemini."""
    with Image.open(BytesIO(image_bytes)) as uploaded_image:
        image = uploaded_image.convert("RGB")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=VISION_MODEL,
        contents=[VISION_PROMPT, image],
    )
    if not response.text:
        raise ValueError("The model returned an empty response.")
    return response.text.strip()


def open_related_products(analysis_text: str) -> None:
    related_products = find_products(analysis_text)
    st.session_state["marketplace_query"] = (
        related_products[0]["name"] if related_products else ""
    )
    st.session_state["active_page"] = "Tribal Marketplace"


def find_products(query: str) -> list[dict[str, str | int]]:
    """Filter listings with lightweight token matching and a small synonym map."""
    query_tokens = set(re.findall(r"[a-z0-9]+", query.casefold()))
    if not query_tokens:
        return PRODUCTS

    expanded_tokens = set(query_tokens)
    for token in query_tokens:
        expanded_tokens.update(SEARCH_SYNONYMS.get(token, set()))

    scored_products = []
    for product in PRODUCTS:
        searchable_text = " ".join(
            str(product[field])
            for field in ("name", "category", "description", "search_terms")
        ).casefold()
        searchable_tokens = set(re.findall(r"[a-z0-9]+", searchable_text))
        score = len(expanded_tokens & searchable_tokens)
        if score:
            scored_products.append((score, product))

    return [product for _, product in sorted(scored_products, key=lambda match: -match[0])]


def render_heritage_archive(api_key: str) -> None:
    st.markdown("## Heritage Archive")
    st.caption("A living record of plants, materials, and community knowledge")

    uploaded_image = st.file_uploader(
        "Choose a plant or craft image",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
    )

    if not uploaded_image:
        st.info("Upload an image to begin a record.")
        return

    image_bytes = uploaded_image.getvalue()
    image_key = hashlib.sha256(image_bytes).hexdigest()
    st.image(image_bytes, caption=uploaded_image.name, width="stretch")

    if (
        st.session_state.get("analysis_image_hash") != image_key
        and st.session_state.get("analysis_failed_hash") != image_key
    ):
        if not api_key.strip():
            st.warning("Enter your Google AI API key in the sidebar to analyze this image.")
            return

        with st.spinner("Examining the image…"):
            try:
                analysis = call_vision_api(image_bytes, api_key.strip())
            except Exception as e:
                st.session_state["analysis_failed_hash"] = image_key
                st.session_state["error_msg"] = str(e)
            else:
                st.session_state["analysis_result"] = analysis
                st.session_state["analysis_image_hash"] = image_key
                st.session_state.pop("analysis_failed_hash", None)
                st.toast("🌿 Traditional knowledge match found!")
                st.balloons()

    if st.session_state.get("analysis_failed_hash") == image_key:
        st.error(f"System Error: {st.session_state.get('error_msg')}")
        if st.button("Retry analysis", key=f"retry_{image_key[:12]}"):
            st.session_state.pop("analysis_failed_hash", None)
            st.rerun()
        return

    if st.session_state.get("analysis_image_hash") != image_key:
        return

    analysis = st.session_state["analysis_result"]
    st.markdown("### AI analysis")
    st.success(analysis)
    st.caption(
        "AI-generated guidance may be inaccurate or incomplete. Confirm traditional "
        "knowledge with relevant communities and obtain consent before sharing."
    )

    st.button(
        "View Related Artisan Products",
        type="primary",
        on_click=open_related_products,
        args=(analysis,),
    )


def render_marketplace() -> None:
    st.markdown("## Tribal Marketplace")
    st.caption("A sample collection from independent artisan listings")

    query = st.text_input(
        "Search the collection",
        key="marketplace_query",
        placeholder="Try bamboo, honey, oil, or handmade gifts",
    )
    matching_products = find_products(query)

    if not matching_products:
        st.info("No listings match that search. Try another word.")
        return

    for row_start in range(0, len(matching_products), 3):
        columns = st.columns(3, gap="medium")
        for column, product in zip(columns, matching_products[row_start : row_start + 3]):
            with column:
                st.markdown(
                    f"""
                    <div class="product-card">
                      <div class="product-category">{product['category']}</div>
                      <h3>{product['name']}</h3>
                      <div class="product-price">₹{product['price']:,}</div>
                      <p class="product-description">{product['description']}</p>
                      <div class="product-artisan">Verified artisan · {product['artisan']}</div>
                      <div class="product-region">{product['region']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Buy Now",
                    key=f"buy_{product['name']}",
                    width="stretch",
                ):
                    st.session_state["purchase_confirmation"] = product["name"]

    purchased_item = st.session_state.pop("purchase_confirmation", None)
    if purchased_item:
        st.success(f"Demo only: your inquiry for {purchased_item} has been noted.")

    st.caption(
        "Sample listings, artisan names, and verification labels are illustrative; "
        "confirm details with participating communities before launch."
    )


def main() -> None:
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "Heritage Archive"

    with st.sidebar:
        st.markdown("# Roots & Routes")
        st.caption("Community knowledge · artisan exchange")
        api_key = st.text_input(
            "Google AI API key",
            type="password",
            key="google_ai_api_key",
            help="Used for image analysis. For production, prefer Streamlit secrets.",
        )
        st.radio(
            "Explore",
            ["Heritage Archive", "Tribal Marketplace"],
            key="active_page",
            label_visibility="collapsed",
        )

    if st.session_state["active_page"] == "Heritage Archive":
        render_heritage_archive(api_key)
    else:
        render_marketplace()


if __name__ == "__main__":
    main()