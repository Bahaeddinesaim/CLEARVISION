from __future__ import annotations

import html
from urllib.parse import quote_plus
import streamlit as st


def topbar(page: str, subtitle: str, live_label: str = "Live pipeline") -> None:
    """Render a polished app topbar."""
    st.markdown(
        f"""
        <div class="cv-topbar">
          <div>
            <div class="cv-page-title">{html.escape(page)}</div>
            <div class="cv-page-subtitle">{html.escape(subtitle)}</div>
          </div>
          <div class="cv-actions">
            <span class="cv-live"><i></i>{html.escape(live_label)}</span>
            <span class="cv-action secondary">Import image</span>
            <span class="cv-action primary">New scan</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(score: float = 0, analyses: int = 0, anomalies: int = 0) -> None:
    """Render a compact product header inspired by the provided mockup."""
    st.markdown(
        f"""
        <div class="app-hero">
          <div class="hero-grid">
            <div>
              <div class="eyebrow">Live pipeline</div>
              <h1>Executive Dashboard</h1>
              <p>Diagnostic par photo: presence, equipements, anomalies et qualite de detection.
              L'historique reste conserve, mais le risque affiche vient de la derniere image.</p>
            </div>
            <div class="hero-status">
              <div class="status-chip"><span>Health score</span><b>{score:.0f}/100</b></div>
              <div class="status-chip"><span>Analyses</span><b>{analyses}</b></div>
              <div class="status-chip"><span>Anomalies photo</span><b>{anomalies}</b></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def horizontal_nav(active_page: str, pages: list[str]) -> None:
    """Render horizontally scrollable navigation cards."""
    meta = {
        "Executive Dashboard": ("Command Center", "Global score, risk and trends", "01", "blue"),
        "Detection Studio": ("Scan Studio", "Upload and analyze a photo", "02", "green"),
        "Audio Noise Detection": ("Noise Lab", "Audio signal analysis", "03", "amber"),
        "Inventory Analytics": ("Inventory", "Objects, gaps and compliance", "04", "violet"),
        "Anomaly Center": ("Anomalies", "Photo-scoped alerts", "05", "red"),
        "Governance Center": ("Governance", "Pipeline and persistence", "06", "amber"),
        "Data Catalog": ("Catalog", "Fields and quality rules", "07", "blue"),
        "Historical Analyses": ("History", "Saved photos and scans", "08", "green"),
        "Data Quality": ("Quality", "Confidence and consistency", "09", "violet"),
        "Settings": ("Settings", "Classroom constraints", "10", "amber"),
    }
    cards = []
    for page in pages:
        title, subtitle, num, tone = meta.get(page, (page, "Open workspace", "00", "blue"))
        active = "active" if page == active_page else ""
        cards.append(
            "<a class='cv-nav-card {tone} {active}' href='?page={href}'>"
            "<span class='cv-nav-num'>{num}</span>"
            "<strong>{title}</strong>"
            "<small>{subtitle}</small>"
            "</a>".format(
                tone=html.escape(tone),
                active=html.escape(active),
                href=quote_plus(page),
                num=html.escape(num),
                title=html.escape(title),
                subtitle=html.escape(subtitle),
            )
        )
    nav_html = (
        "<div class='cv-nav-shell'>"
        "<div class='cv-nav-label'>Workspace navigation</div>"
        "<div class='cv-nav-scroll'>"
        + "".join(cards)
        + "</div></div>"
    )
    st.markdown(nav_html, unsafe_allow_html=True)


def health_panel(
    score: float,
    grade: str,
    risk: str,
    inventory: float,
    conformity: float,
    confidence: float,
    occupancy: float,
) -> None:
    """Render the circular health score panel."""
    pct = max(0, min(100, float(score)))
    offset = 251.2 - (251.2 * pct / 100)
    rows = [
        ("Inventory", inventory, "green"),
        ("Conformity", conformity, "blue"),
        ("Confidence", confidence, "violet"),
        ("Occupancy", occupancy, "amber"),
    ]
    bars = "".join(
        f"""
        <div class="cv-bar-row">
          <div class="cv-bar-label">{html.escape(label)}</div>
          <div class="cv-bar-track"><div class="cv-bar-fill {klass}" style="width:{max(0, min(100, value)):.0f}%"></div></div>
          <div class="cv-bar-value">{max(0, min(100, value)):.0f}%</div>
        </div>
        """
        for label, value, klass in rows
    )
    st.markdown(
        f"""
        <div class="cv-panel cv-health">
          <div class="cv-card-head"><span>Classroom health score</span><b>Latest photo</b></div>
          <div class="cv-score-ring">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" class="ring-bg"></circle>
              <circle cx="50" cy="50" r="40" class="ring-fg" style="stroke-dashoffset:{offset:.1f}"></circle>
            </svg>
            <div class="cv-score-number"><strong>{pct:.0f}</strong><span>/ 100</span></div>
          </div>
          <div class="cv-grade">Grade {html.escape(str(grade))}</div>
          <div class="cv-risk">Risk level: {html.escape(str(risk))}</div>
          <div class="cv-bars">{bars}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def detected_objects_panel(inventory_rows: list[dict], total: int) -> None:
    """Render a premium detected objects list."""
    if not inventory_rows:
        inventory_rows = [{"name": "No detections", "count": 0, "sub": "Import a photo", "confidence": 0, "tone": "blue"}]
    body = "".join(
        f"""
        <div class="cv-det-row">
          <div class="cv-det-icon {html.escape(str(row.get('tone', 'blue')))}">{html.escape(str(row.get('icon', row.get('name', '?')))[0:2].upper())}</div>
          <div class="cv-det-info">
            <div class="cv-det-name">{html.escape(str(row.get('name', 'Object')))}</div>
            <div class="cv-det-sub">{html.escape(str(row.get('sub', 'Detected object')))}</div>
          </div>
          <div class="cv-det-count">{html.escape(str(row.get('count', 0)))}</div>
          <div class="cv-conf">{float(row.get('confidence', 0)):.0f}%</div>
        </div>
        """
        for row in inventory_rows[:7]
    )
    st.markdown(
        f"""
        <div class="cv-panel">
          <div class="cv-card-head"><span>Detected objects</span><b>{total} total</b></div>
          {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def anomaly_cards(anomalies: list[dict]) -> None:
    """Render anomaly cards without relying on dataframe styling."""
    if not anomalies:
        anomalies = [{"severity": "low", "title": "No anomaly detected", "description": "Latest photo looks compliant.", "meta": "Photo scope"}]
    cards = "".join(
        f"""
        <div class="cv-anom-row">
          <span class="cv-sev {html.escape(str(item.get('severity', 'low')).lower())}">{html.escape(str(item.get('severity', 'low')).upper())}</span>
          <div>
            <div class="cv-anom-title">{html.escape(str(item.get('title', 'Anomaly')))}</div>
            <div class="cv-anom-desc">{html.escape(str(item.get('description', '')))}</div>
            <div class="cv-anom-meta">{html.escape(str(item.get('meta', 'Latest photo')))}</div>
          </div>
        </div>
        """
        for item in anomalies[:6]
    )
    st.markdown(
        f"""
        <div class="cv-panel">
          <div class="cv-card-head"><span>Anomaly center</span><b>Photo diagnosis</b></div>
          {cards}
        </div>
        """,
        unsafe_allow_html=True,
    )


def pipeline_panel(raw_count: int, bronze_count: int, silver_count: int, gold_count: int) -> None:
    """Render the medallion pipeline status."""
    rows = [("RAW", raw_count, "green"), ("BRONZE", bronze_count, "blue"), ("SILVER", silver_count, "violet"), ("GOLD", gold_count, "amber")]
    body = "".join(
        f"""
        <div class="cv-pipe-row">
          <span><i class="{klass}"></i>{name}</span>
          <b>{count} rows</b>
        </div>
        """
        for name, count, klass in rows
    )
    st.markdown(
        f"""
        <div class="cv-panel">
          <div class="cv-card-head"><span>Pipeline status</span><b class="ok">Healthy</b></div>
          {body}
          <div class="cv-catalog">
            <span>Catalog coverage</span>
            <div class="cv-wide-track"><div style="width:96%"></div></div>
            <b>96%</b>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi(label: str, value: object, sub: str = "", icon: str = "*") -> None:
    """Render a compact KPI card."""
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))
    safe_sub = html.escape(str(sub))
    safe_icon = html.escape(str(icon))
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-label">{safe_label}</div>
            <div class="kpi-icon">{safe_icon}</div>
          </div>
          <div class="kpi-value">{safe_value}</div>
          <div class="kpi-sub">{safe_sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, body: str) -> None:
    """Render a glass card for contextual content."""
    st.markdown(
        f"""
        <div class="glass-card">
          <div class="section-title">{html.escape(title)}</div>
          <div class="soft-text">{html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "") -> None:
    """Render a section title with optional supporting text."""
    subtitle_html = f"<div class='section-subtitle'>{html.escape(subtitle)}</div>" if subtitle else ""
    st.markdown(f"<div class='section-title'>{html.escape(title)}</div>{subtitle_html}", unsafe_allow_html=True)


def severity_badge(severity: str) -> str:
    """Return a styled severity badge as HTML."""
    normalized = str(severity).strip().lower()
    klass = {
        "low": "success",
        "medium": "warn",
        "high": "danger",
        "critical": "danger",
    }.get(normalized, "violet")
    return f"<span class='badge {klass}'>{html.escape(str(severity).title())}</span>"
