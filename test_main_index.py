"""
Structure & content tests for the portfolio index.html.

These tests parse the HTML and verify that the page's structure, navigation,
project cards, links, and meta information are all intact — a bit like running
a gel check before you submit a cloning result.  If you rename an id, remove a
section, or break a link, one of these will catch it.

Run with:
    pip install pytest beautifulsoup4
    pytest test_index.py -v
"""

import re
import pytest
from pathlib import Path
from bs4 import BeautifulSoup

# ── Load the page once ────────────────────────────────────────────────────────

HTML_FILE = Path(__file__).parent / "index.html"


@pytest.fixture(scope="session")
def soup():
    """
    Parse index.html with BeautifulSoup once and reuse across all tests.

    Why BeautifulSoup instead of regex here?  Unlike the DATA array in the NGT
    tracker (a single flat JS literal), a full HTML page has deeply nested
    structure — a proper parser is the right tool, just as you'd use a sequence
    aligner rather than grep for a multi-exon search.
    """
    html = HTML_FILE.read_text(encoding="utf-8")
    return BeautifulSoup(html, "html.parser")


# ── Meta & head ───────────────────────────────────────────────────────────────

def test_page_title_is_set(soup):
    """<title> must be non-empty — blank titles look unprofessional to recruiters."""
    title = soup.find("title")
    assert title and title.get_text(strip=True), "Page <title> is missing or empty"


def test_page_title_contains_name(soup):
    title = soup.find("title").get_text()
    assert "Youlia" in title or "Denisov" in title, (
        f"Page title '{title}' doesn't contain the author's name"
    )


def test_charset_utf8(soup):
    """<meta charset='UTF-8'> must be present — missing charset can mangle special chars."""
    meta = soup.find("meta", attrs={"charset": True})
    assert meta, "No <meta charset> tag found"
    assert meta["charset"].upper() == "UTF-8", f"Expected UTF-8, got {meta['charset']}"


def test_viewport_meta_exists(soup):
    """Viewport meta is required for mobile-responsive layout."""
    meta = soup.find("meta", attrs={"name": "viewport"})
    assert meta, "Missing <meta name='viewport'> — page won't be mobile-friendly"

# ── Detection of images ───────────────────────────────────────────────────────

def test_image_paths_exist(soup):
    """Images must be in the location stated in the code."""
    imgs = soup.find_all("img", src=True)
    local_imgs = [img["src"] for img in imgs if not img["src"].startswith("http")]
    missing = [src for src in local_imgs if not (HTML_FILE.parent / src).exists()]
    assert not missing, f"Image files not found on disk: {missing}"

    
# ── Navigation ────────────────────────────────────────────────────────────────

EXPECTED_NAV_ANCHORS = {"#about", "#projects", "#resume", "#contact"}

def test_nav_exists(soup):
    assert soup.find("nav"), "No <nav> element found"


def test_nav_links_present(soup):
    """
    All four section anchors must be present in the nav.
    Missing a link here = that section is invisible to visitors who scan the nav.
    """
    nav = soup.find("nav")
    hrefs = {a["href"] for a in nav.find_all("a", href=True)}
    missing = EXPECTED_NAV_ANCHORS - hrefs
    assert not missing, f"Nav is missing links to: {missing}"


# ── Required sections ─────────────────────────────────────────────────────────

REQUIRED_SECTION_IDS = ["hero", "about", "projects", "resume", "contact"]

@pytest.mark.parametrize("section_id", REQUIRED_SECTION_IDS)
def test_section_exists(soup, section_id):
    """
    Each section the nav links to must actually exist in the DOM.
    A broken anchor scrolls nowhere — like a citation pointing to a retracted paper.
    """
    assert soup.find(id=section_id), f"Section id='{section_id}' not found in page"


# ── Hero section ──────────────────────────────────────────────────────────────

def test_hero_has_name(soup):
    hero = soup.find(id="hero")
    assert hero, "Hero section missing"
    h1 = hero.find("h1")
    assert h1, "No <h1> in hero section"
    name_text = h1.get_text()
    assert "Youlia" in name_text or "Denisov" in name_text, (
        f"Hero <h1> doesn't contain the author's name: '{name_text}'"
    )


def test_hero_has_cta_buttons(soup):
    """Hero must have at least one call-to-action button."""
    hero = soup.find(id="hero")
    buttons = hero.find_all("a", class_=re.compile(r"btn"))
    assert len(buttons) >= 1, "Hero section has no CTA buttons"


# ── Projects section ──────────────────────────────────────────────────────────

def test_projects_section_has_cards(soup):
    """There must be at least one project card — an empty portfolio defeats the purpose."""
    projects = soup.find(id="projects")
    cards = projects.find_all(class_="project-card")
    assert len(cards) >= 1, "No project cards found in #projects"


def test_every_card_has_a_title(soup):
    """
    Every project card must have a non-empty title.
    A blank project-title is like a figure with no caption — readers don't know what they're looking at.
    """
    projects = soup.find(id="projects")
    cards = projects.find_all(class_="project-card")
    empty_titles = [
        i for i, card in enumerate(cards)
        if not card.find(class_="project-title") or
           not card.find(class_="project-title").get_text(strip=True)
    ]
    assert not empty_titles, f"Cards at indices {empty_titles} have empty or missing titles"


def test_every_card_has_a_description(soup):
    """Project description must be present and non-empty."""
    projects = soup.find(id="projects")
    cards = projects.find_all(class_="project-card")
    empty_descs = [
        i for i, card in enumerate(cards)
        if not card.find(class_="project-desc") or
           not card.find(class_="project-desc").get_text(strip=True)
    ]
    assert not empty_descs, f"Cards at indices {empty_descs} have empty descriptions"


def test_every_card_has_a_type_badge(soup):
    """Each card should have a project-type badge (e.g. 'Streamlit App', 'Machine Learning')."""
    projects = soup.find(id="projects")
    cards = projects.find_all(class_="project-card")
    missing = [
        i for i, card in enumerate(cards)
        if not card.find(class_="project-type") or
           not card.find(class_="project-type").get_text(strip=True)
    ]
    assert not missing, f"Cards at indices {missing} are missing a project-type badge"


def test_every_card_has_tech_pills(soup):
    """
    Each card should list at least one technology pill.
    No pills = recruiters can't quickly scan what stack was used.
    """
    projects = soup.find(id="projects")
    cards = projects.find_all(class_="project-card")
    no_pills = [
        i for i, card in enumerate(cards)
        if not card.find(class_="tech-pill")
    ]
    assert not no_pills, f"Cards at indices {no_pills} have no tech pills"


def test_live_project_links_are_not_placeholder(soup):
    """
    Links that say 'Live demo' or 'Live dashboard' must not point to '#'.
    A broken live link is the first thing a recruiter clicks.
    """
    projects = soup.find(id="projects")
    bad = []
    for a in projects.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        if ("live" in text or "demo" in text) and a["href"].strip() == "#":
            bad.append(a.get_text(strip=True))
    assert not bad, f"These 'live' links still point to '#': {bad}"


def test_known_tech_stacks_represented(soup):
    """
    Python and JavaScript should appear somewhere in the tech pills —
    sanity check that the stack section hasn't been accidentally cleared.
    """
    projects = soup.find(id="projects")
    pills_text = " ".join(p.get_text() for p in projects.find_all(class_="tech-pill")).lower()
    assert "python" in pills_text, "Python not found in any tech pills"
    assert "javascript" in pills_text or "js" in pills_text, (
        "JavaScript not found in any tech pills"
    )


# ── Contact section ───────────────────────────────────────────────────────────

def test_email_link_present(soup):
    contact = soup.find(id="contact")
    email_link = contact.find("a", href=re.compile(r"^mailto:"))
    assert email_link, "No mailto: link found in #contact"


def test_email_link_correct(soup):
    contact = soup.find(id="contact")
    email_link = contact.find("a", href=re.compile(r"^mailto:"))
    assert "youlia.denisov@gmail.com" in email_link["href"], (
        f"Email link points to wrong address: {email_link['href']}"
    )


def test_linkedin_link_present(soup):
    contact = soup.find(id="contact")
    linkedin = contact.find("a", href=re.compile(r"linkedin\.com", re.I))
    assert linkedin, "No LinkedIn link found in #contact"


def test_github_link_present(soup):
    contact = soup.find(id="contact")
    github = contact.find("a", href=re.compile(r"github\.com", re.I))
    assert github, "No GitHub link found in #contact"


def test_external_contact_links_open_in_new_tab(soup):
    """
    External links (LinkedIn, GitHub) should have target='_blank' so the
    portfolio page isn't replaced when a recruiter clicks through.
    """
    contact = soup.find(id="contact")
    external = [
        a for a in contact.find_all("a", href=True)
        if a["href"].startswith("http")
    ]
    bad = [a["href"] for a in external if a.get("target") != "_blank"]
    assert not bad, f"External contact links missing target='_blank': {bad}"


# ── Resume section ────────────────────────────────────────────────────────────

def test_resume_pdf_link_exists(soup):
    resume = soup.find(id="resume")
    pdf_link = resume.find("a", href=re.compile(r"\.pdf$", re.I))
    assert pdf_link, "No .pdf link found in #resume section"


def test_resume_pdf_has_download_attribute(soup):
    """
    The download attribute triggers a save dialog instead of opening in-browser —
    important for recruiters who want to save your CV quickly.
    """
    resume = soup.find(id="resume")
    pdf_link = resume.find("a", href=re.compile(r"\.pdf$", re.I))
    assert pdf_link and pdf_link.has_attr("download"), (
        "Resume PDF link is missing the 'download' attribute"
    )


# ── About section ─────────────────────────────────────────────────────────────

def test_about_has_content(soup):
    about = soup.find(id="about")
    text = about.get_text(strip=True)
    assert len(text) > 100, "About section seems too short or empty"


def test_about_has_skill_tags(soup):
    """The skills block should list at least a few technologies."""
    about = soup.find(id="about")
    tags = about.find_all(class_="skill-tag")
    assert len(tags) >= 3, f"Only {len(tags)} skill tag(s) found in #about — expected at least 3"


# ── Page-level summary ────────────────────────────────────────────────────────

def test_page_profile(soup, capsys):
    """
    Non-pass/fail: prints a quick inventory of the page.
    Like a describe() call — useful for spotting drift over time.

    Run with: pytest test_index.py::test_page_profile -v -s
    """
    projects   = soup.find(id="projects")
    cards      = projects.find_all(class_="project-card")
    all_pills  = projects.find_all(class_="tech-pill")
    all_links  = soup.find_all("a", href=True)
    ext_links  = [a for a in all_links if a["href"].startswith("http")]

    print("\n── Portfolio Index Profile ───────────────────")
    print(f"  Page title    : {soup.find('title').get_text(strip=True)}")
    print(f"  Sections      : {', '.join(s['id'] for s in soup.find_all(id=True) if s.name == 'section')}")
    print(f"  Project cards : {len(cards)}")

    print(f"\n  Projects:")
    for card in cards:
        title     = card.find(class_="project-title")
        badge     = card.find(class_="project-type")
        pill_list = [p.get_text(strip=True) for p in card.find_all(class_="tech-pill")]
        print(f"    [{badge.get_text(strip=True) if badge else '?':25s}] "
              f"{title.get_text(strip=True) if title else 'NO TITLE'}")
        print(f"      Stack: {', '.join(pill_list)}")

    print(f"\n  Total links   : {len(all_links)}")
    print(f"  External links: {len(ext_links)}")
    print(f"  Skill tags    : {len(soup.find_all(class_='skill-tag'))}")
    print("──────────────────────────────────────────────")

    assert True  # always passes — inspection only
