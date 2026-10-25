# styles.py
# All of Second Look's look and feel lives here.
# app.py calls apply_styles() once, right after st.set_page_config.
#
# Contrast checks (the goal is 7:1 or more for all text):
#   body text  #1B1F24 on white or on the page color: about 16:1
#   body text  #1B1F24 on the striped table rows:     about 15:1
#   body text  #1B1F24 on the light notice box #E9ECF3: about 14:1
#   navy       #14213D on the page color:             about 15:1
#   white text on navy (buttons, headline band, footer): about 16:1
#   white text on the lighter navy hover color #2A3756: about 12:1
#   secondary  #4A5260 on the page color:             about 7.5:1
#   secondary  #4A5260 on white:                      about 7.9:1
#   gold       #9A7B2F is ONLY a thin decorative line, never text.

import streamlit as st

CSS = """
<style>
/* ---------- 1. Colors, font and spacing, all in one place ---------- */
:root {
    --font: "Times New Roman", Times, Georgia, serif;

    --page: #FAF9F6;            /* the page behind everything */
    --card: #FFFFFF;            /* cards */
    --card-border: #D5DAE1;     /* the thin line around cards */
    --navy: #14213D;            /* headings, primary buttons, dark bands */
    --navy-hover: #0A1226;      /* primary buttons under the mouse */
    --navy-soft: #2A3756;       /* buttons under the mouse, inside a navy band */
    --white: #FFFFFF;           /* text inside navy bands */
    --text: #1B1F24;            /* body text */
    --text-secondary: #4A5260;  /* small helper text, and borders on boxes you type in */
    --gold: #9A7B2F;            /* decorative divider ONLY, never text */
    --tint: #E9ECF3;            /* a chosen answer, a button under the mouse, the top notice */
    --row-alt: #F3F4F7;         /* every other row in the Compare table */

    --text-space: 20px;         /* between a heading and the text below it */
    --section-space: 48px;      /* between sections */
    --side-margin: 5vw;         /* about 5% of the window on each side */
    --line-length: 75ch;        /* about 75 characters per line */
    --card-padding: 32px;       /* the space inside a card, next to its border */
}

/* ---------- 2. No animations anywhere ---------- */
*, *::before, *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
}
/* Streamlit fades old content while the page updates. Keep it fully dark. */
.stApp [data-stale="true"] {
    opacity: 1 !important;
}

/* ---------- 3. One font for every piece of text ---------- */
/* Streamlit sizes many things in "rem", so this scales them too. */
html {
    font-size: 22px;
}
/* Everything, including buttons, boxes and drop-down lists.
   The only exception is Streamlit's small picture icons, which need their own font. */
body *:not([data-testid="stIconMaterial"]) {
    font-family: var(--font) !important;
}

/* ---------- 4. The page and body text ---------- */
.stApp,
[data-testid="stAppViewContainer"] {
    background-color: var(--page);
    color: var(--text);
}
.stApp p,
.stApp li,
.stApp label {
    font-size: 22px;
    line-height: 1.6;
    color: var(--text);
}
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] ul,
.stApp [data-testid="stMarkdownContainer"] ol {
    margin: 0 0 var(--text-space) 0;
}
/* The last thing in a block of text has no extra space under it,
   so the space between blocks stays even. */
.stApp [data-testid="stMarkdownContainer"] > *:last-child {
    margin-bottom: 0 !important;
}
/* Streamlit pulls every block of text up by about 22px (a negative margin).
   Because the space under the last paragraph is already gone (the rule above),
   that pull made separate blocks of text touch. Cancel it, so every block
   gets the normal 20px gap. */
.stApp [data-testid="stMarkdown"],
.stApp [data-testid="stMarkdownContainer"] {
    margin-bottom: 0 !important;
}

/* Keep paragraphs to about 75 characters per line, so they stay easy to read */
.stApp [data-testid="stMarkdown"] p,
.stApp [data-testid="stMarkdown"] li,
.stApp [data-testid="stAlert"] p {
    max-width: var(--line-length);
}
/* Button words are short, so they may use the whole button */
.stApp .stButton p {
    max-width: none;
}

/* The notice at the top of every page ("educational, not advice"):
   a light box across the page, with the sentence in the middle.
   On a wide screen it fits on one line; on a narrow one it wraps,
   and every line stays centered. */
.stApp .st-key-notice_top {
    background-color: var(--tint);
    border-radius: 12px;
    padding: 20px 32px;
}
.stApp .st-key-notice_top p {
    max-width: none !important;
    margin: 0 auto !important;
    text-align: center;
}

/* Links: navy AND underlined, so they never depend on color alone */
.stApp a {
    color: var(--navy) !important;
    text-decoration: underline !important;
    text-underline-offset: 3px;
}

/* ---------- 5. Headings ---------- */
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4 {
    color: var(--navy) !important;
    font-weight: 700 !important;
    margin: 0 0 var(--text-space) 0 !important;
    padding: 0 !important;
}
/* Streamlit wraps each heading in its own little box, which adds space
   above and below it. Remove that, so headings sit where we expect. */
.stApp [data-testid="stHeadingWithActionElements"],
.stApp [data-testid="stHeading"] {
    margin: 0 !important;
    padding: 0 !important;
}
/* A heading that is the last thing in its block of text (like a card title
   written on its own) gets no space under it, so the normal 20px gap is the
   only space between it and the next thing. */
.stApp [data-testid="stMarkdownContainer"] > *:last-child h1,
.stApp [data-testid="stMarkdownContainer"] > *:last-child h2,
.stApp [data-testid="stMarkdownContainer"] > *:last-child h3,
.stApp [data-testid="stMarkdownContainer"] > *:last-child h4 {
    margin-bottom: 0 !important;
}
/* Page titles */
.stApp h1 {
    font-size: 44px !important;
    line-height: 1.25 !important;
}
/* Section headings */
.stApp h2,
.stApp h3 {
    font-size: 32px !important;
    line-height: 1.3 !important;
}
/* Card titles (product names, "Worth thinking about", and so on) */
.stApp h4 {
    font-size: 28px !important;
    line-height: 1.3 !important;
}
/* Text inside a heading keeps the heading's size */
.stApp h1 span,
.stApp h2 span,
.stApp h3 span,
.stApp h4 span {
    font-size: inherit !important;
}
/* Hide the little link icons Streamlit puts next to headings */
[data-testid="stHeaderActionElements"] {
    display: none !important;
}

/* ---------- 6. Use the whole window ---------- */
/* No space at the bottom: the footer band sits right at the end of the page. */
.stApp [data-testid="stMainBlockContainer"],
.stApp .block-container {
    max-width: none !important;
    padding: 40px var(--side-margin) 0 var(--side-margin) !important;
}
/* Space between things stacked on top of each other */
.stApp [data-testid="stVerticalBlock"] {
    gap: var(--text-space);
}
/* Space between things side by side (like the five page buttons) */
.stApp [data-testid="stHorizontalBlock"] {
    gap: 16px;
}

/* ---------- 7. Cards ---------- */
/* Every card's key starts with "card_" in app.py.
   The bottom margin plus the normal 20px gap makes about 48px between sections. */
.stApp [class*="st-key-card_"] {
    background-color: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: var(--card-padding);
    margin-bottom: calc(var(--section-space) - var(--text-space));
}
/* The scam card gets a thick navy border, so it stands out by its shape too.
   (It also always has its 🚩 icon and its title in words.) */
.stApp [class*="st-key-card_scam"] {
    border: 4px solid var(--navy);
}

/* Boxes inside a card ("Worth thinking about", "Warning signs", captions):
   a dashed border, so they look different from the card around them */
.stApp [class*="st-key-notes_"] {
    background-color: var(--card);
    border: 2px dashed var(--text-secondary);
    border-radius: 12px;
    padding: 20px 24px;
}
/* The warning signs box, when we found some: a thick solid navy border,
   so it stands out by its shape too. (It also has its 🚩 icon and its count in words.) */
.stApp [class*="st-key-notes_flags_found"] {
    border: 4px solid var(--navy);
}

/* The thin gold line between sections. Decoration only. */
.stApp [data-testid="stMarkdownContainer"] hr {
    border: none !important;
    border-top: 1px solid var(--gold) !important;
    margin: calc(var(--section-space) - var(--text-space)) 0 !important;
    background: none !important;
}

/* The block bars in the gauges */
.stApp .gauge {
    margin: 0 0 8px 0 !important;
}
.stApp .gauge-bar {
    font-size: 30px;
    letter-spacing: 4px;
    color: var(--navy);
}

/* The two badges ("Getting money out" and "Cost").
   They sit side by side when both fit. When the card is too narrow,
   the second one moves under the first, so nothing gets squeezed. */
.stApp .badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 16px 40px;    /* 16px between rows, 40px between the two badges */
}
.stApp .badge {
    flex: 1 1 auto;    /* as wide as its words, and shares any spare room */
    min-width: 0;
}
.stApp .badge p {
    margin: 0 !important;
    max-width: none !important;
}
/* The small title above each badge */
.stApp .badge-title {
    font-size: 22px !important;
    font-weight: 700;
    line-height: 1.3 !important;
    color: var(--text) !important;
}
/* The badge itself: as big as the tier name, with the icon right next to the word */
.stApp .badge-value {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 32px !important;
    line-height: 1.3 !important;
    font-weight: 700;
    color: var(--navy) !important;
}
/* The icon never shrinks or moves onto its own line */
.stApp .badge-icon {
    flex: none;
}

/* ---------- 8. Small helper text and message boxes ---------- */
/* Like "Press Ctrl+Enter" and the letter count under the big text box */
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] *,
.stApp small,
.stApp [data-testid="InputInstructions"],
.stApp [data-testid="InputInstructions"] * {
    color: var(--text-secondary) !important;
    font-size: 18px !important;
}
/* Message boxes (notice, warnings, "Done"): dark text, never colored text */
.stApp [data-testid="stAlert"] * {
    color: var(--text) !important;
}
/* The Demo replay banner at the top of every page (key "replay_banner" in app.py):
   its words may use the whole width of the window, so the banner takes
   as few lines as possible. Every other paragraph keeps its 75-character limit. */
.stApp .st-key-replay_banner [data-testid="stAlert"] p {
    max-width: none !important;
}
/* The command in it (python save_demo_cache.py) is as big as the words around it */
.stApp .st-key-replay_banner code {
    font-size: 1em !important;
    font-weight: 700;
    background: none !important;
    padding: 0 !important;
}

/* ---------- 9. Questions with choices (Your situation, Voice speed, Check an offer) ---------- */
/* The question above the choices: as big as a card title */
.stApp [data-testid="stRadio"] [data-testid="stWidgetLabel"] p {
    font-size: 28px !important;
    font-weight: 700;
    line-height: 1.3;
    color: var(--navy) !important;
}
.stApp [data-testid="stWidgetLabel"] {
    margin-bottom: 12px;
}
/* Space between the choices */
.stApp [data-testid="stRadio"] [role="radiogroup"] {
    gap: 12px;
}
/* Each choice is a big box that is easy to click */
.stApp [data-testid="stRadio"] [role="radiogroup"] label {
    width: 100%;
    min-height: 64px;
    padding: 12px 16px;
    background-color: var(--card);
    border: 2px solid var(--text-secondary);
    border-radius: 12px;
    align-items: center;
    cursor: pointer;
}
/* The round dot: one and a half times bigger */
.stApp [data-testid="stRadio"] [role="radiogroup"] label > div:first-child {
    transform: scale(1.5);
    margin-right: 14px;
}
.stApp [data-testid="stRadio"] [role="radiogroup"] label p {
    font-size: 24px !important;
}
/* The chosen answer: a thicker border and bold words, not just a color */
.stApp [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
    border: 4px solid var(--navy);
    background-color: var(--tint);
}
.stApp [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p {
    font-weight: 700;
}
/* Check an offer, step 1: the three ways sit on one line as three equal boxes
   across the whole card. Streamlit makes the box around a choice widget only
   as wide as its words, so every box from the card down to the choices is told
   to use the full width. On smaller screens they stack (see section 21). */
.stApp .st-key-card_offer_way [data-testid="stElementContainer"],
.stApp .st-key-card_offer_way [data-testid="stRadio"],
.stApp .st-key-card_offer_way [data-testid="stRadio"] > div {
    width: 100% !important;
    max-width: none !important;
}
.stApp .st-key-card_offer_way [role="radiogroup"] {
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
    width: 100% !important;
    max-width: none !important;
}
/* Streamlit wraps each choice in its own little box: let it fill its column */
.stApp .st-key-card_offer_way [role="radiogroup"] > * {
    width: 100% !important;
    min-width: 0;
    margin: 0 !important;
}
.stApp .st-key-card_offer_way [role="radiogroup"] label {
    width: 100% !important;
    height: auto !important;
    flex: none !important;
    margin: 0 !important;
    min-height: 72px;
}
/* Step 1's sentences may use the whole width of the card,
   so the privacy line fits on one line on a wide screen */
.stApp .st-key-card_offer_way p {
    max-width: none !important;
}

/* The Compare checkbox: big and bold, so it is easy to click */
.stApp [data-testid="stCheckbox"] label p {
    font-size: 24px !important;
    font-weight: 700;
}

/* ---------- 10. Check an offer: text box, drop-down, recorder ---------- */
/* Their labels: bold and clear, but a little smaller than the step titles,
   so the steps lead the eye */
.stApp [data-testid="stTextArea"] [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stAudioInput"] [data-testid="stWidgetLabel"] p {
    font-size: 24px !important;
    font-weight: 700;
    line-height: 1.3;
    color: var(--navy) !important;
}
/* The big text box: large dark text, white inside, and a clear border */
.stApp textarea {
    font-size: 22px !important;
    line-height: 1.5 !important;
    color: var(--text) !important;
    background-color: var(--card) !important;
    border: 2px solid var(--text-secondary) !important;
    border-radius: 12px !important;
}
.stApp textarea::placeholder {
    color: var(--text-secondary) !important;
    opacity: 1;
}
/* The drop-down: tall, white inside, with a clear border.
   (!important, because Streamlit's own style removes the border otherwise.) */
.stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    min-height: 60px;
    font-size: 22px;
    background-color: var(--card) !important;
    border: 2px solid var(--text-secondary) !important;
    border-radius: 12px !important;
}
/* Dark words in the drop-down, including "Choose OFFER 1 to 6" */
.stApp [data-testid="stSelectbox"] [data-baseweb="select"] * {
    color: var(--text) !important;
}
/* The open list of choices */
[data-baseweb="popover"] li,
[data-baseweb="popover"] [role="option"] {
    font-size: 22px !important;
    color: var(--text) !important;
}
/* The recorder: a clear border so it is easy to find */
.stApp [data-testid="stAudioInput"] > div:last-child {
    background-color: var(--card);
    border: 2px solid var(--text-secondary);
    border-radius: 12px;
    min-height: 72px;
}

/* The voice player: full width and tall, so its buttons are easy to press */
.stApp audio {
    width: 100%;
    height: 64px;
}

/* "Show me the numbers" and Common questions: big bold title and a clear border */
.stApp [data-testid="stExpander"] details {
    background-color: var(--card);
    border: 2px solid var(--text-secondary);
    border-radius: 12px;
}
.stApp [data-testid="stExpander"] summary p {
    font-size: 24px !important;
    font-weight: 700;
    color: var(--navy) !important;
}

/* ---------- 11. Buttons ---------- */
/* Every button: at least 60px tall, 24px bold words, outlined in navy */
.stApp .stButton > button {
    min-height: 60px;
    width: 100%;
    padding: 10px 16px;
    background-color: var(--card);
    color: var(--navy);
    border: 3px solid var(--navy);
    border-radius: 12px;
    box-shadow: none;
    white-space: normal;  /* long labels wrap instead of being cut off */
}
.stApp .stButton > button * {
    color: inherit !important;
}
.stApp .stButton > button p {
    font-size: 24px !important;
    font-weight: 700;
    line-height: 1.25;
    margin: 0;
}
.stApp .stButton > button:hover,
.stApp .stButton > button:active {
    background-color: var(--tint);
    color: var(--navy);
    border-color: var(--navy);
}

/* Primary buttons (the page you are on, and main actions): filled navy, white words */
.stApp .stButton > button[kind="primary"],
.stApp .stButton > button[data-testid="stBaseButton-primary"] {
    background-color: var(--navy);
    color: var(--white);
    border-color: var(--navy);
}
.stApp .stButton > button[kind="primary"]:hover,
.stApp .stButton > button[kind="primary"]:active,
.stApp .stButton > button[data-testid="stBaseButton-primary"]:hover,
.stApp .stButton > button[data-testid="stBaseButton-primary"]:active {
    background-color: var(--navy-hover);
    color: var(--white);
    border-color: var(--navy-hover);
}

/* The five page buttons share one height, so the row looks even */
.stApp [class*="st-key-nav_"] .stButton > button {
    min-height: 88px;
}

/* ---------- 12. A 3px outline on whatever the Tab key reaches ---------- */
.stApp *:focus-visible,
[data-baseweb="popover"] *:focus-visible {
    outline: 3px solid var(--navy) !important;
    outline-offset: 3px !important;
}
/* Choices and the checkbox: outline the whole box, not the hidden dot */
.stApp label:has(input:focus-visible) {
    outline: 3px solid var(--navy) !important;
    outline-offset: 3px !important;
}
/* The drop-down */
.stApp [data-baseweb="select"]:focus-within > div {
    outline: 3px solid var(--navy) !important;
    outline-offset: 3px !important;
}

/* ---------- 13. No sidebar and no hidden menus ---------- */
/* Streamlit's own menu, Deploy button, colored top line, footer and sidebar */
#MainMenu,
footer,
[data-testid="stMainMenu"],
[data-testid="stAppDeployButton"],
[data-testid="stDecoration"],
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    display: none !important;
}
/* Streamlit's top bar stays, but see-through, so its small "Running…" and
   "Connecting…" message can still show in the top right corner. Without it,
   a stopped or stuck app looks like a blank page.
   Clicks pass through the bar to the page below; only the message reacts. */
header[data-testid="stHeader"] {
    background: transparent !important;
    pointer-events: none;
}
header[data-testid="stHeader"] [data-testid="stStatusWidget"] {
    pointer-events: auto;
}

/* ---------- 14. Full-width bands (Welcome view and the footer) ---------- */
/* A band's key starts with "band_" in welcome.py or footer.py.
   It reaches past the side margins, all the way to both edges of the window. */
.stApp [class*="st-key-band_"] {
    width: calc(100% + 2 * var(--side-margin)) !important;
    max-width: none !important;
    margin-left: calc(-1 * var(--side-margin)) !important;
    margin-right: calc(-1 * var(--side-margin)) !important;
    padding: 64px var(--side-margin) !important;
    margin-bottom: calc(var(--section-space) - var(--text-space));
}

/* A white band ("band_light_"): the six labels */
.stApp [class*="st-key-band_light_"] {
    background-color: var(--card);
    border-top: 1px solid var(--card-border);
    border-bottom: 1px solid var(--card-border);
}

/* A navy band ("band_dark_"): the headline and the footer. All text turns white. */
.stApp [class*="st-key-band_dark_"] {
    background-color: var(--navy);
}
.stApp [class*="st-key-band_dark_"] h1,
.stApp [class*="st-key-band_dark_"] h2,
.stApp [class*="st-key-band_dark_"] h3,
.stApp [class*="st-key-band_dark_"] h4 {
    color: var(--white) !important;
}
.stApp [class*="st-key-band_dark_"] p,
.stApp [class*="st-key-band_dark_"] li,
.stApp [class*="st-key-band_dark_"] strong {
    color: var(--white);
}
.stApp [class*="st-key-band_dark_"] a {
    color: var(--white) !important;
}
/* On navy, the Tab outline is white, so it can still be seen */
.stApp [class*="st-key-band_dark_"] *:focus-visible {
    outline-color: var(--white) !important;
}
/* Buttons on navy: outlined ones are white lines with white words */
.stApp [class*="st-key-band_dark_"] .stButton > button {
    background-color: transparent;
    color: var(--white);
    border-color: var(--white);
}
.stApp [class*="st-key-band_dark_"] .stButton > button:hover,
.stApp [class*="st-key-band_dark_"] .stButton > button:active {
    background-color: var(--navy-soft);
    color: var(--white);
    border-color: var(--white);
}
/* ...and primary ones are filled white with navy words */
.stApp [class*="st-key-band_dark_"] .stButton > button[kind="primary"],
.stApp [class*="st-key-band_dark_"] .stButton > button[data-testid="stBaseButton-primary"] {
    background-color: var(--white);
    color: var(--navy);
    border-color: var(--white);
}
.stApp [class*="st-key-band_dark_"] .stButton > button[kind="primary"]:hover,
.stApp [class*="st-key-band_dark_"] .stButton > button[kind="primary"]:active,
.stApp [class*="st-key-band_dark_"] .stButton > button[data-testid="stBaseButton-primary"]:hover,
.stApp [class*="st-key-band_dark_"] .stButton > button[data-testid="stBaseButton-primary"]:active {
    background-color: var(--tint);
    color: var(--navy);
    border-color: var(--tint);
}

/* ---------- 15. The headline band ---------- */
.stApp .st-key-band_dark_hero {
    padding-top: 80px !important;
    padding-bottom: 80px !important;
    border-bottom: 2px solid var(--gold);
}
/* The headline: larger than a normal page title, on about two lines */
.stApp .st-key-band_dark_hero h1 {
    font-size: 60px !important;
    line-height: 1.15 !important;
    max-width: 20ch;
}
.stApp .st-key-band_dark_hero p {
    font-size: 26px;
    line-height: 1.5;
}
/* The two big buttons sit side by side, not stretched across the whole window */
.stApp .st-key-hero_buttons {
    max-width: 760px;
    margin-top: 12px;
}
.stApp .st-key-hero_buttons .stButton > button {
    min-height: 76px;
}
.stApp .st-key-hero_buttons .stButton > button p {
    font-size: 26px !important;
}

/* ---------- 16. Sections on the Welcome view ---------- */
/* About 48px below each section, like the cards */
.stApp [class*="st-key-section_"] {
    margin-bottom: calc(var(--section-space) - var(--text-space));
}

/* How it works: three white boxes in a row */
.stApp .step-grid {
    list-style: none;
    margin: 0 !important;
    padding: 0 !important;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 24px;
}
.stApp .step-grid li {
    max-width: none !important;
    margin: 0;
    padding: 32px;
    background-color: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
}
.stApp .step-top {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: var(--text-space);
}
/* The step number in a circle: a shape AND a number */
.stApp .step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    flex: none;
    border: 2px solid var(--navy);
    border-radius: 50%;
    color: var(--navy);
    font-size: 24px;
    font-weight: 700;
}
/* The navy line icon */
.stApp .step-icon {
    width: 56px;
    height: 56px;
    flex: none;
    color: var(--navy);
}
.stApp h3.step-title {
    font-size: 28px !important;
    margin: 0 0 12px 0 !important;
}
.stApp .step-grid p {
    margin: 0 !important;
}

/* The six labels: six boxes in a row on a wide screen */
.stApp .tier-grid {
    list-style: none;
    margin: 0 !important;
    padding: 0 !important;
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 16px;
}
.stApp .tier-grid li {
    max-width: none !important;
    margin: 0;
    padding: 24px 20px;
    background-color: var(--page);
    border: 1px solid var(--card-border);
    border-radius: 12px;
}
.stApp .tier-grid p {
    margin: 0 0 8px 0 !important;
}
.stApp .tier-number {
    font-size: 20px !important;
    font-weight: 700;
    color: var(--text-secondary) !important;
}
.stApp .tier-icon {
    font-size: 28px !important;
    line-height: 1.3 !important;
    overflow-wrap: anywhere;  /* a long row of waves wraps instead of spilling out */
}
.stApp .tier-name {
    font-size: 26px !important;
    line-height: 1.25 !important;
    font-weight: 700;
    color: var(--navy) !important;
}
.stApp .tier-waves {
    font-size: 22px !important;
}

/* ---------- 17. The footer ---------- */
.stApp .st-key-band_dark_footer {
    margin-bottom: 0 !important;
    border-top: 2px solid var(--gold);
}
/* The three help lines, side by side */
.stApp .help-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 32px;
    margin: 0 0 32px 0 !important;
}
.stApp .help-grid p {
    margin: 0 0 8px 0 !important;
}
.stApp .help-name {
    font-size: 24px !important;
    font-weight: 700;
}
.stApp .help-number {
    font-size: 30px !important;
    font-weight: 700;
    letter-spacing: 1px;
}

/* ---------- 18. Card grids (Explore products and Your situation) ---------- */
/* A grid's key starts with "grid_" in app.py. The cards inside line up in rows,
   and every card in a row is as tall as the tallest one.
   --grid-columns says how many cards fit in one row. */
.stApp [class*="st-key-grid_"] {
    display: grid !important;
    grid-template-columns: repeat(var(--grid-columns, 2), minmax(0, 1fr));
    gap: 24px !important;
    align-items: stretch;
    margin-bottom: calc(var(--section-space) - var(--text-space));
}
.stApp .st-key-grid_products {
    --grid-columns: 3;
}
.stApp .st-key-grid_questions {
    --grid-columns: 2;
}
/* Each box in the grid stretches to the height of its row... */
.stApp [class*="st-key-grid_"] > * {
    display: flex;
    flex-direction: column;
    min-width: 0;
    width: auto !important;
}
/* ...and the card inside it fills that whole height */
.stApp [class*="st-key-grid_"] [class*="st-key-card_"] {
    flex: 1 1 auto;
    margin-bottom: 0 !important;
}
/* Explore products: the Compare box always sits at the bottom of its card,
   so the boxes line up across a row */
.stApp .st-key-grid_products [class*="st-key-card_"] > :last-child {
    margin-top: auto;
}

/* ---------- 19. Two parts side by side ---------- */
/* A split's key starts with "split_" in app.py or welcome.py.
   On a wide screen the left part (usually the page's words) is a little wider,
   and the right part (usually a card with the next step) fills the rest of the row,
   so the right side of the window is never empty. */
.stApp [class*="st-key-split_"] {
    display: grid !important;
    grid-template-columns: minmax(0, 7fr) minmax(0, 5fr);
    gap: var(--section-space) !important;
    align-items: start;
    margin-bottom: calc(var(--section-space) - var(--text-space));
}
.stApp [class*="st-key-split_"] > * {
    min-width: 0;
    width: auto !important;
}
.stApp [class*="st-key-split_"] [class*="st-key-card_"],
.stApp [class*="st-key-split_"] [class*="st-key-section_"] {
    margin-bottom: 0 !important;
}
/* The words on the left start at the same height as the title inside
   the card on the right (the card's inside space plus its 1px border). */
.stApp .st-key-explore_intro,
.stApp .st-key-compare_intro,
.stApp .st-key-split_welcome .st-key-section_faq {
    padding-top: calc(var(--card-padding) + 1px);
}
/* The scam card and the help card: two equal halves */
.stApp .st-key-split_safety {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

/* ---------- 20. The Compare table ---------- */
/* The table sits in a box that slides sideways if it is wider than the window.
   The box can be reached with the Tab key, then moved with the arrow keys. */
.stApp .cmp-scroll {
    width: 100%;
    overflow-x: auto;
    background-color: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
}
.stApp .cmp-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}
.stApp .cmp-table th,
.stApp .cmp-table td {
    min-width: 260px;
    padding: 20px 24px;
    text-align: left;
    vertical-align: top;
    font-size: 22px;
    line-height: 1.5;
    color: var(--text);
    border-bottom: 1px solid var(--card-border);
}
/* The product names: large column headings, with a thick navy line under them */
.stApp .cmp-table thead th {
    font-size: 28px;
    font-weight: 700;
    line-height: 1.3;
    color: var(--navy);
    vertical-align: bottom;
    background-color: var(--card);
    border-bottom: 3px solid var(--navy);
}
/* The empty-looking top-left corner */
.stApp .cmp-table thead th.cmp-corner {
    font-size: 20px;
    color: var(--text-secondary);
}
/* Each row's label: bold, on the left */
.stApp .cmp-table tbody th {
    font-weight: 700;
    min-width: 240px;
    width: 240px;
}
/* Rows take turns: white, then light gray (row lines show the rows too) */
.stApp .cmp-table tbody tr:nth-child(odd) > * {
    background-color: var(--card);
}
.stApp .cmp-table tbody tr:nth-child(even) > * {
    background-color: var(--row-alt);
}
.stApp .cmp-table tbody tr:last-child > * {
    border-bottom: none;
}
/* The label column stays in place while the products slide sideways */
.stApp .cmp-table th:first-child {
    position: sticky;
    left: 0;
    z-index: 1;
    border-right: 1px solid var(--card-border);
}
/* The yes / no marks, always next to a word */
.stApp .cmp-icon {
    font-size: 24px;
    color: var(--navy);
}

/* ---------- 21. Smaller windows ---------- */
/* Medium windows: the six labels in rows of three, two product cards per row */
@media (max-width: 1499px) {
    .stApp .tier-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}
@media (max-width: 1199px) {
    .stApp .st-key-grid_products {
        --grid-columns: 2;
    }
}
@media (max-width: 1100px) {
    .stApp .tier-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
/* Every split: one column, left part first */
@media (max-width: 999px) {
    .stApp [class*="st-key-split_"] {
        grid-template-columns: minmax(0, 1fr) !important;
    }
    /* Stacked, the words no longer need to line up with a card beside them */
    .stApp .st-key-explore_intro,
    .stApp .st-key-compare_intro,
    .stApp .st-key-split_welcome .st-key-section_faq {
        padding-top: 0;
    }
}
/* Narrow windows: steps, help lines, question cards and the three ways
   go one under another */
@media (max-width: 899px) {
    .stApp .step-grid,
    .stApp .help-grid {
        grid-template-columns: minmax(0, 1fr);
    }
    .stApp .st-key-grid_questions {
        --grid-columns: 1;
    }
    .stApp .st-key-card_offer_way [role="radiogroup"] {
        grid-template-columns: minmax(0, 1fr);
    }
}
/* Phones: every row stacks into one column */
@media (max-width: 640px) {
    :root {
        --card-padding: 20px;
    }
    .stApp [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        flex-wrap: nowrap !important;
    }
    .stApp [data-testid="stHorizontalBlock"] > * {
        width: 100% !important;
        min-width: 100% !important;
        flex: 1 1 auto !important;
    }
    .stApp [class*="st-key-grid_"] {
        --grid-columns: 1;
    }
    .stApp .tier-grid {
        grid-template-columns: minmax(0, 1fr);
    }
    .stApp [class*="st-key-band_"] {
        padding-top: 40px !important;
        padding-bottom: 40px !important;
    }
    .stApp .step-grid li {
        padding: 20px;
    }
    .stApp .st-key-notice_top {
        padding: 16px 20px;
    }
    .stApp .st-key-band_dark_hero h1 {
        font-size: 44px !important;
    }
    /* The Compare table: narrower columns, and the label column slides too */
    .stApp .cmp-table th,
    .stApp .cmp-table td {
        min-width: 200px;
        padding: 16px;
    }
    .stApp .cmp-table tbody th {
        min-width: 170px;
        width: 170px;
    }
    .stApp .cmp-table th:first-child {
        position: static;
    }
}
</style>
"""


def apply_styles():
    """Add Second Look's look and feel to the page.
    Call this once, right after st.set_page_config in app.py."""
    st.markdown(CSS, unsafe_allow_html=True)